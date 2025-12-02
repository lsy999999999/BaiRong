# -*- coding: utf-8 -*-
"""
冲突动态分析脚本
- 功能：读取 round_metrics.csv，分析并可视化冲突随时间的变化。
- 输入：round_metrics.csv
- 输出：
  1. 控制台打印的冲突数据表格（摘要）。
  2. 一张冲突演化图 (fig_conflict_evolution.png)。
"""

import pandas as pd
import matplotlib.pyplot as plt
import os

# --- 1. 参数设置 ---
# 请确保这个路径指向您的 round_metrics.csv 文件
INPUT_CSV_PATH = "D:/yulan-onesim/YuLan-OneSim/my/104/round_metrics.csv"
OUTPUT_IMAGE_PATH = "D:/yulan-onesim/YuLan-OneSim/my/104/fig_conflict_evolution.png"

def analyze_and_visualize_conflict():
    """主函数，执行数据分析和可视化"""

    # --- 2. 数据读取与处理 ---
    if not os.path.exists(INPUT_CSV_PATH):
        print(f"错误：找不到输入文件 '{INPUT_CSV_PATH}'。请检查路径。")
        return

    # 使用 pandas 读取数据
    df = pd.read_csv(INPUT_CSV_PATH)
    
    # 检查必需的列是否存在
    required_columns = ['round', 'contested_raids', 'contested_claims']
    if not all(col in df.columns for col in required_columns):
        print(f"错误：CSV文件缺少必需的列。需要：{required_columns}")
        return

    # 创建一个新列 'total_contested' 来表示总冲突
    df['total_contested'] = df['contested_raids'] + df['contested_claims']
    
    # --- 3. 输出表格 ---
    print("--- 冲突动态数据表 (摘要) ---")
    print("该表格展示了系统在初始、中期和末期的冲突水平。")
    
    # 为了清晰，我们只展示开头、中间和结尾的部分数据
    display_df = df[['round', 'contested_raids', 'contested_claims', 'total_contested']]
    
    print("\n[初始阶段] 前10回合的冲突数据:")
    print(display_df.head(10).to_string(index=False))
    
    if len(df) > 20:
        mid_point = len(df) // 2
        print("\n[中期阶段] 中间10回合的冲突数据:")
        print(display_df.iloc[mid_point-5:mid_point+5].to_string(index=False))

    print("\n[末期阶段] 最后10回合的冲突数据:")
    print(display_df.tail(10).to_string(index=False))
    print("-" * 30)

    # --- 4. 可视化图像 ---
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, 7))

    # 绘制总冲突曲线
    ax.plot(df['round'], df['total_contested'], marker='.', linestyle='-', color='#d62728', label='Total Conflicts (Raids + Claims)', linewidth=2.5, alpha=0.9)
    
    # 绘制两种冲突的散点图，作为辅助信息
    ax.scatter(df['round'], df['contested_raids'], color='#1f77b4', label='Contested Raids', alpha=0.5, s=20)
    ax.scatter(df['round'], df['contested_claims'], color='#ff7f0e', label='Contested Claims', alpha=0.5, s=20)

    # 设置图表标题和标签
    ax.set_title('Evolution of Conflict: From Chaos to Order', fontsize=18, pad=20)
    ax.set_xlabel('Round', fontsize=14)
    ax.set_ylabel('Number of Contested Events per Round', fontsize=14)
    
    # 设置图例
    ax.legend(loc='upper right', fontsize=12)
    
    # 设置坐标轴范围
    ax.set_xlim(0, df['round'].max())
    ax.set_ylim(0, df['total_contested'].max() * 1.1 if not df.empty else 10)
    
    # 优化布局并保存图像
    plt.tight_layout()
    plt.savefig(OUTPUT_IMAGE_PATH, dpi=150)

    print(f"\n[成功] 可视化图表已保存至: {OUTPUT_IMAGE_PATH}")

if __name__ == '__main__':
    analyze_and_visualize_conflict()