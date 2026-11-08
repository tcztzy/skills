# 防御性写作：逐句分类与主张跟踪

脚本实现 [论文 §2.4 和附录 C](https://arxiv.org/html/2610.11355v2#S2.SS4) 的两项分析：**每句扮演什么角色**，以及**原稿中的每项主张在改写后怎样变化**。分类和主张变化由模型判断；遍历、覆盖检查和指标计算由 Python 执行。

每次模型调用均直接包含所需的规则和材料，不依赖模型读取论文或继承其他请求的上下文。论文链接用于说明方法来源。

## 代码从哪里读

`read_document` 先将输入转为正文，再按以下顺序执行 `scripts/audit_defensive_writing.py` 中的内容检查：

1. `split_sentences`：用 pySBD 分句，按空行分段，给每句固定编号。
2. `classify_sentences`：遍历全部句子，每批最多 32 句；要求每个编号恰好返回一次。
3. `sentence_metrics`：由句子标签计数并计算指标。
4. `extract_claims`：从原稿逐段提取主张，保存一个固定列表。
5. `track_claims`、`claim_metrics`：逐项比较改写稿，记录状态并计算 Ret、Soft。
6. `main`：读取文件并按上述顺序执行；有 `--rewrite` 时生成新稿，再运行同一分析。

主张提取独立于句子分类：一句话可以同时包含限制和主张，不能只提取标为 claim 的句子。没有原稿与改写稿的配对时，不计算主张变化。

## 标签与指标

句子采用论文的七类，存在多个适用类别时取表中最先出现的一类：

| 标签 | 作用 |
| --- | --- |
| not_shown | 表明证据没有建立某结论，或限定结果的解释 |
| unsupported_doubt | 提出来源中没有的限制、混杂或必要验证 |
| grounded_limit | 来源已有的限制、条件、成本或不利结果 |
| generic_scope | 仅用笼统的测试条件限缩范围 |
| future_work | 提出未来工作 |
| claim | 报告有利结果，陈述主张、解释或贡献 |
| other | 背景、方法设置、过渡 |

U 包含 not_shown、unsupported_doubt、generic_scope。英文指标为：

- `R_U = 100 × U句数 / 总词数`。
- `R_not_shown = 100 × not_shown句数 / 总词数`。
- `P_U = 含U句子的段落数 / 总段落数`，取值 0–1。本脚本明确以空行分隔的段落为论文中的 text 单位，不计算 U 句子占比，也不平均各段的 R_U。

主张状态为 kept、strengthened、weakened、scoped、retracted、dropped。多种状态适用时按 `retracted > dropped > weakened > scoped > strengthened > kept` 选择：

- `Ret = retracted主张数 / 原稿主张总数`。
- `Soft = (weakened + scoped)主张数 / 原稿主张总数`，不含 retracted 或 dropped。
- 原稿未提取到主张时，两项为 null，不记成 0。

报告保留每句原文、标签、段落编号，以及每项原稿主张、变化状态和改写稿引文。not_shown 的 source_quote 指来源中**原来断言被否定命题**的片段，不是证明限定合理的证据。

## 运行

分类、主张跟踪和改写的语义判断来自模型。真实调用须单独获得用户批准，
并通过既有 `review_executor.py` 的账本。SDK 直连关闭；已初始化的 DSH 状态可
承接携带完整规则、输入和 schema 的文本请求，返回 JSON 后由本地 Pydantic 校验。

首次用 `--prepare-review --model <已授权模型> --responses-jsonl calls.jsonl`
及正常输入/输出参数运行：退出3并导出下一条不可变请求；不会调用模型。
操作方按执行器已有流程为这份请求准备并初始化状态：`prompt` 指向该文件，
`pinned_files` 固定其 SHA-256，`scope.audit_request_sha256` 记录打印的同一哈希。
保留执行器要求的已验证隔离运行配置；不得改凭据、安全设置或用自填字段代替用户批准。

批准后用 `--review-executor /path/to/review_executor.py --review-state /task/controller`
替换 `--prepare-review`。适配器仅调用既有 `run`，不 init/approve、不修改账本状态，
也不重置预算。一轮最多消费一个已授权状态；结果落入 calls.jsonl 后继续到下一请求，
若尚无匹配状态则再次退出3。操作方为下一条请求准备新的明确授权状态，再续接；
所有先前结果严格回放，不重复计费。完成时退出0并写报告及修订稿。

未知结果、预算暂停、错误或不匹配状态不会自动重发；须走原执行器的核对/批准流程。
已经 COMPLETE 的结果可以恢复读取；预算暂停但 outcome_status=COMPLETE 的结果保留，
不追加调用。每条结果保留原 review/request ID 和状态路径，不读取原始会话或思考日志。
适配器不更换模型：`--model` 必须与准备状态一致；现有执行器仍限定其 DSH/DeepSeek 路由。

需要 Python 3.12+、uv；CLI 不需要 API 凭据。用 `--model` 指明记录中的模型。
读取 DOCX、Typst、LaTeX、Markdown 需要 Pandoc。以下命令在 paper-writer 目录运行。

脚本的 shebang 为 `#!/usr/bin/env -S uv run --script`，已设置可执行权限。也可直接运行 `./scripts/audit_defensive_writing.py` 并传入相同参数；uv 会读取文件头的 Python 要求和依赖声明，准备运行环境。

比较原稿和改写稿，计算句子指标及主张变化：

```sh
uv run scripts/audit_defensive_writing.py draft.txt --model recorded-model --responses-jsonl calls.jsonl \
  --original original.txt --report audit.json
```

仅根据来源材料分类；中文用字符分母并明确命名：

```sh
uv run scripts/audit_defensive_writing.py draft.txt --model recorded-model --responses-jsonl calls.jsonl \
  --evidence results.txt --language zh --report audit.json
```

加 `--rewrite revised.txt` 可生成修订稿；报告的 before、after 分别包含修改前后的完整分类与指标，并复用同一个原稿主张列表。U 标签不自动触发删除，指标降低也不等于写得更好。

正文、`--original` 和每个 `--evidence` 均支持 `.txt`、`.docx`、`.typ`、`.tex`、`.md`、`.markdown`，可以混用：

```sh
uv run scripts/audit_defensive_writing.py draft.docx --model recorded-model --responses-jsonl calls.jsonl \
  --original original.typ --evidence results.tex --evidence methods.md \
  --language zh --report audit.json
```

格式只用于读取内容。排版标记由 Pandoc 解析，脚本保留转换所得的标题、摘要、段落、表格文字和图注，再执行同一套内容检查。相对引用从主文件所在目录读取。Pandoc 的转换警告会直接显示。修订输出为 `.txt` 正文，不重建原文档排版。

每行离线记录为 `{"request": {"model": "...", "instructions": "完整规则",
"input": {}, "schema": {}}, "response": {}}`。请求须逐项匹配本次模型、完整规则、
实际材料和输出 schema；响应经 Pydantic 校验，缺失、多余或不匹配记录均报错。
这些记录不是批准凭证；回放只验证流程，不证明模型语义正确，也不触发网络请求。
SDK 客户端参数仅保留给已有函数级离线 MockTransport 测试；CLI 不构造 SDK 客户端。
适配模式保存原账本引用并标注 ledger_executor；纯回放标注 offline_replay。
原稿或来源材料至少提供一种；文本源文件使用 UTF-8 编码。

英文按空白分词；论文未公开精确的计词代码。中文是本实现的适配：统计 Unicode 字母和数字字符，输出 `R_U_per_100_chars`、`R_not_shown_per_100_chars`，不将中文字符冒充英文词数。所有分类均使用指定模型，尚未用人工标注集验证其准确率。

升级依赖后直接运行当前代码与测试，不添加旧版兼容分支。使用 `uv run --upgrade` 可要求 uv 重新解析依赖到符合条件的最新版本。

## 测试

```sh
uv run --with 'openai>=2' --with 'pydantic>=2' --with 'pysbd>=0.3.4' \
  python -m unittest discover -s tests -p 'test_audit_defensive_writing.py'
```

测试覆盖上述格式读取、完整编号、分句、计数分母、主张变化和模拟 API 流程。API 响应是测试数据，测试结果不代表模型分类准确率。

## 实验性扩展 论证关系测量

此扩展借鉴上述论文的构念定义、来源锚定、语义标注和确定性汇总设计；**论证关系标签和覆盖率是本技能提出的试验，不是论文原有或已验证的指标**。原有七类句子、`R_U`、`P_U`、`Ret` 和 `Soft` 的定义和执行流程不变。本模式不运行它们，也不调用模型。

测量对象是文本在所选范围内是否明确建立一项特定关系，而非词语是否出现：

- `difficulty_requirement`：具体任务困难为何产生某项设计要求。
- `requirement_mechanism`：本文的具体机制如何回应该要求。
- `claim_evidence`：所指证据在其条件、强度和范围内支持哪项主张。

先固定 `contract.scope` 以及 `contract.units`（每项含 `id`、`kind`、`relationship`），所有版本使用完全相同的清单；报告保存该清单的 SHA-256，清单不同不可直接比较比例。若清单由看过修改稿后选取，必须声明事后选择，不能声称预注册。固定单位应是需检验的关系，不随段落拆合、重复措辞或版本增删而增减。

每项判断是 `explicit`（文本明确连接两端）、`unclear`（相关描述出现但关系或支撑仍需推断）、`absent`（所选范围内未建立）。只有端点名词、创新措辞或组件清单不能判为 explicit。未写出不等于科学上不成立；构造例子可说明问题，不能替代新颖性或性能证据。每类关系汇总：`explicit_fraction = explicit项数 / 该类固定项数`；同时报告各状态计数、分母和单位ID。无适用项返回 null；unclear 始终留在分母中，不计为 explicit；不加权合成为质量总分、不设置合格阈值。

标注文件使用 `schema_version: "argument-relations-v1"`，并包含：

- `annotator` 和 `annotation_context`：谁作出的语义判断、是否知道版本身份、是否看过他人结果，以及选择和验证的限制。当前助手的标注不能称为独立人工评阅。
- `document_sha256`：对实际转换后的 UTF-8 正文计算 SHA-256；键为 `input`、可选 `original`、`evidence_1` 等，与命令的材料集合完全匹配。
- `contract`：上述固定范围及关系清单。
- `judgments`：每个固定ID恰好一次，含 `id`、`status`、`anchors`、`rationale`、`uncertainty`。unclear 必须说明不确定性。
- 每个 anchor 含 `document`、`sentence_id`、`quote`。用本脚本 `split_sentences(text, language)` 固定句子编号，quote 必须是该句精确片段。报告补入完整原句和段落号。非 absent 项须锚定 input；explicit 的 claim_evidence 还须锚定来源证据。引文核验不代替语义或科学有效性判断。

```sh
uv run scripts/audit_defensive_writing.py draft.txt \
  --evidence evidence.txt --argument-annotations annotations.json --report argument-report.json
```

该模式只读取提供的标注并确定性汇总，无须 `--model`、API凭据或评阅账本；不能与改写、模型响应日志、执行器参数混用。它没有把模型调用藏在汇总步骤中。若日后需外部模型生成标注，仍须遵循上文的单独批准与账本要求。

第一次用于某种写作问题时，先保留原稿与修改稿的完整标注和事实检查，再试最小对照：同义改写应保留关系；删除建立关系的必要内容应降低相应覆盖；只添“创新”等空话不应增加；有证据的收窄不能因此被当作事实丢失。另列固定的受支持原稿主张和关键事实，逐项记录保留、改变、遗漏或不确定；检查数字、单位、实体、否定和范围，不能凭关系覆盖上升认定修改更好。

这些对照若由同一标注者设计并标注，只是初步自检，不能报告分类准确率。没有第二个独立、同协议的完整标注时，一致性返回 null；不能把已知导师版本当金标准，或捏造盲测、独立性及 Cohen's κ。试测只能说明本案例中所选关系如何变化，不能声称对其他论文普遍有效。
