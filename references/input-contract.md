# Code Edition 输入协议

引擎只接受 UTF-8 JSON。未知字段、重复键、非法干支、层级跳跃都会报错；这保证同一语义只有一种
规范表示。四柱是评分边界，历法排盘不在本引擎内完成。

## 单盘

```json
{
  "schema": "bazi-esid.input/1",
  "record_id": "case-001",
  "mode": "single",
  "charts": [
    {
      "id": "A",
      "sex": "male",
      "pillars": {
        "year": "庚午",
        "month": "甲申",
        "day": "乙巳",
        "hour": "庚辰"
      }
    }
  ],
  "timing": {
    "luck": {"A": "辛卯"},
    "year": "乙酉"
  }
}
```

`sex` 只允许 `male`、`female`、`unspecified`，也接受输入别名 `男`、`女`、`未指定`，规范化后总是英文。
时柱未知时显式写 `null`。原局只运行时，`luck` 用 `{}`、`year` 用 `null`；R+D 时给 `luck`，`year`
仍为 `null`。不能只给 `year` 而省略大运。

`sex` 是传统模型内部的计算参数，不用于推断性别认同、性取向、关系角色或社会价值。不得根据姓名、照片、
职业或表达方式猜测该字段；用户未提供时使用 `unspecified`。

## 合婚

```json
{
  "schema": "bazi-esid.input/1",
  "record_id": "pair-001",
  "mode": "compatibility",
  "charts": [
    {
      "id": "A",
      "sex": "male",
      "pillars": {"year": "庚午", "month": "甲申", "day": "乙巳", "hour": "庚辰"}
    },
    {
      "id": "B",
      "sex": "female",
      "pillars": {"year": "癸酉", "month": "甲寅", "day": "丁巳", "hour": "甲辰"}
    }
  ],
  "timing": {
    "luck": {"A": "辛卯", "B": "乙卯"},
    "year": "乙酉"
  }
}
```

合婚 ID 必须恰为 `A`、`B`。只要进入 D 层，双方大运必须同时给出。流年是双方共享的时间坐标，只给
一个。双方完整四柱与性别齐全才生成正式 CFS/R-AFS；否则仍返回可验证的机械事实，但不会补分。

## 批量

```json
{
  "schema": "bazi-esid.batch-input/1",
  "batch_id": "years-001",
  "ranking_metric": "afs",
  "records": [
    {"schema": "bazi-esid.input/1", "record_id": "candidate-a", "mode": "single", "charts": [], "timing": {}},
    {"schema": "bazi-esid.input/1", "record_id": "candidate-b", "mode": "single", "charts": [], "timing": {}}
  ]
}
```

示例中的 `charts`/`timing` 省略内容仅表示嵌入完整单条输入，不能照空数组运行。`ranking_metric` 只允许
`nbs`、`afs`、`cfs`、`r_afs`。引擎只在同规则哈希、同有效层级、同完整度的首个可比较群组内排序；
不能比较的记录进入 `unranked`，不强行排位。

## 规范化与复现

- 干支必须是合法六十甲子组合，不只检查字符存在。
- 所有字符串做 NFC 规范化，JSON 键排序后计算输入哈希。
- 输出不含当前时间、随机数或机器路径。
- 分数使用固定规则与 ROUND_HALF_UP；DSS 比值保留两位，其余报告分保留一位。
- `payload_sha256` 可由 `verify` 命令检查，任何输出篡改都会使校验失败。

## 数据最小化

- 引擎不需要姓名、曾用名、证件号码、联系方式、精确住址或账号标识，不要把这些字段塞入 `record_id`。
- 已有四柱时不要重复收集精确出生日期、时间和地点；需要排盘时只在排盘步骤处理必要资料，并在传给本引擎
  前尽量移除可识别信息。
- 第三方或批量数据必须来自用户有权处理的来源；公开报告应使用不可逆的案例编号并删去识别线索。
- 核心 CLI 不联网、不遥测，也不自行持久化输入；聊天平台、终端历史、日志和用户创建的 JSON 文件仍受各自
  环境的保存政策约束。
