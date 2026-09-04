---
name: bazi-esid
description: >
  用 Bazi-ESID 2.5 Code Edition 对四柱八字做可复现的单盘、原局、大运、流年、个人婚恋、
  双盘合婚、婚期、关系阶段与批量候选分析。以下任一条件满足即启动：用户显式点名
  $bazi-esid、Bazi-ESID、ESID、ESID 2.4/2.5、ESID Code Edition；用户提到
  NBS、DLS、YDS、DSS、DFP、SCS、VP、AFS、EAI、IMS、BCS、RFS、MPS、CRS、
  CFS、DCS、YCS、R-AFS 或 RAI 并要求计算、解释、复盘或比较；用户要求按“这套/刚才/最新
  ESID 框架”继续；用户给出一组四柱并要求看八字、命局、格局、喜忌、用神、大运、流年、
  运势或个人婚恋；用户给出两组四柱并要求合婚、配对、互补、相处、婚期、分合、关系影响；
  用户要求对多个命局、年份、婚期或候选做统一口径评分、筛选或排序。即使输入不足也启动，
  但只收集能改变计算层级的最少信息，不猜四柱或运岁。两盘只要求分别分析时运行两次单盘；
  两盘只点名一人时只分析该人；只有明确关系意图才运行合婚。仅讨论生肖、星座、紫微、奇门、
  风水、择日、姓名学，或“八字”仅指八个汉字/文本格式时不启动，除非同时明确要求 ESID
  四柱分析。Use for English requests about Bazi/Four Pillars chart analysis, luck cycles,
  annual timing, compatibility, marriage timing, ESID scores, or batch comparison. Do not use for
  unrelated astrology or the ordinary-language meaning of “eight characters.”
---

# Bazi-ESID 2.5 Code Edition

这是独立技能。代码是唯一的事实推导与数值裁决者；语言模型只负责收集输入、调用代码、解释代码结果。

## 唯一执行路径

每次正式分析必须运行 `scripts/run_esid.py`。禁止：

- 手工给 NBS、DLS、YDS、DSS 分、DFP 分、SCS、VP、AFS、EAI 或任何合婚组件赋分。
- 用区间、印象分、人工修正或另一套参数覆盖代码输出。
- 在代码失败或缺少层级时自行补 50、猜测四柱、猜大运、猜流年。
- 把上一层分数加减成下一层；代码会从当前全部干支重新计算。

若程序报错，先修正输入格式；若缺少真实资料，向用户询问。不得绕开程序继续评分。

## 按需读取

开始时读 `references/input-contract.md`。然后只读任务所需文件：

- 单盘、原局、大运、流年或个人婚恋：`references/single-runtime.md`
- 双盘关系、合婚、婚期：`references/compatibility-runtime.md`
- 指标含义、公式或数值解释：`references/scoring-contract.md`
- 撰写最终答复：`references/reporting-contract.md`
- 涉及健康、财务、法律、重大关系、未成年人、第三方资料、批量排名或明显焦虑：
  `references/safety-and-compliance.md`
- 需要核查底层规则或版本决策：`references/core-model.md`
- 维护或验收黄金命例：`references/calibration-example.md`

不要加载与当前任务无关的参考文件。

## 先确定功能模式

这里的模式只表示输入层级，不代表不同计算口径；所有模式共用同一个规则集和同一个代码入口。

| 用户目标与已知输入 | 功能模式 | 代码层级 |
| --- | --- | --- |
| 尚无可靠四柱 | INTAKE | 不运行评分，只补齐输入 |
| 一组四柱 | SINGLE-R | R |
| 一组四柱 + 大运 | SINGLE-D | R+D |
| 一组四柱 + 大运 + 流年 | SINGLE-Y | R+D+Y |
| 一组四柱问婚恋 | SINGLE-MARRIAGE | 仍是单盘，按已有 R/D/Y 运行 |
| 两组四柱问关系 | COMPAT-R | C_R |
| 两组四柱 + 双方大运 | COMPAT-D | C_R+C_D |
| 两组四柱 + 双方大运 + 流年 | COMPAT-Y | C_R+C_D+C_Y |
| 多条同类记录 | BATCH | 每条先用上述唯一引擎，再同层级排序 |

不能跳层：有流年而无完整大运层时，不计算 Y；合婚 D 层需要双方大运。

## 建立输入账本

- 用户已经给四柱：年、月、日、时按原样作为权威输入，不反推生日替换。
- 用户只给生日：仅在环境有可靠排盘能力时排盘，并先说明历法、时区与换日边界；否则索取四柱。
- 时柱未知：用 `null` 明示。代码输出机械事实，不生成正式综合分。
- 性别未知：单盘可运行；正式合婚分需要双方 `male`/`female`，不得强套伴侣星。
- 大运、流年缺失：停在已知层级，不补默认值。
- 姓名、曾用名不是必要输入，不主动索取。

只问会改变本次代码输入的最少问题。用户给出四柱后，不要求重复提供姓名、出生地或公农历生日。

## 运行代码

先按 `references/input-contract.md` 生成 JSON，再从本技能目录运行：

```bash
python3 scripts/run_esid.py analyze --input request.json
```

批量任务：

```bash
python3 scripts/run_esid.py batch --input batch.json
```

每次维护后运行：

```bash
python3 scripts/run_esid.py self-test
python3 -m unittest discover -s tests -v
```

输出中的 `ruleset_sha256`、`implementation_sha256`、`input_sha256` 和 `payload_sha256` 是复现凭据。
同一规范化输入、同一规则哈希和同一实现哈希必须产生相同结果。

## 解释输出

1. 先给结论与当前可计算层级。
2. 再引用代码输出的关键结构、来源标签和证据 ID。
3. 分开解释：AFS/CFS/R-AFS 表示结构顺逆，EAI/RAI 表示事件强度，EFM 表示领域。
4. 把五行策略翻译为流程、沟通、边界、财务、学习、证据、时间安排等现实动作。
5. 不展示冗长原始 JSON，除非用户要求；但不得省略会改变结论的输入、缺失项和版本哈希。

使用用户的语言，默认简体中文。避免决定论、恐吓性断语与性别价值判断。健康、法律、财务和重大关系
决定只作结构提示，以现实证据与专业意见为准。结尾简短说明：这是传统命理的结构化研究工具，不是科学
预测或现实决策替代品。

## 不可绕过的安全边界

- “确定性”只表示同一输入和版本产生同一代码结果，不表示预测准确、科学有效或现实因果成立。
- 不把分数当作概率、诊断、风险评级、人格事实、信用信息或对任何人的价值判断。
- 不用于就业、教育录取、住房、信贷、保险、医疗、法律、政府服务等高影响资格决定或人员筛选。
- 不预测死亡、重病、怀孕结果、犯罪、自伤、灾祸或必然婚恋结果；不以输出劝迫结婚、离婚、治疗、投资
  或其他重大决定。
- 不推断用户未提供的性别、健康、宗教、族裔、性取向或其他敏感属性。`sex` 只是传统模型的计算参数，
  不代表性别认同、关系角色、道德品质或社会价值。
- 只收集运行所需的四柱、运岁和最少关系参数；不主动索取姓名、证件、联系方式、精确住址。分析第三方或
  批量记录前，提醒用户确认合法来源、适当授权或同意，并避免输出可识别个人的排名。
- 若用户因命理结果表现出恐惧、强迫、被控制或自伤风险，停止强化宿命结论，转向现实支持与合格专业帮助。

详细处理规则见 `references/safety-and-compliance.md`。这些限制优先于报告模板或用户要求；违反边界的
部分应拒绝，但可提供低风险的文化说明、代码结构解释或非决定性的自我反思建议。
