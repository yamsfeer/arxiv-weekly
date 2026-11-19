# 📚 每周论文精选 · 2026年11月19日

> 共 6 篇 · AI 编码 / 编程代理 2 · LLM 应用工程 2 · Web 全栈 / 前端工程 1 · 开发者工具 / 测试 / 工程效率 1

## 1. 面向编码智能体的免评估递归自我改进

**[Evaluation-Free Recursive Self-Improvement for Coding Agents](https://arxiv.org/abs/2611.21056)**

AI 编码 / 编程代理 · 2026-11-16 · 📊 被引 1 次 · cs.CL / cs.NE

提出 ELITE：演化中不评估下游任务，而是每代提出多样改进、自同一父代独立实现，检视互补、冗余与冲突机制后整合为一致后代，仅做结构与运行有效性检查。SWE-bench Pro 由 60.0% 升至 85.6%（DGM 86.7%、HGM 88.3%），零候选评估，演化耗时降 8.8×/3.2×；跨基准迁移达 73.3%（Verified）、69.3%（Polyglot）。

💡 免下游评测的自改进智能体，可落地且指标扎实可复现

✍️ Zhe Ren、Guowei Rong、Yimeng Chen

[arXiv:2611.21056](https://arxiv.org/abs/2611.21056) · [PDF](https://arxiv.org/pdf/2611.21056)

---

## 2. 利用超时级联降低编码智能体的推理成本

**[Reducing Inference Cost of Coding Agents with Timeout Cascades](https://arxiv.org/abs/2611.24324)**

AI 编码 / 编程代理 · 2026-11-18 · 🆕 新论文 · cs.AI / cs.SE

在软件工程基准上评测 36 个 2024 年以来的开源权重模型，发现小型模型与大型模型的准确率差距主要集中于难题。据此提出先试小模型、必要时升级大模型的混合推理（超时级联），在 SWE-bench Verified 上最多降低 33% GPU 小时成本、全部任务降低 16.4%，且不损准确率，效果接近 oracle 式任务路由器。

💡 小模型先跑超时升级，省33%算力，工程直接可用

✍️ Boxi Zhou、German Sviridov、Dmitrii Ustiugov

[arXiv:2611.24324](https://arxiv.org/abs/2611.24324) · [PDF](https://arxiv.org/pdf/2611.24324)

---

## 3. 随处快思：为任意智能体工作流的决策点提供统一 System-1

**[Thinking Fast, Anywhere: One System-1 for the Decision Points of Any Agent Workflow](https://arxiv.org/abs/2611.23751)**

LLM 应用工程 · 2026-11-18 · 🆕 新论文 · cs.AI / cs.CL / cs.LG

提出 AnyS1，将人工编写的流程技能转化为跨领域通用的决策点来源；离线挖掘 1000 余项公开技能中的可枚举决策，在隔离容器采集执行轨迹构建 Any-DP，训练单个 4B 指针式 System-1。运行时常规决策一次前向完成，置信度低则回退 System-2。在三个未见基准上保持任务可靠性，单回合成本降 75–91%，模型调用时间降 63–92%，并支持零样本阈值迁移。

💡 单次前向替代System-2决策，降本75-91%，agent落地直接可用

✍️ Rui Li、Liyang He、Zheng Zhang

[arXiv:2611.23751](https://arxiv.org/abs/2611.23751) · [PDF](https://arxiv.org/pdf/2611.23751)

---

## 4. 量化在遗留软件系统中改造引入检索增强生成的侵入性

**[Quantifying the Intrusiveness of Retrofitting Retrieval-Augmented Generation onto Legacy Software Systems](https://arxiv.org/abs/2611.23931)**

LLM 应用工程 · 2026-11-18 · 🆕 新论文 · cs.SE

提出三种改造模式（sidecar、SDK 嵌入、朴素侵入式）分类及遗留侵入度评分 LIS/LIS-X，在五个遗留系统上静态评估，并将三种模式作为独立进程实测。代码层面 sidecar < SDK 嵌入 < 朴素侵入式在五系统与 2000 种随机权重下均成立。实测 sidecar 无可检测延迟（0.07 ms），另两种增加 569 与 475 ms 且无差异；二者均传导依赖延迟，并在 RAG 快速失败时返回缺少 AI 字段的成功响应。

💡 RAG接入遗留系统的侵入度量化，有代码与实测，工程可用

✍️ K. M. Tahlil Mahfuz Faruk、Rakib Abdullah

[arXiv:2611.23931](https://arxiv.org/abs/2611.23931) · [PDF](https://arxiv.org/pdf/2611.23931)

---

## 5. 当《人月神话》遇上智能体 Web 系统：面向可扩展开发的结构化协调

**[When the Mythical Man-Month Meets Agentic Web Systems: Structured Coordination for Scalable Development](https://arxiv.org/abs/2611.19140)**

Web 全栈 / 前端工程 · 2026-11-14 · 🆕 新论文 · cs.SE / cs.AI

研究协作智能体系统中智能体数量、单智能体 token 消耗与协调开销的关系，在复杂 Web 软件开发任务上发现非线性缩放：随智能体增多，单智能体 token 消耗先降后趋于饱和。据此提出外科手术团队模型（STM），通过角色专门化、受限的智能体间通信与协调者中介的任务聚合组织智能体。全栈 Web 开发实验显示，STM 的任务完成质量与 token 消耗与代表性基线相当，但执行延迟更高。

💡 多agent协作规模效应与结构化分工，Web开发场景贴切

✍️ Zhiyao Wu、Zi Liang、Haibo Hu

[arXiv:2611.19140](https://arxiv.org/abs/2611.19140) · [PDF](https://arxiv.org/pdf/2611.19140)

---

## 6. CR-Bench-v2：评估 AI 代码审查智能体的实际效用

**[CR-Bench-v2: Evaluating the Real-World Utility of AI Code Review Agents](https://arxiv.org/abs/2611.02566)**

开发者工具 / 测试 / 工程效率 · 2026-11-02 · 🆕 新论文 · cs.SE / cs.LG

自动代码生成亟需自动审查，但审查依赖 diff 外上下文与设计判断，难以完全自动化。现有基准依赖噪声评论和文本相似度，缺乏标准化。我们提出 CR-Bench，将 SWE-Bench 问题重构为带完整仓库上下文的 PR 审查任务，含 584 个实例及 174 个 Verified 子集，每个实例配已知缺陷、修复和分类标签；提出已知缺陷检出率（KDDR）与有用率。评估八个智能体及 Gemini Code Assist，最强系统 KDDR 仅约 33%，后者为 8.1%。

💡 缺陷导向的代码评审基准，指标明确可直接用于 agent 评测

✍️ Kristen Pereira、Neelabh Sinha、Rajat Ghosh

[arXiv:2611.02566](https://arxiv.org/abs/2611.02566) · [PDF](https://arxiv.org/pdf/2611.02566)

---

*由 GitHub Actions + DeepSeek 自动生成 · 数据来源 arXiv & Semantic Scholar*
