# 筛选标准

这份文件是 `/digest` 的地基。它会自我更新——每轮开头，agent 把你在 Notion `Feed Digest`
里标过 Rating 的条目消化成新例子追加到下面，标准有系统性偏差时改写描述。改动进 git，
`git log -p skills/digest/interests.md` 能看到标准怎么漂移的。

你随时可以直接改这个文件。手写的和 agent 写的一样有效。

---

## 我关心什么

- **公司情报**。高速增长的 AI 创业公司——融资、招聘、团队动向、创始人在做什么。尤其是
  冲击独角兽那个阶段的：成长预期已经清晰，失败概率低。**这是最高优先级。**
- **AI Agent 技术趋势**。agent 内部写 code 而不是把任务分发给别的 agent；MCP 和其他
  给 agent 而不是给人的服务；dev tools for AI agent；long-horizon agent 怎么维持状态。
- **创业判断力**。具体 idea 的复盘，尤其是「为什么这个 idea 不成立」——比成功故事有用，
  因为成功故事幸存者偏差太重。
- **产品品味**。简洁、organized、futuristic、离用户近、大 user base、toC。参照系是
  search、Notion、Google Search。
- **开源项目**。有意思的 AI 产品。找开源项目就像找一个好创业公司。
- **湾区 / YC 生态**。

## 我不想看什么

- **自吹自擂的引流帖**。本质是给自己产品导流的软广。**对创业项目要仔细甄别，绝大多数
  创业产品毫无价值。** 一个创业公司出现在清单里，必须是因为它做的事本身值得知道，
  不是因为它的创始人很会写帖子。
- 抖音式内容、短视频、任何以即时快感为卖点的东西。
- 「10 个提升效率的 AI 工具」这类无判断增量的清单体。
- AI PPT generator 那类 short bet 大模型的产品——更好的模型出来它就死了。
- 给前 1% 的人做的产品。我要做剩下 99% 的人的产品。
- 泛泛的 b2b SaaS 讨论。
- 纯模型跑分 / benchmark 刷榜。

---

## Reddit 订阅

Reddit server 用的是匿名 client，没有登录态，拿不到你的订阅流——所以这里手动列。

```
r/LocalLLaMA  r/MachineLearning  r/ExperiencedDevs
r/ycombinator  r/startups  r/SaaS  r/cscareerquestions
```

---

## 例子

下面的例子帮助判断边界。**标着「种子」的是初始推测，不是真实反馈**——真实反馈进来后
应该逐渐把它们挤掉。

### 入选

- 种子 · "Anthropic 开源了 MCP 的 registry 实现" · 具体的 agent 基础设施进展，不是观点
- 种子 · "我们把 agent 的 planning 层换成生成 Python，延迟降了 60%" · 有数字、有机制，
  正好是「agent 内部写 code」这条

### 落选

- 种子 · "2026 年最值得关注的 20 个 AI Agent 工具" · 清单体，无判断增量
- 种子 · "我用 3 个月做到 ARR 10 万，AMA" · 无从核实的自述数字，评论区全是恭喜，
  典型引流帖
- 种子 · "GPT-5 在 SWE-bench 上刷到 82%" · 纯跑分
