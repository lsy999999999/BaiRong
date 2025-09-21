from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict, Any, Optional, List
import asyncio
import time
import os
import json
from loguru import logger

from backend.utils.websocket import connection_manager
from backend.routers.simulation import SIMULATION_REGISTRY
from backend.utils.echarts_helpers import create_line_chart_option, create_pie_chart_option

# Import OneSim components
import onesim
from onesim.monitor.monitor import MonitorManager
from onesim.config import get_config, get_component_registry

# Create router
router = APIRouter(
    tags=["monitor"],
    prefix="/monitor"
)

async def get_monitor_manager():
    """Get monitor manager from component registry"""
    registry = get_component_registry()
    monitor_manager = registry.get_instance("monitor")
    if not monitor_manager:
        logger.warning("Monitor manager not found in registry")
        return None
    return monitor_manager

# --- ECharts Option Helpers ---

# def create_line_chart_option(title: str, x_axis_data: List[str], series_data: List[Any], series_name: str = "Value") -> Dict[str, Any]:
#     """Creates a basic ECharts line chart option."""
#     return {
#         "title": {"text": title, "left": "center"},
#         "tooltip": {"trigger": "axis"},
#         "legend": {"data": [series_name], "bottom": 10},
#         "grid": {"left": '3%', "right": '4%', "bottom": '10%', "containLabel": True},
#         "xAxis": {"type": "category", "boundaryGap": False, "data": x_axis_data},
#         "yAxis": {"type": "value"},
#         "series": [{"name": series_name, "type": "line", "smooth": True, "data": series_data}]
#     }

# def create_pie_chart_option(title: str, series_data: List[Dict[str, Any]], series_name: str = "Distribution") -> Dict[str, Any]:
#     """Creates a basic ECharts pie chart option."""
#     return {
#         "title": {"text": title, "left": "center"},
#         "tooltip": {"trigger": "item"},
#         "legend": {"orient": "vertical", "left": "left", "top": "middle"},
#          "series": [{
#             "name": series_name,
#             "type": "pie",
#             "radius": ["40%", "70%"], # Make it a donut chart
#             "avoidLabelOverlap": False,
#             "itemStyle": {
#                 "borderRadius": 10,
#                 "borderColor": '#fff',
#                 "borderWidth": 2
#             },
#             "label": {
#                 "show": False,
#                 "position": 'center'
#             },
#             "emphasis": {
#                 "label": {
#                     "show": True,
#                     "fontSize": '20', # Smaller font size for emphasis
#                     "fontWeight": 'bold'
#                 }
#             },
#             "labelLine": {
#                 "show": False
#             },
#             "data": series_data # Expects data in format [{"name": "...", "value": ...}, ...]
#         }]
#     }


# --- End ECharts Option Helpers ---

@router.get("/{env_name}/metrics")
async def get_metrics(env_name: str):
    """Get all available metrics for an environment"""
    if env_name not in SIMULATION_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Environment '{env_name}' not found")
    
    # Get metrics data
    metrics_data = await get_all_metrics(env_name)
    
    return {
        "success": True,
        "metrics": metrics_data
    }

@router.get("/{env_name}/metrics/{metric_name}")
async def get_metric(env_name: str, metric_name: str):
    """Get a specific metric for an environment"""
    if env_name not in SIMULATION_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Environment '{env_name}' not found")
    
    monitor_manager = await get_monitor_manager()
    if not monitor_manager:
        return {
            "success": False,
            "message": "Monitor manager not available"
        }
    
    # Get metrics data
    metrics_data = await get_all_metrics(env_name)
    
    # Check if metric exists
    if metric_name not in metrics_data:
        raise HTTPException(status_code=404, detail=f"Metric '{metric_name}' not found")
    
    return {
        "success": True,
        "metric": metrics_data[metric_name]
    }

@router.post("/{env_name}/metrics/{metric_name}/update")
async def trigger_metric_update(env_name: str, metric_name: str):
    """Manually trigger an update for a specific metric"""
    if env_name not in SIMULATION_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Environment '{env_name}' not found")
    
    monitor_manager = await get_monitor_manager()
    if not monitor_manager:
        raise HTTPException(status_code=400, detail="Monitor manager not available")
    
    # Check if metric exists
    if metric_name not in monitor_manager.metrics:
        raise HTTPException(status_code=404, detail=f"Metric '{metric_name}' not found")
    
    # Get sim_env instance from registry
    sim_env = SIMULATION_REGISTRY[env_name].get("sim_env")
    if not sim_env:
        # Try to find it in sim_instance as well
        sim_env = SIMULATION_REGISTRY[env_name].get("sim_instance")
        if not sim_env:
            raise HTTPException(status_code=400, detail=f"Simulation environment not running")
    
    # Update the metric
    try:
        await monitor_manager.update_metric(metric_name, sim_env)
        return {
            "success": True,
            "message": f"Metric '{metric_name}' updated successfully"
        }
    except Exception as e:
        logger.error(f"Error updating metric {metric_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating metric: {str(e)}")

async def prepare_general_metrics(env_name: str):
    """Prepare general metrics based on simulation data, formatted as ECharts options."""
    if env_name not in SIMULATION_REGISTRY:
        return {}

    sim_data = SIMULATION_REGISTRY[env_name]
    sim_env = sim_data.get("sim_env")

    if not sim_env or not hasattr(sim_env, "data"):
        return {}

    general_metrics = {}
    current_time = int(time.time())
    formatted_time = time.strftime('%Y-%m-%d %H:%M:%S')

    if hasattr(sim_env, "data") and "step_data" in sim_env.data:
        rounds_data = sim_env.data["step_data"]
        rounds = sorted([r for r in rounds_data.keys()])

        # Prepare step duration data
        step_duration_x = ["Start"] + [f"Step {r}" for r in rounds]
        step_duration_y = [0] + [rounds_data[r].get("duration", 0) for r in rounds]
        general_metrics["step_duration"] = {
            "name": "step_duration",
            "description": "Duration of each simulation step in seconds.",
            "visualization_type": "line",
            "data": create_line_chart_option(
                title="Step Duration",
                x_axis_data=step_duration_x,
                series_data=step_duration_y,
                series_name="Duration (s)"
            ),
            "timestamp": current_time,
            "formatted_time": formatted_time
        }

        # Prepare token usage data if available
        token_data = {}
        # Initialize with starting point for line charts
        token_data["total_tokens_by_step"] = {"xAxis": ["Start"], "series": [0]}

        for r in rounds:
            if "token_usage" in rounds_data[r]:
                usage = rounds_data[r]["token_usage"]
                step_label = f"Step {r}"

                # Total tokens
                token_data["total_tokens_by_step"]["xAxis"].append(step_label)
                token_data["total_tokens_by_step"]["series"].append(usage.get("total_tokens", 0))

        # Add token data to general metrics as ECharts options
        if token_data["total_tokens_by_step"]["series"]: # Check if data exists
            general_metrics["total_tokens_by_step"] = {
                "name": "total_tokens_by_step",
                "description": "Total LLM tokens used per step.",
                "visualization_type": "line",
                "data": create_line_chart_option(
                    title="Total Tokens per Step",
                    x_axis_data=token_data["total_tokens_by_step"]["xAxis"],
                    series_data=token_data["total_tokens_by_step"]["series"],
                    series_name="Total Tokens"
                ),
                "timestamp": current_time,
                "formatted_time": formatted_time
            }


        # Prepare agent participation data if available
        if hasattr(sim_env, "_agent_decisions") and sim_env._agent_decisions and rounds:    
            last_round = rounds[-1]
            if last_round in sim_env._agent_decisions:
                agent_participation_raw = sim_env._agent_decisions[last_round]
                agent_participation_data = [{"name": k, "value": v} for k, v in agent_participation_raw.items()]

                if agent_participation_data: # Check if data exists
                    general_metrics["agent_participation"] = {
                        "name": "agent_participation",
                        "description": f"Distribution of agent types making decisions in the last step (Step {last_round}).",
                        "visualization_type": "pie",
                        "data": create_pie_chart_option(
                            title=f"Agent Participation (Step {last_round})",
                            series_data=agent_participation_data,
                            series_name="Agent Decisions"
                        ),
                        "timestamp": current_time,
                        "formatted_time": formatted_time
                    }

    return general_metrics

async def get_registered_metrics(env_name: str):
    """Get metrics registered with the monitor manager"""
    monitor_manager = await get_monitor_manager()
    if not monitor_manager:
        return {}
    
    # Get sim_env instance from registry
    sim_env = SIMULATION_REGISTRY[env_name]['sim_env']
    
    if not sim_env:
        return {}
    
    # Force an update of all registered metrics
    try:
        # # 对所有指标进行更新
        # for metric_name in monitor_manager.metrics.keys():
        #     try:
        #         await monitor_manager.update_metric(metric_name, sim_env)
        #     except Exception as e:
        #         logger.error(f"Error updating metric {metric_name}: {e}")
        
        # 使用新的API接口获取所有指标数据
        return monitor_manager.get_metrics_for_api()
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return {}

async def get_all_metrics(env_name: str):
    """Get both general and registered metrics for an environment"""
    # 1. Get general metrics
    general_metrics = await prepare_general_metrics(env_name)
    
    # 2. Get registered metrics
    registered_metrics = await get_registered_metrics(env_name)
    
    # 3. Combine all metrics
    all_metrics = {**general_metrics, **registered_metrics}
    
    return all_metrics

@router.websocket("/ws/{env_name}")
async def websocket_endpoint(websocket: WebSocket, env_name: str):
    """WebSocket endpoint for real-time metric updates"""
    await connection_manager.connect(websocket, f"monitor_{env_name}")
    
    try:
        # Initial metrics data
        metrics_data = await get_all_metrics(env_name)
        await websocket.send_json({
            "type": "metrics_update",
            "data": metrics_data,
            "timestamp": time.time()
        })
        
        # Update frequency - adjust based on simulation state
        update_interval = 1.0  # Default to 1 second
        
        # Send updates periodically
        while True:
            # Wait before sending the next update
            await asyncio.sleep(update_interval)
            
            # Check if simulation is still active
            if env_name not in SIMULATION_REGISTRY or not SIMULATION_REGISTRY[env_name].get("running", False):
                # Simulation not running, slower updates
                update_interval = 5.0
            else:
                # Simulation running, normal update frequency
                update_interval = 1.0
            
            # Get updated metrics data
            metrics_data = await get_all_metrics(env_name)
            
            # Send update to client
            await websocket.send_json({
                "type": "metrics_update",
                "data": metrics_data,
                "timestamp": int(time.time())
            })
            
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, f"monitor_{env_name}")
        logger.info(f"Client disconnected from monitor websocket for environment '{env_name}'")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket, f"monitor_{env_name}")
