# Bazi-ESID 2.5 Code Edition

[![Tests](https://github.com/Jeff33/bazi-esid/actions/workflows/test.yml/badge.svg)](https://github.com/Jeff33/bazi-esid/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

一套让八字分析更一致、更清楚，也更方便复盘的工具。

Bazi-ESID 可以根据已经确认的四柱，分析原局、大运、流年、个人婚恋和双盘关系。它使用统一的计算标准，
不会因为换一种问法就临时改变评分，也不会在结果出来后人为调高或调低分数。

> 本项目用于传统文化研究、娱乐与自我反思，不是科学预测，也不能替代医疗、法律、财务或其他专业意见。

## 它能帮你做什么

- **看单人命局：** 梳理原局结构、承受力、五行倾向和主要关系。
- **看大运与流年：** 比较不同阶段带来了哪些支持、压力和变化。
- **看个人婚恋：** 从个人命局出发，关注关系需求、边界和当前阶段。
- **看双盘关系：** 分析两人的互补、冲突、相处节奏和阶段变化。
- **做统一比较：** 对多个年份或候选方案使用同一标准，减少前后口径不一致。

## 一份分析会告诉你什么

报告不只给一个总分，还会说明：

1. 本次使用了哪些四柱、大运和流年资料；
2. 哪些结构形成支持，哪些结构带来压力或波动；
3. 原局、大运和流年之间发生了什么变化；
4. 当前更值得留意的领域，例如事业、财务、关系、健康压力、学习或迁移；
5. 可以落到现实中的建议，例如沟通、预算、边界、准备、学习和时间安排。

每条主要判断都能回到具体的干支关系和计算记录，方便再次检查，而不是只给一句“好”或“不好”。

## 快速使用

安装本 Skill 后，可以直接这样提问：

```text
$bazi-esid 分析：男命，庚午 甲申 乙巳 庚辰；大运辛卯，流年乙酉。
```

双盘关系示例：

```text
$bazi-esid 分析以下两组四柱的关系与相处重点，并说明评分依据：
A：庚午 甲申 乙巳 庚辰，男
B：癸酉 甲寅 丁巳 甲辰，女
```

如果资料不足，系统只会询问会实际影响本次分析的必要信息，不要求重复提供姓名、出生地或其他无关资料。

## 为什么结果更容易复盘

- **只有一个统一版本：** 不存在 Strict 与 Operation 两套口径。
- **每个阶段重新分析：** 大运和流年加入后，会根据完整结构重新计算，不是简单加几分或减几分。
- **判断依据可以查看：** 重要的合、冲、刑、害、破等关系都会保留来源。
- **相同资料得到相同结果：** 只要输入和版本相同，计算结果就保持一致。

这里的“一致”指计算过程稳定，并不代表命理理论已经得到科学验证，也不代表现实事件一定发生。

## 怎样理解分数

Bazi-ESID 把不同问题分开表达：

| 报告内容 | 普通语言含义 |
| --- | --- |
| 原局基础 | 命局本身的承载、平衡和稳定程度 |
| 大运影响 | 当前十年阶段相对原局带来的支持或阻力 |
| 流年影响 | 某一年相对当前基础带来的变化方向 |
| 年度顺逆 | 当前结构做事是否更容易形成配合 |
| 事件强度 | 这一年是否容易出现明显变化，不直接代表好坏 |
| 领域提示 | 变化更可能集中在哪些生活领域 |
| 双盘关系 | 两人的互补、冲突、持续性和阶段配合 |

分数是这套方法内部的比较工具，不是成功率、疾病概率、人格评级或对一个人价值的判断。完整指标说明见
[评分说明](references/scoring-contract.md)。

## 使用前请了解

请不要用本项目替代现实证据或专业判断，尤其不要用于：

- 诊断疾病、改变治疗、预测寿命或延误就医；
- 投资、交易、借贷、赌博或保证收益；
- 判断法律责任、诉讼结果或犯罪风险；
- 替别人决定结婚、离婚、生育或其他重大人生选择；
- 招聘、升学、住房、信贷、保险、医疗等影响他人机会与权益的筛选；
- 未经同意对第三方进行公开排名、贴标签或建立个人档案。

合婚结果也不能证明爱、忠诚、同意或未来行为。现实中的安全、自由意愿、沟通和长期行动永远比模型分数
更重要。详细边界见 [使用说明与免责声明](DISCLAIMER.md)。

## 隐私

如果已经知道四柱，通常只需要四柱、大运、流年和必要的关系信息，不需要提交姓名、证件号码、联系方式或
精确住址。

核心程序在本地计算，不主动联网、追踪用户或保存资料。但聊天平台、终端记录以及用户自己保存的文件可能有
各自的保存方式。处理伴侣或其他第三方资料前，请确认已经取得适当授权或同意。详见
[隐私说明](PRIVACY.md)。

## 常见问题

### 可以直接输入公历或农历生日吗？

当前核心程序不负责排盘。请优先提供已经确认的年柱、月柱、日柱和时柱，避免节气、时区或换日边界造成误差。

### 分数越高就一定越好吗？

不是。顺逆程度和事件强度是两件事：变化很大不等于变化有利，分数也需要结合具体结构和现实情况理解。

### 可以保证某年结婚、发财或发生某件事吗？

不能。本项目不会把内部评分写成现实概率，也不会作“一定发生”的承诺。

### 不知道时柱还能分析吗？

可以查看已有资料形成的基础关系，但系统会明确标注信息不完整，不生成依赖完整四柱的正式综合分。

<details>
<summary><strong>开发者安装、测试与复现信息</strong></summary>

### 环境要求

Python 3.10 或更高版本。核心程序只使用 Python 标准库。

### 安装为 Codex Skill

```bash
git clone https://github.com/Jeff33/bazi-esid.git ~/.agents/skills/bazi-esid
```

不同产品的安装入口可能变化，请以
[OpenAI Build skills 文档](https://learn.chatgpt.com/docs/build-skills)为准。本仓库是公开源码分发，不表示
已经通过 OpenAI 公共插件目录审核，也不表示获得 OpenAI 背书。

### 本地测试

```bash
git clone https://github.com/Jeff33/bazi-esid.git
cd bazi-esid
python3 scripts/run_esid.py self-test
python3 -m unittest discover -s tests -v
```

### 运行示例

```bash
python3 scripts/run_esid.py analyze --input tests/fixtures/golden_single.json
```

输入格式见 [输入协议](references/input-contract.md)。核心程序不负责从生日换算四柱。

### 检查输出是否被修改

```bash
python3 scripts/run_esid.py analyze --compact --input tests/fixtures/golden_single.json \
  | python3 scripts/run_esid.py verify --compact
```

成功时返回：

```json
{"valid":true}
```

输出中的输入、规则、实现和结果哈希用于确认复现条件与发现内容改动。它们只证明计算一致性，不证明预测
准确性。

当前方法版本：`2.5-code`；引擎版本：`1.0.0`。

</details>

## 开放源码与贡献

本项目使用 [Apache License 2.0](LICENSE)。提交改进前请阅读 [贡献指南](CONTRIBUTING.md)；发现安全
问题请参考 [安全政策](SECURITY.md)。

任何会改变评分结果的修改，都应更新版本、测试和说明，不能只为了让某个命例看起来更理想而调整规则。
测试资料必须删除可识别个人的信息。

原始方法 PDF 不随本仓库发布。Code Edition 对原稿没有完整公布的参数作了明确补充，这些内容属于本项目的
实现选择，不冒充 PDF 原文或公认学术标准。详见 [NOTICE](NOTICE)。

---

**English summary:** Bazi-ESID helps users explore Four Pillars charts, luck cycles, annual timing, and
compatibility through one consistent and reviewable method. It is intended for cultural research, entertainment,
and self-reflection—not scientific prediction or professional decision-making. See [DISCLAIMER.md](DISCLAIMER.md)
and [PRIVACY.md](PRIVACY.md).
