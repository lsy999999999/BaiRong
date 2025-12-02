# -*- coding: utf-8 -*-
"""
分析脚本：读取 decisions.jsonl 回放博弈，统计代理与全局指标。
- 仅用标准库：json, csv, math, statistics, collections, random
- 输入：decisions.jsonl  (由 llm_decider.py 生成，包含每回合每代理的 plan)
- 可选：logs.csv         (用于对照 round_gold/cum_gold，不参与计算)
- 输出：
    - agent_metrics.csv
    - round_metrics.csv
    - ownership_timeseries.csv
使用：python src/analyze_decisions.py
"""

import json
import csv
import os
import math
import random
from collections import defaultdict, OrderedDict
from typing import Any, Dict, List, Tuple

# -------------------------
# 可调参数
# -------------------------

DECISIONS_PATH ="D:/yulan-onesim/YuLan-OneSim/my/104/104_decisions.jsonl"  # 必须存在
LOGS_CSV_PATH  = "D:/yulan-onesim/YuLan-OneSim/my/104/104_logs.csv"          # 可选，仅对照
OUT_AGENT_CSV  = "D:/yulan-onesim/YuLan-OneSim/my/104/agent_metrics.csv"
OUT_ROUND_CSV  = "D:/yulan-onesim/YuLan-OneSim/my/104/round_metrics.csv"
OUT_OWN_CSV    = "D:/yulan-onesim/YuLan-OneSim/my/104/ownership_timeseries.csv"

# 回放时随机种子（需与生成时一致才能完全对齐，否则仅保证统计一致性）
REPLAY_SEED = 42

# -------------------------
# 基础类型
# -------------------------
Cell = Tuple[int, int]

def _cell_key(c: Cell) -> str:
    return f"{c[0]},{c[1]}"

# -------------------------
# 读取 decisions.jsonl
# -------------------------
def load_decisions(path: str) -> List[Dict[str, Any]]:
    recs = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                recs.append(json.loads(line))
            except Exception:
                # 忽略坏行
                pass
    if not recs:
        raise FileNotFoundError(f"No valid records in {path}")
    return recs

def infer_world(recs: List[Dict[str, Any]]) -> Tuple[int,int,List[str],int,int,int]:
    """从第一条记录中推断 grid_shape/agents/S/smax/rounds"""
    first = recs[0]
    obs = first.get("observation", {})
    rows, cols = obs.get("grid_shape", [2,2])
    S = obs.get("stamina_budget", 10)
    smax = obs.get("max_mining_per_plot", 3)
    # 代理列表：按 decisions.jsonl 出现顺序（更接近生成器顺序）
    seen = OrderedDict()
    for r in recs:
        a = r.get("agent_id")
        if a and a not in seen:
            seen[a] = True
    agents = list(seen.keys())
    rounds = max(int(r.get("round_index", 0)) for r in recs) + 1
    return rows, cols, agents, S, smax, rounds

# -------------------------
# 回放（与模拟器一致的结算逻辑）
# -------------------------
def resolve_round(ownership: Dict[Cell, str|None],
                  plans: Dict[str, Dict[str, Any]],
                  smax: int,
                  q: int = 1,
                  rnd: random.Random = random) -> Tuple[Dict[str,int], List[Dict[str,Any]]]:
    """返回 (round_gold, public_log)，会原地修改 ownership"""
    # a) 抢占/防御
    defend_map: Dict[Cell, str] = {}
    for aid, p in plans.items():
        for rc in p.get("defend", []):
            cell = (rc[0], rc[1])
            if ownership.get(cell) == aid:
                defend_map[cell] = aid

    raids_map: Dict[Cell, List[str]] = defaultdict(list)
    for aid, p in plans.items():
        for rc in p.get("raids", []):
            cell = (rc[0], rc[1])
            cur = ownership.get(cell)
            if cur is not None and cur != aid:
                raids_map[cell].append(aid)

    public_log: List[Dict[str,Any]] = []

    for cell, challengers in raids_map.items():
        cur = ownership.get(cell)
        if cur is None:
            continue
        if defend_map.get(cell) == cur:
            public_log.append({"type":"raid_blocked","cell":[cell[0],cell[1]],"owner":cur,"challengers":challengers[:]})
        else:
            winner = rnd.choice(challengers)
            ownership[cell] = winner
            public_log.append({"type":"raid_success","cell":[cell[0],cell[1]],"from":cur,"to":winner,"others":[x for x in challengers if x!=winner]})

    # b) 占领空地
    claim_map: Dict[Cell, List[str]] = defaultdict(list)
    for aid, p in plans.items():
        for rc in p.get("claims", []):
            cell = (rc[0], rc[1])
            if ownership.get(cell) is None:
                claim_map[cell].append(aid)

    for cell, claimers in claim_map.items():
        if ownership.get(cell) is not None:
            continue
        if len(claimers) == 1:
            ownership[cell] = claimers[0]
            public_log.append({"type":"claim_success","cell":[cell[0],cell[1]],"to":claimers[0]})
        else:
            winner = rnd.choice(claimers)
            ownership[cell] = winner
            public_log.append({"type":"claim_tie","cell":[cell[0],cell[1]],"to":winner,"others":[x for x in claimers if x!=winner]})

    # c) 采矿
    defend_set = {(r,c) for (r,c),own in ownership.items() if defend_map.get((r,c)) == own}
    round_gold: Dict[str,int] = defaultdict(int)
    for aid, p in plans.items():
        for m in p.get("mining", []):
            cell = tuple(m["cell"])
            st = int(m.get("stamina", 0))
            if ownership.get(cell) == aid and cell in defend_set and st > 0:
                round_gold[aid] += q * min(st, smax)

    return round_gold, public_log

# -------------------------
# 统计工具
# -------------------------
def count_actions(plan: Dict[str,Any]) -> Tuple[int,int,int,int]:
    claims = len(plan.get("claims", []))
    raids  = len(plan.get("raids", []))
    defend = len(plan.get("defend", []))
    mining = sum(int(m.get("stamina",0)) for m in plan.get("mining", []))
    return claims, raids, defend, mining

def gini(values: List[float]) -> float:
    """Gini 系数，0=完全均等，1=极不均等。"""
    n = len(values)
    if n == 0:
        return 0.0
    vals = sorted(v for v in values if v >= 0)
    if not vals:
        return 0.0
    cum = 0.0
    for i, v in enumerate(vals, 1):
        cum += i * v
    s = sum(vals)
    return (2*cum)/(n*s) - (n+1)/n

# -------------------------
# 主流程
# -------------------------
def main():
    if not os.path.exists(DECISIONS_PATH):
        raise FileNotFoundError(f"Missing {DECISIONS_PATH}")

    recs = load_decisions(DECISIONS_PATH)
    rows, cols, agents, S, smax, R = infer_world(recs)

    print(f"[info] grid={rows}x{cols}, agents={len(agents)}, rounds={R}, S={S}, smax={smax}")

    # 组织为每回合 -> agent -> plan
    by_round: Dict[int, Dict[str, Dict[str,Any]]] = defaultdict(dict)
    for r in recs:
        ridx = int(r.get("round_index", 0))
        aid  = r.get("agent_id")
        plan = r.get("plan", {})
        if aid:
            by_round[ridx][aid] = plan

    # 回放
    rnd = random.Random(REPLAY_SEED)
    ownership: Dict[Cell, str|None] = {(r,c): None for r in range(rows) for c in range(cols)}
    cum_gold: Dict[str,int] = {a:0 for a in agents}

    # 动作累计
    act_counts = {a: {"claims":0,"raids":0,"defend":0,"mining_stamina":0} for a in agents}
    # 成功率分子/分母
    raid_success = {a: {"win":0, "try":0} for a in agents}
    claim_success = {a: {"win":0, "try":0} for a in agents}
    defend_block  = {a: {"block":0, "attacked":0} for a in agents}
    # 每回合持地
    own_ts: List[Dict[str,int]] = []

    # 回合级指标
    round_rows: List[Dict[str,Any]] = []

    for t in range(R):
        plans = by_round.get(t, {})
        # 统计预算与动作
        total_claims=total_raids=total_defend=total_mine=0
        for a in agents:
            p = plans.get(a, {"claims":[],"raids":[],"defend":[],"mining":[]})
            c,r_,d,m = count_actions(p)
            act_counts[a]["claims"] += c
            act_counts[a]["raids"]  += r_
            act_counts[a]["defend"] += d
            act_counts[a]["mining_stamina"] += m
            total_claims += c; total_raids += r_; total_defend += d; total_mine += m

        # 结算
        round_gold, public_log = resolve_round(ownership, plans, smax, q=1, rnd=rnd)
        for a,g in round_gold.items():
            cum_gold[a] += g

        # 成功/防御统计
        for evt in public_log:
            tp = evt.get("type")
            if tp == "raid_success":
                winner = evt.get("to")
                frm    = evt.get("from")
                cell   = tuple(evt.get("cell",[0,0]))
                if winner in raid_success: raid_success[winner]["win"] += 1
                # 所有挑战者都 +try（含胜者）
                for a in evt.get("others", []) + [winner]:
                    if a in raid_success: raid_success[a]["try"] += 1
            elif tp == "raid_blocked":
                owner  = evt.get("owner")
                chals  = evt.get("challengers",[])
                if owner in defend_block:
                    defend_block[owner]["block"] += 1
                    defend_block[owner]["attacked"] += 1
                for a in chals:
                    if a in raid_success:
                        raid_success[a]["try"] += 1
            elif tp in ("claim_success","claim_tie"):
                winner = evt.get("to")
                others = evt.get("others", [])
                if winner in claim_success:
                    claim_success[winner]["win"] += 1
                    claim_success[winner]["try"] += 1
                for a in others:
                    if a in claim_success:
                        claim_success[a]["try"] += 1

        # 每回合持地统计
        own_count = {a:0 for a in agents}
        for (r0,c0), own in ownership.items():
            if own in own_count:
                own_count[own] += 1
        own_ts.append({"round": t, **own_count})

        # 回合级汇总
        total_gold = sum(round_gold.get(a,0) for a in agents)
        # 争夺度
        contested_raids = sum(1 for e in public_log if e["type"] in ("raid_success","raid_blocked"))
        contested_claims= sum(1 for e in public_log if e["type"] in ("claim_tie",))
        # 理论上界（给出一个保守上界：min(总采矿体力, defend后仍归属的地数*smax)）
        defended_owned = 0
        # 粗估 defend 成功的集合：通过 public_log 的 raid_blocked 记账 + 未被列出为 raid_success 且被 defend 的地
        defended_cells = set()
        for a,p in plans.items():
            for rc in p.get("defend", []):
                cell = (rc[0], rc[1])
                # 最终如果还归属 a，则视为有效可矿（近似；与模拟器一致）
                if ownership.get(cell) == a:
                    defended_cells.add(cell)
        defended_owned = len(defended_cells)
        theo_cap = min(total_mine, defended_owned * smax)
        eff = (total_gold / theo_cap) if theo_cap > 0 else 0.0

        round_rows.append({
            "round": t,
            "total_gold": total_gold,
            "contested_raids": contested_raids,
            "contested_claims": contested_claims,
            "claims": total_claims,
            "raids": total_raids,
            "defend": total_defend,
            "mining_stamina": total_mine,
            "theoretical_upper_gold": theo_cap,
            "efficiency": round(eff, 4),
        })

    # 代理级指标导出
    with open(OUT_AGENT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["agent","cum_gold","avg_plots","claims","claim_win_rate","raids","raid_win_rate","defend","defend_block_rate","mining_stamina","budget_utilization"])
        # 平均持地
        avg_plots = {a: sum(row.get(a,0) for row in own_ts)/len(own_ts) for a in agents}
        total_budget = len(agents) * (by_round.__len__()) * 0  # 下面再逐代理算
        for a in agents:
            clm = act_counts[a]["claims"]
            rds = act_counts[a]["raids"]
            dfd = act_counts[a]["defend"]
            mns = act_counts[a]["mining_stamina"]
            # 胜率
            c_try = max(1, claim_success[a]["try"])
            r_try = max(1, raid_success[a]["try"])
            d_att = max(1, defend_block[a]["attacked"])
            c_rate = claim_success[a]["win"] / c_try
            r_rate = raid_success[a]["win"] / r_try
            d_rate = defend_block[a]["block"] / d_att
            # 预算利用
            # 每回合 S，回合数 R（从上面 infer），这里我们从 decisions.jsonl 推断回合数
            budget_used = clm + rds + dfd + mns
            budget_total = S * len(by_round)  # 对单代理
            util = budget_used / budget_total if budget_total>0 else 0.0
            w.writerow([
                a, cum_gold[a], round(avg_plots[a],3),
                clm, round(c_rate,3),
                rds, round(r_rate,3),
                dfd, round(d_rate,3),
                mns, round(util,3)
            ])

    # 回合级指标导出
    with open(OUT_ROUND_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(round_rows[0].keys()))
        w.writeheader()
        for row in round_rows:
            w.writerow(row)

    # 持地时序导出
    own_fields = ["round"] + agents
    with open(OUT_OWN_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=own_fields)
        w.writeheader()
        for row in own_ts:
            w.writerow(row)

    # 控制台摘要
    total_gold_all = sum(row["total_gold"] for row in round_rows)
    gini_gold = gini([float(v) for v in cum_gold.values()])
    print("\n=== SUMMARY ===")
    print(f"Total gold: {total_gold_all}")
    print(f"Final cumulative gold per agent: {cum_gold}")
    print(f"Gini (cum gold): {round(gini_gold,4)}")
    print(f"Wrote: {OUT_AGENT_CSV}, {OUT_ROUND_CSV}, {OUT_OWN_CSV}")

if __name__ == "__main__":
    main()
