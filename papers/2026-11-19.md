# 📚 每周论文精选 · 2026年11月19日

> 共 6 篇 · AI 编码 / 编程代理 2 · LLM 应用工程 2 · Web 全栈 / 前端工程 1 · 开发者工具 / 测试 / 工程效率 1

## 1. 从代码仓库到训练环境：以环境演化循环扩展长程编程智能体

**[From Repositories to Training Environments: Scaling Long-Horizon Coding Agents with Environment Evolution Loop](https://arxiv.org/abs/2611.21152)**

AI 编码 / 编程代理 · 2026-11-16 · 🆕 新论文 · cs.CL

提出 RepoFactory 自动化流水线，将真实代码库转为可验证环境，使智能体依据语言规范从零构建完整项目；其环境演化循环利用代理反馈优化有效性、结构耦合与实现范围。在17个软件领域生成10,159个环境。训练 Qwen3.5-35B-A3B 得 RepoHorizen-35B-A3B，在 NL2Repo-Bench 提升22.6个百分点，五项基准平均提升8.5个百分点，显著优于未演化环境。

💡 万级可验证仓库环境合成，训练编码agent，工程可复现

✍️ Yang Tian、Tianyu Zheng、Xiyuan Yang

[arXiv:2611.21152](https://arxiv.org/abs/2611.21152) · [PDF](https://arxiv.org/pdf/2611.21152)

---

## 2. 上下文是有代价的：前缀缓存下编程智能体的上下文增删

**[Context Has a Price: Adding and Removing Context for LLM Coding Agents under Prefix Caching](https://arxiv.org/abs/2611.22238)**

AI 编码 / 编程代理 · 2026-11-17 · 🆕 新论文 · cs.AI

在超过2万次开源模型于 SWE-bench 等基准的运行中，分别计量未缓存输入、缓存输入与输出 token。加入检索代码可减少18–34%读取与搜索命令，却使成本增加33–42%；删除旧观察在无缓存折扣时节省19–36%，在一折缓存时反增38–116%；更短提示不必然更省，因智能体可能增加步骤；并发实验共享缓存前缀还会扭曲成本比较。

💡 前缀缓存下上下文增删的真实成本测度，反直觉且有用

✍️ Zerui Yang、Miaomiao Dong、Quan Xue

[arXiv:2611.22238](https://arxiv.org/abs/2611.22238) · [PDF](https://arxiv.org/pdf/2611.22238)

---

## 3. ARISE：面向精准且低成本企业智能体的实用自演化记忆

**[ARISE: Practical Self-Evolving Memory for Accurate and Cost-Efficient Enterprise Agents](https://arxiv.org/abs/2611.23588)**

LLM 应用工程 · 2026-11-17 · 🆕 新论文 · cs.AI / cs.MA

ARISE 使企业智能体无需更新模型权重、工具或流程逻辑，即可从失败中演化记忆：由模型或教师模型归因失败、提出修正，保存为可检索的微观记忆并整合为宏观规则，仅在留出集准确率提升时接受更新。在14个企业流程领域、5个模型上，ARISE-Teacher 较基线在 SOP-Bench 和 τ²-bench 分别提升10.9和5.8个百分点，优于 GEPA；ARISE-Self 在 SOP-Bench 提升10.0个百分点，且调用与输出 token 更少。

💡 失败驱动的agent记忆自演化，免改权重，实验扎实可落地

✍️ Jiangyun Zhang、Zhou Tang、Kristen Surrao

[arXiv:2611.23588](https://arxiv.org/abs/2611.23588) · [PDF](https://arxiv.org/pdf/2611.23588)

---

## 4. 智能体框架工程 Beta：以需求为中心的智能体框架演化

**[Agentic Harness Engineering Beta: Requirement-Centered Evolution of Agent Harnesses](https://arxiv.org/abs/2611.24924)**

LLM 应用工程 · 2026-11-18 · 🆕 新论文 · cs.SE / cs.AI

现有智能体框架演化常忽视隐性需求，依赖单一演化智能体与基准分数，易产生狭窄补丁和局部最优。AHE-Beta 引入以需求为中心的闭环：模拟用户以问题形式提出需求，团队式修改形成可泛化变更，仅在解决已验证需求并通过评审时合并。留出任务上 pass@1 由21.9%升至33.3%，token 减少40.8%，优于 Claude Code、Meta-Harness 和 AHE；盲测48组中31组偏好 AHE-Beta，五项维度评分均更高，增益可迁移至其他模型。

💡 以需求驱动的harness演化，pass@1显著提升且有人类A/B，直接可借鉴

✍️ Jiahang Lin、Jiahao Chen、Yiding Wang

[arXiv:2611.24924](https://arxiv.org/abs/2611.24924) · [PDF](https://arxiv.org/pdf/2611.24924)

---

## 5. Injectra：为基于 Web 的桌面应用改造可扩展性

**[Injectra: Retrofitting Extensibility into Web-Based Desktop Applications](https://arxiv.org/abs/2611.20713)**

Web 全栈 / 前端工程 · 2026-11-16 · 🆕 新论文 · cs.SE / cs.HC

提出 Injectra，一种面向现有桌面客户端的通用代码注入与功能增强系统，适用于 Electron 内嵌浏览器或 Tauri 系统 WebView 构建界面的应用。系统解耦宿主集成与增强代码，结合运行时集成与启动前引导，通过统一通道注入 JavaScript、HTML 和 CSS，以修改界面渲染、交互行为并扩展客户端功能，并提供 CLI 供外部工具、AI 智能体与 MCP 复用。已在38款 macOS 应用上全部注入成功，并验证 Windows 版本；基于选择标注的 LLM 工具可生成并注入增强代码。

💡 Electron/WebView应用JS注入扩展，CLI+MCP可复用

✍️ Qin Sun

[arXiv:2611.20713](https://arxiv.org/abs/2611.20713) · [PDF](https://arxiv.org/pdf/2611.20713)

---

## 6. 少提示，多推断：静态分析引导的 Python 大语言模型类型标注

**[Prompt Less, Infer More: Static Analysis-Guided LLM Type Annotation for Python](https://arxiv.org/abs/2610.41617)**

开发者工具 / 测试 / 工程效率 · 2026-10-30 · 🆕 新论文 · cs.SE

类型标注可提升 Python 程序的可维护性与可靠性，但人工标注耗时易错，实际项目普遍标注不足。现有 LLM 类型推断常在准确率与效率间取舍，未充分利用项目级类型证据。我们提出 SALT，由静态分析引导 LLM：静态解析类型、确定查询优先级并构建简洁的类型感知上下文。在 12 个真实项目上，SALT 准确率最优，LLM 成本较强基线降低达 78.5%，且在 GPT-5.5 上同样有效。

💡 静态分析引导LLM补类型标注，降本78%，AI编程工具可直接用

✍️ Wonseok Oh、Michael Pradel、Hakjoo Oh

[arXiv:2610.41617](https://arxiv.org/abs/2610.41617) · [PDF](https://arxiv.org/pdf/2610.41617)

---

*由 GitHub Actions + DeepSeek 自动生成 · 数据来源 arXiv & Semantic Scholar*
