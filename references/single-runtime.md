# Code Edition 单盘运行规范

## 运行层级

- SINGLE-R：一组完整四柱，输出节点、能量、DSS、DFP、互动、VP、NBS。
- SINGLE-D：再给大运，从 R+D 全部节点重算，增加 DLS；不生成 AFS。
- SINGLE-Y：再给流年，从 R+D+Y 全部节点重算，增加 YDS、SCS、AFS、EAI、EFM。
- SINGLE-MARRIAGE：代码仍按对应 R/D/Y 单盘运行，解释时聚焦日支、伴侣星、边界与关系领域；不得输出
  只有双盘才成立的 CFS、RFS、MPS 或 R-AFS。

## 执行

1. 把用户确认的年、月、日、时四柱写入规范 JSON；不要改盘。
2. 大运只放在 `timing.luck.A`，流年只放在 `timing.year`。
3. 运行 `python3 scripts/run_esid.py analyze --input request.json`。
4. 检查退出码为 0、`integrity.payload_sha256` 存在、`policy.execution_path` 为 `code_only`。
5. 只解释 `result.layers` 中实际存在的层级和分数。

## R 层解释顺序

1. `day_master` 与 `season_anchor`。
2. `energy` 的五行分布；它是引擎内部相对能量，不是客观物理量。
3. `dss.ratio/band/score`：承载，不直接等于吉凶。
4. `dfp`：木火土金水在该层的边际收益。
5. `interactions`：优先解释命中月支、日支与强结果五行的证据。
6. `nbs`：完整时柱才有。

## D 层解释顺序

先对比 R 与 D 的 DSS、DFP、能量和互动，再解释 DLS。必须说明大运一柱既可能带来根，也可能同时带来
压力；不能只按大运天干或地支单字下结论。D 层结果已经包含 R，不把 R 分数再加一次。

## Y 层解释顺序

1. 对比 D 与 Y 的 DSS/DFP，说明流年改变了什么。
2. 引用包含 `Y` 来源的互动，特别是流年是否直接作用大运药根、月支或日支。
3. 展示 AFS 组件与总分；不要二次计算或修改。
4. 分开报告 EAI 及 EFM。AFS 低而 EAI 高表示大动且阻力高，不等于“坏事必发生”。
5. 给与结构一致的现实动作：流程、证据、学习、缓冲、边界、预算、沟通或时间安排。

## 信息不足

- 时柱 `null`：代码仍给机械节点、能量、DSS、DFP和互动，但 `complete=false`，不生成 NBS/DLS/YDS/AFS
  等正式综合分。
- 无大运：停在 R。
- 有大运无流年：停在 D。
- 性别未知：普通单盘可运行；传统伴侣星只作未决项。
- 只有出生资料而无法可靠排盘：索取四柱，不心算日柱、节气边界或起运时间。
