# BBilingual 参考手册

[English](reference.md) | **简体中文**

快速开始之外的所有内容：安装、全部设置、翻译后端、本地模型、语言、字体、隐私、已知限制和故障排查。

[安装](#安装) · [配置](#配置) · [使用本地模型](#使用本地模型推荐) · [翻译后端](#翻译后端) ·
[用自己的语言输入](#用自己的语言输入) · [语言](#语言) · [外观](#外观) · [字体](#更好看的字体) · [哪些会翻译](#哪些会被翻译哪些不会) ·
[隐私](#隐私与安全) · [已知限制](#已知限制) · [故障排查](#故障排查) · [开发](#开发)

## 安装

环境要求：带有 `MessageDisplay` hook 的 Claude Code 版本（在 2.1.285 到 2.1.289 上测试过）、Python 3.9 或更新版本（只用标准库；在 3.12 上开发，CI 运行 3.9 到 3.12）、Linux、macOS、Windows 或 WSL。

```bash
claude plugin marketplace add Ahorns/BBilingual
claude plugin install bbilingual@bbilingual
```

如果想从本地克隆直接试用而不安装：

```bash
claude --plugin-dir /path/to/BBilingual
```

在你完成配置之前，安装插件不会改变任何东西。在此之前，每次会话的第一条消息会显示一行提示，说明 BBilingual 尚未配置。

## 配置

所有设置都是环境变量。可以写进你的 shell 配置文件，也可以写进 `~/.claude/settings.json` 的 `env` 块里，这样每个 Claude Code 会话都会生效：

```json
{
  "env": {
    "BBILINGUAL_BACKEND": "openai",
    "BBILINGUAL_API_BASE": "https://api.openai.com/v1",
    "BBILINGUAL_MODEL": "YOUR_MODEL_NAME",
    "BBILINGUAL_TARGET": "zh-CN"
  }
}
```

不要把密钥写进这个文件：请改为在 shell 配置文件或密钥管理器里导出 `BBILINGUAL_API_KEY`。修改设置后请重新启动 `claude`；正在运行的会话仍使用旧设置。

| 变量 | 含义 | 默认值 |
|---|---|---|
| `BBILINGUAL_BACKEND` | `openai`、`deepseek`、`deepl` 或 `command` | 未设置：插件什么也不做 |
| `BBILINGUAL_TARGET` | 目标语言：语言代码（`fr`、`ja`、`zh-CN`、`zh-TW`、`pt` 等）或语言名称 | `zh-CN` |
| `BBILINGUAL_MODEL` | 模型名称 | `openai` 后端必填；`deepseek` 有默认值 |
| `BBILINGUAL_API_BASE` | 聊天 API 的基础 URL | `https://api.openai.com/v1` |
| `BBILINGUAL_API_KEY` | API 密钥（本地服务可不填；DeepL 也会读取 `DEEPL_API_KEY`，DeepSeek 读取 `DEEPSEEK_API_KEY`） | 无 |
| `BBILINGUAL_CMD` | `command` 后端要运行的命令 | `command` 后端必填 |
| `BBILINGUAL_PROMPT_EXTRA` | 给模型的额外指令：领域、术语表、语气 | 无 |
| `BBILINGUAL_TEMPERATURE` | 仅在设置时才发送（有些模型不接受默认值以外的值） | 不发送 |
| `BBILINGUAL_EXTRA_BODY` | 合并进每个聊天请求的 JSON 对象，用于需要额外字段的服务，例如 `{"thinking": {"type": "disabled"}}`。它不能替换模型和消息 | 无 |
| `BBILINGUAL_STYLE` | 译文的颜色：`dim`、`italic`、`gray`、`cyan`、`green`、`yellow` | 普通 |
| `BBILINGUAL_INPUT` | [输入翻译](#用自己的语言输入)的初始值：`on`、`confirm` 或 `off`（`/bbinput` 会覆盖它） | `off` |
| `BBILINGUAL_LOG` | 设为 `1` 会在本地记录英文与译文对照（见[隐私](#隐私与安全)） | 关闭 |
| `BBILINGUAL_DISABLE` | 设为 `1` 会关闭这个 hook，可以只对一次会话，也可以永久 | 关闭 |

如果只想在某一次对话中关闭 BBilingual，用 `BBILINGUAL_DISABLE=1 claude` 启动即可。在 Claude Code 里，`/bbilingual off` 会立刻关掉 Claude 回复下面的译文（无需重启），`/bbilingual on` 再打开；你的选择会被记住。单独输入 `/bbilingual` 会显示当前设置。这个命令和 `/bbinput` 一样，需要 Claude Code 2.1.287 或更新版本。

## 使用本地模型（推荐）

用运行在你自己电脑上的模型来翻译，是最好的默认选择：

- **私密。** Claude 的回复可能引用你的代码、路径和报错信息。用本地模型，这些内容都不会离开你的电脑。
- **免费、可离线。** 不需要 API 密钥，没有账单，没有速率限制，没有网络也能用。
- **可自由调整。** 你可以选择适合你的语言和领域的模型与指令。

代价是质量和速度：小型本地模型的翻译质量不如大型云端模型，速度则取决于你的硬件。对于“边读边看”的用途，小模型通常已经够用。

用 [Ollama](https://ollama.com) 设置（LM Studio、llama.cpp server 和 vLLM 的做法相同）：

```bash
ollama pull YOUR_MODEL            # 选一个模型，见下文
```

```json
{
  "env": {
    "BBILINGUAL_BACKEND": "openai",
    "BBILINGUAL_API_BASE": "http://localhost:11434/v1",
    "BBILINGUAL_MODEL": "YOUR_MODEL",
    "BBILINGUAL_TARGET": "ja"
  }
}
```

不需要 API 密钥。重新启动 `claude`，随便问点什么即可。

**如何选择模型。** 翻译质量随模型规模提升，但每一批文字都要等翻译完成才会显示，所以在笔记本上，大约 30 亿到 80 亿参数的模型是个不错的起点。请选择训练过你目标语言的模型：中文、日文、韩文可以选对这些语言支持较好的系列（例如 Qwen），欧洲语言可以选通用的多语言系列（例如 Gemma 或 Llama）。去 Ollama 模型库查看最新的名称，然后拿一段你自己能判断好坏的文字，试两个候选模型。这些只是起步建议，不是基准测试结果。

**保持速度。**
- 第一次请求要把模型加载进内存，会比较慢。Ollama 会在几分钟后卸载闲置的模型；在 Ollama 服务的环境里设置 `OLLAMA_KEEP_ALIVE=1h` 可以让它保持更久。
- 同一个模型的更小或量化更激进的版本更快，但准确度略低。
- 有 GPU 或 Apple 芯片，差别会非常大。

如果你发现某个模型翻译你的语言效果很好，欢迎在 issue 或 pull request 里告诉我们。

## 翻译后端

### `openai`：任何兼容 OpenAI 的聊天 API

每一批文字发送一次请求，发往 `{BBILINGUAL_API_BASE}/chat/completions`。模型还能看到同一条消息中更早的几行，因此术语保持一致。

| 服务 | `BBILINGUAL_API_BASE` |
|---|---|
| OpenAI | `https://api.openai.com/v1` |
| OpenRouter | `https://openrouter.ai/api/v1` |
| Poe | `https://api.poe.com/v1` |
| DeepSeek | `https://api.deepseek.com`（或使用 [`deepseek`](#deepseek) 预设） |
| Ollama（本地） | `http://localhost:11434/v1` |
| LM Studio（本地） | `http://localhost:1234/v1` |
| vLLM、llama.cpp server 等 | 该服务的 `/v1` 地址 |

上表中的基础 URL 是各服务文档中的默认值。该协议已用 Poe 和一个本地模拟服务测试过；其他服务使用相同的协议，但请以它们自己的文档为准。

请选择小而快的模型：每一批文字都要等翻译完成才会显示。模型名称请查看对应服务自己的模型列表。现成的设置示例见 [`examples/`](../examples)。

### `deepseek`

DeepSeek API 的预设：设置 `BBILINGUAL_BACKEND=deepseek` 和 `DEEPSEEK_API_KEY`（或 `BBILINGUAL_API_KEY`）就够了，不需要别的。它使用 `https://api.deepseek.com` 和模型 `deepseek-flash`，并且关闭思考模式：DeepSeek 的模型默认会先思考再回答，这会让翻译变慢并多用 token。你设置的 `BBILINGUAL_MODEL`、`BBILINGUAL_API_BASE` 和 `BBILINGUAL_EXTRA_BODY` 仍然优先。模型名称会变化，请查看 DeepSeek 的文档。你的文字会发送到 DeepSeek 的服务器，适用它自己的条款。现成的设置：[`examples/settings-deepseek.json`](../examples/settings-deepseek.json)。

### `deepl`

每一行发送一次请求到 DeepL API。设置 `BBILINGUAL_API_KEY`（或 `DEEPL_API_KEY`）。以 `:fx` 结尾的密钥使用免费接口。

### `command`：你自己的后端

`BBILINGUAL_CMD` 每行运行一次，最多同时运行 8 个。文本通过标准输入传入；请在标准输出只打印译文，不要有其他内容。命令以非零状态退出或输出为空时，该行保持不翻译。环境变量会被继承，所以你的程序可以通过 `BBILINGUAL_TARGET` 知道目标语言。[`examples/custom_backend.py`](../examples/custom_backend.py) 是一个完整的示例，它会调用 LibreTranslate 服务。

## 用自己的语言输入

显示 hook 把 Claude 的英文翻译成你的语言；输入功能则相反：你输入的、不是纯英文的内容，会在 Claude 收到之前被翻译成英文，所以你可以用自己的语言写提示词。对话里显示的是 Claude 实际收到的英文，你的原文不会保留在那里。

它默认关闭，需要你打开。用 `/bbinput` 命令切换，你的选择会跨会话保留：

| 命令 | 效果 |
|---|---|
| `/bbinput on` | 翻译后直接发送英文 |
| `/bbinput confirm` | 先显示英文并询问“发送 / 取消”（在“其他”里输入的文字会被改为发送这段） |
| `/bbinput off` | 什么也不做（默认） |
| `/bbinput` | 显示当前设置 |

`BBILINGUAL_INPUT`（`on`、`confirm` 或 `off`）设置初始值，`/bbinput` 会覆盖它。在 `on` 模式下没有弹窗，也不会提问：你在对话里看到的就是 Claude 收到的英文。

- **会翻译什么：** 含有非纯英文字母的文字：中文、日文、韩文、西里尔字母、阿拉伯文、希伯来文、印度系文字、泰文，或带重音的拉丁字母。模型会被告知把代码、文件路径、@ 提及、URL 和技术术语保持原样。
- **粘贴的内容：** 只翻译不是英文的那些行。你粘贴的英文文本、日志或代码会一字不动地保留，你自己写的中文段落的译文会放在原来的位置。
- **不会翻译什么：** 纯英文、斜杠命令（`/...`）、shell 行（`!...`）以及超过 4000 个字符的粘贴内容，都会原样通过。
- **失败时：** 如果翻译失败或结果与原文相同，会原样发送你输入的内容（在 `confirm` 模式下会先询问你）。
- **Claude 还在工作时：** 此时输入的消息会排在 Claude Code 的队列里。这个队列由 Claude Code 自己显示，显示的仍是你输入的原文，但消息会立刻被翻译，所以 Claude 收到的是英文。
- **后端：** 需要 `openai` 后端（任何兼容 OpenAI 的 API 或本地模型），模型、密钥和基础 URL 与显示 hook 相同。`deepl` 和 `command` 在这里不能翻译成英文。
- **隐私：** 你输入的内容会发送到你的翻译后端，和 Claude 的回复一样。[本地模型](#使用本地模型推荐)可以让它留在你的电脑上。
- **要求：** Claude Code 2.1.287 或更新版本。它使用 Claude Code 的 mods API，Anthropic 称其为抢先体验功能，以后可能会变化。显示翻译使用的是常规 hook API。

## 语言

`BBILINGUAL_TARGET` 可以填常见的语言代码（`fr`、`de`、`es`、`pt`、`it`、`ru`、`ar`、`hi`、`vi`、`th`、`id`、`tr`、`nl`、`pl`、`ja`、`ko`、`zh-CN`、`zh-TW`），也可以填你的模型能理解的任何语言名称（例如 `Swedish`）。BBilingual 假定 Claude 使用英文输出。

对于中文、日文和韩文，插件还会去掉 CJK 字符与拉丁字母单词或数字之间的空格，因为 Claude Code 是在空格处折行的，多余的一个空格会让一长行过早地断开。译文行内剩下的空格（两个英文单词之间、`87.0 %` 中）会换成不换行空格，原因相同。已经以 CJK 为主的行不会再次被翻译。

可以用 `BBILINGUAL_PROMPT_EXTRA` 来引导翻译器，例如：

```
BBILINGUAL_PROMPT_EXTRA="The text is about neuroscience. Translate 'spike' as 脉冲 and keep 'STDP' in English."
```

## 外观

- 每一行译文都紧跟在原文下面，缩进与原文一致（列表和编号会对齐）。
- 标题的译文放在同一行：`## Results / 结果`。
- 表格会随着输出以原文显示；表格结束后，会紧接着出现一张完整的译文表格。
- `BBILINGUAL_STYLE=gray` 只给译文上色；原文保持原来的颜色。颜色作用于段落、列表和标题，但不会用在表格里：Claude Code 会把单元格里含有颜色代码的表格画错（见[工作原理文档](how-it-works.md)）。

## 更好看的字体

终端把每个字符画在固定的网格里，而一个中文、日文或韩文字符应当正好占两个格子，宽度是拉丁字母的两倍。如果你的字体不遵守这条规则，表格边框可能会向一侧漂移，各行看起来也会参差不齐。专门为此设计的字体能同时解决这两个问题，让混排文字读起来舒服得多。以下是免费、开源（SIL 开源字体许可）的选择：

| 字体 | 说明 | 下载 |
|---|---|---|
| **Sarasa Mono（更纱黑体等宽）** | 拉丁字母与 CJK 严格按 1:2 网格设计。请选择对应你语言的版本：SC、TC、J 或 K | <https://github.com/be5invis/Sarasa-Gothic> |
| **Noto Sans Mono CJK** | 字符覆盖非常完整。版本有 SC、TC、JP、KR | <https://fonts.google.com/noto> 或 <https://github.com/notofonts/noto-cjk> |
| **Maple Mono** | 带 CJK 版本的编程字体（请找 CN 版本） | <https://github.com/subframe7536/maple-font> |

请到各项目页面查看最新的发布版本和变体名称。

**安装后，在终端里选用它。** 请把字体安装在绘制终端的那台电脑上，而不是 WSL 或远程服务器里，然后重启终端。

- **Windows Terminal**（WSL 也适用）：设置，进入你的配置文件，然后是外观，再到字体。它支持用逗号分隔填写多个字体名，后面的字体会用于第一个字体没有的字符，例如 `Cascadia Mono, Microsoft YaHei UI`。
- **macOS 终端或 iTerm2**：设置，描述文件（Profiles），文本（Text），字体（Font）。iTerm2 还可以为非 ASCII 文字单独指定字体。
- **Linux、kitty、WezTerm、Alacritty**：在终端的设置或配置文件里设置字体族。

把字体和 `BBILINGUAL_STYLE=gray` 搭配使用，译文读起来就像原文下面安静的第二行。如果你不能或不想更换字体，其他东西都不需要改。

## 哪些会被翻译，哪些不会

会翻译：段落、标题、列表项、编号项、引用、含有文字的表格单元格。

不会翻译：围栏代码块、已经是目标文字的行（CJK 目标语言时）、表格分隔行、只有数字等不含文字的单元格，以及翻译器原样返回原文的任何一行。哪些内容值得翻译由翻译器自己判断，所以状态行或进度条是翻译还是忽略，取决于所用的模型。

## 隐私与安全

- **发送了什么，发到哪里。** Claude 回复的文字只会发送到你配置的翻译后端，不会发往其他任何地方。BBilingual 没有服务器、没有遥测、没有数据分析。本地后端（Ollama、LM Studio）会把一切留在你的电脑上；云端 API 则会按它自己的条款接收你的文字。
- **你输入的内容。** 打开[输入翻译](#用自己的语言输入)后，你输入的内容（不是纯英文时）也会发送到翻译后端，且只发送这些。它默认关闭。
- **你的回复可能包含什么。** 回复可能引用你的代码、文件路径、报错信息，以及 Claude 读到的机密内容。请选择你信任的翻译后端，或者更好的做法，使用[本地模型](#使用本地模型推荐)。
- **临时文件。** 在一条消息流式输出期间，会在 `$TMPDIR/bbilingual-<uid>`（权限 0700）里保存几个存放近期文字的小文件，消息结束时删除；遗留的文件会在一小时后清理。
- **日志默认关闭。** 设置 `BBILINGUAL_LOG=1` 后，每一行译文都会连同原文一起追加到 `~/.cache/bbilingual/log.jsonl`（权限 0600，超过 5 MB 自动轮换）。那是你的对话文字存在磁盘上：用完请删除该文件，也不要把它贴到公开的 issue 里。
- **API 密钥** 从环境变量读取，只会发送到你配置的 API 基础地址。不要提交含有密钥的 `settings.json`。
- `BBILINGUAL_CMD` 是通过 shell 运行的，信任程度与你设置里的其他内容相同。

## 已知限制

- **Claude Code 里无法在表格单元格内换行：** `<br>` 和 Unicode 行分隔符要么被原样显示，要么被忽略。这就是表格的译文是第二张表格的原因。
- **旧消息不会被翻译。** hook 只在回复流式输出时运行。用 `claude -c` 或 `--resume` 重新打开一段对话时，之前的回复是直接从对话记录重绘的，不会经过它（已在 Claude Code 2.1.289 上验证）。
- **延迟。** 每一批文字要等翻译返回后才会显示，使用小模型通常是一到三秒。表格在结束时用一次请求整体翻译。
- **较弱的模型可能把英文原样抄回来**，整批都是如此。当一批中大部分内容原样返回时，BBilingual 会再请求一次，但真正的解决办法是换一个更好的模型。
- **翻译质量取决于你的后端。** 便宜的模型有时会漏译，或者对同一个术语翻译不一致。换更好的模型，或者使用 `BBILINGUAL_PROMPT_EXTRA`，会有帮助。
- 已在 Linux 和 WSL（配合 Windows Terminal）上测试。在原生 Windows 上，hook 能在 Python 3.12 下运行（用中文输出检查过），但 `python3` 必须能启动 Python 3.9+：微软商店版 Python 带有它，python.org 的安装包没有。

## 故障排查

**什么都没有被翻译。** 在 Claude Code 窗口里运行 `! echo $BBILINGUAL_BACKEND`，它必须打印出一个后端名称。设置是在 `claude` 启动时读取的，所以修改后请开启新的会话。运行 `/plugin` 检查 BBilingual 是否已启用。

**输入没有被翻译。** 输入 `/bbinput` 查看设置，它必须显示 `on` 或 `confirm`。它只处理含有非英文字母的文字，需要 `openai` 后端，并且需要 Claude Code 2.1.287 或更新版本。手动试一下翻译器：`echo '你好' | python3 scripts/to_english.py`。

**手动试一下 hook。** 下面的命令会打印 Claude Code 会收到的 JSON 返回值：

```bash
echo '{"index":0,"final":true,"message_id":"x","session_id":"s","delta":"Hello world.\n"}' \
  | BBILINGUAL_BACKEND=command BBILINGUAL_CMD="echo 你好世界" python3 scripts/bilingual.py
```

**看起来不对劲。** 用 `BBILINGUAL_LOG=1` 启动 Claude Code，复现问题，然后运行 `python3 scripts/show_log.py --flagged`，查看插件标记出的行（`no_translation`、`same_as_english`、`no_cjk`、`english_left:...`）。`python3 scripts/note.py "what looked wrong"` 会在最近一批内容旁边添加一条备注。提交 issue 时，请只附上你愿意公开的文字。

## 开发

```bash
python3 -m unittest discover -s tests -v     # 约 25 秒，不需要联网
```

hook 只有一个文件：[`scripts/bilingual.py`](../scripts/bilingual.py)，只用标准库。[`docs/how-it-works.md`](how-it-works.md)（英文）解释了设计，以及关于 Claude Code 渲染方式的发现。提交 pull request 之前，请先阅读 [CONTRIBUTING.md](../CONTRIBUTING.md)。
