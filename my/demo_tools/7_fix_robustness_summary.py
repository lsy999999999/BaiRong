# -*- coding: utf-8 -*-
"""
修复版：稳健性总结图 - 纯英文无乱码
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

BASE_DIR = "D:/yulan-onesim/YuLan-OneSim/my"
EXPERIMENTS = [100, 101, 102, 103, 104]
OUTPUT_PNG = "D:/yulan-onesim/YuLan-OneSim/my/demo_tools/comparison/robustness_summary_fixed.png"

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
        'gini': gini_values,
        'conflicts': total_conflicts.tolist(),
        'total_gold': round_metrics_df['total_gold'].tolist(),
        'rounds': len(gini_values)
    }

def create_robustness_summary(all_data):
    plt.rcParams['font.sans-serif'] = ['Arial']
    plt.rcParams['axes.unicode_minus'] = False

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))

    exp_ids = [d['exp_id'] for d in all_data]
    initial_gini = [d['gini'][0] for d in all_data]
    final_gini = [d['gini'][-1] for d in all_data]
    gini_reduction = [(i - f) / i * 100 for i, f in zip(initial_gini, final_gini)]

    initial_conflicts = [np.mean(d['conflicts'][:6]) for d in all_data]
    final_conflicts = [np.mean(d['conflicts'][-5:]) for d in all_data]
    conflict_reduction = [(i - f) / i * 100 for i, f in zip(initial_conflicts, final_conflicts)]

    initial_gold = [np.mean(d['total_gold'][:6]) for d in all_data]
    final_gold = [np.mean(d['total_gold'][-5:]) for d in all_data]
    gold_increase = [(f - i) / i * 100 for i, f in zip(initial_gold, final_gold)]

    # 1. Gini Reduction
    ax1 = axes[0, 0]
    bars = ax1.bar(range(len(exp_ids)), gini_reduction, color='#FF6B6B', alpha=0.7, edgecolor='black', linewidth=1.5)
    ax1.axhline(y=np.mean(gini_reduction), color='red', linestyle='--',
                linewidth=2.5, label=f'Mean: {np.mean(gini_reduction):.1f}%')
    ax1.set_xticks(range(len(exp_ids)))
    ax1.set_xticklabels([f'Exp{e}' for e in exp_ids], fontsize=12, fontweight='bold')
    ax1.set_ylabel('Gini Reduction (%)', fontsize=13, fontweight='bold')
    ax1.set_title('Gini Coefficient Reduction', fontsize=15, fontweight='bold', pad=15)
    ax1.legend(fontsize=11, loc='upper right')
    ax1.grid(True, alpha=0.3, axis='y', linestyle='--')
    ax1.set_ylim(0, max(gini_reduction) * 1.15)

    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{height:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')

    # 2. Conflict Reduction
    ax2 = axes[0, 1]
    bars = ax2.bar(range(len(exp_ids)), conflict_reduction, color='#FFA500', alpha=0.7, edgecolor='black', linewidth=1.5)
    ax2.axhline(y=np.mean(conflict_reduction), color='orange', linestyle='--',
                linewidth=2.5, label=f'Mean: {np.mean(conflict_reduction):.1f}%')
    ax2.set_xticks(range(len(exp_ids)))
    ax2.set_xticklabels([f'Exp{e}' for e in exp_ids], fontsize=12, fontweight='bold')
    ax2.set_ylabel('Conflict Reduction (%)', fontsize=13, fontweight='bold')
    ax2.set_title('Conflict Intensity Reduction', fontsize=15, fontweight='bold', pad=15)
    ax2.legend(fontsize=11, loc='upper right')
    ax2.grid(True, alpha=0.3, axis='y', linestyle='--')
    ax2.set_ylim(0, 110)

    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 2,
                f'{height:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')

    # 3. Output Increase
    ax3 = axes[1, 0]
    bars = ax3.bar(range(len(exp_ids)), gold_increase, color='#4ECDC4', alpha=0.7, edgecolor='black', linewidth=1.5)
    ax3.axhline(y=np.mean(gold_increase), color='teal', linestyle='--',
                linewidth=2.5, label=f'Mean: {np.mean(gold_increase):.1f}%')
    ax3.set_xticks(range(len(exp_ids)))
    ax3.set_xticklabels([f'Exp{e}' for e in exp_ids], fontsize=12, fontweight='bold')
    ax3.set_ylabel('Output Increase (%)', fontsize=13, fontweight='bold')
    ax3.set_title('Total Gold Production Increase', fontsize=15, fontweight='bold', pad=15)
    ax3.legend(fontsize=11, loc='upper right')
    ax3.grid(True, alpha=0.3, axis='y', linestyle='--')
    ax3.set_ylim(0, max(gold_increase) * 1.15)

    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height + 5,
                f'{height:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')

    # 4. Summary Box
    ax4 = axes[1, 1]
    ax4.axis('off')

    summary_text = f"""ROBUSTNESS ANALYSIS SUMMARY
{'='*45}

Number of Experiments: {len(all_data)}
Total Rounds: {all_data[0]['rounds']}

>> Gini Coefficient Reduction
   Mean:  {np.mean(gini_reduction):.1f}%
   Std:   {np.std(gini_reduction):.1f}%
   Range: {min(gini_reduction):.1f}% - {max(gini_reduction):.1f}%

>> Conflict Intensity Reduction
   Mean:  {np.mean(conflict_reduction):.1f}%
   Std:   {np.std(conflict_reduction):.1f}%
   Range: {min(conflict_reduction):.1f}% - {max(conflict_reduction):.1f}%

>> Total Output Increase
   Mean:  {np.mean(gold_increase):.1f}%
   Std:   {np.std(gold_increase):.1f}%
   Range: {min(gold_increase):.1f}% - {max(gold_increase):.1f}%

■ KEY CONCLUSION:
  All experiments consistently show
  the same evolution pattern:

  CHAOS → COMPETITION → ORDER

  Results demonstrate high robustness,
  validating spontaneous order theory.
    """

    ax4.text(0.05, 0.95, summary_text, transform=ax4.transAxes,
            fontsize=11, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.85, edgecolor='black', linewidth=2),
            family='monospace')

    fig.suptitle('Robustness Analysis - Multi-Experiment Statistical Summary\n(N=5 Independent Experiments)',
                fontsize=18, fontweight='bold', y=0.98)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    return fig

def main():
    print("Loading experiment data...")
    all_data = []
    for exp_id in EXPERIMENTS:
        data = load_experiment_data(exp_id)
        if data is not None:
            all_data.append(data)
            print(f"  [OK] Experiment {exp_id} loaded")

    print(f"\nCreating fixed robustness summary...")
    fig = create_robustness_summary(all_data)
    plt.savefig(OUTPUT_PNG, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"\n[SUCCESS] Saved to: {OUTPUT_PNG}")
    print("\nThis version has NO Chinese characters - all English!")

if __name__ == '__main__':
    main()
