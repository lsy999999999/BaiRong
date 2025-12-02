# -*- coding- utf-8 -*-
"""
财富分配对比分析脚本
- 功能：整合多个实验组的数据，对比分析基尼系数的演化过程和最终财富分布。
- 输入：多个实验目录下的 round_metrics_enhanced.csv 和 agent_metrics.csv 文件。
- 输出：
  1. 一张合并的基尼系数演化对比图 (fig_comp_gini_combined.png)。
  2. 一张最终财富分布的对比箱线图 (fig_comp_wealth_boxplot.png)。
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import re

# --- 1. 参数设置 ---

# 基础路径
BASE_PATH = "D:/yulan-onesim/YuLan-OneSim/my/"

# 定义你的实验组
EXPERIMENT_GROUPS = {
    "10 Agents, 80 Plots (Low Density)": "100",
    "10 Agents, 100 Plots (Baseline)": "101",
    "12 Agents, 100 Plots (Medium Density)": "102",
    "50 Agents, 100 Plots (High Density)": "103"
}

# 输入文件名
ROUND_METRICS_FILENAME = "round_metrics_enhanced.csv"
AGENT_METRICS_FILENAME = "agent_metrics.csv"

# 输出图表的目录
OUTPUT_DIR = os.path.join(BASE_PATH, "comparative_analysis_figures")

# 平滑窗口大小
SMOOTHING_WINDOW = 10

# --- 2. 主流程 ---

def analyze_combined_wealth_metrics():
    """主函数，执行数据加载、计算和可视化"""

    # 创建输出目录
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # --- Part 1: 基尼系数演化对比 ---

    all_round_dfs = []
    for label, dir_name in EXPERIMENT_GROUPS.items():
        file_path = os.path.join(BASE_PATH, dir_name, ROUND_METRICS_FILENAME)
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            df['group'] = label
            all_round_dfs.append(df)
        else:
            print(f"[Warning] Round metrics file not found for group '{label}' at: {file_path}")
    
    if not all_round_dfs:
        print("[Error] No round metrics data loaded. Halting Gini plot generation.")
        return

    master_round_df = pd.concat(all_round_dfs, ignore_index=True)

    # 绘制基尼系数对比图
    plt.style.use('seaborn-v0_8-whitegrid')
    fig1, ax1 = plt.subplots(figsize=(14, 8))
    
    sns.lineplot(
        data=master_round_df,
        x='round',
        y='gini_coefficient',
        hue='group',
        linewidth=2.5,
        alpha=0.8,
        ax=ax1
    )
    
    ax1.set_title('Comparative Evolution of Wealth Inequality (Gini Coefficient)', fontsize=18, pad=20)
    ax1.set_xlabel('Round', fontsize=14)
    ax1.set_ylabel('Gini Coefficient (0=Equality)', fontsize=14)
    ax1.legend(title='Experiment Groups', fontsize=12)
    ax1.grid(True, which='both', linestyle='--', linewidth=0.5)
    ax1.set_xlim(0, master_round_df['round'].max())
    ax1.set_ylim(0, max(0.5, master_round_df['gini_coefficient'].max() * 1.1))

    gini_output_path = os.path.join(OUTPUT_DIR, 'fig_comp_gini_combined.png')
    plt.tight_layout()
    plt.savefig(gini_output_path, dpi=150)
    plt.close()
    print(f"[SUCCESS] Saved combined Gini evolution chart to: {gini_output_path}")


    # --- Part 2: 最终财富分布对比 ---

    all_agent_dfs = []
    for label, dir_name in EXPERIMENT_GROUPS.items():
        file_path = os.path.join(BASE_PATH, dir_name, AGENT_METRICS_FILENAME)
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            df['group'] = label
            all_agent_dfs.append(df)
        else:
            print(f"[Warning] Agent metrics file not found for group '{label}' at: {file_path}")

    if not all_agent_dfs:
        print("[Error] No agent metrics data loaded. Halting wealth distribution plot generation.")
        return
        
    master_agent_df = pd.concat(all_agent_dfs, ignore_index=True)
    
    # 绘制最终财富分布对比箱线图
    fig2, ax2 = plt.subplots(figsize=(14, 8))
    
    sns.boxplot(
        data=master_agent_df,
        x='group',
        y='cum_gold',
        ax=ax2
    )
    
    ax2.set_title('Final Cumulative Wealth Distribution by Group', fontsize=18, pad=20)
    ax2.set_xlabel('Experiment Groups', fontsize=14)
    ax2.set_ylabel('Cumulative Gold per Agent', fontsize=14)
    plt.xticks(rotation=15, ha="right") # 倾斜标签防止重叠
    
    boxplot_output_path = os.path.join(OUTPUT_DIR, 'fig_comp_wealth_boxplot.png')
    plt.tight_layout()
    plt.savefig(boxplot_output_path, dpi=150)
    plt.close()
    print(f"[SUCCESS] Saved combined wealth distribution boxplot to: {boxplot_output_path}")


if __name__ == '__main__':
    analyze_combined_wealth_metrics()