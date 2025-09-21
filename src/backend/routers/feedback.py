from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import Dict, Any, List, Optional
import os
import json
import time
from loguru import logger
import asyncio
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from backend.models.feedback import (
    RateDecisionDataRequest, RefineDecisionDataRequest, FeedbackResponse,
    UpdateDecisionDataRequest, SaveDecisionDataRequest, SaveResponse  # 添加新的响应模型
)
from backend.utils.model_management import load_model_if_needed
from llm_tuning.data_processing_pipeline import verify_data, analyze_reasons, refine_data

# Import SIMULATION_REGISTRY from simulation module
from backend.routers.simulation import SIMULATION_REGISTRY

router = APIRouter(
    tags=["feedback"],
    prefix="/feedback"
)

# 为每个环境创建独立的锁，以防止_pending_decisions的并发修改
ENV_LOCKS = {}
# 使用线程池执行耗时操作
THREAD_POOL = ThreadPoolExecutor(max_workers=4)
# 保存任务状态
TASK_STATUS = {}

def get_env_lock(env_name):
    """获取或创建环境锁"""
    if env_name not in ENV_LOCKS:
        ENV_LOCKS[env_name] = asyncio.Lock()
    return ENV_LOCKS[env_name]

@router.get("/decisions", response_model=FeedbackResponse)
async def get_decisions(env_name: str):
    """获取决策数据"""
    # 检查环境是否存在
    env_path = os.path.join("src", "envs", env_name)
    if not os.path.exists(env_path):
        raise HTTPException(status_code=404, detail=f"环境 '{env_name}' 不存在")
    
    try:
        # Access environment from SIMULATION_REGISTRY
        if env_name not in SIMULATION_REGISTRY:
            raise HTTPException(status_code=404, detail=f"环境 '{env_name}' 未运行或不可用")
        
        registry = SIMULATION_REGISTRY[env_name]
        sim_env = registry.get("sim_env")
        
        if not sim_env:
            raise HTTPException(status_code=404, detail=f"环境 '{env_name}' 的模拟环境未初始化")
        
        # Get pending decisions from the environment
        decisions = getattr(sim_env, '_pending_decisions', [])
        
        
        return FeedbackResponse(
            success=True,
            message=f"成功获取 {len(decisions)} 条决策数据",
            data=decisions
        )
    except Exception as e:
        logger.error(f"获取决策数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取决策数据失败: {str(e)}")

@router.post("/update", response_model=FeedbackResponse)
async def update_decision_data(request: UpdateDecisionDataRequest):
    """更新决策数据"""
    env_name = request.env_name
    updated_data = request.updated_data
    
    # 检查环境是否存在
    env_path = os.path.join("src", "envs", env_name)
    if not os.path.exists(env_path):
        raise HTTPException(status_code=404, detail=f"环境 '{env_name}' 不存在")
    
    # 检查更新的数据是否为空
    if not updated_data:
        raise HTTPException(status_code=400, detail="未提供任何更新的决策数据")
    
    # 获取模拟环境
    if env_name not in SIMULATION_REGISTRY:
        raise HTTPException(status_code=404, detail=f"环境 '{env_name}' 未运行或不可用")
    
    registry = SIMULATION_REGISTRY[env_name]
    sim_env = registry.get("sim_env")
    
    if not sim_env:
        raise HTTPException(status_code=404, detail=f"环境 '{env_name}' 的模拟环境未初始化")
    
    # 获取环境锁
    env_lock = get_env_lock(env_name)
    
    async with env_lock:
        try:
            # 获取当前_pending_decisions
            all_decisions = getattr(sim_env, '_pending_decisions', [])
            
            # 创建决策ID到索引的映射
            decision_map = {}
            for i, d in enumerate(all_decisions):
                # 使用唯一标识符作为键
                d_id = d.get('decision_id', '')
                if d_id:
                    decision_map[d_id] = i
            
            # 更新决策数据
            updated_count = 0
            for decision in updated_data:
                decision_id = decision.get('decision_id', '')
                if decision_id and decision_id in decision_map:
                    # 整体替换决策数据
                    idx = decision_map[decision_id]
                    all_decisions[idx] = decision
                    updated_count += 1
                    continue
                
                # 如果找不到ID匹配，尝试使用其他方式匹配
                agent_id = decision.get('agent_id')
                decision_made = decision.get('decision_made')
                decision_context = decision.get('decision_context')
                
                if not agent_id:
                    continue
                    
                found = False
                for i, d in enumerate(all_decisions):
                    if (d.get('agent_id') == agent_id and 
                        d.get('decision_made') == decision_made and
                        (not decision_context or d.get('decision_context') == decision_context)):
                        # 整体替换决策数据
                        all_decisions[i] = decision
                        updated_count += 1
                        found = True
                        break
                
            
            # 将更新后的数据写回sim_env
            sim_env._pending_decisions = all_decisions
            
            logger.info(f"已更新 {updated_count} 条决策数据")
            
            return FeedbackResponse(
                success=True,
                message=f"成功更新 {updated_count} 条决策数据",
                data=updated_data
            )
        except Exception as e:
            logger.error(f"更新决策数据失败: {e}")
            raise HTTPException(status_code=500, detail=f"更新决策数据失败: {str(e)}")

@router.post("/rate", response_model=FeedbackResponse)
async def rate_decision_data(request: RateDecisionDataRequest):
    """对决策数据进行评分"""
    env_name = request.env_name
    selected_data = request.selected_data
    model_name = request.model_name
    
    # 检查环境是否存在
    env_path = os.path.join("src", "envs", env_name)
    if not os.path.exists(env_path):
        raise HTTPException(status_code=404, detail=f"环境 '{env_name}' 不存在")
    
    # 检查选择的数据是否为空
    if not selected_data:
        raise HTTPException(status_code=400, detail="未选择任何决策数据")
    
    # 加载模型
    model = await load_model_if_needed(model_name)
    
    # 获取模拟环境
    if env_name not in SIMULATION_REGISTRY:
        raise HTTPException(status_code=404, detail=f"环境 '{env_name}' 未运行或不可用")
    
    registry = SIMULATION_REGISTRY[env_name]
    sim_env = registry.get("sim_env")
    
    if not sim_env:
        raise HTTPException(status_code=404, detail=f"环境 '{env_name}' 的模拟环境未初始化")
    
    try:
        # 在线程池中执行耗时操作 - 同步等待结果
        future = THREAD_POOL.submit(lambda: asyncio.run(verify_data(selected_data, model_name)))
        scores = future.result()  # 这里会阻塞直到评分完成
        
        # 将评分添加到决策数据
        rated_data = []
        for i, decision in enumerate(selected_data):
            decision["rating"] = scores[i]
            rated_data.append(decision)
        
        # 获取环境锁并更新数据
        env_lock = get_env_lock(env_name)
        async with env_lock:
            # 获取当前_pending_decisions
            all_decisions = getattr(sim_env, '_pending_decisions', [])
            
            # 创建决策ID到索引的映射
            decision_map = {}
            for i, d in enumerate(all_decisions):
                # 使用唯一标识符作为键
                d_id = d.get('decision_id', '')
                if d_id:
                    decision_map[d_id] = i
            
            # 更新评分后的数据
            updated_count = 0
            for rated_decision in rated_data:
                decision_id = rated_decision.get('decision_id', '')
                if decision_id and decision_id in decision_map:
                    # 只更新评分相关字段，保留其他字段
                    idx = decision_map[decision_id]
                    all_decisions[idx]['rating'] = rated_decision['rating']
                    updated_count += 1
                    continue
                
                # 如果找不到ID匹配，尝试使用其他方式匹配
                agent_id = rated_decision.get('agent_id')
                decision_made = rated_decision.get('decision_made')
                decision_context = rated_decision.get('decision_context')
                
                if not agent_id:
                    continue
                    
                for i, d in enumerate(all_decisions):
                    if (d.get('agent_id') == agent_id and 
                        d.get('decision_made') == decision_made and
                        (not decision_context or d.get('decision_context') == decision_context)):
                        # 更新评分字段
                        all_decisions[i]['rating'] = rated_decision['rating']
                        updated_count += 1
                        break
            
            # 将更新后的数据写回sim_env
            sim_env._pending_decisions = all_decisions
            
            logger.info(f"已更新 {updated_count} 条决策数据的评分")
        
        # logger.info(f"all_decisions in rate: {all_decisions}")
        # 返回与原接口相同的响应格式
        return FeedbackResponse(
            success=True,
            message=f"成功评分 {len(rated_data)} 条决策数据，更新了 {updated_count} 条记录",
            data=all_decisions
        )
    
    except Exception as e:
        logger.error(f"评分失败: {e}")
        raise HTTPException(status_code=500, detail=f"评分失败: {str(e)}")

@router.post("/refine", response_model=FeedbackResponse)
async def refine_decision_data(request: RefineDecisionDataRequest):
    """优化决策数据"""
    env_name = request.env_name
    selected_data = request.selected_data
    model_name = request.model_name
    
    # 检查环境是否存在
    env_path = os.path.join("src", "envs", env_name)
    if not os.path.exists(env_path):
        raise HTTPException(status_code=404, detail=f"环境 '{env_name}' 不存在")
    
    # 检查选择的数据是否为空
    if not selected_data:
        raise HTTPException(status_code=400, detail="未选择任何决策数据")
    
    # 加载模型
    model = await load_model_if_needed(model_name)
    
    # 获取模拟环境
    if env_name not in SIMULATION_REGISTRY:
        raise HTTPException(status_code=404, detail=f"环境 '{env_name}' 未运行或不可用")
    
    registry = SIMULATION_REGISTRY[env_name]
    sim_env = registry.get("sim_env")
    
    if not sim_env:
        raise HTTPException(status_code=404, detail=f"环境 '{env_name}' 的模拟环境未初始化")
    
    try:
        # 1. 在线程池中执行分析数据质量原因
        scores = [item.get('rating', 0) for item in selected_data]
        future_analysis = THREAD_POOL.submit(lambda: asyncio.run(analyze_reasons(selected_data, scores, threshold=None, model_config=model_name)))
        reason_analysis = future_analysis.result()  # 阻塞等待结果
        
        # 2. 应用分析结果到数据
        for idx, reason in reason_analysis:
            selected_data[idx]['reason'] = reason
        
        # 3. 在线程池中执行refine_data优化数据
        future_refine = THREAD_POOL.submit(lambda: asyncio.run(refine_data(selected_data, reason_analysis, model_name)))
        refined_data = future_refine.result()  # 阻塞等待结果
        
        # 获取环境锁并更新数据
        env_lock = get_env_lock(env_name)
        async with env_lock:
            # 获取当前_pending_decisions
            all_decisions = getattr(sim_env, '_pending_decisions', [])
            
            # 创建决策ID到索引的映射
            decision_map = {}
            for i, d in enumerate(all_decisions):
                # 使用唯一标识符作为键
                d_id = d.get('decision_id', '')
                if d_id:
                    decision_map[d_id] = i
            
            # 更新优化后的数据
            updated_count = 0
            for refined_decision in refined_data:
                decision_id = refined_decision.get('decision_id', '')
                if decision_id and decision_id in decision_map:
                    # 只更新优化相关字段，保留其他字段
                    idx = decision_map[decision_id]
                    # 直接使用reason字段
                    all_decisions[idx]['reason'] = refined_decision.get('reason')
                    all_decisions[idx]['feedback'] = refined_decision.get('feedback')
                    updated_count += 1
                    continue
                
                # 如果找不到ID匹配，尝试使用其他方式匹配
                agent_id = refined_decision.get('agent_id')
                decision_context = refined_decision.get('decision_context')
                
                if not agent_id:
                    continue
                    
                for i, d in enumerate(all_decisions):
                    if (d.get('agent_id') == agent_id and
                        (not decision_context or d.get('decision_context') == decision_context)):
                        # 更新优化字段
                        # 直接使用reason字段
                        all_decisions[i]['reason'] = refined_decision.get('reason')
                        all_decisions[i]['feedback'] = refined_decision.get('feedback')
                        updated_count += 1
                        break
            
            # 将更新后的数据写回sim_env
            sim_env._pending_decisions = all_decisions
            
            logger.info(f"已更新 {updated_count} 条决策数据的优化结果")
        
        # logger.info(f"all_decisions in refine: {all_decisions}")
        # 返回与原接口相同的响应格式
        return FeedbackResponse(
            success=True,
            message=f"成功优化 {len(refined_data)} 条决策数据，更新了 {updated_count} 条记录",
            data=all_decisions
        )
    
    except Exception as e:
        logger.error(f"优化失败: {e}")
        raise HTTPException(status_code=500, detail=f"优化失败: {str(e)}")

# @router.get("/task_status/{task_id}", response_model=FeedbackResponse)
# async def get_task_status(task_id: str):
#     """获取任务状态"""
#     if task_id not in TASK_STATUS:
#         raise HTTPException(status_code=404, detail=f"任务 '{task_id}' 不存在")
    
#     task_info = TASK_STATUS[task_id]
    
#     # 如果任务已完成，返回完整的数据
#     if task_info["status"] == "completed" and "data" in task_info:
#         return FeedbackResponse(
#             success=True,
#             message=task_info["message"],
#             data=task_info["data"]
#         )
    
#     # 否则返回任务状态信息
#     return FeedbackResponse(
#         success=task_info["status"] != "failed",
#         message=task_info["message"],
#         data={
#             "status": task_info["status"],
#             "completed": task_info.get("completed", 0),
#             "total": task_info.get("total", 0)
#         }
#     )

@router.post("/save", response_model=SaveResponse)
async def save_decision_data(request: SaveDecisionDataRequest):
    """保存决策数据到文件"""
    env_name = request.env_name
    
    # 检查环境是否存在
    env_path = os.path.join("src", "envs", env_name)
    if not os.path.exists(env_path):
        raise HTTPException(status_code=404, detail=f"环境 '{env_name}' 不存在")
    
    # 获取模拟环境
    if env_name not in SIMULATION_REGISTRY:
        raise HTTPException(status_code=404, detail=f"环境 '{env_name}' 未运行或不可用")
    
    registry = SIMULATION_REGISTRY[env_name]
    sim_env = registry.get("sim_env")
    
    if not sim_env:
        raise HTTPException(status_code=404, detail=f"环境 '{env_name}' 的模拟环境未初始化")
    
    # 获取环境锁
    env_lock = get_env_lock(env_name)
    
    async with env_lock:
        try:
            # 获取当前_pending_decisions
            all_decisions = getattr(sim_env, '_pending_decisions', [])
            
            # 检查决策数据是否为空
            if not all_decisions:
                raise HTTPException(status_code=400, detail="没有需要保存的决策数据")
            
            # 创建datasets目录路径
            dataset_dir = os.path.join(env_path, "datasets")
            os.makedirs(dataset_dir, exist_ok=True)
            
            # 使用时间戳创建文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"decisions_{timestamp}.json"
            export_path = os.path.join(dataset_dir, filename)
            absolute_path = os.path.abspath(export_path)
            
            # 将决策数据保存到文件
            try:
                with open(export_path, "w", encoding="utf-8") as f:
                    json.dump(all_decisions, f, indent=4, ensure_ascii=False)
                
                return SaveResponse(
                    success=True,
                    file_path=absolute_path
                )
            except Exception as e:
                logger.error(f"保存决策数据失败: {e}")
                raise HTTPException(status_code=500, detail=f"保存决策数据失败: {str(e)}")
        
        except Exception as e:
            logger.error(f"保存决策数据失败: {e}")
            raise HTTPException(status_code=500, detail=f"保存决策数据失败: {str(e)}")
        

