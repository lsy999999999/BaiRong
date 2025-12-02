# -*- coding: utf-8 -*-
"""
网格演化静态帧序列 - 不需要ffmpeg的替代方案
生成关键回合的静态图，可以在PPT中手动翻页展示
"""

import json
import csv
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
import random

# =================== 配置 ===================
DECISIONS_PATH = "D:/yulan-onesim/YuLan-OneSim/my/104/104_decisions.jsonl"
OWNERSHIP_CSV = "D:/yulan-onesim/YuLan-OneSim/my/104/ownership_timeseries.csv"
OUTPUT_DIR = "D:/yulan-onesim/YuLan-OneSim/my/demo_tools/grid_frames"

GRID_ROWS = 10
GRID_COLS = 10

# 选择要展示的关键回合
KEY_ROUNDS = [0, 2, 5, 10, 15, 20, 25, 29]  # 8个关键帧

# =================== 数据加载 ===================
def load_ownership_timeseries():
    """从CSV加载每回合的领地归属"""
    with open(OWNERSHIP_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        data = list(reader)

    agents = [k for k in data[0].keys() if k != 'round']

    rounds_data = []
    for row in data:
        round_num = int(row['round'])
        ownership = {agent: int(row[agent]) for agent in agents}
        rounds_data.append({
            'round': round_num,
            'ownership': ownership
        })

    return rounds_data, agents

def load_decisions():
    """加载决策数据"""
    decisions_by_round = {}

    with open(DECISIONS_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            round_idx = rec['round_index']
            agent_id = rec['agent_id']
            plan = rec['plan']

            if round_idx not in decisions_by_round:
                decisions_by_round[round_idx] = {}

            decisions_by_round[round_idx][agent_id] = {
                'claims': plan.get('claims', []),
                'raids': plan.get('raids', []),
                'defend': plan.get('defend', []),
                'mining': plan.get('mining', [])
            }

    return decisions_by_round

def reconstruct_ownership_grid(rounds_data, agents):
    """重建网格归属"""
    grids = []
    ownership = {(r, c): None for r in range(GRID_ROWS) for c in range(GRID_COLS)}

    decisions = load_decisions()
    rnd = random.Random(42)

    for round_num in range(len(rounds_data)):
        plans = decisions.get(round_num, {})

        # a) 处理抢占/防御
        defend_map = {}
        for aid, p in plans.items():
            for rc in p.get('defend', []):
                cell = (rc[0], rc[1])
                if ownership.get(cell) == aid:
                    defend_map[cell] = aid

        raids_map = {}
        for aid, p in plans.items():
            for rc in p.get('raids', []):
                cell = (rc[0], rc[1])
                cur = ownership.get(cell)
                if cur is not None and cur != aid:
                    if cell not in raids_map:
                        raids_map[cell] = []
                    raids_map[cell].append(aid)

        for cell, challengers in raids_map.items():
            cur = ownership.get(cell)
            if cur is None:
                continue
            if defend_map.get(cell) != cur:
                winner = rnd.choice(challengers)
                ownership[cell] = winner

        # b) 处理占领空地
        claim_map = {}
        for aid, p in plans.items():
            for rc in p.get('claims', []):
                cell = (rc[0], rc[1])
                if ownership.get(cell) is None:
                    if cell not in claim_map:
                        claim_map[cell] = []
                    claim_map[cell].append(aid)

        for cell, claimers in claim_map.items():
            if ownership.get(cell) is not None:
                continue
            if len(claimers) == 1:
                ownership[cell] = claimers[0]
            else:
                winner = rnd.choice(claimers)
                ownership[cell] = winner

        # 保存当前回合的网格状态
        grid = np.zeros((GRID_ROWS, GRID_COLS), dtype=int)
        for (r, c), owner in ownership.items():
            if owner is not None:
                agent_idx = agents.index(owner) if owner in agents else -1
                grid[r, c] = agent_idx + 1

        grids.append(grid.copy())

    return grids

# =================== 创建静态帧 ===================
def create_frame(grid, round_num, agents, output_path):
    """创建单个静态帧"""
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False

    fig, ax = plt.subplots(figsize=(10, 9))

    # 颜色映射
    colors = ['#000000'] + list(plt.cm.tab20.colors[:len(agents)])
    cmap = ListedColormap(colors)

    im = ax.imshow(grid, cmap=cmap, vmin=0, vmax=len(agents),
                   interpolation='nearest', aspect='auto')

    # 添加网格线
    ax.set_xticks(np.arange(-0.5, GRID_COLS, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, GRID_ROWS, 1), minor=True)
    ax.grid(which='minor', color='white', linestyle='-', linewidth=0.5)
    ax.tick_params(which='minor', size=0)

    # 标题
    if round_num <= 5:
        phase = 'Chaos Phase (混沌期)'
        phase_color = 'red'
    elif round_num <= 15:
        phase = 'Competition Phase (竞争期)'
        phase_color = 'orange'
    else:
        phase = 'Order Phase (秩序期)'
        phase_color = 'green'

    ax.set_title(f'Round {round_num}: {phase}\nProperty Rights Evolution',
                 fontsize=16, fontweight='bold', color=phase_color, pad=15)

    # 统计信息
    occupied = np.sum(grid > 0)
    empty = np.sum(grid == 0)
    unique_owners = len(np.unique(grid[grid > 0]))

    stats_text = f'Occupied: {occupied}/{GRID_ROWS*GRID_COLS}\n'
    stats_text += f'Empty: {empty}\n'
    stats_text += f'Active Owners: {unique_owners}/{len(agents)}'

    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
            ha='left', va='top', fontsize=11,
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9))

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

# =================== 主函数 ===================
def main():
    import os

    # 创建输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Loading data...")
    rounds_data, agents = load_ownership_timeseries()

    print("Reconstructing ownership grids...")
    grids = reconstruct_ownership_grid(rounds_data, agents)

    print(f"Creating frames for rounds: {KEY_ROUNDS}")
    for round_num in KEY_ROUNDS:
        if round_num < len(grids):
            output_path = f"{OUTPUT_DIR}/frame_round_{round_num:02d}.png"
            create_frame(grids[round_num], round_num, agents, output_path)
            print(f"  [OK] Frame {round_num} saved to {output_path}")

    print("\nDone!")
    print(f"\n生成的帧图片位置: {OUTPUT_DIR}")
    print(f"\n使用方式：")
    print(f"1. 将这些图片按顺序插入PPT（每张占一页）")
    print(f"2. 演讲时通过翻页展示演化过程")
    print(f"3. 或者使用PPT的页面切换动画效果")
    print(f"\n💡 更好的方案：直接在演示时打开 interactive_dashboard.html")

if __name__ == '__main__':
    main()
