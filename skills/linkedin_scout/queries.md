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

（空。第一批种子跑完并拿到评分后填。）

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

## 搜帖 · 探索池（未验证）

配 `date_posted="past-week"`。**这条渠道没有地点 facet**，捞到的人必须单独查湾区。

选词原则：**挑构建者会写、而营销的人不会写的短语。** 第一次实测用
`AI agents evals production` 搜出来六个人，零个合格——CISO 的招聘帖、投票、猎头、
newsletter 推广。原因是结构性的：LinkedIn 内容搜索按互动量排序，而 LinkedIn 上互动量
高的就是招聘帖和 thought leadership。所以这里的词要具体到只有干活的人才会用。

1. `shipped our agent to production`
2. `inference cost per token`
3. `eval harness regression`
4. `we open sourced`
5. `context window limitation`
6. `agent reliability failure mode`
7. `fine-tuned on our own data`
8. `latency p99 LLM`
9. `training run compute`
10. `built an MCP server`
11. `prompt caching hit rate`
12. `benchmark results reproduce`
13. `RAG retrieval quality`
14. `multi-agent orchestration lessons`
15. `model weights released`

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
