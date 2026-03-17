---
name: skill-manager
description: 管理 Codex skills：盘点/安装/更新/定制（语言与命令风格），以及将 Claude Code 的 skill（通常位于 ~/.claude/skills）转换为 Codex skill（~/.codex/skills），包括清理不兼容 frontmatter、替换常见占位符并生成 agents/openai.yaml。
---

# Skill Manager

## 快速开始

### 盘点本机已安装的 Codex skills

- 默认目录：`$CODEX_HOME/skills`（若未设置 CODEX_HOME，则通常是 `~/.codex/skills`）
- Bash 示例（WSL）：

```bash
codex_home="${CODEX_HOME:-$HOME/.codex}"
ls -1 "$codex_home/skills" | sort
```

### 获取/安装开源 skills（curated 或 GitHub 路径）

优先复用系统自带的 `skill-installer` 脚本（会走网络）：

- 列表：`~/.codex/skills/.system/skill-installer/scripts/list-skills.py`
- 安装：`~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py`

### 将 Claude Code skill 转为 Codex skill

使用本 skill 自带脚本：

```bash
python3 "$HOME/.codex/skills/skill-manager/scripts/convert-claude-skill.py" \
  --src "$HOME/.claude/skills/latex-to-word"
```

转换后需要 **重启 Codex** 才能加载新 skill。

## 偏好（Preferences）

本 skill 支持用一个 JSON 文件记录偏好，用于：
- 选择输出语言（中文/英文）
- 替换常见占位符（例如 `$ARGUMENTS`）
- 决定是否插入 “Codex 使用说明” 提示块

默认偏好文件（可自行修改）：

- `references/preferences.json`

## Claude → Codex 转换规则（概念层）

### 1) Frontmatter 兼容性

Codex 的 skill frontmatter 建议只保留：

- `name`
- `description`

转换时移除 Claude 专用字段（常见：`argument-hint`、`disable-model-invocation`），并把有用的信息（如参数提示）移动到正文的 “Codex 使用说明”。

### 2) 变量与占位符

Claude skill 常用 `$ARGUMENTS` 表达“用户输入的参数”。Codex 不会自动注入该变量；转换时：

- 用偏好里的 `variable_rewrites` 做文本替换（默认：`$ARGUMENTS` → “用户提供的参数”）
- 同时在正文插入说明，提示需要在对话里明确给出路径/参数

### 3) agents/openai.yaml

Codex skill 建议提供 `agents/openai.yaml` 以便 UI 展示。转换脚本会在缺失时自动生成最小可用版本（`display_name` / `short_description` / `default_prompt`）。

## 脚本

### `scripts/convert-claude-skill.py`

将一个 Claude skill 目录（包含 `SKILL.md`）复制到 `~/.codex/skills/<skill-name>` 并做兼容性转换：

- 清理 frontmatter（只保留 `name` / `description`）
- 按偏好替换占位符（默认跳过 fenced code blocks）
- 在正文插入 “Codex 使用说明”
- 生成 `agents/openai.yaml`（若缺失）

### `scripts/validate-skill.py`

无需额外依赖的轻量校验器（避免依赖 PyYAML），用于快速检查：

- `SKILL.md` frontmatter 是否存在、是否包含 `name` / `description`
- `name` 是否为 hyphen-case
- `description` 长度与字符限制（不包含 `<`/`>`）

## 来源登记（Sources Registry）

为了让“以后从哪里找 skill”不丢失，本 skill 维护一个来源登记表：

- `references/sources.json`

里面记录常用的官方/第三方仓库（例如 `openai/skills`、`huggingface/skills`、`K-Dense-AI/claude-scientific-skills` 等），并支持标注：

- `restricted: true`：明确禁止安装/合并（例如部分仓库的 LICENSE 禁止在本地保留副本或创建派生作品）

## 套件合并（Suites）

为了减少 skill 数量并避免触发分裂，可以把同域、强耦合的一组 skill 合并成一个“套件入口 skill”（suite），并把原始 skills vendoring 到套件内部：

- 套件定义：`references/suites.json`
- 构建输出：`~/.codex/skills/<suite-name>/`
  - 套件入口：`SKILL.md`（中文导航文档 + 路由规则）
  - vendored 内容：`vendor/<source-id>/<skill>/...`
  - UI 元数据：`agents/openai.yaml`

本仓库默认包含两个套件入口（可按需增删）：

- `huggingface-suite`：Hub/CLI、datasets、training、evaluation、tracking、Gradio
- `research-suite`：scientific-writing、EDA、statistical-analysis、scientific-visualization

并把 `pytorch-lightning` 作为 standalone skill 单独安装（触发更精准）。

## 全局 Skill Runtime 约定

为了让 skills 对所有 WSL2 项目都可用，而不是偶然依赖当前仓库的 `.venv`，共享依赖统一收口到：

- `~/.codex/skill-runtimes/`

其中按能力域划分共享 runtime：

- `docs-python`：`doc` / `pdf` / `latex-to-word`
- `science-python`：`jupyter-notebook` / `research-suite` 及相关 scientific skills
- `ml-python`：`huggingface-suite` / `pytorch-lightning`
- `core-tools`：`codex` / `gh` / `playwright` / `pandoc` / `scrot` / MCP 配置与凭据

默认 bootstrap 入口：

```bash
python3 "$HOME/.codex/skills/skill-manager/scripts/bootstrap-global-skill-runtime.py"
```

新终端自动可见约定：

- bootstrap 会生成 `~/.codex/skill-runtimes/shell-init.sh`
- 共享 shell 入口 `~/.local/bin/env` 会在新开的 WSL shell 中自动 source 该文件
- 手动刷新入口：`codex-skill-runtime-refresh`

默认规则：

- skills 的 bundled Python helper 应优先调用对应 domain runtime，而不是依赖当前 shell 解析到的 `python3`。
- 审计脚本应优先 probe 共享 runtime，不得把“当前项目 `.venv` 刚好有包”当作正式 ready。

## 新增脚本

### `scripts/sync-sources.py`

同步来源缓存（避免 GitHub API 限流），将仓库 clone/pull 到：

- `~/.codex/tmp/skill-sources/<source-id>/`

Bash 示例（WSL）：

```bash
python3 "$HOME/.codex/skills/skill-manager/scripts/sync-sources.py" --all
```

### `scripts/build-suites.py`

根据 `sources.json` + `suites.json` 构建套件与 standalone skills：

- 生成/更新：`huggingface-suite`、`research-suite`、`pytorch-lightning`
- 若目标目录已存在：移动到 `~/.codex/skills/_backup/<name>-<timestamp>/` 后重建（可重复运行）

Bash 示例（WSL）：

```bash
python3 "$HOME/.codex/skills/skill-manager/scripts/build-suites.py" --all
```

构建后需要 **重启 Codex** 才能加载新/更新的 skills。
