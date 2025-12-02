from onesim.simulator import BasicSimEnv
from onesim.events import Event
from .events import StartEvent

def _export_ownership_map(self, matrix):
    """
    matrix: 形如 [[owner_id_or_None, ...], [...]] 的 2D 结构
    返回: [{"cell":[r,c], "owner":"agent_x"|"none"}...]
    """
    out = []
    for r, row in enumerate(matrix):
        for c, owner in enumerate(row):
            out.append({
                "cell": [r, c],
                "owner": (owner if owner is not None else "none")
            })
    return out


class SimEnv(BasicSimEnv):
    async def _create_start_event(self, target_id: str) -> Event:
        source_id = self.data.get('environment_id', 'ENV')
        return StartEvent(from_agent_id=source_id, to_agent_id=target_id)
    # ① 取当前占有矩阵（按你工程里的实际存放位置做“多路兜底”）
    def _get_current_ownership_matrix(self):
        """
        返回一个 2D 矩阵（rows x cols），单元为所有者 id 或 None
        """
        mat = getattr(self, "ownership_matrix", None)
        if mat is None:
            state = getattr(self, "state", None)
            if isinstance(state, dict):
                mat = state.get("ownership_matrix") or state.get("ownership") or state.get("ownership_map")
        if mat is None:
            # 兜底：按网格尺寸构造全空
            rows = getattr(self, "grid_rows", None) or getattr(self, "rows", None) or 2
            cols = getattr(self, "grid_cols", None) or getattr(self, "cols", None) or 2
            mat = [[None for _ in range(int(cols))] for _ in range(int(rows))]
        return mat

    # ② 导出为约定结构： [{"cell":[r,c], "owner":"agent_x|none"}, ...]
    def _export_ownership_map(self, matrix):
        out = []
        for r, row in enumerate(matrix):
            for c, owner in enumerate(row):
                out.append({
                    "cell": [int(r), int(c)],
                    "owner": str(owner) if owner is not None else "none"
                })
        return out

    # ③ 构造并发出 StartEvent（你的“# ... 其他参数准备”就补成下面这样）
    async def _create_start_event(self, target_id: str) -> StartEvent:
        # —— 基本参数（带兜底）——
        round_index = getattr(self, "current_step", None)
        if round_index is None:
            round_index = getattr(self, "round_index", 0)
        stamina_budget = getattr(self, "stamina_budget", None)
        if stamina_budget is None:
            stamina_budget = getattr(self, "S", 10)
        max_mining = getattr(self, "max_mining_per_plot", 3)

        # —— 拿占有矩阵并导出为结构化 ownership_map —— 
        ownership_matrix = self._get_current_ownership_matrix()
        ownership_map_payload = self._export_ownership_map(ownership_matrix)

        # —— 可选：上一轮公开日志 / 个人摘要 / 随机种子 —— 
        last_log = getattr(self, "public_log_last_log", None)
        if last_log is None:
            # 有些实现把日志放在 self.public_log = {"last_log":[...]} 里
            plog = getattr(self, "public_log", None)
            if isinstance(plog, dict):
                last_log = plog.get("last_log", [])
            elif isinstance(plog, list):
                last_log = plog
            else:
                last_log = []

        personal_summary = getattr(self, "personal_summary_overall", None)
        if not isinstance(personal_summary, dict):
            personal_summary = {}

        run_seed = getattr(self, "run_seed", None)
        if run_seed is None:
            run_seed = getattr(self, "seed", "0")

        # —— 组装并返回 StartEvent —— 
        return StartEvent(
            from_agent_id="ENV",
            to_agent_id=target_id,
            round_index=int(round_index),
            stamina_budget=int(stamina_budget),
            max_mining_per_plot=int(max_mining),
            ownership_map=ownership_map_payload,
            public_log_last_log=last_log,
            personal_summary_overall=personal_summary,
            run_seed=str(run_seed),
        )