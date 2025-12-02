# -*- coding: utf-8 -*-
"""
交互式网格演化动画 - 展示财产权从混沌到秩序的形成过程
输入: 104_decisions.jsonl, ownership_timeseries.csv
输出: grid_evolution.mp4 (可嵌入PPT) + 交互式HTML
"""

import json
import csv
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Rectangle
from matplotlib.colors import ListedColormap
import numpy as np

# =================== 配置 ===================
DECISIONS_PATH = "D:/yulan-onesim/YuLan-OneSim/my/104/104_decisions.jsonl"
OWNERSHIP_CSV = "D:/yulan-onesim/YuLan-OneSim/my/104/ownership_timeseries.csv"
OUTPUT_VIDEO = "D:/yulan-onesim/YuLan-OneSim/my/demo_tools/grid_evolution.mp4"
OUTPUT_HTML = "D:/yulan-onesim/YuLan-OneSim/my/demo_tools/grid_evolution_interactive.html"

GRID_ROWS = 10
GRID_COLS = 10
FPS = 2  # 每秒2帧，30回合约15秒

# =================== 数据加载 ===================
def load_ownership_timeseries():
    """从CSV加载每回合的领地归属"""
    with open(OWNERSHIP_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        data = list(reader)

    # 提取代理列表
    agents = [k for k in data[0].keys() if k != 'round']

    # 构建回合数据
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
    """加载决策数据以获取每回合的行动信息"""
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
    """从统计数据重建完整的网格归属（近似）"""
    # 注意：这里需要从decisions.jsonl中重建，因为ownership_timeseries只有统计数据
    # 我们需要回放模拟来获得准确的网格状态

    grids = []
    ownership = {(r, c): None for r in range(GRID_ROWS) for c in range(GRID_COLS)}

    # 简化版本：从decisions回放
    decisions = load_decisions()

    import random
    rnd = random.Random(42)  # 与模拟器一致的种子

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
                # 将agent_id映射到索引
                agent_idx = agents.index(owner) if owner in agents else -1
                grid[r, c] = agent_idx + 1  # 0表示空地，1-20表示代理

        grids.append(grid.copy())

    return grids

# =================== 可视��� ===================
def create_animation(grids, rounds_data, agents):
    """创建动画"""
    fig, ax = plt.subplots(figsize=(12, 10))

    # 颜色映射：0=黑色(空地)，1-20=不同颜色
    colors = ['#000000'] + list(plt.cm.tab20.colors[:len(agents)])
    cmap = ListedColormap(colors)

    im = ax.imshow(grids[0], cmap=cmap, vmin=0, vmax=len(agents),
                   interpolation='nearest', aspect='auto')

    # 添加网格线
    ax.set_xticks(np.arange(-0.5, GRID_COLS, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, GRID_ROWS, 1), minor=True)
    ax.grid(which='minor', color='white', linestyle='-', linewidth=0.5)
    ax.tick_params(which='minor', size=0)

    # 标题
    title = ax.text(0.5, 1.05, '', transform=ax.transAxes,
                    ha='center', fontsize=16, fontweight='bold')

    # 添加阶段标注
    phase_text = ax.text(0.5, 1.02, '', transform=ax.transAxes,
                         ha='center', fontsize=12, style='italic')

    # 统计信息
    stats_text = ax.text(0.02, 0.98, '', transform=ax.transAxes,
                         ha='left', va='top', fontsize=10,
                         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    def update(frame):
        im.set_array(grids[frame])

        # 更新标题
        round_num = frame
        title.set_text(f'Round {round_num}: Property Rights Evolution')

        # 阶段判断
        if round_num <= 5:
            phase = 'Chaos Phase (初始混沌)'
            phase_color = 'red'
        elif round_num <= 15:
            phase = 'Competition Phase (激烈竞争)'
            phase_color = 'orange'
        else:
            phase = 'Order Phase (秩序稳定)'
            phase_color = 'green'

        phase_text.set_text(phase)
        phase_text.set_color(phase_color)

        # 统计信息
        grid = grids[frame]
        occupied = np.sum(grid > 0)
        empty = np.sum(grid == 0)

        # 计算集中度（多少个代理拥有领地）
        unique_owners = len(np.unique(grid[grid > 0]))

        stats = f'Round {round_num}\n'
        stats += f'Occupied: {occupied}/{GRID_ROWS*GRID_COLS}\n'
        stats += f'Empty: {empty}\n'
        stats += f'Active Owners: {unique_owners}/{len(agents)}'

        stats_text.set_text(stats)

        return im, title, phase_text, stats_text

    ani = animation.FuncAnimation(fig, update, frames=len(grids),
                                  interval=1000/FPS, blit=True, repeat=True)

    return ani, fig

# =================== 主函数 ===================
def main():
    print("Loading data...")
    rounds_data, agents = load_ownership_timeseries()

    print("Reconstructing ownership grids...")
    grids = reconstruct_ownership_grid(rounds_data, agents)

    print(f"Creating animation for {len(grids)} rounds...")
    ani, fig = create_animation(grids, rounds_data, agents)

    # 保存视频
    print(f"Saving video to {OUTPUT_VIDEO}...")
    Writer = animation.writers['ffmpeg']
    writer = Writer(fps=FPS, metadata=dict(artist='Property Rights Simulation'),
                    bitrate=1800)
    ani.save(OUTPUT_VIDEO, writer=writer)

    print("Done! Video saved.")
    print(f"\n使用方式：")
    print(f"1. 将 {OUTPUT_VIDEO} 嵌入PPT中")
    print(f"2. 在汇报时播放，展示从混沌到秩序的演化过程")

if __name__ == '__main__':
    main()
