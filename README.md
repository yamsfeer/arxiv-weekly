# arxiv-weekly

每周一自动从 arxiv 抓取论文，用 DeepSeek 翻译成中文，发送邮件摘要。

**关注话题：**
- Web 前后端开发（WebAssembly、WebGPU、微服务等）
- 计算机图形学与游戏（cs.GR）
- AI 辅助软件开发（代码生成、编程助手）
- AI 应用开发（Agent、RAG、工具调用）

---

## 部署步骤

### 1. Fork / 创建仓库

把本项目推送到你自己的 GitHub 仓库。

### 2. 配置 Secrets

在 GitHub 仓库页面：**Settings → Secrets and variables → Actions → New repository secret**

| Secret 名称 | 说明 |
|-------------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API Key，从 [platform.deepseek.com](https://platform.deepseek.com) 获取 |
| `SERVERCHAN_SENDKEY` | Server酱 SendKey，从 [sct.ftqq.com](https://sct.ftqq.com) 微信扫码登录后获取 |

### 3. 开启 Actions 写权限

**Settings → Actions → General → Workflow permissions** → 选 **Read and write permissions**

### 4. 测试运行

**Actions → Weekly Paper Digest → Run workflow** 手动触发一次，查看是否正常收到邮件。

---

## 自动运行时间

每周一 **09:00（北京时间）** 自动运行。

---

## 费用估算

每次运行约翻译 10 篇论文，使用 DeepSeek Chat 模型，**单次费用约 ¥0.01**。

---

## 项目结构

```
├── .github/workflows/weekly.yml   # GitHub Actions 定时任务
├── data/seen_ids.json             # 已推送论文 ID（自动更新，避免重复）
├── main.py                        # 主入口
├── arxiv_fetcher.py               # arxiv API 抓取
├── semantic_fetcher.py            # Semantic Scholar 引用数查询
├── translator.py                  # DeepSeek 中文翻译
├── email_sender.py                # QQ 邮箱发送
└── requirements.txt
```
