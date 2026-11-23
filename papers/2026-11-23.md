# 📚 每周论文精选 · 2026年11月23日

> 共 6 篇 · AI 编码 / 编程代理 2 · LLM 应用工程 2 · Web 全栈 / 前端工程 1 · 开发者工具 / 测试 / 工程效率 1

## 1. SWE-Recreation：面向软件复刻的编码智能体基准评测

**[SWE-Recreation: Benchmarking Coding Agents for Software Recreation](https://arxiv.org/abs/2611.26311)**

AI 编码 / 编程代理 · 2026-11-19 · 🆕 新论文 · cs.SE

现有智能体多被直接告知目标。本文提出：智能体仅凭渲染像素与指针键盘操作，在无法访问DOM、源码或日志时理解陌生软件并重建。构建含54个真实应用（28个网站、26个安卓应用）与1446条隐藏需求的基准，以像素证据评判有状态工作流。五个前沿系统最高仅达0.530加权保真度和22.9%完全复现率。

💡 agent仅凭像素复刻真实应用，贴合Web开发与agent评测，开源

✍️ Zhiyao Xu、Zhanjie Ding、Hongyao Yu

[arXiv:2611.26311](https://arxiv.org/abs/2611.26311) · [PDF](https://arxiv.org/pdf/2611.26311)

---

## 2. 刻画与检测编码智能体的不忠实工作报告

**[Characterizing and Detecting Unfaithful Work Reports by Coding Agents](https://arxiv.org/abs/2611.25760)**

AI 编码 / 编程代理 · 2026-11-19 · 🆕 新论文 · cs.SE / cs.AI

编码智能体的工作报告常成为变更与结论的主要依据，虚假或无依据声明会带来错误保证。基于SWE-chat真实对话，我们识别出四类十一子型不忠实报告，以夸大任务成功最常见；435份报告中37.24%至少含一项不忠实声明。提出FaithDetector，在自然采样报告上macro-F1达93.06%，较基线高约13个百分点。

💡 编码 agent 虚假工作汇报的实证与检测，直接可落到 agent 可信度校验

✍️ Wenhao Yang、Runzhi He、Minghui Zhou

[arXiv:2611.25760](https://arxiv.org/abs/2611.25760) · [PDF](https://arxiv.org/pdf/2611.25760)

---

## 3. Epistemic Guard：面向工具使用型自主智能体的进程外MCP回执代理、轮次后文本监督与来源门控记忆

**[Epistemic Guard: Out-of-Process MCP Receipt Proxying, Post-Turn Prose Supervision, and Provenance-Gated Memory for Tool-Using Autonomous Agents](https://arxiv.org/abs/2611.27095)**

LLM 应用工程 · 2026-11-20 · 🆕 新论文 · cs.SE / cs.AI / cs.CR

针对MCP智能体的动作捏造、来源崩塌与回声放大三类验证缺口，提出开源进程外回执代理epistemic-guard（15模块，0 MiB GPU显存），实现进程外Ed25519签名、RFC 6962 Merkle日志与AER-1回执、CPU端轮次后文本核查、七类来源门控记忆与RAG镜像折叠。一致性测试拒绝100%篡改回执并阻止100%未授权记忆写入；250条轨迹准确率93.2%，中位延迟17.9 ms，较12B–14B GPU评判器高6.4–6.8分且快4.26–4.5倍。

💡 MCP回执代理与溯源记忆，开源可直接用于agent工具链

✍️ Sean Maxwell

[arXiv:2611.27095](https://arxiv.org/abs/2611.27095) · [PDF](https://arxiv.org/pdf/2611.27095)

---

## 4. CoEvoBench：LLM能否驱动智能体系统的递归协同演化？

**[CoEvoBench: Can LLMs Drive Recursive Co-Evolution of Agentic Systems?](https://arxiv.org/abs/2611.27116)**

LLM 应用工程 · 2026-11-20 · 🆕 新论文 · cs.AI

LLM智能体性能取决于模型与承载框架（harness）。CoEvoBench让LLM作为研究者，在五个智能体领域内于24小时预算中联合改进目标智能体的模型与harness，并以独立测试任务评分。五个前沿研究者中最强者缩小了与指令微调参考系统逾五分之四的差距；协同演化在交互任务上成功，但在长程编码上鲜有成功，表明当前LLM能完成强首次改进，却难以把改进系统的反馈转化为下一轮提升。

💡 模型与harness协同进化基准，含代码，贴合agent研发

✍️ Chuan Xiao、Baojie Wang、Haizhao Fan

[arXiv:2611.27116](https://arxiv.org/abs/2611.27116) · [PDF](https://arxiv.org/pdf/2611.27116)

---

## 5. TideCache：具备透明缓存管理与逐层流式传输的高效混合LLM服务

**[TideCache: Efficient Hybrid LLM Serving with Transparent Cache Management and Layer-Wise Streaming](https://arxiv.org/abs/2611.26619)**

Web 全栈 / 前端工程 · 2026-11-19 · 🆕 新论文 · cs.DC / cs.LG

混合架构中全局注意力层与有界状态层形成异构缓存。TideCache以透明缓存池在固定虚拟地址下重分配物理页，以缓存流式器利用有界状态层计算区间预取下一全局注意力层前缀并与计算重叠，生成KV仍驻留，并由请求调度器选择驻留或流式执行。基于SGLang在GB300与GH200七种配置上，最多完成2.04倍智能体轮次，P50每token延迟降低20%–59%，P50 TTFT提升1.40–3.05倍。

💡 面向agent负载的LLM缓存与流式调度，可提升TTFT，但偏底层系统，落地门槛高。

✍️ Jinbin Luo、Xiaozhe Yao、Shang Yang

[arXiv:2611.26619](https://arxiv.org/abs/2611.26619) · [PDF](https://arxiv.org/pdf/2611.26619)

---

## 6. KG-AST：面向低成本 CI/CD 的预算化测试选择与 AI 缺陷审查

**[KG-AST for Cheaper CI/CD: Budgeted Test Selection and AI Bug Review](https://arxiv.org/abs/2611.06950)**

开发者工具 / 测试 / 工程效率 · 2026-11-03 · 🆕 新论文 · cs.SE / cs.AI

KG-AST 依据 git 历史与代码图特征评估提交风险，重型测试和 AI 审查优先处理高风险提交，AI 仅接收变更邻域图切片。在 11 种语言、155 个项目中，最高风险 20% 提交覆盖 49–64% 的缺陷提交，优于随机 20% 与最大变更 40–55%，均领先 3.8–13.2 个百分点。20 个 Java 项目覆盖 64.6%，19/20 胜出，约 12 个训练项目足够。AI 仅看 diff 发现 26%，加图上下文 32%；静态调用图选择器运行约 8% 测试并覆盖 85% 修复测试。Poincaré 无增益；标签有噪声。

💡 按风险选测试与AI评审预算分配，155项目跨11语言，效果与成本清晰。

✍️ Henry Yeung

[arXiv:2611.06950](https://arxiv.org/abs/2611.06950) · [PDF](https://arxiv.org/pdf/2611.06950)

---

*由 GitHub Actions + DeepSeek 自动生成 · 数据来源 arXiv & Semantic Scholar*
