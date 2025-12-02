# -*- coding: utf-8 -*-
"""
修改版：多组实验对比GIF - 使用具体参数标签
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from PIL import Image
import io
import os

# =================== 配置 ===================
BASE_DIR = "D:/yulan-onesim/YuLan-OneSim/my"

# 实验配置：ID -> (代理数, 地块数, 显示标签)
EXPERIMENTS = {
    100: (10, 100, '10 agents, 100 plots'),
    101: (10, 80, '10 agents, 80 plots'),
    102: (12, 100, '12 agents, 100 plots'),
    103: (50, 100, '50 agents, 100 plots'),
    104: (20, 100, '20 agents, 100 plots')
}

OUTPUT_GIF = "D:/yulan-onesim/YuLan-OneSim/my/demo_tools/comparison/multi_experiment_evolution_labeled.gif"
DURATION_PER_FRAME = 600  # 每帧600ms

# =================== 工具函数 ===================
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
        'label': EXPERIMENTS[exp_id][2],  # 使用自定义标签
        'gini': gini_values,
        'conflicts': total_conflicts.tolist(),
        'total_gold': round_metrics_df['total_gold'].tolist(),
        'rounds': len(gini_values)
    }

# =================== 创建对比GIF ==========
def create_comparison_gif(all_data):
    """创建多实验对比的GIF动画"""
    print("Generating comparison GIF with custom labels...")

    plt.rcParams['font.sans-serif'] = ['Arial']
    plt.rcParams['axes.unicode_minus'] = False

    max_rounds = max(len(d['gini']) for d in all_data)
    colors = plt.cm.Set2(np.linspace(0, 1, len(all_data)))

    frames = []

    for round_num in range(max_rounds):
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))

        # ========== 子图1: Gini演化 ==========
        ax1 = axes[0]
        for i, data in enumerate(all_data):
            if round_num < len(data['gini']):
                ax1.plot(range(round_num + 1), data['gini'][:round_num + 1],
                        linewidth=3, color=colors[i],
                        label=data['label'], marker='o', markersize=5,
                        markevery=max(1, round_num//5))

        ax1.set_xlim(0, max_rounds - 1)
        ax1.set_ylim(0, max(max(d['gini']) for d in all_data) + 0.1)
        ax1.set_xlabel('Round', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Gini Coefficient', fontsize=12, fontweight='bold')
        ax1.set_title('Wealth Inequality Evolution', fontsize=14, fontweight='bold', pad=10)
        ax1.legend(loc='upper right', fontsize=9, framealpha=0.9)
        ax1.grid(True, alpha=0.3, linestyle='--')

        # ========== 子图2: 冲突演化 ==========
        ax2 = axes[1]
        for i, data in enumerate(all_data):
            if round_num < len(data['conflicts']):
                ax2.plot(range(round_num + 1), data['conflicts'][:round_num + 1],
                        linewidth=3, color=colors[i],
                        label=data['label'], marker='s', markersize=4,
                        markevery=max(1, round_num//5))

        ax2.set_xlim(0, max_rounds - 1)
        ax2.set_ylim(0, max(max(d['conflicts']) for d in all_data) + 2)
        ax2.set_xlabel('Round', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Total Conflicts', fontsize=12, fontweight='bold')
        ax2.set_title('Conflict Intensity Evolution', fontsize=14, fontweight='bold', pad=10)
        ax2.legend(loc='upper right', fontsize=9, framealpha=0.9)
        ax2.grid(True, alpha=0.3, linestyle='--')

        # ========== 子图3: 产出演化 ==========
        ax3 = axes[2]
        for i, data in enumerate(all_data):
            if round_num < len(data['total_gold']):
                ax3.plot(range(round_num + 1), data['total_gold'][:round_num + 1],
                        linewidth=3, color=colors[i],
                        label=data['label'])

        ax3.set_xlim(0, max_rounds - 1)
        ax3.set_ylim(0, max(max(d['total_gold']) for d in all_data) + 10)
        ax3.set_xlabel('Round', fontsize=12, fontweight='bold')
        ax3.set_ylabel('Total Gold', fontsize=12, fontweight='bold')
        ax3.set_title('Total Output Evolution', fontsize=14, fontweight='bold', pad=10)
        ax3.legend(loc='lower right', fontsize=9, framealpha=0.9)
        ax3.grid(True, alpha=0.3, linestyle='--')

        # 阶段标注
        if round_num <= 5:
            phase = f'Round {round_num}: Chaos Phase'
            phase_color = 'red'
        elif round_num <= 15:
            phase = f'Round {round_num}: Competition Phase'
            phase_color = 'orange'
        else:
            phase = f'Round {round_num}: Order Phase'
            phase_color = 'green'

        fig.suptitle(f'{phase}\nMulti-Experiment Comparison (N={len(all_data)})',
                    fontsize=16, fontweight='bold', color=phase_color)

        plt.tight_layout(rect=[0, 0, 1, 0.95])

        # 转换为PIL Image
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        pil_image = Image.open(buf).copy()
        buf.close()
        plt.close(fig)

        frames.append(pil_image)

        if (round_num + 1) % 5 == 0:
            print(f"  Generated frame {round_num + 1}/{max_rounds}")

    # 保存GIF
    print("Saving GIF...")
    frames[0].save(
        OUTPUT_GIF,
        save_all=True,
        append_images=frames[1:],
        duration=DURATION_PER_FRAME,
        loop=0,
        optimize=False
    )

    file_size = os.path.getsize(OUTPUT_GIF) / 1024 / 1024
    print(f"GIF saved: {OUTPUT_GIF} ({file_size:.2f} MB)")

# =================== 主函数 ===================
def main():
    print("="*60)
    print("  Multi-Experiment GIF Generator (Custom Labels)")
    print("="*60)
    print()

    print("Loading experiment data...")
    all_data = []
    for exp_id in EXPERIMENTS.keys():
        agents, plots, label = EXPERIMENTS[exp_id]
        print(f"  Loading Exp{exp_id}: {label}...")
        data = load_experiment_data(exp_id)
        if data is not None:
            all_data.append(data)
            print(f"    [OK] {data['rounds']} rounds loaded")
        else:
            print(f"    [SKIP] Data not found")

    if len(all_data) == 0:
        print("\n[ERROR] No experiment data found!")
        return

    print(f"\n[OK] Loaded {len(all_data)} experiments")
    print("\nCreating GIF animation with custom labels...")
    create_comparison_gif(all_data)

    print("\n" + "="*60)
    print("SUCCESS!")
    print("="*60)
    print(f"File: {OUTPUT_GIF}")
    print("\nLabels used:")
    for exp_id, (agents, plots, label) in EXPERIMENTS.items():
        print(f"  Exp{exp_id} → {label}")
    print("="*60)

if __name__ == '__main__':
    main()
