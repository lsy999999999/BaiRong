# -*- coding: utf-8 -*-
"""
综合Dashboard - 汇报时的交互式可视化面板
可以实时切换回合，查看各项指标的动态变化
"""

import json
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# =================== 配置 ===================
DECISIONS_PATH = "D:/yulan-onesim/YuLan-OneSim/my/104/104_decisions.jsonl"
OWNERSHIP_CSV = "D:/yulan-onesim/YuLan-OneSim/my/104/ownership_timeseries.csv"
ROUND_METRICS_CSV = "D:/yulan-onesim/YuLan-OneSim/my/104/round_metrics.csv"
AGENT_METRICS_CSV = "D:/yulan-onesim/YuLan-OneSim/my/104/agent_metrics.csv"
OUTPUT_HTML = "D:/yulan-onesim/YuLan-OneSim/my/demo_tools/interactive_dashboard.html"

GRID_ROWS = 10
GRID_COLS = 10

# =================== 数据加载 ===================
def load_all_data():
    """加载所有数据"""
    # 1. 领地时序
    ownership_df = pd.read_csv(OWNERSHIP_CSV)

    # 2. 回合指标
    round_metrics_df = pd.read_csv(ROUND_METRICS_CSV)

    # 3. 代理指标
    agent_metrics_df = pd.read_csv(AGENT_METRICS_CSV)

    # 4. 决策数据（重建网格）
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

            decisions_by_round[round_idx][agent_id] = plan

    return ownership_df, round_metrics_df, agent_metrics_df, decisions_by_round

def reconstruct_grids(ownership_df, decisions_by_round):
    """重建每回合的网格状态"""
    agents = [col for col in ownership_df.columns if col != 'round']

    import random
    rnd = random.Random(42)

    grids = []
    ownership = {(r, c): None for r in range(GRID_ROWS) for c in range(GRID_COLS)}

    for round_num in range(len(ownership_df)):
        plans = decisions_by_round.get(round_num, {})

        # 简化的结算逻辑（与模拟器一致）
        # a) 抢占/防御
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

        # b) 占领空地
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

        # 保存网格
        grid = [[None for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        for (r, c), owner in ownership.items():
            grid[r][c] = owner

        grids.append(grid)

    return grids, agents

def calculate_gini_timeseries(ownership_df):
    """计算每回合的Gini系数"""
    agents = [col for col in ownership_df.columns if col != 'round']
    gini_values = []

    for _, row in ownership_df.iterrows():
        values = [row[agent] for agent in agents]
        gini = calculate_gini(values)
        gini_values.append(gini)

    return gini_values

def calculate_gini(values):
    """计算Gini系数"""
    values = sorted([v for v in values if v >= 0])
    n = len(values)
    if n == 0 or sum(values) == 0:
        return 0.0

    cum = sum((i + 1) * v for i, v in enumerate(values))
    s = sum(values)
    return (2 * cum) / (n * s) - (n + 1) / n

# =================== 创建Dashboard ===================
def create_dashboard(ownership_df, round_metrics_df, agent_metrics_df, grids, agents):
    """创建交互式Dashboard"""

    # 计算Gini时序
    gini_values = calculate_gini_timeseries(ownership_df)

    # 创建子图
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=(
            '网格状态 (Grid Ownership)',
            '财富不平等演化 (Gini Coefficient)',
            '冲突演化 (Conflict Evolution)',
            '体力分配演化 (Stamina Allocation)',
            '总产出演化 (Total Gold Production)',
            '领地数量演化 (Territory Distribution)'
        ),
        specs=[
            [{'type': 'heatmap', 'rowspan': 2}, {'type': 'scatter'}],
            [None, {'type': 'scatter'}],
            [{'type': 'scatter'}, {'type': 'scatter'}]
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.15
    )

    # ========== 1. 网格热力图（可交互切换回合）==========
    # 为每个回合创建一帧
    frames = []
    for round_num, grid in enumerate(grids):
        # 将agent名称映射为数字
        grid_numeric = np.zeros((GRID_ROWS, GRID_COLS))
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                owner = grid[r][c]
                if owner is not None:
                    grid_numeric[r][c] = agents.index(owner) + 1

        heatmap_data = go.Heatmap(
            z=grid_numeric,
            colorscale='Viridis',
            showscale=False,
            hovertemplate='Row: %{y}<br>Col: %{x}<br>Owner: %{z}<extra></extra>'
        )

        frames.append(go.Frame(
            data=[heatmap_data],
            name=str(round_num),
            traces=[0]
        ))

    # 初始网格
    grid_numeric = np.zeros((GRID_ROWS, GRID_COLS))
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            owner = grids[0][r][c]
            if owner is not None:
                grid_numeric[r][c] = agents.index(owner) + 1

    fig.add_trace(
        go.Heatmap(
            z=grid_numeric,
            colorscale='Viridis',
            showscale=False,
            hovertemplate='Row: %{y}<br>Col: %{x}<br>Owner: %{z}<extra></extra>'
        ),
        row=1, col=1
    )

    # ========== 2. Gini系数演化 ==========
    fig.add_trace(
        go.Scatter(
            x=list(range(len(gini_values))),
            y=gini_values,
            mode='lines+markers',
            name='Gini Coefficient',
            line=dict(color='red', width=2),
            marker=dict(size=6)
        ),
        row=1, col=2
    )

    # 添加阶段分隔线
    fig.add_vline(x=5, line_dash="dash", line_color="gray", row=1, col=2)
    fig.add_vline(x=15, line_dash="dash", line_color="gray", row=1, col=2)

    # ========== 3. 冲突演化 ==========
    fig.add_trace(
        go.Scatter(
            x=round_metrics_df['round'],
            y=round_metrics_df['contested_raids'] + round_metrics_df['contested_claims'],
            mode='lines+markers',
            name='Total Conflicts',
            line=dict(color='orange', width=2)
        ),
        row=2, col=2
    )

    # ========== 4. 体力分配堆叠图 ==========
    stamina_categories = ['claims', 'raids', 'defend', 'mining_stamina']
    colors = ['#FFA07A', '#FF6347', '#4682B4', '#90EE90']

    for i, cat in enumerate(stamina_categories):
        fig.add_trace(
            go.Scatter(
                x=round_metrics_df['round'],
                y=round_metrics_df[cat],
                mode='lines',
                name=cat.replace('_', ' ').title(),
                stackgroup='one',
                fillcolor=colors[i]
            ),
            row=3, col=1
        )

    # ========== 5. 总产出演化 ==========
    fig.add_trace(
        go.Scatter(
            x=round_metrics_df['round'],
            y=round_metrics_df['total_gold'],
            mode='lines+markers',
            name='Total Gold',
            line=dict(color='gold', width=2),
            fill='tozeroy'
        ),
        row=3, col=2
    )

    # ========== 6. 领地分布（顶部代理）==========
    # 选择最终领地最多的前5个代理
    final_ownership = ownership_df.iloc[-1]
    top_agents = final_ownership[agents].nlargest(5).index.tolist()

    for agent in top_agents:
        fig.add_trace(
            go.Scatter(
                x=ownership_df['round'],
                y=ownership_df[agent],
                mode='lines',
                name=agent,
                line=dict(width=2)
            ),
            row=3, col=2
        )

    # 更新布局
    fig.update_layout(
        title_text="财产权演化综合Dashboard - From Chaos to Order",
        title_font_size=20,
        showlegend=True,
        height=1200,
        hovermode='closest',
        # 添加滑动条控制回合
        sliders=[{
            'active': 0,
            'yanchor': 'top',
            'y': 0.95,
            'xanchor': 'left',
            'currentvalue': {
                'prefix': 'Round: ',
                'visible': True,
                'xanchor': 'right'
            },
            'pad': {'b': 10, 't': 50},
            'len': 0.45,
            'x': 0.0,
            'steps': [
                {
                    'args': [[f.name], {
                        'frame': {'duration': 0, 'redraw': True},
                        'mode': 'immediate',
                        'transition': {'duration': 0}
                    }],
                    'label': str(k),
                    'method': 'animate'
                }
                for k, f in enumerate(frames)
            ]
        }]
    )

    # 设置帧
    fig.frames = frames

    # 更新坐标轴标签
    fig.update_xaxes(title_text="Round", row=1, col=2)
    fig.update_yaxes(title_text="Gini Coefficient", row=1, col=2)

    fig.update_xaxes(title_text="Round", row=2, col=2)
    fig.update_yaxes(title_text="Conflicts", row=2, col=2)

    fig.update_xaxes(title_text="Round", row=3, col=1)
    fig.update_yaxes(title_text="Stamina %", row=3, col=1)

    fig.update_xaxes(title_text="Round", row=3, col=2)
    fig.update_yaxes(title_text="Gold / Territory", row=3, col=2)

    return fig

# =================== 主函数 ===================
def main():
    print("Loading all data...")
    ownership_df, round_metrics_df, agent_metrics_df, decisions_by_round = load_all_data()

    print("Reconstructing grids...")
    grids, agents = reconstruct_grids(ownership_df, decisions_by_round)

    print("Creating interactive dashboard...")
    fig = create_dashboard(ownership_df, round_metrics_df, agent_metrics_df, grids, agents)

    print(f"Saving to {OUTPUT_HTML}...")
    fig.write_html(OUTPUT_HTML)

    print("Done!")
    print(f"\n使用方式：")
    print(f"1. 在浏览器中打开 {OUTPUT_HTML}")
    print(f"2. 使用滑动条切换回合，观察各指标的动态变化")
    print(f"3. 汇报时可以在浏览器中演示，或录制成视频嵌入PPT")

if __name__ == '__main__':
    main()
