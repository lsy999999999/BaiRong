import json
import csv
import os
import random
from collections import defaultdict, OrderedDict
from typing import Any, Dict, List, Tuple
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# --- 1. 参数设置 ---
# 脚本会自动尝试在 '101/' 子目录和当前目录中查找文件
DECISIONS_PATH = "D:/yulan-onesim/YuLan-OneSim/my/104/104_decisions.jsonl" 
REPLAY_SEED = 42

# --- 输出文件 ---
OUT_ROUND_ENHANCED_CSV = "D:/yulan-onesim/YuLan-OneSim/my/104/round_metrics_enhanced.csv"
FIG_STAMINA_ALLOCATION = "D:/yulan-onesim/YuLan-OneSim/my/104/fig_stamina_allocation.png"
FIG_TURNOVER_RATE = "D:/yulan-onesim/YuLan-OneSim/my/104/fig_territory_turnover.png"
FIG_GINI_EVOLUTION = "D:/yulan-onesim/YuLan-OneSim/my/104/fig_gini_evolution.png"

# --- 2. 辅助函数 ---

Cell = Tuple[int, int]

def load_decisions(path: str) -> List[Dict[str, Any]]:
    """Robustly loads decisions, trying both the primary path and a fallback."""
    if not os.path.exists(path):
        fallback_path = os.path.basename(path)
        if os.path.exists(fallback_path):
            path = fallback_path
            print(f"Info: Could not find at primary path. Using fallback: {path}")
        else:
            raise FileNotFoundError(f"Missing file at primary path ({DECISIONS_PATH}) and fallback ({fallback_path})")

    recs = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    recs.append(json.loads(line))
                except json.JSONDecodeError:
                    print(f"Warning: Skipping malformed line in {path}")
    if not recs:
        raise ValueError(f"No valid records found in {path}")
    return recs

def infer_world(recs: List[Dict[str, Any]]) -> Tuple[int, int, List[str], int, int, int]:
    first = recs[0]
    obs = first.get("observation", {})
    rows, cols = obs.get("grid_shape", [10, 10])
    S = obs.get("stamina_budget", 10)
    smax = obs.get("max_mining_per_plot", 3)
    seen = OrderedDict()
    for r in recs:
        a = r.get("agent_id")
        if a and a not in seen:
            seen[a] = True
    agents = list(seen.keys())
    rounds = max(int(r.get("round_index", 0)) for r in recs) + 1
    return rows, cols, agents, S, smax, rounds

def resolve_round(ownership: Dict[Cell, str|None],
                  plans: Dict[str, Dict[str, Any]],
                  smax: int, q: int = 1,
                  rnd: random.Random = random) -> Tuple[Dict[str, int], List[Dict[str, Any]]]:
    # (This function remains the same as provided before)
    defend_map: Dict[Cell, str] = {}
    for aid, p in plans.items():
        for rc in p.get("defend", []):
            cell = tuple(rc)
            if ownership.get(cell) == aid:
                defend_map[cell] = aid
    raids_map: Dict[Cell, List[str]] = defaultdict(list)
    for aid, p in plans.items():
        for rc in p.get("raids", []):
            cell = tuple(rc)
            cur = ownership.get(cell)
            if cur is not None and cur != aid:
                raids_map[cell].append(aid)
    public_log: List[Dict[str, Any]] = []
    for cell, challengers in raids_map.items():
        cur = ownership.get(cell)
        if cur is None: continue
        if defend_map.get(cell) == cur:
            public_log.append({"type": "raid_blocked", "cell": list(cell), "owner": cur, "challengers": challengers[:]})
        else:
            winner = rnd.choice(challengers)
            ownership[cell] = winner
            public_log.append({"type": "raid_success", "cell": list(cell), "from": cur, "to": winner, "others": [x for x in challengers if x != winner]})
    claim_map: Dict[Cell, List[str]] = defaultdict(list)
    for aid, p in plans.items():
        for rc in p.get("claims", []):
            cell = tuple(rc)
            if ownership.get(cell) is None:
                claim_map[cell].append(aid)
    for cell, claimers in claim_map.items():
        if ownership.get(cell) is not None: continue
        if len(claimers) == 1:
            winner = claimers[0]
        else:
            winner = rnd.choice(claimers)
        ownership[cell] = winner
        log_entry = {"type": "claim_success" if len(claimers) == 1 else "claim_tie", "cell": list(cell), "to": winner}
        if len(claimers) > 1:
            log_entry["others"] = [x for x in claimers if x != winner]
        public_log.append(log_entry)
    round_gold: Dict[str, int] = defaultdict(int)
    for aid, p in plans.items():
        for m in p.get("mining", []):
            cell = tuple(m["cell"])
            st = int(m.get("stamina", 0))
            # Mining is only successful if the agent OWNS the plot at the end of the round and DEFENDED it.
            if ownership.get(cell) == aid and cell in defend_map and st > 0:
                round_gold[aid] += q * min(st, smax)
    return round_gold, public_log

def gini(values: List[float]) -> float:
    n = len(values)
    if n == 0: return 0.0
    vals = sorted(v for v in values if v >= 0)
    if not vals or sum(vals) == 0: return 0.0
    s = sum(vals)
    cum = np.cumsum(vals)
    return (2 * np.sum(np.arange(1, n + 1) * np.array(vals)) / (n * s)) - (n + 1) / n if n > 0 and s > 0 else 0.0


def count_stamina(plan: Dict[str, Any]) -> Tuple[int, int, int, int]:
    s_claim = len(plan.get("claims", []))
    s_raid = len(plan.get("raids", []))
    s_defend = len(plan.get("defend", []))
    s_mining = sum(int(m.get("stamina", 0)) for m in plan.get("mining", []))
    return s_claim, s_raid, s_defend, s_mining

# --- 3. 主分析流程 ---
def main():
    try:
        recs = load_decisions(DECISIONS_PATH)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        return

    rows, cols, agents, S, smax, R = infer_world(recs)
    print(f"[Info] World: {rows}x{cols}, Agents: {len(agents)}, Rounds: {R}, S: {S}, s_max: {smax}")

    by_round: Dict[int, Dict[str, Dict[str, Any]]] = defaultdict(dict)
    for r in recs:
        by_round[int(r["round_index"])][r["agent_id"]] = r.get("plan", {})

    rnd = random.Random(REPLAY_SEED)
    ownership: Dict[Cell, str | None] = {(r, c): None for r in range(rows) for c in range(cols)}
    cum_gold: Dict[str, int] = {a: 0 for a in agents}
    round_metrics_list = []

    for t in range(R):
        plans = by_round.get(t, {})
        ownership_before = ownership.copy()

        total_s_claim, total_s_raid, total_s_defend, total_s_mining = 0, 0, 0, 0
        for a in agents:
            p = plans.get(a, {})
            c, r, d, m = count_stamina(p)
            total_s_claim += c
            total_s_raid += r
            total_s_defend += d
            total_s_mining += m

        total_stamina_spent = total_s_claim + total_s_raid + total_s_defend + total_s_mining
        stamina_ratios = {
            "claim_ratio": total_s_claim / total_stamina_spent if total_stamina_spent > 0 else 0,
            "raid_ratio": total_s_raid / total_stamina_spent if total_stamina_spent > 0 else 0,
            "defend_ratio": total_s_defend / total_stamina_spent if total_stamina_spent > 0 else 0,
            "mining_ratio": total_s_mining / total_stamina_spent if total_stamina_spent > 0 else 0,
        }

        round_gold, public_log = resolve_round(ownership, plans, smax, q=1, rnd=rnd)
        for a, g in round_gold.items():
            cum_gold[a] += g

        turnover_count = sum(1 for cell, owner in ownership_before.items() if owner != ownership.get(cell))
        current_gini = gini(list(cum_gold.values()))

        round_metrics_list.append({
            "round": t,
            "total_gold": sum(round_gold.values()),
            "contested_raids": sum(1 for e in public_log if "raid" in e["type"]),
            "contested_claims": sum(1 for e in public_log if e["type"] == "claim_tie"),
            **stamina_ratios,
            "territory_turnover": turnover_count,
            "gini_coefficient": current_gini,
        })

    df_rounds = pd.DataFrame(round_metrics_list)
    df_rounds.to_csv(OUT_ROUND_ENHANCED_CSV, index=False)
    print(f"\n[Output] Enhanced round metrics saved to {OUT_ROUND_ENHANCED_CSV}")

    # --- 4. 可视化 ---
    plt.style.use('seaborn-v0_8-whitegrid')

    # 可视化 1: 体力分配演化图
    fig1, ax1 = plt.subplots(figsize=(12, 7))
    stamina_cols = ['mining_ratio', 'defend_ratio', 'claim_ratio', 'raid_ratio']
    ax1.stackplot(
        df_rounds['round'], df_rounds[stamina_cols].T,
        labels=['Mining', 'Defend', 'Claim', 'Raid'], alpha=0.8,
        colors=['#2ca02c', '#1f77b4', '#ff7f0e', '#d62728']
    )
    ax1.set_title('Evolution of System-wide Stamina Allocation', fontsize=16)
    ax1.set_xlabel('Round', fontsize=12)
    ax1.set_ylabel('Percentage of Total Stamina', fontsize=12)
    ax1.set_xlim(0, R - 1)
    ax1.set_ylim(0, 1)
    ax1.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=4)
    plt.tight_layout(pad=3.0)
    plt.savefig(FIG_STAMINA_ALLOCATION)
    print(f"[Output] Stamina allocation evolution chart saved to {FIG_STAMINA_ALLOCATION}")

    # 可视化 2: 领地更迭率
    fig2, ax2 = plt.subplots(figsize=(12, 7))
    ax2.plot(df_rounds['round'], df_rounds['territory_turnover'], marker='o', linestyle='-', color='#1f77b4')
    ax2.set_title('Territory Turnover Rate per Round', fontsize=16)
    ax2.set_xlabel('Round', fontsize=12)
    ax2.set_ylabel('Number of Plots Changing Ownership', fontsize=12)
    ax2.set_xlim(0, R - 1)
    plt.tight_layout()
    plt.savefig(FIG_TURNOVER_RATE)
    print(f"[Output] Territory turnover rate chart saved to {FIG_TURNOVER_RATE}")

    # 可视化 3: 财富基尼系数演化
    fig3, ax3 = plt.subplots(figsize=(12, 7))
    ax3.plot(df_rounds['round'], df_rounds['gini_coefficient'], marker='o', linestyle='-', color='#d62728')
    ax3.set_title('Evolution of Wealth Inequality (Gini Coefficient)', fontsize=16)
    ax3.set_xlabel('Round', fontsize=12)
    ax3.set_ylabel('Gini Coefficient (0=Equality, 1=Inequality)', fontsize=12)
    ax3.set_xlim(0, R - 1)
    ax3.set_ylim(0, max(0.5, df_rounds['gini_coefficient'].max() * 1.1) if not df_rounds['gini_coefficient'].empty else 0.5)
    plt.tight_layout()
    plt.savefig(FIG_GINI_EVOLUTION)
    print(f"[Output] Gini coefficient evolution chart saved to {FIG_GINI_EVOLUTION}")

    print("\nAnalysis complete.")

if __name__ == "__main__":
    main()