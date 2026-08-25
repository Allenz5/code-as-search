# 搜索池

`/linkedin_scout` 每轮从这里取 query，跑完按 `Connection Digest` 里的战绩改这里。
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

**类型比 query 值钱得多，而且它由人提供，不由 agent 生成。** 招聘帖和线下活动这两个
最有价值的类型都是 Allen 提的。别去发明类型，**每轮报告主动问一句有没有新的** ——
问本身就是机制。

配 `date_posted="past-week"`。**这条渠道没有地点 facet**，捞到的人必须单独查湾区。

### 内容搜索到底是怎么工作的（2026-08-24 实测，五个 query）

这三条是机制事实，不是观察，选词必须建立在它们之上：

1. **词袋匹配，不认短语。** `we open sourced` 返回的是所有泛泛谈 open source 的帖子 ——
   短语结构被拆掉了。加引号 `"we open sourced"` 直接返回 **No results found**，说明
   **没有短语操作符**。所以任何依赖词序或第一人称句式的 query 都不可能成立。
2. **没有任何作者侧的过滤维度** —— 没有地点、没有职级、没有公司。你加的每个限定词都在
   筛**帖子的用词**。`San Francisco AI hackathon` 捞到的是"帖子里提到旧金山"的人（广告牌、
   加州法案、Qwen），不是"人在旧金山"的人。
3. **由 1 和 2 推出**：唯一有结构性优势的 query 家族是**作者身份由帖子类型本身决定**的
   那种。招聘帖就是 —— 发帖的人按定义就是在招人的那个人。其余类型只能赌"聊这个话题的人
   恰好是目标"，而任何 AI 话题下声音最大的都是顾问、DevRel 和做 marketing 的。

**修正后的选词原则**：宽词 + 翻到底仍然对（滚动修复后单 query 从 6 篇涨到 126–153 篇），
但它不足以救回一个机制上就没有作者信号的 query。**优先扩充作者身份由类型决定的 query，
其余类型接受低产出并靠减分词筛。**

**选词教训（作废的那版）**：第一批用长而具体的短语（`shipped our agent to production`），
当时归因于"太罕见"。真实原因是上面第 1 条 —— 短语根本没被当短语匹配。

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

### 类型 G：AI 线下活动 —— 唯一自带地点信号的类型

24. `AI meetup`
25. `AI hackathon`
26. `demo day`
27. `SF AI event`
28. `speaking at`

**这个类型有一个别的类型都没有的性质：它自带地点。** 搜帖渠道最大的缺陷是没有 geo
facet，每个候选人都要单独查湾区。但一个人发帖说他去了旧金山的 AI meetup，这件事本身
就说明他人在湾区。所以这个类型的候选人**廉价筛那一层就便宜得多**，值得多给配额。

副作用是它也会捞到活动主办方、社区运营和到处站台的人 —— 那些是 axis 1 的典型失败。
战绩单独看。

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

## 搜帖实测记录（2026-08-24 第二轮，滚动已修）

| query | 类型 | 帖子 | 过减分筛 | 像样的 | 结论 |
|---|---|---|---|---|---|
| `ai hiring` | A | 153 | — | — | 重复最多的首行是 IT 外包派遣刷屏（C2C/W2/Hotlist） |
| `hiring founding engineer` | A | 126 | 23 | 3 | **五个里最好的一个**，但地点偏 NYC/LA/remote |
| `AI meetup` | G | ~20 | — | 0 | 全球均匀分布：Pune、卢森堡、东京、伊兹密尔、阿肯色 |
| `San Francisco AI hackathon` | G | 多 | 26 | 2 | 捞到的是"谈论 SF 的人"，顾问/CISO/教授居多 |
| `we open sourced` | C | 多 | 31 | 0 | 被拆成 "open source"，顾问和 DevRel 居多 |

**类型 G 的立论错了，需要重想。** 我当初写"线下活动自带地点信号"，理由是"发帖说去了
SF 的 meetup 就说明人在湾区"。错在把**帖子提到的地点**当成了**作者的地点** —— 见机制
第 2 条。地理限定词在这条渠道上不解决地点问题。这个类型是 Allen 提的，不擅自退役，但
现有的五个 query 需要换思路，或者接受它只是又一个普通话题类型。

**类型 A 是唯一被验证有结构性优势的。** 建议扩充。

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
