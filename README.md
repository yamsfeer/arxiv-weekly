# arxiv-weekly

每周一 09:00（北京时间）自动从 arXiv 抓取论文，用 DeepSeek 翻译成中文，以**飞书交互式卡片**推送到手机。

卡片里能直接读中文标题、中文摘要和原文链接，聊天记录长期保留、可搜索；每期还会在 `papers/` 里留一份 Markdown 归档，卡片底部有按钮直达，不依赖任何第三方推送工具。

**关注话题（每周共 10 篇，按配额分配）：**

| 话题 | 每期篇数 | 范围 |
|------|---------|------|
| Web 前后端开发 | 3 | WebAssembly、WebGPU、浏览器、前后端框架、微服务、REST API |
| 计算机图形学与游戏 | 3 | cs.GR：渲染、动画、几何、游戏 |
| AI 辅助软件开发 | 2 | 代码生成、代码补全、程序合成、自动调试 |
| AI 应用开发 | 2 | Agent、RAG、工具调用、Context Engineering |

> 配额可以用环境变量 `MAX_PAPERS` 和 `arxiv_fetcher.py` 里的 `quota` 调整。

---

## 快速开始

### 1. Fork 这个仓库

Fork 到你自己的 GitHub 账号下即可（公开 / 私有都行）。

### 2. 选一种飞书通道

两种都支持，配好任意一种就能用。**推荐 A（群机器人）**，3 分钟搞定，不需要企业管理员。

#### 通道 A：群自定义机器人（推荐）

1. 在飞书里建一个群，把想收周报的人拉进来（只有自己也行）。
2. 群设置 → **群机器人** → **添加机器人** → **自定义机器人**，起个名字，比如「论文周报」。
3. 复制生成的 **Webhook 地址**，形如 `https://open.feishu.cn/open-apis/bot/v2/hook/xxxx`。
4. 安全设置二选一：
   - **签名校验**（推荐）：勾上后复制密钥，填到仓库 Secret `FEISHU_WEBHOOK_SECRET`；
   - **自定义关键词**：填 `论文`（卡片标题里带这两个字）。
   - ⚠️ **不要开 IP 白名单**，GitHub Actions 的出口 IP 不固定，开了会一直收不到。

#### 通道 B：自建应用私聊（发给你个人）

1. 打开 [飞书开放平台](https://open.feishu.cn/app)，**创建企业自建应用**。
2. 「添加应用能力」→ 添加**机器人**。
3. 「权限管理」→ 开通 `im:message:send_as_bot`（以应用身份发消息）。
4. 「版本管理与发布」→ 创建版本并发布（自己是管理员就直接通过）。
5. 在「凭证与基础信息」拿到 **App ID** 和 **App Secret**。

### 3. 配置 Secrets

仓库页面：**Settings → Secrets and variables → Actions → New repository secret**

| Secret | 必填 | 说明 |
|--------|------|------|
| `DEEPSEEK_API_KEY` | 是 | DeepSeek API Key，[platform.deepseek.com](https://platform.deepseek.com) |
| `FEISHU_WEBHOOK` | 通道 A | 群机器人 webhook 地址 |
| `FEISHU_WEBHOOK_SECRET` | 可选 | 群机器人「签名校验」的密钥 |
| `FEISHU_APP_ID` | 通道 B | 自建应用 App ID |
| `FEISHU_APP_SECRET` | 通道 B | 自建应用 App Secret |
| `FEISHU_RECEIVE_ID` | 通道 B | 收件人，填你的飞书**邮箱**（默认按 email 解析） |
| `FEISHU_RECEIVE_ID_TYPE` | 可选 | `email` / `open_id` / `user_id`，默认 `email` |
| `SEMANTIC_SCHOLAR_API_KEY` | 可选 | 有就填，引用数查询更稳；不填也不影响推送 |

两个通道都配了的话，默认走自建应用；想强制指定就加环境变量 `FEISHU_CHANNEL=webhook` 或 `app`。

> 从微信版迁移过来：飞书配好后可以把 `SERVERCHAN_SENDKEY` 这个 Secret 删掉，代码里已经没有微信推送了。

### 4. 开启 Actions 写权限

**Settings → Actions → General → Workflow permissions** → 选 **Read and write permissions**（要提交 `papers/` 和 `data/seen_ids.json`）。

### 5. 验证

**Actions → Weekly Paper Digest → Run workflow**，把 `dry_run` 勾上先跑一次（不推送），确认抓取和翻译正常；再手动跑一次正式的。

不想等 Actions，也可以在本地直接发一张测试卡片：

```bash
export FEISHU_WEBHOOK="https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
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
| `--max-papers N` | 本次推送 N 篇（默认 10） |
| `--no-translate` | 跳过翻译，直接用英文原文 |

---

## 定时与手动触发

- 定时：每周一 **09:00 北京时间**（`cron: '0 1 * * 1'`）。GitHub 的定时任务有几分钟到十几分钟延迟，属正常。
- 手动：Actions 页面 `Run workflow`，可选 `dry_run` 和 `max_papers`。
- 本期没有新论文时，会推一张「本周无新论文」的灰色卡片，方便确认任务还活着。

## 费用

每次翻译 10 篇论文，DeepSeek 单次约 ¥0.01；arXiv 与 Semantic Scholar 免费。

---

## 项目结构

```
├── .github/workflows/weekly.yml   # 定时任务：测试 → 抓取 → 推送 → 提交归档
├── main.py                        # 主入口（命令行参数见上）
├── config.py                      # 时区、路径、篇数、抓取窗口等配置
├── arxiv_fetcher.py               # 话题定义（查询式/关键词/配额）+ arXiv 抓取
├── ids.py                         # arXiv id 与标题规范化（去重口径）
├── selector.py                    # 按话题配额挑选、排序
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

- 群机器人：确认 webhook 没被删、没开 IP 白名单、关键词里含「论文」；签名密钥填错会返回 `19021`。
- 自建应用：确认应用已发布、开通了 `im:message:send_as_bot`，且 `FEISHU_RECEIVE_ID` 是你在该企业下的邮箱。
- Actions 日志里搜 `[feishu]`，错误码含义见 `feishu.py` 里的 `ERROR_HINTS`。

**引用数都是 0？** 正常。本周新提交的论文还没被 Semantic Scholar 收录，挑选时以话题相关度为主，引用数只作辅助。

**翻译失败了？** 不影响推送，会自动回退成英文原文；检查 `DEEPSEEK_API_KEY` 是否有效。

**想多推几篇？** 手动触发时填 `max_papers`，或改仓库变量 `MAX_PAPERS`。配额总和固定时，多出来的名额按分数跨话题补满。

**历史归档在哪？** [papers/README.md](papers/README.md) 有完整索引，`papers/latest.md` 永远是最新一期。
