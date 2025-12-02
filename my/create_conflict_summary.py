# -*- coding: utf-8 -*-
"""
冲突动态总结与对比脚本
- 功能：读取多个实验组的 round_metrics_enhanced.csv，
        生成一张总结性表格和一张热力图，对比不同竞争压力下，
        冲突随时间阶段的变化。
- 输入：多个实验目录下的 round_metrics_enhanced.csv 文件。
- 输出：
  1. 控制台打印的冲突动态总结表。
  2. 一张对比热力图 (fig_summary_conflict_heatmap.png)。
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
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
OUTPUT_IMAGE_PATH = os.path.join(BASE_PATH, "comparative_analysis_figures", "fig_summary_conflict_heatmap.png")

# 定义时间阶段 (回合分箱)
# 格式: (起始回合, 结束回合)
ROUND_BINS = [
    (0, 5),
    (6, 10),
    (11, 15),
    (16, 20),
    (21, 200) # 假设最多200回合，代表 21+
]

# --- 2. 辅助函数 ---

def calculate_plots_per_agent(group_label: str) -> float:
    """从组别标签中解析并计算人均土地"""
    try:
        # 使用正则表达式查找数字
        agents = int(re.search(r'(\d+)\s+Agents', group_label).group(1))
        plots = int(re.search(r'(\d+)\s+Plots', group_label).group(1))
        return plots / agents if agents > 0 else 0
    except (AttributeError, ValueError):
        # 如果解析失败，返回0或NaN
        print(f"[Warning] Could not parse agents/plots from label: '{group_label}'")
        return 0

# --- 3. 主流程 ---

def create_summary_table_and_heatmap():
    """主函数，执行所有操作"""

    summary_data = []

    # 遍历每个实验组
    for label, dir_name in EXPERIMENT_GROUPS.items():
        file_path = os.path.join(BASE_PATH, dir_name, INPUT_FILENAME)
        
        if not os.path.exists(file_path):
            print(f"[Warning] File not found for group '{label}', skipping.")
            continue
            
        df = pd.read_csv(file_path)
        
        # 计算总冲突
        df['total_contested'] = df['contested_raids'] + df['contested_claims']
        
        # 创建一个字典来存储该组的结果
        row_data = {
            "Group": label,
            "Plots per Agent": f"{calculate_plots_per_agent(label):.2f}"
        }
        
        # 按时间阶段计算平均冲突
        for start, end in ROUND_BINS:
            # 筛选出当前时间段的数据
            bin_df = df[(df['round'] >= start) & (df['round'] <= end)]
            
            # 计算平均冲突数，如果该阶段没有数据则为0
            mean_conflict = bin_df['total_contested'].mean() if not bin_df.empty else 0.0
            
            # 格式化列名
            if end > 200: # 最后一个分箱
                 col_name = f"Rounds {start}+"
            else:
                 col_name = f"Rounds {start}-{end}"
            
            row_data[col_name] = f"{mean_conflict:.2f}"
            
        summary_data.append(row_data)

    if not summary_data:
        print("[Error] No data was processed. Halting.")
        return

    # --- 4. 输出表格 ---
    summary_df = pd.DataFrame(summary_data)
    
    print("="*80)
    print("                  Comparative Analysis of Conflict Dynamics")
    print("="*80)
    print("Values represent the AVERAGE number of total conflicts per round within each time segment.")
    print("-" * 80)
    print(summary_df.to_string(index=False))
    print("="*80)


    # --- 5. 可视化热力图 ---
    # 准备用于热力图的数据
    heatmap_df = summary_df.set_index(['Group', 'Plots per Agent']).astype(float)
    
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(14, 8))
    
    sns.heatmap(heatmap_df, annot=True, fmt=".2f", cmap="Reds", linewidths=.5, ax=ax,
                annot_kws={"size": 12})
    
    ax.set_title('Heatmap of Average Conflicts per Round', fontsize=18, pad=20)
    ax.set_xlabel('Round Segments', fontsize=14)
    ax.set_ylabel('Experimental Groups (Sorted by Competition Intensity)', fontsize=14)
    plt.xticks(rotation=45)
    plt.yticks(rotation=0)
    
    # 创建输出目录
    output_dir = os.path.dirname(OUTPUT_IMAGE_PATH)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    plt.tight_layout()
    plt.savefig(OUTPUT_IMAGE_PATH, dpi=150)
    
    print(f"\n[SUCCESS] Summary heatmap saved to: {OUTPUT_IMAGE_PATH}")

if __name__ == '__main__':
    create_summary_table_and_heatmap()