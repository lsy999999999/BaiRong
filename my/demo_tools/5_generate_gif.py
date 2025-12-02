# -*- coding: utf-8 -*-
"""
网格演化GIF动图生成器 - 不需要ffmpeg
使用Pillow库生成GIF动画
"""

import json
import csv
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
import random
from PIL import Image
import io

# =================== 配置 ===================
DECISIONS_PATH = "D:/yulan-onesim/YuLan-OneSim/my/104/104_decisions.jsonl"
OWNERSHIP_CSV = "D:/yulan-onesim/YuLan-OneSim/my/104/ownership_timeseries.csv"
OUTPUT_GIF = "D:/yulan-onesim/YuLan-OneSim/my/demo_tools/grid_evolution.gif"

GRID_ROWS = 10
GRID_COLS = 10

# GIF参数
DURATION_PER_FRAME = 500  # 每帧显示时间(毫秒)，500ms = 0.5秒
SKIP_FRAMES = 1  # 每N帧保存一次(1=全部保存，2=每2帧保存1次)

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

# =================== 生成帧图像 ===================
def create_frame_image(grid, round_num, agents):
    """创建单帧的图像（返回PIL Image对象）"""
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

    # 标题和阶段
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

    # 转换为PIL Image
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    pil_image = Image.open(buf).copy()
    buf.close()
    plt.close(fig)

    return pil_image

# =================== 生成GIF ===================
def create_gif(grids, agents):
    """生成GIF动画"""
    print(f"Generating {len(grids)} frames...")

    frames = []
    for i, grid in enumerate(grids):
        if i % SKIP_FRAMES == 0:  # 按设定跳帧
            print(f"  Processing frame {i+1}/{len(grids)}...")
            frame_image = create_frame_image(grid, i, agents)
            frames.append(frame_image)

    print(f"Saving GIF with {len(frames)} frames...")

    # 保存为GIF
    frames[0].save(
        OUTPUT_GIF,
        save_all=True,
        append_images=frames[1:],
        duration=DURATION_PER_FRAME,
        loop=0,  # 0表示无限循环
        optimize=False  # 不优化以保持质量
    )

    print(f"GIF saved to: {OUTPUT_GIF}")
    print(f"File size: {round(Image.open(OUTPUT_GIF).tell() / 1024 / 1024, 2)} MB")

# =================== 主函数 ===================
def main():
    print("="*60)
    print("  GIF动图生成器 - 财产权演化动画")
    print("="*60)
    print()

    # 检查Pillow
    try:
        from PIL import Image
        print("[OK] Pillow已安装")
    except ImportError:
        print("[ERROR] 缺少Pillow库，请运行: pip install Pillow")
        return

    print("\n[Step 1/4] Loading data...")
    rounds_data, agents = load_ownership_timeseries()

    print("[Step 2/4] Reconstructing ownership grids...")
    grids = reconstruct_ownership_grid(rounds_data, agents)

    print(f"[Step 3/4] Creating GIF animation...")
    print(f"  - Total rounds: {len(grids)}")
    print(f"  - Frame skip: {SKIP_FRAMES} (showing every {SKIP_FRAMES} frame(s))")
    print(f"  - Duration per frame: {DURATION_PER_FRAME}ms")
    print()

    create_gif(grids, agents)

    print("\n[Step 4/4] Done!")
    print("\n" + "="*60)
    print("使用方式:")
    print("="*60)
    print(f"1. 打开文件: {OUTPUT_GIF}")
    print("2. 在PowerPoint中插入此GIF (插入 -> 图片)")
    print("3. GIF会自动循环播放")
    print()
    print("提示:")
    print("- 如果GIF文件太大，可以增大SKIP_FRAMES(如改为2)")
    print("- 如果播放太快，可以增大DURATION_PER_FRAME(如改为800)")
    print("- 如果需要调整，修改脚本顶部的参数后重新运行")
    print("="*60)

if __name__ == '__main__':
    main()
