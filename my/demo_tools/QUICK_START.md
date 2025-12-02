# Demo工具包使用快速指南

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install matplotlib pandas plotly numpy
```

### 2. 一键生成所有材料
```bash
python generate_all.py
```

### 3. 查看生成结果
- `key_findings.png` - 核心发现图（插入PPT）
- `interactive_dashboard.html` - 交互式面板（浏览器打开）
- `grid_evolution.mp4` - 动画视频（需要ffmpeg，可选）

---

## 📁 文件说明

### 生成脚本（按推荐顺序运行）
1. `3_key_findings_visualization.py` - 生成关键发现的7合1静态图
2. `2_interactive_dashboard.py` - 生成可交互的网页Dashboard
3. `1_grid_evolution_animation.py` - 生成网格演化MP4视频（需ffmpeg）

### 文档
- `README.md` - 完整使用说明（本文档）
- `PRESENTATION_GUIDE.md` - 详细汇报话术和Q&A应对

### 生成的输出
- `key_findings.png` - 高清静态图（300dpi，适合打印）
- `interactive_dashboard.html` - 单文件网页（可离线使用）
- `grid_evolution.mp4` - 动画视频（可嵌入PPT）

---

## 🎯 Demo展示方案

### 方案A：视频+静态图（推荐）
**适用场景**：正式汇报
1. PPT插入`grid_evolution.mp4`展示演化过程
2. 切换到`key_findings.png`讲解核心发现
3. Q&A时打开`interactive_dashboard.html`回答细节问题

**优点**：流畅专业
**缺点**：需要安装ffmpeg生成视频

### 方案B：交互式演示
**适用场景**：小组讨论、研讨会
1. 直接在浏览器中打开`interactive_dashboard.html`
2. 拖动滑动条演示不同回合
3. 实时响应听众提问

**优点**：灵活互动
**缺点**：需要现场操作

### 方案C：纯静态图（备选）
**适用场景**：网络或设备问题
1. 只使用`key_findings.png`
2. 配合现有的104文件夹中的其他PNG图

**优点**：最稳定
**缺点**：缺少动态感

---

## 💡 核心信息（3句话总结）

1. **问题**：无法律框架下，理性个体能否自发形成产权秩序？
2. **方法**：20个LLM驱动的AI代理在10×10网格中进行30回合博弈
3. **发现**：系统从混沌（Gini=0.65）收敛到秩序（Gini=0.14），冲突降低90%，产出提升30%

---

## 🎤 1分钟电梯演讲

> "我们用AI模拟了财产权的起源过程。20个大语言模型驱动的代理在一个网格世界中竞争资源，它们可以占领空地、抢夺他人领地、防御自己的土地、或者在土地上采矿生产。
>
> 结果非常有趣：系统经历了三个阶段——混沌期的疯狂抢占、竞争期的激烈争夺、最后自发形成了秩序期。财富不平等度从0.65降到0.14，冲突减少90%，总产出增长30%。
>
> 这验证了哈耶克的自发秩序理论：不需要外部强制，理性个体的博弈本身就能催生稳定的产权制度。这对区块链治理、多智能体系统设计都有启示。"

---

## 🔧 故障排除

### Q: generate_all.py报错找不到文件
**A**: 检查DECISIONS_PATH等路径是否正确，确保指向`my/104/`文件夹

### Q: 视频生成失败
**A**: 需要安装ffmpeg。如果暂时无法安装，跳过视频，直接使用交互式Dashboard

### Q: 图表中文显示方块
**A**: 安装中文字体包或在脚本中修改`plt.rcParams['font.sans-serif']`

### Q: HTML打开很慢
**A**: 正常，因为包含了30帧数据。首次加载需要3-5秒

---

## 📊 关键数据速查

| 指标 | 初期 | 后期 | 变化 |
|------|------|------|------|
| Gini系数 | 0.65 | 0.14 | ↓ 78% |
| 冲突次数/回合 | 20 | 2 | ↓ 90% |
| 总产出增长 | - | - | ↑ 30%+ |
| 秩序形成时间 | - | ~16回合 | - |

---

## 📞 需要帮助？

- 查看完整文档：`README.md`
- 汇报话术：`PRESENTATION_GUIDE.md`
- 查看主代码：`D:/yulan-onesim/YuLan-OneSim/llm_decider.py`
- 数据分析逻辑：`D:/yulan-onesim/YuLan-OneSim/my/analyze_decisions.py`

---

**最后的最后：相信你的研究，自信展示！Good luck! 🎉**
