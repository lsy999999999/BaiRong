# -*- coding: utf-8 -*-
"""
冲突与竞争压力关系分析脚本
- 功能：标准化冲突数据，探索“人均土地”与“人均冲突数”之间的定量关系。
- 输入：多个实验目录下的 round_metrics_enhanced.csv 文件。
- 输出：
  1. 控制台打印的关系总结表。
  2. 一张散点图与回归拟合曲线 (fig_conflict_vs_density.png)。
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import re

# --- 1. 参数设置 ---

# 基础路径
BASE_PATH = "D:/yulan-onesim/YuLan-OneSim/my/"

# 定义实验组
EXPERIMENT_GROUPS = {
    "10 Agents, 80 Plots": "100",
    "10 Agents, 100 Plots": "101",
    "12 Agents, 100 Plots": "102",
    "50 Agents, 100 Plots": "103"
}

# 输入文件名
INPUT_FILENAME = "round_metrics_enhanced.csv"

# 输出图表路径
OUTPUT_DIR = os.path.join(BASE_PATH, "comparative_analysis_figures")
OUTPUT_IMAGE_PATH = os.path.join(OUTPUT_DIR, "fig_conflict_vs_density.png")

# 定义时间阶段
ROUND_BINS = {
    'Early Game (Rounds 0-20)': (0, 10),
    'Mid Game (Rounds 10-20)': (10, 20),
    'Late Game (Rounds 20+)': (20, 100) # 捕捉后期稳定状态
}

# --- 2. 辅助函数 ---

def parse_group_info(group_label: str) -> (int, int):
    """从组标签解析出代理数和土地数"""
    try:
        agents = int(re.search(r'(\d+)\s+Agents', group_label).group(1))
        plots = int(re.search(r'(\d+)\s+Plots', group_label).group(1))
        return agents, plots
    except (AttributeError, ValueError):
        return 0, 0

# --- 3. 主流程 ---

def analyze_conflict_density():
    # 创建输出目录
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    analysis_data = []

    # 加载和处理每个实验组的数据
    for label, dir_name in EXPERIMENT_GROUPS.items():
        file_path = os.path.join(BASE_PATH, dir_name, INPUT_FILENAME)
        if not os.path.exists(file_path):
            print(f"[Warning] File not found for group '{label}', skipping.")
            continue
            
        df = pd.read_csv(file_path)
        agents_count, plots_count = parse_group_info(label)
        
        if agents_count == 0:
            continue

        plots_per_agent = plots_count / agents_count
        df['total_contested'] = df['contested_raids'] + df['contested_claims']
        
        # 按时间阶段聚合
        for stage, (start, end) in ROUND_BINS.items():
            stage_df = df[(df['round'] >= start) & (df['round'] <= end)]
            if stage_df.empty:
                continue
            
            # 计算人均冲突数
            avg_total_conflict = stage_df['total_contested'].mean()
            per_capita_conflict = avg_total_conflict / agents_count

            analysis_data.append({
                "Group": label,
                "Stage": stage,
                "Plots per Agent": plots_per_agent,
                "Avg Per-Capita Conflict": per_capita_conflict
            })

    if not analysis_data:
        print("[Error] No data was processed. Halting.")
        return

    # --- 4. 输出表格 ---
    summary_df = pd.DataFrame(analysis_data)
    
    print("="*80)
    print("        Relationship between Competition Pressure and Per-Capita Conflict")
    print("="*80)
    print("This table shows the average number of conflicts initiated PER AGENT per round.")
    print("-" * 80)
    # 为了更好的可读性，我们按 人均土地 和 阶段 进行排序
    print(summary_df.sort_values(by=['Plots per Agent', 'Stage']).to_string(index=False))
    print("="*80)

    # --- 5. 可视化散点图与拟合曲线 ---
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(14, 9))
    
    # 使用seaborn进行散点图和回归拟合
    # hue='Stage' 会为不同阶段的点使用不同颜色
    sns.scatterplot(
        data=summary_df,
        x='Plots per Agent',
        y='Avg Per-Capita Conflict',
        hue='Stage',
        s=150, # 点的大小
        alpha=0.8,
        style='Stage', # 不同阶段使用不同形状的点
        ax=ax
    )
    
    # 绘制总体的回归拟合线
    sns.regplot(
        data=summary_df,
        x='Plots per Agent',
        y='Avg Per-Capita Conflict',
        scatter=False, # 不重复绘制散点
        color='black',
        line_kws={'linestyle':'--', 'linewidth':2},
        label='Overall Trend',
        ax=ax
    )
    
    ax.set_title('Per-Capita Conflict as a Function of Resource Availability', fontsize=18, pad=20)
    ax.set_xlabel('Plots per Agent (Lower = Higher Competition)', fontsize=14)
    ax.set_ylabel('Average Conflicts per Agent per Round', fontsize=14)
    
    # 调整图例
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, title='Game Stage', fontsize=12)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_IMAGE_PATH, dpi=150)
    
    print(f"\n[SUCCESS] Conflict vs. Density analysis chart saved to: {OUTPUT_IMAGE_PATH}")

if __name__ == '__main__':
    analyze_conflict_density()