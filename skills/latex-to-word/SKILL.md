---
name: latex-to-word
description: "将 LaTeX (.tex) 文件转换为 Word (.docx) 格式。通过自动预处理解决 pandoc 对自定义命令、tabularx、resizebox 等的兼容性问题，最大限度减少后续手动调整。"
---

# LaTeX → Word (.docx) 转换

将用户指定的 `.tex` 文件转换为 `.docx`，通过预处理 + pandoc 流水线，最大限度保留内容结构并减少手动调整。

## 输入

- `$ARGUMENTS`：要转换的 `.tex` 文件路径（相对或绝对均可）

## 前置检查

1. 确认 `pandoc` 已安装（`which pandoc`）。如未安装，提示用户安装后重试。
2. 确认 `python3` 或 `python` 可用。
3. 确认用户指定的 `.tex` 文件存在且可读。

## 流程

### Step 1：分析源文件

读取 `.tex` 文件**全文**，识别以下 pandoc 不兼容元素：

| 类别 | 识别方法 | 示例 |
|------|----------|------|
| 非标准文档类 | `\documentclass` 行中非 `article`/`report`/`book` | `ctexart`, `IEEEtran` |
| 自定义列类型 | `\newcolumntype{X}` | `\newcolumntype{Y}{...}` |
| `tabularx` 环境 | `\begin{tabularx}` | 需转为 `tabular` |
| `\resizebox` 包裹 | `\resizebox{\textwidth}{!}{` 或 `\resizebox{\textwidth}{!}{%` | 需去掉包裹（注意两种写法） |
| `\allowbreak` | 直接搜索 | 需删除 |
| `\ignorespaces` | 直接搜索 | 需删除 |
| `\cmidrule(lr)` | `\cmidrule` 后带 `(...)` 裁剪参数 | 去掉裁剪参数 |
| `\path{...}` | 在 `\newcommand` 定义或正文中 | 改为 `\texttt{...}` |
| 不必要的格式命令 | `\setlist`, `\captionsetup`, `\hypersetup` | 需删除 |
| 枚举可选参数 | `\begin{enumerate}[label=...]` | 需简化 |
| `\renewcommand\tabularxcolumn` | 直接搜索 | 需删除 |

将所有发现的问题记录下来，用于生成预处理脚本。

### Step 2：生成预处理 Python 脚本

在源文件同目录下生成 `_preprocess_for_pandoc.py`，脚本需：

**必做（通用规则）：**

```python
import re, os

src = r"<源文件绝对路径>"
dst = r"<同目录>/_for_pandoc.tex"

with open(src, 'r', encoding='utf-8') as f:
    content = f.read()

# === 通用规则 ===

# 1. 非标准文档类 → article
content = re.sub(
    r'\\documentclass(\[[^\]]*\])\{[^}]+\}',
    r'\\documentclass\1{article}',
    content
)

# 2. 删除 \newcolumntype 定义行（整行匹配）
content = re.sub(r'\\newcolumntype\{.\}.*\n', '', content)

# 3. 删除 \renewcommand\tabularxcolumn 及其上方的注释行
content = re.sub(
    r'(%.*tabularx.*\n)?\\renewcommand\\tabularxcolumn.*\n',
    '', content
)

# 4. 全局替换自定义列标识符：C{...} → c（只出现在列规格中）
content = re.sub(r'C\{[^}]+\}', 'c', content)

# 5. tabularx → tabular（先替换 C{} 后再做，此时列规格中无嵌套大括号）
def simplify_tabularx(m):
    colspec = m.group(1)
    # 替换所有非标准列标识符（根据分析结果添加）
    colspec = colspec.replace('Y', 'l').replace('X', 'l')
    return r'\begin{tabular}{' + colspec + '}'

content = re.sub(
    r'\\begin\{tabularx\}\{[^}]+\}\{([^}]+)\}',
    simplify_tabularx, content
)
content = content.replace(r'\end{tabularx}', r'\end{tabular}')

# 6. 删除 \resizebox{...}{!}{ 包裹（兼容带 % 和不带 % 两种写法）
content = re.sub(r'\\resizebox\{[^}]+\}\{[^}]+\}\{%?\s*\n', '', content)
# 修复对应的多余闭合大括号（两种模式）：
# 模式 A：\end{tabular}} → \end{tabular}（同行双闭合）
content = re.sub(r'(\\end\{tabular\})\}', r'\1', content)
# 模式 B：\end{tabular}\n    }\n → \end{tabular}\n（换行后单独 } 行）
content = re.sub(r'(\\end\{tabular\})\s*\n\s*\}', r'\1', content)

# 7. 删除 \allowbreak
content = content.replace(r'\allowbreak', '')

# 8. 删除 \ignorespaces
content = content.replace(r'\ignorespaces', '')

# 9. \path{...} → \texttt{...}（正文中和 \newcommand 定义中）
content = re.sub(r'\\path\{([^}]*)\}', r'\\texttt{\1}', content)

# 10. 删除格式设置命令
content = re.sub(r'\\setlist\{[^}]*\}', '', content)
content = re.sub(r'\\captionsetup\{[^}]*\}', '', content)
content = re.sub(r'\\hypersetup\{[^}]*\}', '', content)

# 11. 删除不再需要的 \usepackage
for pkg in ['tabularx', 'enumitem']:
    content = content.replace(r'\usepackage{' + pkg + '}', '')

# 12. 简化带可选参数的 enumerate
content = re.sub(
    r'\\begin\{enumerate\}\[[^\]]+\]',
    r'\\begin{enumerate}', content
)

# 13. 简化 \cmidrule 裁剪参数：\cmidrule(lr){2-3} → \cmidrule{2-3}
content = re.sub(r'\\cmidrule\([^)]*\)', r'\\cmidrule', content)

# 14. 删除独立行的 \small
content = re.sub(r'\n\\small\n', '\n', content)

# 15. 合并连续空行
content = re.sub(r'\n{3,}', '\n\n', content)

with open(dst, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Done: {dst}")
print(f"Size: {len(content)} chars")
```

**按需添加（根据 Step 1 分析结果）：**

- 如果发现 `\href{...}{\path{...}}` 模式 → 将整个 `\newcommand` 定义替换为 pandoc 友好版本
- 如果发现其他自定义列标识符（如 `L`, `R`, `P{}`）→ 在 `simplify_tabularx` 中添加对应替换
- 如果发现 `\makecell` → 保留（pandoc 会忽略但不报错）
- 如果发现 `\multirow` → 保留（pandoc 有基本支持但复杂合并单元格可能需手动调整）
- 如果发现 `tabulary` / `supertabular` 等其他表格环境 → 类似 tabularx 处理
- 如果文件使用 BibTeX 引用（`\cite`）→ 考虑是否需要传 `--bibliography` 给 pandoc

### Step 3：运行预处理脚本

```bash
cd "<源文件目录>"
python _preprocess_for_pandoc.py
```

验证 `_for_pandoc.tex` 已生成，并快速检查：
- 无 `tabularx`、`resizebox`、`\allowbreak` 残留
- `\begin{tabular}` 列规格中无自定义列标识符

### Step 4：pandoc 转换

```bash
pandoc _for_pandoc.tex \
  -o "<输出文件名>.docx" \
  --from latex \
  --to docx \
  --resource-path="<源文件目录>" \
  --standalone
```

输出文件名规则：与源文件同名，扩展名改为 `.docx`。
如果同名 `.docx` 已存在且被占用（Permission denied），则追加 `_new` 后缀。

### Step 5：清理临时文件

删除：
- `_for_pandoc.tex`
- `_preprocess_for_pandoc.py`

### Step 6：报告结果

向用户报告：
1. 输出文件路径和大小
2. pandoc 是否有警告（如有，列出）
3. 提示可能需要手动调整的内容：
   - 表格格式（列宽、对齐）
   - 含 `\multirow` 的合并单元格表格
   - 中英文混排字体
   - 标题层级样式
   - 复杂多行数学公式

## 关键注意事项

- **保留 `\newcommand` 定义**：pandoc 能正确展开大多数 `\newcommand`，不要盲目删除或手动展开
- **图片路径**：`--resource-path` 设为源文件所在目录，pandoc 会自动查找引用的图片
- **编码**：始终使用 UTF-8 读写
- **不要修改源文件**：所有预处理操作在副本 `_for_pandoc.tex` 上进行
