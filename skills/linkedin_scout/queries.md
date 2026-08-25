# 搜索池

`/linkedin_scout` 每轮从这里取 query，跑完按 `Connection Feed` 里的战绩改这里。
战绩本身不存在这个文件里——它每轮从 Notion 现算（按 `Source` 和 `Channel` 分组数
各档 Rating）。两个状态存储会漂移，一个不会。这里只存 query 本身和定性笔记。

命中率 = 👍 ÷ (👍 + 😐 + 👎)，只在该 query 累计产出 ≥ 8 人后才判定。

| 情况 | 动作 |
|---|---|
| 命中率 > 40% | 提升为常驻，并派生变体 |
| 命中率 < 15%，且大量 👎 | 退役——人群找错了 |
| 命中率 < 15%，但几乎没有 👎、大量 😐 | **收紧，不退役**——人群对了但不够分量 |
| 已退役满 30 天 | 复活试一次（LinkedIn 结果会变，永久退役是在赌它不变） |

新 query 一律先 `pages=1`（约 10 人）试水，命中率过得去才升到 `pages=3`。直接上 3 页
等于把 30 个位置押在一个没验证过的猜测上。

---

## 搜人 · 已验证

（空。首跑 2026-08-24 只产生了"写入数"，还没有任何 Rating —— **命中率必须等评分**，
写入数不是命中率。下表是首跑的产量，不是战绩，别拿它当已验证。）

| query | 读了 | 写入 | 首跑观察 |
|---|---|---|---|
| `research engineer large language models` | 6 | 6 | 前沿实验室浓度最高 |
| `founding AI engineer` | 3 | 3 | 创业公司路径，牵引力差别很大 |
| `member of technical staff` | 2 | 2 | 30 人里只有 2 个可用，见定性笔记 |
| `post-training reinforcement learning engineer` | 2 | 2 | 未满 8 人，不判定 |
| `founding engineer AI agents` | 0 | 0 | 候选进了池子但没挤进读取名额 |
| `AI infrastructure inference optimization` | 2 | 0 | **2 读 0 写** —— 两个都是高管，见下 |
| `applied AI engineer evals` | 0 | 0 | 候选质量偏低，没挤进名额 |

## 搜人 · 种子（未验证）

全部配 `geo_urn="90000084"`、`network=["S","O"]`、`pages=3`。一度连接不用找——已经连上了。

1. `founding engineer AI agents`
2. `founding AI engineer`
3. `member of technical staff`
4. `research engineer large language models`
5. `AI infrastructure inference optimization`
6. `applied AI engineer evals`
7. `co-founder CTO AI startup`
8. `post-training reinforcement learning engineer`
9. `AI product engineer 0 to 1`
10. `machine learning systems engineer distributed training`

## 搜帖 · 查询池

**这条渠道不设渠道级退役。** 单个 query 照常按命中率退役，但渠道本身留着 —— 帖子能触达
的人和搜人触达的人不是同一批，而且它是唯一能按"这个人在做什么、在说什么"找人的入口。
搜人只能按头衔和公司找。

**搜帖的 query 要比搜人更多花样，这是硬要求。** 搜人是一个稳定人群的不同说法；搜帖是
**不同种类的帖子会曝光不同种类的人**，而种类本身要靠想出来。所以这里按"帖子类型"组织，
每轮从多个类型各取几个，不要全从一个类型里取。

配 `date_posted="past-week"`。**这条渠道没有地点 facet**，捞到的人必须单独查湾区。

**选词教训（2026-08-24）**：第一批我用的是长而具体的短语（`shipped our agent to
production`、`prompt caching hit rate`）。方向错了 —— 太罕见的短语匹配数本来就少，
剩下的又都是长篇引流帖。**宽而常见的词 + 真正翻到底，好过窄而精确的词只看一屏。**

### 类型 A：招聘帖 —— 曝光的是发帖的人，不是帖子的主题

小公司的 AI 招聘帖多半是技术创始人或工程负责人自己发的。这是唯一一种"内容平庸但作者
恰好正是目标"的帖子类型。

1. `ai hiring`
2. `hiring founding engineer`
3. `hiring AI engineer`
4. `looking for a technical cofounder`

### 类型 B：发布与上线 —— 曝光的是造东西的人

5. `we just launched`
6. `introducing our`
7. `shipped this week`
8. `now in beta`

### 类型 C：开源

9. `open source`
10. `released on GitHub`
11. `our repo`
12. `MIT license`

### 类型 D：技术主题 —— 宽词，靠翻页取量

13. `ai engineer`
14. `inference`
15. `evals`
16. `fine-tuning`
17. `agents in production`
18. `reinforcement learning`

### 类型 E：换工作 —— 曝光的是刚进精英实验室的人

19. `excited to join`
20. `starting at`
21. `joining the team at`

### 类型 F：融资 —— 高风险高回报

会捞到创始人，也会捞到大量 VC 和做 marketing 的。留着，但战绩要单独看。

22. `raised our seed`
23. `Series A`

### 不做的类型：论文与会议

`our paper` / `NeurIPS` / `ICML` / `accepted at` 这一类**明确不做**。论文发布帖曝光的
是学者 —— 博士生、教授、实验室的研究方向 —— 而画像要的是在公司里造产品的人。注意这不是
说研究员不合格：首跑写进库的十三个人里有一多半是前沿实验室的 research engineer。区别在
**入口**，不在人：从论文帖进来的是学术身份的人，从招聘帖、上线帖、开源帖进来的才是
在做产品的人。别再把这个类型加回来。

## 定向渠道

- **`get_company_employees(slug, keywords)`** —— 精英公司名单，slug 通过
  `search_companies` 拿。公司清单随 👍 的人所在公司增补。
- **`get_company_posts(slug)`** —— 同一批公司的主页帖，找露脸的作者。
- **`get_sidebar_profiles(username)`** —— 种子必须是**已经 👍 的人**。这是信噪比最高的
  渠道，因为它由真实反馈驱动。
- **`get_feed(num_posts=100)`** —— 你自己的信息流，已经在视野里发技术内容的人。

## 退役区

（空。退役的 query 移到这里并注明日期和理由，30 天后复活重试。）

## 定性笔记

- `AI agents evals production`（搜帖，2026-08-24 首测）：6 个结果零合格，其中三个精确
  命中反例（猎头、CISO 招聘帖、marketing）。不是运气差，是内容搜索按互动量排序的结构
  性后果。保留在池子里作为对照，看新的选词原则能不能跑赢它。

- **`member of technical staff` 要收紧，不要退役**（搜人，2026-08-24）：3 页 30 人里
  28 个是 VMware / Oracle / Salesforce / AMD / Pure Storage / NetApp / Nutanix /
  Cohesity。**这是传统企业的职级头衔，不是前沿实验室的用法** —— 池子里放这个词的时候
  我假设的是后者，假设错了。它确实捞到了 Anthropic 和 OpenAI 各一个，说明人群里有对的
  人，只是被淹没到 6% 以下。下一轮改成加公司限定或与 AI 词组合，不要单独用。

- **`research engineer large language models` 是首轮质量最高的 query**（搜人，
  2026-08-24）：3 页里出现 DeepMind Gemini post-training、Meta Superintelligence
  Labs、Apple Foundation Model、Databricks Mosaic Research、Amazon AGI、Scale AI。
  "research engineer" 这个词组似乎能有效区分前沿实验室和普通工程岗 —— 待评分验证。

- **`AI infrastructure inference optimization` 招来的是高管，不是构建者**（搜人，
  2026-08-24）：这个 query 送去读取的两个人都被判 no —— Ajit Mathews（Meta Senior
  Director，25 年全是组织建设）和 Sachin Katti（OpenAI VP Compute Strategy，前 Intel
  CTO）。都是 axis 1 失败，公司和地点毫无问题。原因可能是 "infrastructure" +
  "optimization" 这类词在 headline 里更常被管这摊事的人使用，而不是写 kernel 的人。
  下轮换成具体技术名词试试（vLLM、CUDA kernel、speculative decoding）。

- **搜帖渠道第二次零产出**（2026-08-24）：`shipped our agent to production` 和
  `built an MCP server` 两个 query，约 12 个作者，0 合格。作者构成是 DevRel 主管、
  招人的猎头、Account Executive、Salesforce 行政助理、GTM、一个外州学生、两个引流帖。
  但**这个结论已经作废** —— 当时每个 query 只看到一屏，因为抓取器根本没滚动
  （`window.scrollTo` 在 LinkedIn 自己的滚动容器里是空操作）。而互动量排序的信息流
  第一屏，恰好就是最会做互动的那一层。这条渠道从没被测过，只是在它最差的点上被采样了
  三次。修复见 commit a5ab7d2，选词方向已按"宽词 + 翻到底"重写。

## 本轮主动削减（必须记录，否则下轮看不出是"没有"还是"没找"）

2026-08-24 首跑：

- **搜帖只跑了 2 个 query，计划是 12–15。** 理由：这条渠道唯一的先验是 0/6，而它的每个
  候选还都要额外人工查湾区（没有 geo facet）。在 profile 读取尚未开始的第一天，把 15 次
  页面加载押在未验证渠道上，等于拿已验证渠道的预算去赌。稳态目标仍然是 12–15。
- **搜人跑了 7 个 query，计划是 10。** 未跑：`co-founder CTO AI startup`、
  `AI product engineer 0 to 1`、`machine learning systems engineer distributed
  training`。理由同上 —— 候选池已经远超 20 个读取名额，多跑 query 不会改变读谁。
- **`AI infrastructure inference optimization` 和 `post-training reinforcement
  learning engineer` 用了 pages=2 而不是 3。**
- **company_employees / company_posts / sidebar / feed 四条渠道本轮完全没跑。**
  sidebar 需要已 👍 的人做种子，冷启动时无法运行；其余三条是预算取舍。
