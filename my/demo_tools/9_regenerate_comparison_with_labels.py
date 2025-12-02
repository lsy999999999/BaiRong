# -*- coding: utf-8 -*-
"""
修改版：多组实验对比静态图 - 使用具体参数标签
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec
import os

BASE_DIR = "D:/yulan-onesim/YuLan-OneSim/my"

# 实验配置
EXPERIMENTS = {
    100: '10 agents, 100 plots',
    101: '10 agents, 80 plots',
    102: '12 agents, 100 plots',
    103: '50 agents, 100 plots',
    104: '20 agents, 100 plots'
}

OUTPUT_PNG = "D:/yulan-onesim/YuLan-OneSim/my/demo_tools/comparison/multi_experiment_comparison_labeled.png"

def calculate_gini(values):
    values = sorted([v for v in values if v >= 0])
    n = len(values)
    if n == 0 or sum(values) == 0:
        return 0.0
    cum = sum((i + 1) * v for i, v in enumerate(values))
    s = sum(values)
    return (2 * cum) / (n * s) - (n + 1) / n

def load_experiment_data(exp_id):
    exp_dir = f"{BASE_DIR}/{exp_id}"
    ownership_csv = f"{exp_dir}/ownership_timeseries.csv"
    round_metrics_csv = f"{exp_dir}/round_metrics.csv"

    if not os.path.exists(ownership_csv) or not os.path.exists(round_metrics_csv):
        return None

    ownership_df = pd.read_csv(ownership_csv)
    round_metrics_df = pd.read_csv(round_metrics_csv)

    agents = [col for col in ownership_df.columns if col != 'round']
    gini_values = []
    for _, row in ownership_df.iterrows():
        values = [row[agent] for agent in agents]
        gini = calculate_gini(values)
        gini_values.append(gini)

    total_conflicts = (round_metrics_df['contested_raids'] +
                      round_metrics_df['contested_claims'])

    return {
        'exp_id': exp_id,
        'label': EXPERIMENTS[exp_id],
        'gini': gini_values,
        'conflicts': total_conflicts.tolist(),
        'total_gold': round_metrics_df['total_gold'].tolist(),
        'rounds': len(gini_values)
    }

def create_comparison_static(all_data):
    plt.rcParams['font.sans-serif'] = ['Arial']
    plt.rcParams['axes.unicode_minus'] = False

    fig = plt.figure(figsize=(18, 10))
    gs = GridSpec(2, 3, figure=fig, hspace=0.35, wspace=0.3)

    colors = plt.cm.Set2(np.linspace(0, 1, len(all_data)))

    # ========== 1. Gini系数对比 ==========
    ax1 = fig.add_subplot(gs[0, :2])
    for i, data in enumerate(all_data):
        ax1.plot(data['gini'], linewidth=2.5, alpha=0.85,
                color=colors[i], label=data['label'],
                marker='o', markersize=4, markevery=3)

    # 平均线
    max_rounds = max(len(d['gini']) for d in all_data)
    avg_gini = []
    for r in range(max_rounds):
        values = [d['gini'][r] for d in all_data if r < len(d['gini'])]
        avg_gini.append(np.mean(values))

    ax1.plot(avg_gini, linewidth=3.5, color='red', linestyle='--',
            label='Average', alpha=0.9)

    ax1.set_xlabel('Round', fontsize=13, fontweight='bold')
    ax1.set_ylabel('Gini Coefficient', fontsize=13, fontweight='bold')
    ax1.set_title('Wealth Inequality Evolution Comparison',
                  fontsize=15, fontweight='bold', pad=15)
    ax1.legend(loc='upper right', fontsize=10, ncol=2)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(0, max(max(d['gini']) for d in all_data) + 0.1)

    # ========== 2. 初始vs最终Gini对比 ==========
    ax2 = fig.add_subplot(gs[0, 2])
    labels_short = [d['label'].split(',')[0] for d in all_data]  # 简化标签
    initial_gini = [d['gini'][0] for d in all_data]
    final_gini = [d['gini'][-1] for d in all_data]

    x = np.arange(len(labels_short))
    width = 0.35

    bars1 = ax2.bar(x - width/2, initial_gini, width, label='Initial',
                   color='#FF6B6B', alpha=0.8, edgecolor='black')
    bars2 = ax2.bar(x + width/2, final_gini, width, label='Final',
                   color='#4ECDC4', alpha=0.8, edgecolor='black')

    ax2.set_ylabel('Gini Coefficient', fontsize=11, fontweight='bold')
    ax2.set_title('Initial vs Final Inequality', fontsize=13, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels_short, fontsize=8, rotation=15, ha='right')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3, axis='y')

    # 添加数值标签
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}', ha='center', va='bottom', fontsize=7)

    # ========== 3. 冲突演化对比 ==========
    ax3 = fig.add_subplot(gs[1, :2])
    for i, data in enumerate(all_data):
        ax3.plot(data['conflicts'], linewidth=2.5, alpha=0.85,
                color=colors[i], label=data['label'],
                marker='s', markersize=3, markevery=3)

    # 平均线
    avg_conflicts = []
    for r in range(max_rounds):
        values = [d['conflicts'][r] for d in all_data if r < len(d['conflicts'])]
        avg_conflicts.append(np.mean(values))

    ax3.plot(avg_conflicts, linewidth=3.5, color='red', linestyle='--',
            label='Average', alpha=0.9)

    ax3.set_xlabel('Round', fontsize=13, fontweight='bold')
    ax3.set_ylabel('Total Conflicts', fontsize=13, fontweight='bold')
    ax3.set_title('Conflict Intensity Evolution Comparison',
                  fontsize=15, fontweight='bold', pad=15)
    ax3.legend(loc='upper right', fontsize=10, ncol=2)
    ax3.grid(True, alpha=0.3)

    # ========== 4. 产出演化对比 ==========
    ax4 = fig.add_subplot(gs[1, 2])
    for i, data in enumerate(all_data):
        ax4.plot(data['total_gold'], linewidth=2, alpha=0.8,
                color=colors[i], label=labels_short[i])

    ax4.set_xlabel('Round', fontsize=11, fontweight='bold')
    ax4.set_ylabel('Total Gold', fontsize=11, fontweight='bold')
    ax4.set_title('Output Evolution', fontsize=13, fontweight='bold')
    ax4.legend(loc='lower right', fontsize=9)
    ax4.grid(True, alpha=0.3)

    # ========== 总标题 ==========
    fig.suptitle(f'Multi-Experiment Comparison (N={len(all_data)}) - Robustness Validation\nDifferent Configurations, Same Evolution Pattern',
                fontsize=18, fontweight='bold', y=0.98)

    return fig

def main():
    print("Loading experiment data...")
    all_data = []
    for exp_id, label in EXPERIMENTS.items():
        print(f"  Loading Exp{exp_id}: {label}...")
        data = load_experiment_data(exp_id)
        if data is not None:
            all_data.append(data)
            print(f"    [OK]")

    print(f"\nCreating comparison figure...")
    fig = create_comparison_static(all_data)
    plt.savefig(OUTPUT_PNG, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"\n[SUCCESS] Saved to: {OUTPUT_PNG}")

if __name__ == '__main__':
    main()
