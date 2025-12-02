# -*- coding: utf-8 -*-
"""
增强版分析脚本（含可视化）
- 输入：decisions.jsonl（必需）
- 输出：
  - CSV：agent_metrics.csv, round_metrics.csv, ownership_timeseries.csv
  - 图：fig_round_total_gold.png, fig_agent_cum_gold.png, fig_ownership_lines.png, fig_contest_heatmap.png
结算顺序：抢占/防御 -> 占空地 -> 采矿（与模拟器一致）
图表规范：仅 matplotlib；每张图独立画布；不指定颜色。
"""

import os
import csv
import json
import math
import random
from collections import defaultdict, OrderedDict
from typing import Any, Dict, List, Tuple

# 画图
import matplotlib.pyplot as plt

# -------------------------
# 可调整常量
# -------------------------

DECISIONS_PATH ="D:/yulan-onesim/YuLan-OneSim/my/104/104_decisions.jsonl"  # 必须存在

OUT_AGENT_CSV = "D:\\yulan-onesim\\YuLan-OneSim\\my\\104\\agent_metrics.csv"
OUT_ROUND_CSV = "D:\\yulan-onesim\\YuLan-OneSim\\my\\104\\round_metrics.csv"
OUT_OWN_CSV   = "D:\\yulan-onesim\\YuLan-OneSim\\my\\104\\ownership_timeseries.csv"

FIG_ROUND_GOLD   = "D:\\yulan-onesim\\YuLan-OneSim\\my\\104\\fig_round_total_gold.png"
FIG_AGENT_GOLD   = "D:\\yulan-onesim\\YuLan-OneSim\\my\\104\\fig_agent_cum_gold.png"
FIG_OWN_LINES    = "D:\\yulan-onesim\\YuLan-OneSim\\my\\104\\fig_ownership_lines.png"
FIG_CONTEST_HEAT = "D:\\yulan-onesim\\YuLan-OneSim\\my\\104\\fig_contest_heatmap.png"

REPLAY_SEED = 42  # 回放随机种子（便于复现实验）
Q_RATE      = 1   # y = q * min(stamina, smax)，保持与仿真一致

# -------------------------
# 基础类型与工具
# -------------------------
Cell = Tuple[int, int]

def _as_cell_tuple(x) -> Cell | None:
    """把各种坐标写法规范成 (r, c)：[r,c] / (r,c) / 'r,c' / '(r,c)' / {'cell':[r,c]} / {'row':r,'col':c} / {'r':r,'c':c}"""
    if x is None:
        return None
    if isinstance(x, dict):
        if "cell" in x:
            return _as_cell_tuple(x["cell"])
        if "row" in x and "col" in x:
            try:
                return int(x["row"]), int(x["col"])
            except Exception:
                return None
        if "r" in x and "c" in x:
            try:
                return int(x["r"]), int(x["c"])
            except Exception:
                return None
        return None
    if isinstance(x, (list, tuple)) and len(x) == 2:
        try:
            return int(x[0]), int(x[1])
        except Exception:
            return None
    if isinstance(x, str):
        s = x.strip().strip("()[]")
        if "," in s:
            a, b = s.split(",", 1)
            try:
                return int(a.strip()), int(b.strip())
            except Exception:
                return None
    return None

def _unique_keep_order(seq):
    seen = set()
    out = []
    for t in seq:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out

def gini(values: List[float]) -> float:
    n = len(values)
    if n == 0:
        return 0.0
    vals = sorted(max(0.0, float(v)) for v in values)
    if not vals:
        return 0.0
    s = sum(vals)
    if s == 0:
        return 0.0
    cum = 0.0
    for i, v in enumerate(vals, 1):
        cum += i * v
    return (2*cum)/(n*s) - (n+1)/n

# -------------------------
# 数据读取与世界推断
# -------------------------
def load_decisions(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing {path}")
    recs = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                recs.append(json.loads(line))
            except Exception:
                pass
    if not recs:
        raise RuntimeError(f"No valid records in {path}")
    return recs

def infer_world(recs: List[Dict[str, Any]]) -> Tuple[int,int,List[str],int,int,int]:
    first = recs[0]
    obs = first.get("observation", {})
    rows, cols = obs.get("grid_shape", [2,2])
    S = obs.get("stamina_budget", 10)
    smax = obs.get("max_mining_per_plot", 3)
    # 代理 id 顺序：按出现先后
    seen = OrderedDict()
    for r in recs:
        aid = r.get("agent_id")
        if aid and aid not in seen:
            seen[aid] = True
    agents = list(seen.keys())
    rounds = max(int(r.get("round_index", 0)) for r in recs) + 1
    return rows, cols, agents, S, smax, rounds

# -------------------------
# 结算（与模拟器一致）
# -------------------------
def resolve_round(ownership: Dict[Cell, str|None],
                  plans: Dict[str, Dict[str, Any]],
                  smax: int,
                  q: int,
                  rnd: random.Random,
                  contest_heat: List[List[int]]) -> Tuple[Dict[str,int], List[Dict[str,Any]]]:
    """
    返回：round_gold, public_log
    会原地修改 ownership；同时累计 contest_heat（每格被争夺次数）
    """
    # 预处理 defend
    defend_map: Dict[Cell, str] = {}
    for aid, p in plans.items():
        for rc in p.get("defend", []) or []:
            t = _as_cell_tuple(rc)
            if t is None:
                continue
            if ownership.get(t) == aid:
                defend_map[t] = aid

    # 抢占请求
    raids_map: Dict[Cell, List[str]] = defaultdict(list)
    for aid, p in plans.items():
        for rc in p.get("raids", []) or []:
            t = _as_cell_tuple(rc)
            if t is None:
                continue
            cur = ownership.get(t)
            if cur is not None and cur != aid:
                raids_map[t].append(aid)

    public_log: List[Dict[str,Any]] = []

    # a) 抢占/防御
    for cell, challengers in raids_map.items():
        cur = ownership.get(cell)
        if cur is None:
            continue
        # 统计争夺热度
        contest_heat[cell[0]][cell[1]] += 1
        if defend_map.get(cell) == cur:
            public_log.append({"type":"raid_blocked","cell":[cell[0],cell[1]],"owner":cur,"challengers":challengers[:]})
        else:
            winner = rnd.choice(challengers)
            ownership[cell] = winner
            public_log.append({"type":"raid_success","cell":[cell[0],cell[1]],"from":cur,"to":winner,"others":[x for x in challengers if x!=winner]})

    # b) 占领空地
    claim_map: Dict[Cell, List[str]] = defaultdict(list)
    for aid, p in plans.items():
        for rc in p.get("claims", []) or []:
            t = _as_cell_tuple(rc)
            if t is None:
                continue
            if ownership.get(t) is None:
                claim_map[t].append(aid)

    for cell, claimers in claim_map.items():
        if ownership.get(cell) is not None:
            continue
        if len(claimers) == 1:
            ownership[cell] = claimers[0]
            public_log.append({"type":"claim_success","cell":[cell[0],cell[1]],"to":claimers[0]})
        else:
            # 多人抢空地 -> 也算一次“争夺”
            contest_heat[cell[0]][cell[1]] += 1
            winner = rnd.choice(claimers)
            ownership[cell] = winner
            public_log.append({"type":"claim_tie","cell":[cell[0],cell[1]],"to":winner,"others":[x for x in claimers if x!=winner]})

    # c) 采矿（仅“已防御且仍归属”的地块）
    defend_set = {cell for cell, own in ownership.items() if defend_map.get(cell) == own}
    round_gold: Dict[str,int] = defaultdict(int)
    for aid, p in plans.items():
        for m in p.get("mining", []) or []:
            if not isinstance(m, dict):
                # 垃圾条目忽略
                continue
            t = _as_cell_tuple(m.get("cell"))
            if t is None:
                continue
            try:
                st = int(m.get("stamina", 0))
            except Exception:
                st = 0
            if st <= 0:
                continue
            if ownership.get(t) == aid and t in defend_set:
                round_gold[aid] += q * min(st, smax)

    return round_gold, public_log

# -------------------------
# 主分析
# -------------------------
def analyze():
    recs = load_decisions(DECISIONS_PATH)
    rows, cols, agents, S, smax, R = infer_world(recs)
    print(f"[info] grid={rows}x{cols}, agents={len(agents)}, rounds={R}, S={S}, smax={smax}")

    # round -> agent -> plan
    by_round: Dict[int, Dict[str, Dict[str,Any]]] = defaultdict(dict)
    for r in recs:
        ridx = int(r.get("round_index", 0))
        aid  = r.get("agent_id")
        plan = r.get("plan", {})
        if aid:
            by_round[ridx][aid] = plan

    # 状态
    rnd = random.Random(REPLAY_SEED)
    ownership: Dict[Cell, str|None] = {(r,c): None for r in range(rows) for c in range(cols)}
    cum_gold: Dict[str,int] = {a:0 for a in agents}

    # 统计容器
    act_counts = {a: {"claims":0,"raids":0,"defend":0,"mining_stamina":0} for a in agents}
    raid_success = {a: {"win":0, "try":0} for a in agents}
    claim_success = {a: {"win":0, "try":0} for a in agents}
    defend_block  = {a: {"block":0, "attacked":0} for a in agents}

    own_ts: List[Dict[str,int]] = []
    round_rows: List[Dict[str,Any]] = []
    # 每格被争夺热度
    contest_heat = [[0 for _ in range(cols)] for _ in range(rows)]

    # 回合循环
    for t in range(R):
        plans = by_round.get(t, {})
        # 动作量统计
        total_claims=total_raids=total_defend=total_mine=0
        for a in agents:
            p = plans.get(a, {})
            c = len((p.get("claims") or []))
            r_ = len((p.get("raids")  or []))
            d = len((p.get("defend") or []))
            m = sum(int(x.get("stamina",0)) for x in (p.get("mining") or []) if isinstance(x,dict))
            act_counts[a]["claims"] += c
            act_counts[a]["raids"]  += r_
            act_counts[a]["defend"] += d
            act_counts[a]["mining_stamina"] += m
            total_claims += c; total_raids += r_; total_defend += d; total_mine += m

        # 结算
        round_gold, public_log = resolve_round(ownership, plans, smax, Q_RATE, rnd, contest_heat)
        for a,g in round_gold.items():
            cum_gold[a] += g

        # 成功与防御统计
        for evt in public_log:
            tp = evt.get("type")
            if tp == "raid_success":
                winner = evt.get("to")
                others = evt.get("others",[])
                if winner in raid_success: raid_success[winner]["win"] += 1
                for a in others + [winner]:
                    if a in raid_success: raid_success[a]["try"] += 1
            elif tp == "raid_blocked":
                owner = evt.get("owner")
                chals = evt.get("challengers",[])
                if owner in defend_block:
                    defend_block[owner]["block"] += 1
                    defend_block[owner]["attacked"] += 1
                for a in chals:
                    if a in raid_success:
                        raid_success[a]["try"] += 1
            elif tp in ("claim_success","claim_tie"):
                winner = evt.get("to")
                others = evt.get("others",[])
                if winner in claim_success:
                    claim_success[winner]["win"] += 1
                    claim_success[winner]["try"] += 1
                for a in others:
                    if a in claim_success:
                        claim_success[a]["try"] += 1

        # 每回合持地
        oc = {a:0 for a in agents}
        for (r0,c0), own in ownership.items():
            if own in oc:
                oc[own] += 1
        own_ts.append({"round": t, **oc})

        # 回合级汇总
        total_gold = sum(round_gold.get(a,0) for a in agents)
        contested_raids  = sum(1 for e in public_log if e["type"] in ("raid_success","raid_blocked"))
        contested_claims = sum(1 for e in public_log if e["type"] == "claim_tie")

        # 粗估理论上界：min(总采矿体力, 防御后仍归属的地 * smax)
        # 近似计算“有效防御地”
        defended_cells = set()
        for a,p in plans.items():
            for rc in (p.get("defend") or []):
                tt = _as_cell_tuple(rc)
                if tt and ownership.get(tt) == a:
                    defended_cells.add(tt)
        theo_cap = min(total_mine, len(defended_cells) * smax)
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

    # --- 导出 CSV ---
    # 1) 代理级
    with open(OUT_AGENT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["agent","cum_gold","avg_plots","claims","claim_win_rate","raids","raid_win_rate","defend","defend_block_rate","mining_stamina","budget_utilization"])
        avg_plots = {a: sum(row.get(a,0) for row in own_ts)/len(own_ts) for a in agents}
        for a in agents:
            clm = act_counts[a]["claims"]
            rds = act_counts[a]["raids"]
            dfd = act_counts[a]["defend"]
            mns = act_counts[a]["mining_stamina"]
            c_try = max(1, claim_success[a]["try"])
            r_try = max(1, raid_success[a]["try"])
            d_att = max(1, defend_block[a]["attacked"])
            c_rate = claim_success[a]["win"] / c_try
            r_rate = raid_success[a]["win"] / r_try
            d_rate = defend_block[a]["block"] / d_att
            # 预算利用（对单代理）
            # 注意：未直接读 S/R，这里从 decisions 推断 R；预算=R*S
            # S 在 infer_world 中拿到了
            budget_used  = clm + rds + dfd + mns
            budget_total = S * len(own_ts)
            util = budget_used / budget_total if budget_total>0 else 0.0
            w.writerow([
                a, cum_gold[a], round(avg_plots[a],3),
                clm, round(c_rate,3),
                rds, round(r_rate,3),
                dfd, round(d_rate,3),
                mns, round(util,3),
            ])

    # 2) 回合级
    with open(OUT_ROUND_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(round_rows[0].keys()))
        w.writeheader()
        for row in round_rows:
            w.writerow(row)

    # 3) 持地时序
    own_fields = ["round"] + agents
    with open(OUT_OWN_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=own_fields)
        w.writeheader()
        for row in own_ts:
            w.writerow(row)

    # --- 画图 ---
    # a) 每回合总产金
    plt.figure()
    xs = [row["round"] for row in round_rows]
    ys = [row["total_gold"] for row in round_rows]
    plt.plot(xs, ys)
    plt.title("Total Gold per Round")
    plt.xlabel("Round")
    plt.ylabel("Gold")
    plt.tight_layout()
    plt.savefig(FIG_ROUND_GOLD, dpi=150)
    plt.close()

    # b) 代理累计产金条形图
    plt.figure()
    xnames = list(agents)
    ygold = [cum_gold[a] for a in agents]
    plt.bar(range(len(xnames)), ygold)
    plt.xticks(range(len(xnames)), xnames, rotation=30, ha="right")
    plt.title("Cumulative Gold by Agent")
    plt.xlabel("Agent")
    plt.ylabel("Gold")
    plt.tight_layout()
    plt.savefig(FIG_AGENT_GOLD, dpi=150)
    plt.close()

    # c) 各代理持地折线图（每回合）
    plt.figure()
    for a in agents:
        ys = [row.get(a,0) for row in own_ts]
        plt.plot(xs, ys, label=a)
    # 不加图例颜色指定；用户多代理时图例可能较长，可视需要自行打开 legend
    # plt.legend()
    plt.title("Owned Plots per Round (by Agent)")
    plt.xlabel("Round")
    plt.ylabel("Plots Owned")
    plt.tight_layout()
    plt.savefig(FIG_OWN_LINES, dpi=150)
    plt.close()

    # d) 争夺热度热力图（每格被争夺次数：抢占冲突+空地多人竞争）
    # 使用 imshow 的默认配色，不指定颜色
    plt.figure()
    plt.imshow(contest_heat, aspect="auto")
    plt.title("Contest Heatmap (higher = more contested)")
    plt.xlabel("Col")
    plt.ylabel("Row")
    plt.tight_layout()
    plt.savefig(FIG_CONTEST_HEAT, dpi=150)
    plt.close()

    # 控制台摘要
    total_gold_all = sum(r["total_gold"] for r in round_rows)
    gini_gold = gini([cum_gold[a] for a in agents])
    print("\n=== SUMMARY ===")
    print(f"Total gold: {total_gold_all}")
    print(f"Final cumulative gold per agent: {cum_gold}")
    print(f"Gini (cum gold): {round(gini_gold,4)}")
    print(f"Wrote CSV: {OUT_AGENT_CSV}, {OUT_ROUND_CSV}, {OUT_OWN_CSV}")
    print(f"Wrote FIG: {FIG_ROUND_GOLD}, {FIG_AGENT_GOLD}, {FIG_OWN_LINES}, {FIG_CONTEST_HEAT}")

if __name__ == "__main__":
    analyze()
