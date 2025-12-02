# -*- coding: utf-8 -*-
"""
多实验组对比分析脚本
- 功能：读取多个实验目录下的 round_metrics_enhanced.csv，
        生成对比图表，以分析不同参数设置下的系统演化差异。
- 输入：多个 round_metrics_enhanced.csv 文件。
- 输出：一系列对比图表，如 fig_comp_gini.png, fig_comp_turnover.png 等。
"""

import pandas as pd
import matplotlib.pyplot as plt
import os

# --- 1. 参数设置 ---

# 基础路径，所有实验组目录都在这个路径下
BASE_PATH = "D:/yulan-onesim/YuLan-OneSim/my/"

# 定义你的实验组
# 格式：'图例标签': '实验结果目录名'
EXPERIMENT_GROUPS = {
    "10 Agents, 80 Plots (Low Density)": "100",
    "10 Agents, 100 Plots (Baseline)": "101",
    "12 Agents, 100 Plots (Medium Density)": "102",
    "50 Agents, 100 Plots (High Density)": "103"
}

# 输入文件名 (假设每个目录下都有这个文件)
INPUT_FILENAME = "round_metrics_enhanced.csv"

# 输出图表的目录
OUTPUT_DIR = os.path.join(BASE_PATH, "comparative_analysis_figures")

# 平滑窗口大小（用于平滑曲线，让趋势更清晰）
SMOOTHING_WINDOW = 10

# --- 2. 数据加载与合并 ---

def load_and_combine_data(base_path, groups, filename):
    """加载所有实验组的数据并合并到一个 DataFrame 中"""
    all_dfs = []
    for label, dir_name in groups.items():
        file_path = os.path.join(base_path, dir_name, filename)
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            df['group'] = label  # 添加一个新列来标识组别
            all_dfs.append(df)
            print(f"[INFO] Successfully loaded data for group: '{label}'")
        else:
            print(f"[WARNING] File not found for group '{label}' at: {file_path}")

    if not all_dfs:
        print("[ERROR] No data was loaded. Please check your paths and filenames.")
        return None

    return pd.concat(all_dfs, ignore_index=True)

# --- 3. 可视化函数 ---

def plot_comparative_chart(df, y_column, title, y_label, output_path, smoothing=True):
    """通用的对比图表绘制函数"""
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(14, 8))

    # 为每个组绘制一条线
    for name, group_df in df.groupby('group'):
        x = group_df['round']
        y = group_df[y_column]
        
        if smoothing:
            # 应用移动平均来平滑曲线
            y = y.rolling(window=SMOOTHING_WINDOW, min_periods=1).mean()
        
        ax.plot(x, y, label=name, linewidth=2.5, alpha=0.8)

    ax.set_title(title, fontsize=18, pad=20)
    ax.set_xlabel('Round', fontsize=14)
    ax.set_ylabel(y_label, fontsize=14)
    ax.legend(title='Experiment Groups', fontsize=12)
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)
    ax.set_xlim(0, df['round'].max())
    
    # 动态设置y轴范围
    min_y = df[y_column].min()
    max_y = df[y_column].max()
    ax.set_ylim(min_y * 0.9, max_y * 1.1)


    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"[SUCCESS] Saved comparative chart to: {output_path}")

# --- 4. 主流程 ---

def main():
    # 创建输出目录
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"[INFO] Created output directory: {OUTPUT_DIR}")

    # 加载数据
    master_df = load_and_combine_data(BASE_PATH, EXPERIMENT_GROUPS, INPUT_FILENAME)

    if master_df is not None:
        # 图表 1: 财富基尼系数对比
        plot_comparative_chart(
            df=master_df,
            y_column='gini_coefficient',
            title='Comparative Evolution of Wealth Inequality (Gini Coefficient)',
            y_label='Gini Coefficient',
            output_path=os.path.join(OUTPUT_DIR, 'fig_comp_gini_evolution.png')
        )

        # 图表 2: 领地换手率对比
        plot_comparative_chart(
            df=master_df,
            y_column='territory_turnover',
            title='Comparative Territory Stability (Turnover Rate)',
            y_label='Number of Plots Changing Ownership',
            output_path=os.path.join(OUTPUT_DIR, 'fig_comp_turnover.png')
        )

        # 图表 3: 冲突策略占比对比 (使用 raid_ratio)
        plot_comparative_chart(
            df=master_df,
            y_column='raid_ratio',
            title='Comparative Conflict Strategy (Raid Stamina Ratio)',
            y_label='Proportion of Stamina Spent on Raids',
            output_path=os.path.join(OUTPUT_DIR, 'fig_comp_raid_ratio.png')
        )

        # 图表 4: 生产策略占比对比 (使用 mining_ratio)
        plot_comparative_chart(
            df=master_df,
            y_column='mining_ratio',
            title='Comparative Production Strategy (Mining Stamina Ratio)',
            y_label='Proportion of Stamina Spent on Mining',
            output_path=os.path.join(OUTPUT_DIR, 'fig_comp_mining_ratio.png')
        )
        
        # 图表 5: 系统总产金对比
        plot_comparative_chart(
            df=master_df,
            y_column='total_gold',
            title='Comparative System Efficiency (Total Gold per Round)',
            y_label='Total Gold Produced',
            output_path=os.path.join(OUTPUT_DIR, 'fig_comp_total_gold.png')
        )


if __name__ == '__main__':
    main()