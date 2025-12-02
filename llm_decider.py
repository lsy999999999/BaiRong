# -*- coding: utf-8 -*-
"""
Standalone multi-agent LLM decider + environment simulator.
- No third-party deps (uses urllib).
- Forces JSON-only outputs from LLM; robustly parses and repairs plans.
- Enforces rules & budget; simulates round resolution; writes logs.

Place as: src/llm_decider.py
Run:     python llm_decider.py
"""

import json
import random
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
from typing import Any, Dict, List, Tuple

# =========================
# CONSTANTS (EDIT HERE)
# =========================
BASE_URL = "http://111.6.167.248:9887/v1"
API_KEY  = "sk-xxx"
MODEL    = "/data/pretrain_dir/Qwen3-8B"

GRID_ROWS = 10        # 可改
GRID_COLS = 10       # 可改
N_AGENTS  = 20       # 代理数量
ROUNDS    = 30        # 回合数
S_BUDGET  = 10       # 每回合体力
SMAX      = 3        # 单地采矿上限
Q_RATE    = 1        # 产出率 y = q * min(s, smax)

RANDOM_SEED = 42     # 方便复现实验
PRINT_HEARTBEAT_EVERY_SEC = 3.0

OUT_DECISIONS = "D:/yulan-onesim/YuLan-OneSim/my/104/104_decisions.jsonl"
OUT_CSV       = "D:/yulan-onesim/YuLan-OneSim/my/104/104_logs.csv"

# =========================
# PROMPTS
# =========================

def _as_cell_tuple(x):
    """
    把各种坐标写法规范成 (r, c)：
    - [r, c] / (r, c)
    - "r,c" / "(r,c)" / "[r,c]"
    - {"cell":[r,c]} / {"row":r, "col":c}
    返回 (r, c) 或 None
    """
    if x is None:
        return None
    # dict 形式
    if isinstance(x, dict):
        if "cell" in x:
            return _as_cell_tuple(x["cell"])
        if "row" in x and "col" in x:
            try:
                return int(x["row"]), int(x["col"])
            except Exception:
                return None
        # 有时 LLM 会给 {"r":0,"c":1}
        if "r" in x and "c" in x:
            try:
                return int(x["r"]), int(x["c"])
            except Exception:
                return None
        return None

    # list/tuple 形式
    if isinstance(x, (list, tuple)) and len(x) == 2:
        try:
            return int(x[0]), int(x[1])
        except Exception:
            return None

    # 字符串 "0,1" / "(0,1)" / "[0,1]"
    if isinstance(x, str):
        s = x.strip().strip("()[]")
        if "," in s:
            parts = s.split(",")
            if len(parts) == 2:
                try:
                    return int(parts[0].strip()), int(parts[1].strip())
                except Exception:
                    return None
    return None


def _unique_keep_order(seq):
    """去重但保持原有顺序"""
    seen = set()
    out = []
    for t in seq:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out

def system_prompt() -> str:
    return (
        "你是一名在二维网格世界进行资源管理博弈的【矿工代理】。所有代理同质，回合制决策。\n"
        "—— 世界与收益 ——\n"
        "• 网格：R×C 个地块，地块同质；\n"
        "• 回合：每回合体力预算 S（每回合重置，不可结转）；\n"
        "• 采矿：单地采矿体力上限 s_max，产出 y = q * min(s_mine, s_max)，本文 q=1；\n"
        "• 资源不枯竭（R0→∞ 近似）：总存量不减，仅当回合采矿有上限；\n"
        "• 个人当回合收益 = 本回合各自拥有地块的采矿产出之和（单位黄金）。\n"
        "\n"
        "—— 产权/占有与四类动作（成本→条件→结果）——\n"
        "1) 占领 claim（成本=1/地）：\n"
        "   条件：目标地必须是当前无人占有（owner=none）。\n"
        "   结果：若多人同时 claim 同一空地，系统均等随机 1 人成功，其他人的体力作废；结算顺序晚于抢占/防御、早于采矿。\n"
        "2) 维持/防御 defend（成本=1/地）：\n"
        "   条件：只能对【你当前拥有】的地块设置；\n"
        "   结果：若本回合该地遭到任意数目的抢占，只要该地被你标为 defend，则本回合该地的所有抢占全部失败；即使无人抢占也会扣 1 体力。\n"
        "   关键：本框架中【只能对你当回合在 defend 中的地块进行采矿】。\n"
        "3) 抢占 raid（成本=1/地）：\n"
        "   条件：目标地必须被他人拥有（≠none 且 ≠你自己）。\n"
        "   结果：若原占有人本回合 defend 该地，则所有抢占全部失败；若未 defend，则在所有抢占者中均等随机 1 人成为新占有人。\n"
        "4) 采矿 mining（成本=投入体力之和）：\n"
        "   条件：仅对【你拥有且本回合在 defend 列表中的地】；每地 0..s_max 整数体力；\n"
        "   结果：该地产出 y = q * min(stamina, s_max)；采矿在占有关系生效后结算。\n"
        "\n"
        "—— 结算顺序 ——\n"
        "a) 抢占/防御 → b) 占空地 → c) 采矿；\n"
        "若你未防御就被改写占有权，你将失去在该地采矿的资格与收益。\n"
        "\n"
        "—— 信息集 ——\n"
        "• 可见：ownership_map（每地当前 owner）、上一回合公共日志、你的 S 与 s_max；\n"
        "• 不可见：他人当回合的防御/抢占计划；\n"
        "• 随机：多方冲突与空地竞争采用均等随机；\n"
        "• 目标：在满足 S 预算与规则约束下，最大化长期个人累计产出。\n"
        "\n"
        "—— 预算与裁剪（重要）——\n"
        "系统按优先级对超预算动作确定性裁剪；默认优先级：defend > mining > raids > claims；\n"
        "你可在 priority.category_order 中自定义，并用各类 *_order 指定类内顺序。\n"
        "\n"
        "—— 严格输出要求 ——\n"
        "只返回严格 JSON，对应 schema：\n"
        "{\n"
        '  "round_index": <int>,\n'
        '  "agent_id": "<string>",\n'
        '  "claims": [[row,col], ...],\n'
        '  "raids": [[row,col], ...],\n'
        '  "defend": [[row,col], ...],\n'
        '  "mining": [{"cell":[row,col], "stamina": <int>} , ...],\n'
        '  "priority": {\n'
        '      "category_order": ["defend","mining","raids","claims"],\n'
        '      "claims_order": [[row,col], ...],\n'
        '      "raids_order": [[row,col], ...],\n'
        '      "defend_order": [[row,col], ...],\n'
        '      "mining_order": [[row,col], ...]\n'
        "  }\n"
        "}\n"
        "不要输出任何解释、<think>、Markdown 或代码块，只能是 JSON。"
    )


def decision_prompt(agent_id: str, rows: int, cols: int, S: int, smax: int) -> str:
    return (
        f"你的代理ID：{agent_id}。下面 observation 会给出：\n"
        f"• round_index, grid_shape=[{rows},{cols}], stamina_budget=S={S}, max_mining_per_plot=s_max={smax}\n"
        "• ownership_map: [{\"cell\":[r,c], \"owner\":\"agent_k|none\"}, ...]\n"
        "• previous_public_log: 上回合的转移与占空地记录（如有）\n"
        "• your_last_round_summary: 你个人上回合结算摘要（如有）\n"
        "\n"
        "请生成本回合【完整动作包】并只返回 JSON（严格符合 schema）。\n"
        "自检规则：\n"
        "• 坐标在网格内；同列表不重复；\n"
        "• defend/mining 仅对你当前拥有的地；mining 还必须在本回合 defend 该地；\n"
        "• claims 只能对 owner=none；raids 只能对 owner≠none 且 ≠你；\n"
        "• 预算：len(claims)+len(raids)+len(defend)+sum(mining.stamina) ≤ S；\n"
        "• 若不做某类动作，返回 []。"
    )

# =========================
# HTTP (no requests)
# =========================

def _post_chat(messages: List[Dict[str, str]], temperature: float = 0.0, force_json: bool = True) -> str:
    """Call OpenAI-compatible /chat/completions; return text."""
    url = f"{BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 1024,
    }
    if force_json:
        # 如果服务端不支持，会在下面 fallback
        payload["response_format"] = {"type": "json_object"}

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            j = json.loads(body)
            return j["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        # fallback: 去掉 response_format 再试一次
        if force_json and e.code in (400, 404, 415, 422, 500):
            return _post_chat(messages, temperature, force_json=False)
        raise
    except Exception:
        raise

# =========================
# JSON PARSING & REPAIR
# =========================

def _strip_noise(text: str) -> str:
    # 去除<think>...</think> 与代码围栏
    while "<think>" in text and "</think>" in text:
        start = text.find("<think>")
        end = text.find("</think>", start)
        if end != -1:
            text = text[:start] + text[end + len("</think>") :]
        else:
            break
    fences = ("```json", "```JSON", "```")
    for f in fences:
        text = text.replace(f, "")
    return text.strip()

def _extract_first_json(text: str) -> str:
    """提取第一个完整的 JSON 对象字符串（括号匹配）。"""
    s = _strip_noise(text)
    start = s.find("{")
    if start == -1:
        return ""
    depth = 0
    for i in range(start, len(s)):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                return s[start : i + 1]
    return ""

def parse_plan(text: str) -> Dict[str, Any]:
    """尽力把模型输出转为 dict；失败返回 {}。"""
    cand = _extract_first_json(text)
    if not cand:
        return {}
    try:
        return json.loads(cand)
    except Exception:
        # 粗暴修复一些引号/尾逗号问题（有限度）
        cand2 = cand.replace("'", '"')
        cand2 = cand2.replace(",}", "}")
        cand2 = cand2.replace(",]", "]")
        try:
            return json.loads(cand2)
        except Exception:
            return {}

# =========================
# WORLD REPRESENTATION
# =========================

Cell = Tuple[int, int]

def all_cells(rows: int, cols: int) -> List[Cell]:
    return [(r, c) for r in range(rows) for c in range(cols)]

def init_world(rows: int, cols: int, agents: List[str]) -> Dict[str, Any]:
    """ownership: dict[cell->owner or None]"""
    ownership = {cell: None for cell in all_cells(rows, cols)}
    state = {
        "rows": rows,
        "cols": cols,
        "agents": agents[:],
        "ownership": ownership,
        "public_log": [],
        "cumulative_gold": {a: 0 for a in agents},
    }
    return state

def owner_of(state: Dict[str, Any], cell: Cell) -> str | None:
    return state["ownership"].get(cell)

def owned_cells(state: Dict[str, Any], agent_id: str) -> List[Cell]:
    return [c for c, o in state["ownership"].items() if o == agent_id]

def empty_cells(state: Dict[str, Any]) -> List[Cell]:
    return [c for c, o in state["ownership"].items() if o is None]

# =========================
# PLAN VALIDATION & REPAIR
# =========================

def _uniq_cells(cells: List[Cell], rows: int, cols: int) -> List[Cell]:
    seen, out = set(), []
    for r, c in cells or []:
        if not isinstance(r, int) or not isinstance(c, int):
            continue
        if 0 <= r < rows and 0 <= c < cols:
            t = (r, c)
            if t not in seen:
                seen.add(t)
                out.append(t)
    return out

def _budget_cost(plan: Dict[str, Any]) -> int:
    claims = plan.get("claims", [])
    raids  = plan.get("raids", [])
    defend = plan.get("defend", [])
    mining = plan.get("mining", [])
    mine_sum = sum(int(x.get("stamina", 0)) for x in (mining or []) if isinstance(x, dict))
    return len(claims) + len(raids) + len(defend) + mine_sum

def _clip_by_priority(plan: dict, stamina_budget: int) -> dict:
    """
    根据 priority 做“可裁剪”的排序与预算裁剪。
    - priority.category_order: 影响四类之间被裁剪时的保留顺序
    - priority.*_order: 影响同类内被裁剪时的保留顺序
    任何非法/缺失都忽略，绝不抛错。
    """
    # 读取四类
    claims = plan.get("claims") or []
    raids  = plan.get("raids")  or []
    defend = plan.get("defend") or []          # 形如 [[r,c], ...] 或 [{"cell":[r,c]}, ...]
    mining = plan.get("mining") or []          # 形如 [{"cell":[r,c], "stamina":n}, ...]

    # 规范各类数据结构
    norm_claims = [_as_cell_tuple(x) for x in claims]
    norm_claims = [t for t in norm_claims if t is not None]

    norm_raids  = [_as_cell_tuple(x) for x in raids]
    norm_raids  = [t for t in norm_raids if t is not None]

    # defend -> 只保留坐标列表
    norm_defend = []
    for x in defend:
        t = _as_cell_tuple(x)
        if t is not None:
            norm_defend.append(t)

    # mining -> 转成 {cell:(r,c), stamina:int}
    norm_mining = []
    for m in mining:
        if isinstance(m, dict):
            t = _as_cell_tuple(m.get("cell"))
            st = m.get("stamina", 0)
        else:
            # 兼容把 [r,c] 当 mining 的极端错误写法，直接视为 0 体力（会被裁掉）
            t = _as_cell_tuple(m)
            st = 0
        if t is None:
            continue
        try:
            st = int(st)
        except Exception:
            st = 0
        norm_mining.append({"cell": t, "stamina": max(0, st)})

    # 读 priority
    pr = plan.get("priority") or {}
    cat_order = pr.get("category_order") or ["defend", "mining", "raids", "claims"]  # 默认把防御最难被剪
    # 规范化坐标顺序
    def _order_list(name):
        lst = pr.get(name) or []
        cells = []
        for x in lst:
            t = _as_cell_tuple(x)
            if t is not None:
                cells.append(t)
        return _unique_keep_order(cells)

    claims_order = _order_list("claims_order")
    raids_order  = _order_list("raids_order")
    defend_order = _order_list("defend_order")
    mining_order = _order_list("mining_order")   # 注意：mining 里的对象是 dict，这里只给 cell 顺序

    # 类内排序（把存在于 order 的排前面）
    def _sort_by_order(items, key_fn, order_cells):
        if not order_cells:
            return items
        order_index = {c:i for i,c in enumerate(order_cells)}
        def _key(x):
            c = key_fn(x)
            return (order_index.get(c, 10**9),)  # 不在 order 里的排后面
        return sorted(items, key=_key)

    # claims/raids/defend
    norm_claims = _sort_by_order(norm_claims, lambda t: t, claims_order)
    norm_raids  = _sort_by_order(norm_raids,  lambda t: t, raids_order)
    norm_defend = _sort_by_order(norm_defend, lambda t: t, defend_order)
    # mining：按 cell 顺序
    norm_mining = _sort_by_order(norm_mining, lambda d: d["cell"], mining_order)

    # 预算裁剪（顺序：按 cat_order 逐类填充，超过预算就截断）
    cat_order = [c for c in cat_order if c in ("claims","raids","defend","mining")]
    if not cat_order:
        cat_order = ["defend","mining","raids","claims"]

    used = 0
    out_claims = []
    out_raids  = []
    out_defend = []
    out_mining = []

    def _take_claims(lst):
        nonlocal used, out_claims
        for c in lst:
            if used + 1 > stamina_budget: break
            out_claims.append(list(c))
            used += 1

    def _take_raids(lst):
        nonlocal used, out_raids
        for c in lst:
            if used + 1 > stamina_budget: break
            out_raids.append(list(c))
            used += 1

    def _take_defend(lst):
        nonlocal used, out_defend
        for c in lst:
            if used + 1 > stamina_budget: break
            out_defend.append(list(c))
            used += 1

    def _take_mining(lst):
        nonlocal used, out_mining
        for m in lst:
            if used >= stamina_budget: break
            remaining = stamina_budget - used
            if m["stamina"] <= 0: 
                continue
            take = min(remaining, int(m["stamina"]))
            if take <= 0:
                continue
            out_mining.append({"cell": list(m["cell"]), "stamina": take})
            used += take

    for cat in cat_order:
        if used >= stamina_budget:
            break
        if cat == "defend":
            _take_defend(norm_defend)
        elif cat == "mining":
            _take_mining(norm_mining)
        elif cat == "raids":
            _take_raids(norm_raids)
        elif cat == "claims":
            _take_claims(norm_claims)

    # 输出规范化后的 plan
    return {
        "claims": out_claims,
        "raids":  out_raids,
        "defend": out_defend,
        "mining": out_mining,
        "priority": {
            "category_order": cat_order,
            "claims_order": [list(t) for t in claims_order],
            "raids_order":  [list(t) for t in raids_order],
            "defend_order": [list(t) for t in defend_order],
            "mining_order": [list(t) for t in mining_order],
        }
    }

def validate_and_repair_plan(state: Dict[str, Any], agent_id: str, raw: Dict[str, Any], S: int, smax: int) -> Dict[str, Any]:
    rows, cols = state["rows"], state["cols"]
    owner = lambda cell: owner_of(state, cell)

    claims = _uniq_cells(raw.get("claims", []), rows, cols)
    raids  = _uniq_cells(raw.get("raids",  []), rows, cols)
    defend = _uniq_cells(raw.get("defend", []), rows, cols)

    # 过滤非法：claims 只能空地；raids 只能他人拥有；defend 只能自己拥有
    claims = [c for c in claims if owner(c) is None]
    raids  = [c for c in raids  if (owner(c) is not None and owner(c) != agent_id)]
    defend = [c for c in defend if owner(c) == agent_id]

    # mining: 仅对 已拥有且在 defend 中的地；0..smax
    defend_set = set(defend)
    mining_in  = raw.get("mining", []) or []
    mining: List[Dict[str, Any]] = []
    for m in mining_in:
        if not isinstance(m, dict) or "cell" not in m:
            continue
        cell = tuple(m["cell"])
        try:
            st = int(m.get("stamina", 0))
        except Exception:
            st = 0
        st = max(0, min(st, smax))
        if owner(cell) == agent_id and cell in defend_set and st > 0:
            mining.append({"cell": [cell[0], cell[1]], "stamina": st})

    plan = {
        "round_index": int(raw.get("round_index", 0)),
        "agent_id": agent_id,
        "claims": [list(c) for c in claims],
        "raids":  [list(c) for c in raids],
        "defend": [list(c) for c in defend],
        "mining": mining,
        "priority": raw.get("priority") or {
            "category_order": ["defend","mining","raids","claims"],
            "defend_order": [list(c) for c in defend],
            "mining_order": [list(m["cell"]) for m in mining],
            "raids_order": [list(c) for c in raids],
            "claims_order": [list(c) for c in claims],
        },
    }

    # 预算裁剪
    if _budget_cost(plan) > S:
        plan = _clip_by_priority(plan, S)

    # 若 LLM 仍然“空动作”，做兜底：先守土→采满→扩张空地
    if _budget_cost(plan) == 0:
        budget = S
        my_cells = owned_cells(state, agent_id)
        # defend 优先
        for c in my_cells:
            if budget <= 0: break
            plan["defend"].append(list(c)); budget -= 1
        # mining 次之
        for c in my_cells:
            if budget <= 0: break
            take = min(smax, budget)
            if take > 0:
                plan["mining"].append({"cell": [c[0], c[1]], "stamina": take}); budget -= take
        # claims 最后
        for c in empty_cells(state):
            if budget <= 0: break
            plan["claims"].append(list(c)); budget -= 1

    plan["agent_id"] = agent_id
    return plan

# =========================
# ENV RESOLUTION
# =========================

def resolve_round(state: Dict[str, Any], plans: Dict[str, Dict[str, Any]], smax: int, q: int = 1) -> Dict[str, Any]:
    """按规则结算一回合，返回 round_summary（含个人收益、占有变更等）。"""
    rows, cols = state["rows"], state["cols"]
    ownership = state["ownership"]
    public_log = []

    # a) 抢占/防御
    defend_map = {}  # cell -> owner_id (防御者)
    for aid, p in plans.items():
        for rc in p.get("defend", []):
            cell = (rc[0], rc[1])
            if ownership.get(cell) == aid:
                defend_map[cell] = aid

    raids_map: Dict[Cell, List[str]] = {}
    for aid, p in plans.items():
        for rc in p.get("raids", []):
            cell = (rc[0], rc[1])
            cur = ownership.get(cell)
            if cur is not None and cur != aid:
                raids_map.setdefault(cell, []).append(aid)

    # 逐地块处理抢占
    for cell, challengers in raids_map.items():
        cur = ownership.get(cell)
        if cur is None:
            continue
        if defend_map.get(cell) == cur:
            public_log.append({"type": "raid_blocked", "cell": list(cell), "owner": cur, "challengers": challengers[:]})
            continue
        # 未防御：随机挑 1 人成功
        winner = random.choice(challengers)
        ownership[cell] = winner
        public_log.append({"type": "raid_success", "cell": list(cell), "from": cur, "to": winner, "others": [x for x in challengers if x != winner]})

    # b) 占领空地
    claim_map: Dict[Cell, List[str]] = {}
    for aid, p in plans.items():
        for rc in p.get("claims", []):
            cell = (rc[0], rc[1])
            if ownership.get(cell) is None:
                claim_map.setdefault(cell, []).append(aid)

    for cell, claimers in claim_map.items():
        if ownership.get(cell) is not None:
            continue
        if len(claimers) == 1:
            ownership[cell] = claimers[0]
            public_log.append({"type": "claim_success", "cell": list(cell), "to": claimers[0]})
        else:
            winner = random.choice(claimers)
            ownership[cell] = winner
            public_log.append({"type": "claim_tie", "cell": list(cell), "to": winner, "others": [x for x in claimers if x != winner]})

    # c) 采矿
    round_gold = {a: 0 for a in state["agents"]}
    defend_set = {(r, c) for (r, c), own in ownership.items() if defend_map.get((r, c)) == own}
    for aid, p in plans.items():
        for m in p.get("mining", []):
            cell = tuple(m["cell"])
            st = int(m.get("stamina", 0))
            if ownership.get(cell) == aid and cell in defend_set and st > 0:
                round_gold[aid] += q * min(st, smax)

    # 汇总
    for a, g in round_gold.items():
        state["cumulative_gold"][a] += g

    summary = {
        "public_log": public_log,
        "round_gold": round_gold,
        "ownership_after": {f"{r},{c}": ownership[(r, c)] for r in range(rows) for c in range(cols)},
    }
    state["public_log"] = public_log
    return summary

# =========================
# DRIVER
# =========================

def build_observation(state: Dict[str, Any], round_index: int, agent_id: str) -> Dict[str, Any]:
    rows, cols = state["rows"], state["cols"]
    ownership_map = [{"cell": [r, c], "owner": state["ownership"][(r, c)] or "none"}
                     for r in range(rows) for c in range(cols)]
    return {
        "round_index": round_index,
        "grid_shape": [rows, cols],
        "stamina_budget": S_BUDGET,
        "max_mining_per_plot": SMAX,
        "ownership_map": ownership_map,
        "previous_public_log": state["public_log"][-50:],  # 限长
        "your_last_round_summary": {},  # 简化：如需可扩展
    }

def decide_with_llm(agent_id: str, obs: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    sys_msg = {"role": "system", "content": system_prompt()}
    user_msg = {"role": "user", "content": decision_prompt(agent_id, obs["grid_shape"][0], obs["grid_shape"][1], obs["stamina_budget"], obs["max_mining_per_plot"]) + "\n\nobservation:\n" + json.dumps(obs, ensure_ascii=False)}
    print(f"   → send to LLM for {agent_id} ...", flush=True)
    txt = _post_chat([sys_msg, user_msg], temperature=0.0, force_json=True)
    plan = parse_plan(txt)
    return txt, plan

def run():
    random.seed(RANDOM_SEED)
    agents = [f"agent_{i+1}" for i in range(N_AGENTS)]
    state = init_world(GRID_ROWS, GRID_COLS, agents)

    # CSV header
    with open(OUT_CSV, "w", encoding="utf-8") as fcsv:
        fcsv.write("round,agent,claims,raids,defend,mining,round_gold,cum_gold\n")

    print(f"World: {GRID_ROWS}x{GRID_COLS}, agents={N_AGENTS}, R={ROUNDS}, S={S_BUDGET}, smax={SMAX}\n", flush=True)

    with open(OUT_DECISIONS, "w", encoding="utf-8") as fout:
        for r in range(ROUNDS):
            print(f"\n===== ROUND {r} =====", flush=True)
            plans: Dict[str, Dict[str, Any]] = {}
            raw_texts: Dict[str, str] = {}

            last_beat = time.time()

            for a in agents:
                # 心跳
                now = time.time()
                if now - last_beat >= PRINT_HEARTBEAT_EVERY_SEC:
                    print(f"  [heartbeat] still working at round {r} ...", flush=True)
                    last_beat = now

                obs = build_observation(state, r, a)
                try:
                    raw_txt, raw_plan = decide_with_llm(a, obs)
                except Exception as e:
                    print(f"   ! LLM call failed for {a}: {e} -> using fallback", flush=True)
                    raw_txt, raw_plan = ("", {})

                plan = validate_and_repair_plan(state, a, raw_plan, S_BUDGET, SMAX)
                plans[a] = plan
                raw_texts[a] = raw_txt

                # 写 JSONL（含模型原文，方便你调研）
                rec = {
                    "round_index": r,
                    "agent_id": a,
                    "observation": obs,
                    "raw_model_text": raw_txt,
                    "plan": plan,
                }
                fout.write(json.dumps(rec, ensure_ascii=False) + "\n")

                # 控制台简短回显
                print(f"   {a}: cost={_budget_cost(plan)}  claims={len(plan['claims'])} raids={len(plan['raids'])} defend={len(plan['defend'])} mining={sum(m['stamina'] for m in plan['mining'])}", flush=True)

            # 结算
            summary = resolve_round(state, plans, SMAX, q=Q_RATE)

            # 写 CSV
            with open(OUT_CSV, "a", encoding="utf-8") as fcsv:
                for a in agents:
                    rg = summary["round_gold"][a]
                    cg = state["cumulative_gold"][a]
                    p = plans[a]
                    fcsv.write(
                        f'{r},{a},"{json.dumps(p["claims"])}","{json.dumps(p["raids"])}","{json.dumps(p["defend"])}","{json.dumps(p["mining"])}",{rg},{cg}\n'
                    )

            # 回合汇总打印
            print(f"  public_log: {summary['public_log']}", flush=True)
            print("  round_gold:", summary["round_gold"], flush=True)
            print("  cum_gold  :", state["cumulative_gold"], flush=True)

    print("\nAll rounds finished.")
    print(f"→ decisions: {OUT_DECISIONS}")
    print(f"→ logs     : {OUT_CSV}")

if __name__ == "__main__":
    run()
