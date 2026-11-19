# arxiv-weekly

每周一 09:00（北京时间）自动从 arXiv 抓取论文，用 DeepSeek 打分、翻译，以**飞书交互式卡片**推送到手机。

卡片里能直接读中文标题、中文摘要和原文链接；每期在 `papers/` 留一份 Markdown 归档（`latest.md` 固定链接），卡片底部有按钮直达。不依赖任何第三方推送工具，消息长期保留、可搜索。

**关注方向（每周 6 篇）：**

| 方向 | 每期篇数 | 范围 |
|------|---------|------|
| AI 编码 / 编程代理 | 2 | coding agent、repo 级代码生成、程序修复、SWE-bench |
| LLM 应用工程 | 2 | RAG、tool use、context engineering、agent 评测 |
| Web 全栈 / 前端工程 | 1 | WebAssembly、WebGPU、浏览器、前后端框架、微服务 |
| 开发者工具 / 测试 / 工程效率 | 1 | IDE、code review、测试生成、静态分析、CI |
| 计算机图形学与游戏 | 0–1 | cs.GR；**只在分数明显更高时才替补进来**，最多 1 篇 |

> 配额、查询式、权重都在 `arxiv_fetcher.py` / `quality.py` / `selector.py` 里，篇数可以用环境变量 `MAX_PAPERS` 调。

---

## 选题方法（算分）

### 第 1 步：候选池

- **窗口 21 天**：新论文不等于好论文，给三周机会，也保证还追得上新方向。
- 5 个话题各抓最多 50 条，按提交时间倒序。
- 按 arXiv id（去版本号）和标题指纹去重，跨话题重复只算一次。
- 每个话题按「关键词相关度 + 引用数」预筛 **15 篇**，只把这一批送去 LLM 打分（控制成本）。

### 第 2 步：每篇的分数

| 项 | 怎么算 | 权重 / 上限 |
|---|---|---|
| 相关性（LLM） | 0–100，按 `quality.py` 里的读者画像评 | × 0.45 |
| 扎实度（LLM） | 0–100，新颖性、技术贡献、实验、可复现性；换数据集/微小增量/纯综述压分 | × 0.40 |
| 关键词相关度 | 标题命中 ×3 + 摘要命中 ×1 | × 0.15，封顶 100 |
| 录用加分 | `comment` / `journal_ref` 含 `accepted`、`to appear`、`camera-ready`、`oral`、`spotlight`、`best paper` | +8 |
| 代码加分 | 标题或摘要含 github / gitlab / huggingface /「code is available」 | +2 |
| 引用速度 | `引用数 ÷ 发表月数 × 0.25`（老论文的引用不能和白纸一样算） | 最多 +5 |
| 新鲜度 | 0–7 天 +3；8–14 天 +2；15–21 天 +1 | 最多 +3 |

```
score = 0.45 × 相关性
      + 0.40 × 扎实度
      + 0.15 × min(关键词 × 4, 100)
      + 录用(0/8) + 代码(0/2)
      + min(引用 ÷ 月数 × 0.25, 5)
      + 新鲜度(0–3)
```

没有 `DEEPSEEK_API_KEY` 时退化成纯启发式：

```
score = min(关键词 × 8, 70) + min(引用, 25) + 录用 + 代码 + 引用速度 + 新鲜度
```

> 为什么这样配：引用和新鲜度都只是"小加分"。新论文引用通常是 0，如果按引用排序，实际效果就是按时间排；如果按时间排，水论文只要提交得巧就能进。所以主权重给 LLM 的**相关性 + 扎实度**，时间只负责轻轻推一把。

### 第 3 步：从分数到 6 篇

1. **配额轮转**：AI 编码 2 篇、LLM 应用 2 篇、Web 1 篇、开发者工具 1 篇，每个方向轮流取，避免被高分方向吃光。
2. **补满**：某个方向候选不够时，剩下的名额按分数跨方向补。
3. **图形学替补**：只有当它的最高分比"至少有两篇的方向里最弱那篇"高 **5 分**以上，才顶掉一篇；所以图形学可能一周 0 篇。
4. **展示顺序**：按方向分组，组内分数降序。

### 第 4 步：去重与"已读"

- 只有**真正推送成功**的 6 篇写进 `data/seen_ids.json`（`id → 日期`）。
- 没选中的论文下周仍在这 21 天窗口里，可以再竞争一次——好论文不会因为撞上更强的一周被埋掉。
- 记录保留 120 天，过期自动清理。
- arXiv id 统一去版本号（`2611.09693v1` → `2611.09693`），重新提交不会被当成新论文再推一遍。

### 想调口味，改哪里

| 想改什么 | 改哪里 |
|---|---|
| 关注的领域 / 读者画像 | `quality.py` 的 `INTEREST_PROFILE` |
| 话题查询式、关键词、配额外 | `arxiv_fetcher.py` 的 `TOPICS` |
| 各分项权重、替补门槛 | `quality.py` 的 `score_paper`、`selector.py` 的 `REPLACE_MARGIN` |
| 每周篇数 / 抓取窗口 | 环境变量 `MAX_PAPERS` / `DAYS_BACK` |

---

## 快速开始

### 1. Fork 这个仓库

Fork 到你自己的 GitHub 账号下即可（公开 / 私有都行）。

### 2. 选一种飞书通道

两种都支持，配好任意一种就能用。**推荐 A（自建应用）**——它不依赖群设置里的「自定义机器人」入口，个人版也能用；部分企业租户会把那个入口藏起来。

#### 通道 A：自建应用机器人（推荐）

1. 打开 [飞书开放平台](https://open.feishu.cn/app)，**创建企业自建应用**（个人版也可以用）。
2. 「添加应用能力」→ 添加**机器人**。
3. 「权限管理」→ 开通 `im:message:send_as_bot`（以应用身份发消息）。
4. 「版本管理与发布」→ 创建版本并发布。
5. 在「凭证与基础信息」拿到 **App ID** 和 **App Secret**。
6. 建一个群，把机器人拉进去（群设置 → 群机器人 → 添加机器人），或者直接私聊机器人。

#### 通道 B：群自定义机器人（webhook）

1. 群设置 → **群机器人** → **添加机器人** → **自定义机器人**。
2. 复制 **Webhook 地址**，形如 `https://open.feishu.cn/open-apis/bot/v2/hook/xxxx`。
3. 安全设置二选一：**签名校验**（密钥填 `FEISHU_WEBHOOK_SECRET`）或**自定义关键词**填「论文」。
4. ⚠️ **不要开 IP 白名单**，GitHub Actions 的出口 IP 不固定。

> 如果群设置里找不到「自定义机器人」，说明这个租户没开放，改用通道 A。

### 3. 配置 Secrets

仓库页面：**Settings → Secrets and variables → Actions**

| 名称 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `DEEPSEEK_API_KEY` | Secret | 是 | DeepSeek API Key，[platform.deepseek.com](https://platform.deepseek.com) |
| `FEISHU_APP_ID` | Secret | 通道 A | 自建应用 App ID |
| `FEISHU_APP_SECRET` | Secret | 通道 A | 自建应用 App Secret |
| `FEISHU_RECEIVE_ID` | Secret | 通道 A | 收件人：群 `chat_id`（`oc_...`）或你的飞书邮箱 |
| `FEISHU_WEBHOOK` | Secret | 通道 B | 群机器人 webhook 地址 |
| `FEISHU_WEBHOOK_SECRET` | Secret | 可选 | 群机器人「签名校验」密钥 |
| `FEISHU_RECEIVE_ID_TYPE` | Variable | 可选 | `chat_id` / `email` / `open_id`，默认 `email` |
| `FEISHU_CHANNEL` | Variable | 可选 | 强制走 `app` 或 `webhook` |
| `SEMANTIC_SCHOLAR_API_KEY` | Secret | 可选 | 有就填，引用数查询更稳 |

`chat_id` 的拿法：用 [lark-cli](https://github.com/larksuite/cli) 跑
`lark-cli im +chat-search --query 群名`，或在群里 @机器人 后看日志里的 chat_id。

两个通道都配了的话默认走自建应用；想强制指定就设 `FEISHU_CHANNEL`。

> 从微信版迁移过来：飞书配好后可以把 `SERVERCHAN_SENDKEY` 这个 Secret 删掉，代码里已经没有微信推送了。

### 4. 开启 Actions 写权限

**Settings → Actions → General → Workflow permissions** → 选 **Read and write permissions**（要提交 `papers/` 和 `data/seen_ids.json`）。

### 5. 验证

**Actions → Weekly Paper Digest → Run workflow**，把 `dry_run` 勾上先跑一次（不推送），确认抓取、打分和翻译正常；再手动跑一次正式的。

不想等 Actions，也可以在本地直接发一张测试卡片：

```bash
export FEISHU_APP_ID=cli_xxx
export FEISHU_APP_SECRET=xxx
export FEISHU_RECEIVE_ID=oc_xxx
export FEISHU_RECEIVE_ID_TYPE=chat_id
python main.py --test-push
```

---

## 本地调试

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q            # 单元测试，不需要任何密钥

# 完整跑一遍但不推送、不写文件，会打印归档内容和卡片 JSON
DEEPSEEK_API_KEY=sk-xxx python main.py --dry-run
```

常用参数：

| 参数 | 作用 |
|------|------|
| `--dry-run` | 不推送、不写文件、不更新去重记录 |
| `--test-push` | 只发一张测试卡片，验证飞书配置 |
| `--max-papers N` | 本次推送 N 篇（默认 6） |
| `--no-translate` | 跳过翻译，直接用英文原文 |

---

## 定时与手动触发

- 定时：每周一 **09:00 北京时间**（`cron: '0 1 * * 1'`）。GitHub 的定时任务有几分钟到十几分钟延迟，属正常。
- 手动：Actions 页面 `Run workflow`，可选 `dry_run` 和 `max_papers`。
- 本期没有新论文时，会推一张「本周无新论文」的灰色卡片，方便确认任务还活着。

## 费用

每次 6 篇翻译 + 约 75 篇打分，DeepSeek 单次约 ¥0.1；arXiv 与 Semantic Scholar 免费。

---

## 项目结构

```
├── .github/workflows/weekly.yml   # 定时任务：测试 → 抓取 → 推送 → 提交归档
├── main.py                        # 主入口（命令行参数见上）
├── config.py                      # 时区、路径、篇数、抓取窗口等配置
├── arxiv_fetcher.py               # 话题定义（查询式/关键词/配额/替补）+ arXiv 抓取
├── quality.py                     # 质量信号 + 读者画像 + LLM 打分
├── ids.py                         # arXiv id 与标题规范化（去重口径）
├── selector.py                    # 按配额轮转 + 图形学替补
├── semantic_fetcher.py            # Semantic Scholar 批量查引用数
├── translator.py                  # DeepSeek 中文翻译
├── digest.py                      # 归档 Markdown / 卡片文案渲染
├── feishu.py                      # 飞书卡片构建 + webhook / 自建应用发送
├── paper_saver.py                 # 写入 papers/、latest.md 和归档索引
├── store.py                       # seen_ids（带日期、自动过期清理）
├── papers/README.md               # 每周归档索引（自动生成）
├── data/seen_ids.json             # 已推送论文记录（自动更新）
└── tests/                         # 单元测试（pytest）
```

---

## 下一步（还没做）

现在的卡片是"翻译 + 摘要"，但**读懂一篇论文**通常还缺三样东西：

1. **人话版导读**：一句话结论、为什么值得读、用类比讲清方法、关键数字、3 个术语、2 个自测问题。
2. **中文阅读页**：点标题不要直接跳到英文 arXiv，而是先看一页中文精读，再决定要不要读原文。
3. **针对论文提问**：比如"这个方法和我做的项目有什么关系"、"第三段的假设是什么"。

计划按这个顺序做，每步都能单独用。

---

## 常见问题

**卡片没收到？**

- 自建应用：确认应用已发布、开通了 `im:message:send_as_bot`，机器人是群成员，`FEISHU_RECEIVE_ID` 是群 `chat_id`（`oc_...`）或你的飞书邮箱。
- 群机器人：确认 webhook 没被删、没开 IP 白名单、关键词里含「论文」；签名密钥填错会返回 `19021`。
- Actions 日志里搜 `[feishu]`，错误码含义见 `feishu.py` 里的 `ERROR_HINTS`。

**引用数都是 0？** 正常。新提交的论文还没被 Semantic Scholar 收录，排序以相关度和 LLM 打分为主，引用只作辅助。

**图形学怎么好久没出现了？** 它是替补：只有分数明显高于第 6 篇时才会顶掉一篇，最多 1 篇。

**翻译失败了？** 不影响推送，会自动回退成英文原文；检查 `DEEPSEEK_API_KEY` 是否有效。没有这个 key 时打分和翻译都会跳过。

**想多推几篇？** 手动触发时填 `max_papers`，或改仓库变量 `MAX_PAPERS`。

**历史归档在哪？** [papers/README.md](papers/README.md) 有完整索引，`papers/latest.md` 永远是最新一期。
