# -*- coding: utf-8 -*-
"""
核心发现可视化 - 三阶段演化 + 关键指标
专门为汇报设计的高质量静态图表组合
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import numpy as np

# =================== 配置 ===================
OWNERSHIP_CSV = "D:/yulan-onesim/YuLan-OneSim/my/104/ownership_timeseries.csv"
ROUND_METRICS_CSV = "D:/yulan-onesim/YuLan-OneSim/my/104/round_metrics.csv"
AGENT_METRICS_CSV = "D:/yulan-onesim/YuLan-OneSim/my/104/agent_metrics.csv"
OUTPUT_PNG = "D:/yulan-onesim/YuLan-OneSim/my/demo_tools/key_findings.png"

# =================== 数据加载 ===================
def load_data():
    ownership_df = pd.read_csv(OWNERSHIP_CSV)
    round_metrics_df = pd.read_csv(ROUND_METRICS_CSV)
    agent_metrics_df = pd.read_csv(AGENT_METRICS_CSV)
    return ownership_df, round_metrics_df, agent_metrics_df

def calculate_gini(values):
    values = sorted([v for v in values if v >= 0])
    n = len(values)
    if n == 0 or sum(values) == 0:
        return 0.0
    cum = sum((i + 1) * v for i, v in enumerate(values))
    s = sum(values)
    return (2 * cum) / (n * s) - (n + 1) / n

def calculate_gini_timeseries(ownership_df):
    agents = [col for col in ownership_df.columns if col != 'round']
    gini_values = []
    for _, row in ownership_df.iterrows():
        values = [row[agent] for agent in agents]
        gini = calculate_gini(values)
        gini_values.append(gini)
    return gini_values

# =================== 创建图表 ===================
def create_key_findings_figure(ownership_df, round_metrics_df, agent_metrics_df):
    """���建关键发现的综合图表"""

    # 设置中文字体 - 改进版，确保emoji和中文都能显示
    import platform
    system = platform.system()

    if system == 'Windows':
        # Windows系统优先使用微软雅黑
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
    else:
        # MacOS或Linux
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']

    plt.rcParams['axes.unicode_minus'] = False

    # 创建大图
    fig = plt.figure(figsize=(18, 12))
    gs = GridSpec(3, 3, figure=fig, hspace=0.35, wspace=0.3)

    # ���义三个阶段
    phase_ranges = {
        'Chaos (混沌期)': (0, 5, '#FF6B6B'),
        'Competition (竞争期)': (6, 15, '#FFA500'),
        'Order (秩序期)': (16, 29, '#4ECDC4')
    }

    # 计算Gini时序
    gini_values = calculate_gini_timeseries(ownership_df)
    agents = [col for col in ownership_df.columns if col != 'round']

    # ========== 1. 主图：Gini系数演化 + 三阶段标注 ==========
    ax1 = fig.add_subplot(gs[0, :])
    ax1.plot(range(len(gini_values)), gini_values,
             linewidth=3, color='#2C3E50', marker='o', markersize=6,
             label='Wealth Inequality (Gini)')

    # 添加阶段背景色
    for phase, (start, end, color) in phase_ranges.items():
        ax1.axvspan(start, end, alpha=0.2, color=color, label=phase)

    # 添加关键点标注
    ax1.annotate(f'Initial: {gini_values[0]:.3f}',
                 xy=(0, gini_values[0]),
                 xytext=(2, gini_values[0] + 0.05),
                 fontsize=11, fontweight='bold',
                 arrowprops=dict(arrowstyle='->', color='red', lw=2))

    ax1.annotate(f'Stable: {gini_values[-1]:.3f}',
                 xy=(len(gini_values)-1, gini_values[-1]),
                 xytext=(len(gini_values)-5, gini_values[-1] + 0.05),
                 fontsize=11, fontweight='bold',
                 arrowprops=dict(arrowstyle='->', color='green', lw=2))

    ax1.set_xlabel('Round', fontsize=13, fontweight='bold')
    ax1.set_ylabel('Gini Coefficient', fontsize=13, fontweight='bold')
    ax1.set_title('核心发现1: 财富不平等从混沌到收敛 (Gini: 0.65 → 0.14)',
                  fontsize=15, fontweight='bold', pad=15)
    ax1.legend(loc='upper right', fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(0, 0.75)

    # ========== 2. 冲突强度演化 ==========
    ax2 = fig.add_subplot(gs[1, 0])
    total_conflicts = round_metrics_df['contested_raids'] + round_metrics_df['contested_claims']

    ax2.fill_between(round_metrics_df['round'], total_conflicts,
                     alpha=0.6, color='#E74C3C')
    ax2.plot(round_metrics_df['round'], total_conflicts,
             linewidth=2, color='#C0392B', marker='o', markersize=4)

    # 阶段平均值
    for phase, (start, end, color) in phase_ranges.items():
        phase_data = total_conflicts[start:end+1]
        avg = phase_data.mean()
        ax2.axhline(y=avg, xmin=start/30, xmax=(end+1)/30,
                   linestyle='--', color=color, linewidth=2, alpha=0.7)
        ax2.text((start+end)/2, avg+1, f'Avg: {avg:.1f}',
                ha='center', fontsize=9, fontweight='bold')

    ax2.set_xlabel('Round', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Conflicts', fontsize=11, fontweight='bold')
    ax2.set_title('核心发现2: 冲突强度显著下降', fontsize=13, fontweight='bold')
    ax2.grid(True, alpha=0.3)

    # ========== 3. 总产出演化 ==========
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.plot(round_metrics_df['round'], round_metrics_df['total_gold'],
             linewidth=2.5, color='#F39C12', marker='s', markersize=5)
    ax3.fill_between(round_metrics_df['round'], round_metrics_df['total_gold'],
                    alpha=0.3, color='#F39C12')

    # 趋势线
    z = np.polyfit(round_metrics_df['round'], round_metrics_df['total_gold'], 2)
    p = np.poly1d(z)
    ax3.plot(round_metrics_df['round'], p(round_metrics_df['round']),
            linestyle='--', color='red', linewidth=2, alpha=0.7, label='Trend')

    ax3.set_xlabel('Round', fontsize=11, fontweight='bold')
    ax3.set_ylabel('Total Gold', fontsize=11, fontweight='bold')
    ax3.set_title('核心发现3: 产出随秩序提升而增长', fontsize=13, fontweight='bold')
    ax3.legend(loc='lower right')
    ax3.grid(True, alpha=0.3)

    # ========== 4. 体力分配转变（堆叠面积图）==========
    ax4 = fig.add_subplot(gs[1, 2])

    # 计算百分比
    total_stamina = (round_metrics_df['claims'] + round_metrics_df['raids'] +
                    round_metrics_df['defend'] + round_metrics_df['mining_stamina'])

    claims_pct = round_metrics_df['claims'] / total_stamina * 100
    raids_pct = round_metrics_df['raids'] / total_stamina * 100
    defend_pct = round_metrics_df['defend'] / total_stamina * 100
    mining_pct = round_metrics_df['mining_stamina'] / total_stamina * 100

    ax4.stackplot(round_metrics_df['round'],
                 claims_pct, raids_pct, defend_pct, mining_pct,
                 labels=['Claim (扩张)', 'Raid (抢占)', 'Defend (防御)', 'Mining (采矿)'],
                 colors=['#3498DB', '#E74C3C', '#95A5A6', '#2ECC71'],
                 alpha=0.8)

    ax4.set_xlabel('Round', fontsize=11, fontweight='bold')
    ax4.set_ylabel('Stamina Allocation (%)', fontsize=11, fontweight='bold')
    ax4.set_title('策略转变: 从扩张到生产', fontsize=13, fontweight='bold')
    ax4.legend(loc='upper left', fontsize=9)
    ax4.set_ylim(0, 100)
    ax4.grid(True, alpha=0.3, axis='y')

    # ========== 5. 活跃领主数量（领地>0的代理数）==========
    ax5 = fig.add_subplot(gs[2, 0])

    active_owners = []
    for _, row in ownership_df.iterrows():
        count = sum(1 for agent in agents if row[agent] > 0)
        active_owners.append(count)

    ax5.plot(ownership_df['round'], active_owners,
            linewidth=2.5, color='#9B59B6', marker='D', markersize=5)
    ax5.axhline(y=len(agents), linestyle='--', color='gray',
               linewidth=1.5, alpha=0.7, label=f'Total Agents ({len(agents)})')

    ax5.set_xlabel('Round', fontsize=11, fontweight='bold')
    ax5.set_ylabel('Active Owners', fontsize=11, fontweight='bold')
    ax5.set_title('产权持有者数量稳定', fontsize=13, fontweight='bold')
    ax5.legend()
    ax5.grid(True, alpha=0.3)

    # ========== 6. 最终财富分布（Top 10）==========
    ax6 = fig.add_subplot(gs[2, 1])

    top10_agents = agent_metrics_df.nlargest(10, 'cum_gold')

    colors_bar = plt.cm.viridis(np.linspace(0, 1, 10))
    bars = ax6.barh(range(10), top10_agents['cum_gold'].values, color=colors_bar)

    ax6.set_yticks(range(10))
    ax6.set_yticklabels(top10_agents['agent'].values, fontsize=9)
    ax6.set_xlabel('Cumulative Gold', fontsize=11, fontweight='bold')
    ax6.set_title('最终财富分布 (Top 10)', fontsize=13, fontweight='bold')
    ax6.grid(True, alpha=0.3, axis='x')

    # 添加数值标签
    for i, (bar, val) in enumerate(zip(bars, top10_agents['cum_gold'].values)):
        ax6.text(val + 2, i, f'{val:.0f}', va='center', fontsize=9)

    # ========== 7. 关键统计摘要框 ==========
    ax7 = fig.add_subplot(gs[2, 2])
    ax7.axis('off')

    # 计算关键统计
    initial_gini = gini_values[0]
    final_gini = gini_values[-1]
    gini_reduction = (initial_gini - final_gini) / initial_gini * 100

    initial_conflicts = total_conflicts.iloc[:6].mean()
    final_conflicts = total_conflicts.iloc[-5:].mean()
    conflict_reduction = (initial_conflicts - final_conflicts) / initial_conflicts * 100

    initial_gold = round_metrics_df['total_gold'].iloc[:6].mean()
    final_gold = round_metrics_df['total_gold'].iloc[-5:].mean()
    gold_increase = (final_gold - initial_gold) / initial_gold * 100

    # 使用简化的文本内容，避免emoji显示问题
    summary_text = f"""
【关键统计摘要】
{'='*32}

◆ 不平等度降低
   Gini: {initial_gini:.3f} → {final_gini:.3f}
   降幅: {gini_reduction:.1f}%

◆ 冲突强度下降
   初期平均: {initial_conflicts:.1f}
   后期平均: {final_conflicts:.1f}
   降幅: {conflict_reduction:.1f}%

◆ 产出效率提升
   初期平均: {initial_gold:.1f}
   后期平均: {final_gold:.1f}
   增幅: {gold_increase:.1f}%

■ 核心结论
   理性个体博弈自发形成
   稳定产权秩序
   验证了自发秩序理论
    """

    ax7.text(0.1, 0.95, summary_text, transform=ax7.transAxes,
            fontsize=11, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    # ========== 总标题 ==========
    fig.suptitle('从混沌到秩序：AI模拟财产权生成的关键发现\nFrom Chaos to Order: Property Rights Emergence in AI Simulation',
                fontsize=18, fontweight='bold', y=0.98)

    return fig

# =================== 主函数 ===================
def main():
    print("Loading data...")
    ownership_df, round_metrics_df, agent_metrics_df = load_data()

    print("Creating key findings visualization...")
    fig = create_key_findings_figure(ownership_df, round_metrics_df, agent_metrics_df)

    print(f"Saving to {OUTPUT_PNG}...")
    plt.savefig(OUTPUT_PNG, dpi=300, bbox_inches='tight')
    print("Done!")

    print(f"\n使用方式：")
    print(f"1. 将 {OUTPUT_PNG} 插入PPT作为核心发现页")
    print(f"2. 可以逐个讲解七个子图中的发现")
    print(f"3. 右下角的统计摘要框总结了量化结果")

if __name__ == '__main__':
    main()
