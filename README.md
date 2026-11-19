# arxiv-weekly

每周一 09:00（北京时间）自动从 arXiv 抓取论文，用 DeepSeek 打分、翻译，以**飞书交互式卡片**推送到手机。

卡片里能直接读中文标题、中文摘要和原文链接，聊天记录长期保留、可搜索；每期还会在 `papers/` 里留一份 Markdown 归档，卡片底部有按钮直达，不依赖任何第三方推送工具。

**关注方向（每周 6 篇）：**

| 方向 | 每期篇数 | 范围 |
|------|---------|------|
| AI 编码 / 编程代理 | 2 | coding agent、repo 级代码生成、程序修复、SWE-bench |
| LLM 应用工程 | 2 | RAG、tool use、context engineering、agent 评测 |
| Web 全栈 / 前端工程 | 1 | WebAssembly、WebGPU、浏览器、前后端框架、微服务 |
| 开发者工具 / 测试 / 工程效率 | 1 | IDE、code review、测试生成、静态分析、CI |
| 计算机图形学与游戏 | 0–1 | cs.GR；**只在分数明显更高时才替补进来**，最多 1 篇 |

> 配额和查询式都在 `arxiv_fetcher.py` 里，篇数可以用环境变量 `MAX_PAPERS` 调。

---

## 选题逻辑（为什么不是"最新 10 篇"）

1. **21 天窗口**：新论文不等于好论文。给论文三周机会，既追新方向，又不被"今天刚提交"绑架。
2. **质量信号**：arXiv `comment` 里的 `accepted at / to appear in …` 强加分；摘要里有代码链接加分；引用数按发表月数归一化。
3. **LLM 打分**：每个方向先按关键词+引用取前 15 篇，把标题、摘要和一段「读者画像」交给 DeepSeek，评**相关性**和**扎实度**（换数据集、微小增量、纯综述会压分）。读者画像在 `quality.py` 的 `INTEREST_PROFILE`，改口味只改这一段。
4. **时间只做轻加分**：0–7 天 +3、8–14 天 +2、15–21 天 +1，新的有优势但不垄断。
5. **只有推送过的才算已读**：没选中的论文下周还能再竞争一次，好论文不会因为撞上更强的一周被埋掉。

---

## 快速开始

### 1. Fork 这个仓库

Fork 到你自己的 GitHub 账号下即可（公开 / 私有都行）。

### 2. 选一种飞书通道

两种都支持，配好任意一种就能用。**推荐 A（自建应用）**——它不依赖群设置里的「自定义机器人」入口，个人版也能用；部分企业租户会把那个入口藏起来。

#### 通道 A：自建应用机器人（推荐）

1. 打开 [飞书开放平台](https://open.feishu.cn/app)，**创建企业自建应用**（个人版也可以）。
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
`lark-cli im +chat-search --query 群名`，或在群里 @机器人 后用日志里的 chat_id。

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

每次 6 篇翻译 + 约 60 篇打分，DeepSeek 单次约 ¥0.1；arXiv 与 Semantic Scholar 免费。

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

## 常见问题

**卡片没收到？**

- 自建应用：确认应用已发布、开通了 `im:message:send_as_bot`，机器人是群成员，`FEISHU_RECEIVE_ID` 是群 `chat_id`（`oc_...`）或你的飞书邮箱。
- 群机器人：确认 webhook 没被删、没开 IP 白名单、关键词里含「论文」；签名密钥填错会返回 `19021`。
- Actions 日志里搜 `[feishu]`，错误码含义见 `feishu.py` 里的 `ERROR_HINTS`。

**引用数都是 0？** 正常。本周新提交的论文还没被 Semantic Scholar 收录，排序以相关度和 LLM 打分为主，引用只作辅助。

**图形学怎么好久没出现了？** 它是替补：只有分数明显高于第 6 篇时才会顶掉一篇，最多 1 篇。

**翻译失败了？** 不影响推送，会自动回退成英文原文；检查 `DEEPSEEK_API_KEY` 是否有效。没有这个 key 时打分和翻译都会跳过。

**想多推几篇？** 手动触发时填 `max_papers`，或改仓库变量 `MAX_PAPERS`。

**历史归档在哪？** [papers/README.md](papers/README.md) 有完整索引，`papers/latest.md` 永远是最新一期。
