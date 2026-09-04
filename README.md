# Bazi-ESID 2.5 Code Edition

[![Tests](https://github.com/Jeff33/bazi-esid/actions/workflows/test.yml/badge.svg)](https://github.com/Jeff33/bazi-esid/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

Bazi-ESID 是一个以四柱八字为输入的确定性结构化研究工具，同时提供可由 ChatGPT/Codex 调用的 Skill
说明和纯 Python 计算引擎。代码是数值结果的唯一裁决者：不存在 Strict/Operation 双模式，也不允许语言
模型在运行后人工改分。

> **重要声明：** 本项目把传统命理规则转化为可复现计算，仅供文化研究、娱乐与自我反思。它不是科学预测、
> 事实认定、医学诊断、法律意见、投资建议或重大人生决策工具。确定性只代表相同输入与版本产生相同输出，
> 不代表预测准确或理论已经科学验证。详见 [DISCLAIMER.md](DISCLAIMER.md)。

## 核心特性

- 单一代码口径：`scripts/run_esid.py` 是唯一入口。
- 分层重算：支持原局 R、大运 D、流年 Y，以及双盘关系 C_R/C_D/C_Y。
- 严格输入：非法干支、未知字段、重复键和层级跳跃会直接报错。
- 可复现：输出携带输入、规则、实现和 payload 的 SHA-256 凭据。
- 可审计：互动包含来源、位置、规则 ID、稳定证据 ID 和去重组。
- 本地优先：核心引擎仅使用 Python 标准库，不联网、不遥测、不自行保存输入。

当前方法版本为 `2.5-code`，引擎版本为 `1.0.0`。

## 适用范围

可以用于：

- 单盘原局、大运、流年和个人婚恋的结构化复盘；
- 双盘合婚、关系阶段和婚期的内部指标计算；
- 同规则、同层级、同完整度记录的批量回归或比较；
- 研究规则变化对确定性输出的影响。

不得用于就业、教育、住房、信贷、保险、医疗、法律或政府服务等高影响资格决定，也不得据此诊断疾病、
保证收益、断言死亡/犯罪/忠诚，或胁迫他人作婚恋及其他重大决定。

## 快速开始

要求：Python 3.10 或更高版本；运行引擎不需要第三方 Python 包。

```bash
git clone https://github.com/Jeff33/bazi-esid.git
cd bazi-esid
python3 scripts/run_esid.py self-test
python3 -m unittest discover -s tests -v
```

### 运行单盘命例

```bash
python3 scripts/run_esid.py analyze --input tests/fixtures/golden_single.json
```

最小输入结构：

```json
{
  "schema": "bazi-esid.input/1",
  "record_id": "case-001",
  "mode": "single",
  "charts": [
    {
      "id": "A",
      "sex": "unspecified",
      "pillars": {
        "year": "庚午",
        "month": "甲申",
        "day": "乙巳",
        "hour": "庚辰"
      }
    }
  ],
  "timing": {"luck": {}, "year": null}
}
```

引擎不负责从公历/农历生日排盘。若已经确认四柱，应直接提供年、月、日、时柱；完整协议见
[references/input-contract.md](references/input-contract.md)。

### 校验输出完整性

```bash
python3 scripts/run_esid.py analyze --compact --input tests/fixtures/golden_single.json \
  | python3 scripts/run_esid.py verify --compact
```

校验成功返回：

```json
{"valid":true}
```

`payload_sha256` 用于发现输出被修改；`input_sha256`、`ruleset_sha256` 和
`implementation_sha256` 用于锁定复现条件。哈希不证明模型在经验或科学意义上的有效性。

## 作为 Skill 使用

仓库根目录本身就是一个 Skill，包含必需的 `SKILL.md`，以及可选的 `scripts/`、`references/`、
`assets/` 和 `agents/openai.yaml`。

Codex 本地用户可将仓库放到用户技能目录：

```bash
git clone https://github.com/Jeff33/bazi-esid.git ~/.agents/skills/bazi-esid
```

随后可显式调用：

```text
$bazi-esid 分析：男命，庚午 甲申 乙巳 庚辰；大运辛卯，流年乙酉。
```

产品入口和安装方式可能更新，请以 [OpenAI 的 Build skills 文档](https://learn.chatgpt.com/docs/build-skills)
为准。本 GitHub 仓库是源码分发，不表示已经通过 OpenAI 公共插件目录审核，也不表示获得 OpenAI 背书。

## 输出指标

- 单盘：DSS、DFP、NBS、DLS、YDS、SCS、VP、AFS、EAI、EFM。
- 合婚：IMS、BCS、RFS、MPS、CRS、CHS、HOI、CFS、DCS、YCS、R-SCS、RVP、R-AFS、RAI。

这些数值只在本规则集内部有定义，不是客观概率、人口常模、人格测验、医学量表或信用评级。公式与分档见
[references/scoring-contract.md](references/scoring-contract.md)。

## 隐私

引擎只需要四柱、运岁、匿名记录 ID 和必要关系参数。不要提交姓名、证件、联系方式、精确住址或其他不必要
的可识别信息；处理第三方或批量资料前，应确认合法来源、适当授权或同意。核心 CLI 不联网或持久化数据，
但聊天平台、终端历史、日志及用户创建的输入文件可能另有保存机制。详见 [PRIVACY.md](PRIVACY.md)。

## 项目结构

```text
.
├── SKILL.md
├── agents/openai.yaml
├── assets/icon.svg
├── references/
├── scripts/run_esid.py
├── scripts/esid_engine/
└── tests/
```

原始方法 PDF 不随本仓库发布。Code Edition 对原稿未公开的常量和算法作了明确冻结，并将这些补齐项标识
为新的确定性实现，而不是冒充 PDF 原文或公认学术标准。详见 [NOTICE](NOTICE)。

## 贡献与版本

任何影响数值的常量或算法修改都必须：

1. 更新引擎版本；
2. 使实现或规则哈希发生变化；
3. 更新黄金 fixture 的明确期望值；
4. 通过自检和完整测试；
5. 在变更说明中解释口径变化。

提交测试数据前必须去除个人身份信息。完整要求见 [CONTRIBUTING.md](CONTRIBUTING.md)，安全问题见
[SECURITY.md](SECURITY.md)。

## 许可证

本项目使用 [Apache License 2.0](LICENSE)。许可证授予代码和仓库内文档的使用权，但不构成对
`Bazi-ESID` 名称或任何第三方商标的额外授权，也不改变 [DISCLAIMER.md](DISCLAIMER.md) 中的使用边界。

---

**English summary:** Bazi-ESID is a deterministic, offline Four Pillars research engine packaged as an
OpenAI-compatible skill. Reproducibility means computational consistency, not scientific validity or predictive
accuracy. Do not use it for medical, legal, financial, high-impact eligibility, or coercive relationship decisions.
See [DISCLAIMER.md](DISCLAIMER.md) and [PRIVACY.md](PRIVACY.md).
