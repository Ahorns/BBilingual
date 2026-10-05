<p align="center">
  <img src="assets/banner.svg" alt="BBilingual: prompt Claude in English, read the answer in your language" width="100%">
</p>

<p align="center">
  <b>English</b> ·
  <a href="README.zh-CN.md">简体中文</a> ·
  <a href="docs/translations/README.ja.md">日本語</a> ·
  <a href="docs/translations/README.ko.md">한국어</a> ·
  <a href="docs/translations/README.es.md">Español</a> ·
  <a href="CONTRIBUTING.md#translating-the-readme">add yours</a>
</p>

<p align="center">
  <a href="https://github.com/Ahorns/BBilingual/actions/workflows/test.yml"><img alt="tests" src="https://github.com/Ahorns/BBilingual/actions/workflows/test.yml/badge.svg"></a>
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/github/license/Ahorns/BBilingual"></a>
  <a href="https://github.com/Ahorns/BBilingual/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/Ahorns/BBilingual?style=social"></a>
</p>

<h3 align="center">Work with Claude in English for the best results,<br>and read everything in your own language.</h3>

<p align="center">
  <img src="assets/demo.svg" alt="Claude Code answering in English, with a gray translation under every line and the code block left untranslated" width="900">
</p>

BBilingual is a [Claude Code](https://code.claude.com) plugin. It shows a translation under every
English assistant message, in your terminal, in real time. The translation is display only: Claude
still thinks, writes and remembers in English.

<table>
  <tr>
    <td width="33%" valign="top"><b>🧠 Claude stays at its best</b><br>It never sees the translation, so its answers are the ones an English speaker would get.</td>
    <td width="33%" valign="top"><b>🌍 Any language</b><br>Chinese, Japanese, Korean, Spanish, French, Arabic&hellip; whatever your translator can write.</td>
    <td width="33%" valign="top"><b>🔒 Private by default</b><br>Nothing is sent until you set a backend. With a local model nothing leaves your machine.</td>
  </tr>
  <tr>
    <td valign="top"><b>🧩 Bring your own backend</b><br>Ollama, LM Studio, any OpenAI-compatible API, DeepL, or your own command.</td>
    <td valign="top"><b>🧱 Layout-aware</b><br>Code is never translated. Headings, bullets, quotes and tables keep their shape.</td>
    <td valign="top"><b>🪶 Tiny</b><br>One hook file, Python standard library only, nothing to build.</td>
  </tr>
</table>

## Quick start

```bash
# 1. install the plugin
claude plugin marketplace add Ahorns/BBilingual
claude plugin install bbilingual@bbilingual

# 2. get a translator, for example a local model (pick any model you like)
ollama pull YOUR_MODEL
```

```jsonc
// 3. in ~/.claude/settings.json (change "zh-CN" to your language, for example "ja", "es", "fr")
{
  "env": {
    "BBILINGUAL_BACKEND": "openai",
    "BBILINGUAL_API_BASE": "http://localhost:11434/v1",
    "BBILINGUAL_MODEL": "YOUR_MODEL",
    "BBILINGUAL_TARGET": "zh-CN"
  }
}
```

Start a new `claude` and ask anything. Prefer a hosted API or DeepL? See [Backends](#backends).

## Why BBilingual

**The problem.** Large language models work best in English. Most of what they learned is in English,
so prompts and answers in English tend to be more accurate and more precise, especially for code,
science and other technical work. In other languages the answers are often somewhat weaker (how much
depends on the model and the language), and non-English text usually takes more tokens, so it also
costs more and fills the context sooner. (This project did not measure it; it is the general pattern
reported for these models.)

But English answers are hard work for people whose English is not strong. Students, researchers and
engineers who read English slowly, or with a dictionary open, face a screen of dense technical text
that is tiring to follow, and it is easy to miss a detail. Asking Claude to answer in your own
language fixes the reading, but it moves Claude out of the language it is best in. So people end up
choosing between answers that are better and answers they can read comfortably.

| | Ask in your own language | Ask in English | **English + BBilingual** |
|---|:---:|:---:|:---:|
| Claude's answers | often a little weaker | at their best | **at their best** |
| Easy for you to read | ✅ | ❌ hard work | **✅** |
| The original English to check | ❌ | ✅ | **✅** |
| Tokens used | more | fewer | **fewer** |

**The idea: do not choose.** Claude works in English the whole time. BBilingual translates only what
is drawn on your screen, line by line, as it arrives (the picture is under [How it works](#how-it-works)).

- **Claude performs at its best.** It never sees the translation and is never asked to write in two
  languages, so its answers are the ones it would give an English speaker.
- **You read in your own language**, at your own pace, and the original English stays right above
  each translation. If a translation looks odd, the exact words are there to check, and code blocks
  are never translated.
- **You pick up the vocabulary.** Reading technical English next to a translation you can trust is
  a gentle way to learn the terms you will meet again and again.

**Who it is for.** Anyone who codes or does research with Claude in a second language: students,
non-native English speakers on international teams, and anyone learning English through real work.

**What it does not do.** BBilingual translates Claude's answers, not what you type. You still write your
prompts in English; plain, simple wording is fine, and Claude understands it well. It is a reading aid,
not a perfect translation: for an exact command, a number or a subtle point, look at the English.

## How it works

<p align="center">
  <img src="assets/how-it-works.svg" alt="You write in English, Claude answers in English, the MessageDisplay hook sends each line to your translator, and your terminal shows English plus your language. The conversation and Claude's context stay English." width="100%">
</p>

The translation is **display only**. It is added through Claude Code's `MessageDisplay` hook, which
changes what is drawn on screen and nothing else. The transcript, the conversation history and
Claude's context all keep the original English, so Claude is never asked to write bilingual text,
never reads your translation back, and answers exactly as it would without the plugin.

- **Bring your own backend**: a local model through Ollama or LM Studio (recommended: nothing leaves
  your machine), any OpenAI-compatible API (OpenAI, OpenRouter, Poe, ...), DeepL, or your own program.
- **Any target language**: French, Japanese, Portuguese, Chinese, ... with extra care for Chinese,
  Japanese and Korean.
- **Layout-aware**: code blocks are never translated; headings, bullets, quotes and tables keep
  their shape; markdown (bold, code, links) survives.
- **Private by default**: nothing is sent anywhere until you configure a backend, and nothing is
  logged unless you switch the log on.

## Contents

[Quick start](#quick-start) · [Why](#why-bbilingual) · [How it works](#how-it-works) · [Install](#install) · [Configure](#configure) · [Use a local model](#use-a-local-model-recommended) ·
[Backends](#backends) · [Languages](#languages) · [Appearance](#appearance) · [Fonts](#fonts-for-a-better-look) · [What is and is not translated](#what-is-and-is-not-translated) ·
[Privacy](#privacy-and-security) · [Limitations](#limitations) · [Troubleshooting](#troubleshooting) ·
[Development](#development)

## Install

Requirements: a Claude Code version that has the `MessageDisplay` hook (tested with 2.1.285 to
2.1.287), Python 3.9 or newer (standard library only; developed on 3.12, CI runs 3.9 to 3.12),
Linux, macOS or WSL.

```bash
claude plugin marketplace add Ahorns/BBilingual
claude plugin install bbilingual@bbilingual
```

To try it from a local clone without installing:

```bash
claude --plugin-dir /path/to/BBilingual
```

Installing the plugin changes nothing until you configure it. Until then, the first message of a
session shows a one-line hint saying that BBilingual is not configured.

## Configure

All settings are environment variables. Put them in your shell profile, or in the `env` block of
`~/.claude/settings.json` so that every Claude Code session gets them:

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

Keep secrets out of that file: export `BBILINGUAL_API_KEY` from your shell profile or a secret
manager instead. Start a new `claude` after changing settings; running sessions keep the old ones.

| Variable | Meaning | Default |
|---|---|---|
| `BBILINGUAL_BACKEND` | `openai`, `deepl` or `command` | not set: the plugin does nothing |
| `BBILINGUAL_TARGET` | Target language: a code (`fr`, `ja`, `zh-CN`, `zh-TW`, `pt`, ...) or a name | `zh-CN` |
| `BBILINGUAL_MODEL` | Model name | needed for `openai` |
| `BBILINGUAL_API_BASE` | Base URL of the chat API | `https://api.openai.com/v1` |
| `BBILINGUAL_API_KEY` | API key (optional for local servers; DeepL also reads `DEEPL_API_KEY`) | none |
| `BBILINGUAL_CMD` | Command for the `command` backend | needed for `command` |
| `BBILINGUAL_PROMPT_EXTRA` | Extra instructions for the model: domain, glossary, tone | none |
| `BBILINGUAL_TEMPERATURE` | Sent only if set (some models reject anything but their default) | not sent |
| `BBILINGUAL_STYLE` | Colour for the translated text: `dim`, `italic`, `gray`, `cyan`, `green`, `yellow` | plain |
| `BBILINGUAL_LOG` | `1` records English/translation pairs locally (see [Privacy](#privacy-and-security)) | off |
| `BBILINGUAL_DISABLE` | `1` switches the hook off, for one session or for good | off |

To switch BBILINGUAL off for a single conversation, start it with `BBILINGUAL_DISABLE=1 claude`.

## Use a local model (recommended)

Translating with a model that runs on your own computer is the best default:

- **Private.** Claude's replies can quote your code, paths and error messages. With a local model
  none of it leaves your machine.
- **Free and offline.** No API key, no bill, no rate limit, and it works without a network.
- **Yours to tune.** Pick the model and the instructions that suit your language and your field.

The price is quality and speed: a small local model translates less well than a large hosted one,
and how fast it is depends on your hardware. For reading along, small models are usually good enough.

Setup with [Ollama](https://ollama.com) (LM Studio, the llama.cpp server and vLLM work the same way):

```bash
ollama pull YOUR_MODEL            # choose a model, see below
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

No API key is needed. Start a new `claude` and ask anything.

**Choosing a model.** Translation quality grows with model size, but each batch of text waits for the
translation, so a model of roughly 3 to 8 billion parameters is a good starting point on a laptop. Pick
one that was trained on your target language: families with strong Chinese, Japanese and Korean (for
example Qwen) for those languages, and general multilingual families (for example Gemma or Llama) for
European ones. Browse the Ollama library for current names, then try two candidates on a paragraph you
can judge yourself. These are starting suggestions, not benchmarks.

**Keeping it fast.**
- The first request loads the model into memory and is slower. Ollama unloads idle models after a few
  minutes; `OLLAMA_KEEP_ALIVE=1h` in the environment of the Ollama server keeps it loaded longer.
- Smaller or more heavily quantized variants of a model are faster and a little less accurate.
- A GPU, or Apple silicon, makes a large difference.

If you find a model that translates your language well, please say so in an issue or a pull request.

## Backends

### `openai`: any OpenAI-compatible chat API

One request per batch of lines, sent to `{BBILINGUAL_API_BASE}/chat/completions`. The model also
sees a few earlier lines of the same message, so terminology stays consistent.

| Service | `BBILINGUAL_API_BASE` |
|---|---|
| OpenAI | `https://api.openai.com/v1` |
| OpenRouter | `https://openrouter.ai/api/v1` |
| Poe | `https://api.poe.com/v1` |
| Ollama (local) | `http://localhost:11434/v1` |
| LM Studio (local) | `http://localhost:1234/v1` |
| vLLM, llama.cpp server, ... | the server's `/v1` URL |

The base URLs above are the services' documented defaults. The protocol was tested against Poe and
against a local stand-in server; the others speak the same protocol but check their documentation.

Pick a small, fast model: each batch of text waits for the translation before it appears. Check
the service's own model list for names. See [`examples/`](examples) for ready-made settings.

### `deepl`

One request per line to the DeepL API. Set `BBILINGUAL_API_KEY` (or `DEEPL_API_KEY`). Keys ending
in `:fx` use the free endpoint.

### `command`: your own backend

`BBILINGUAL_CMD` is run once per line, up to 8 at a time. The text arrives on standard input; print
the translation, and nothing else, on standard output. A non-zero exit status or empty output leaves
that line untranslated. The environment is inherited, so `BBILINGUAL_TARGET` tells your program the
language. [`examples/custom_backend.py`](examples/custom_backend.py) is a complete example that talks
to a LibreTranslate server.

## Languages

`BBILINGUAL_TARGET` takes a common code (`fr`, `de`, `es`, `pt`, `it`, `ru`, `ar`, `hi`, `vi`, `th`,
`id`, `tr`, `nl`, `pl`, `ja`, `ko`, `zh-CN`, `zh-TW`) or any language name your model understands
(for example `Swedish`). BBILINGUAL assumes Claude writes English.

For Chinese, Japanese and Korean the plugin also removes spaces between CJK characters and Latin
words or numbers, because Claude Code wraps lines at spaces and a stray space makes a long line break
early. Spaces that remain inside a translated line (between two English words, in `87.0 %`) become
no-break spaces for the same reason. Lines that are already mostly CJK are not translated again.

Use `BBILINGUAL_PROMPT_EXTRA` to steer the translator, for example:

```
BBILINGUAL_PROMPT_EXTRA="The text is about neuroscience. Translate 'spike' as 脉冲 and keep 'STDP' in English."
```

## Appearance

- Each translated line sits directly under its original, indented like it (bullets and numbered
  lists line up).
- A heading carries its translation on the same line: `## Results / 结果`.
- A table is shown in the original language as it arrives. When it ends, a complete translated table
  follows it.
- `BBILINGUAL_STYLE=gray` colours only the translation; the original keeps its normal colour. Colour
  is applied to paragraphs, bullets and headings but not inside tables: Claude Code mis-draws a table
  whose cells contain colour codes (see [how it works](docs/how-it-works.md)).

## Fonts for a better look

A terminal draws every character on a fixed grid, and a Chinese, Japanese or Korean character should
take exactly two cells, twice as wide as a Latin letter. If your font does not follow that rule,
table borders can drift sideways and lines look uneven. A font designed for it fixes both and
makes mixed text much nicer to read. Free, open-source (SIL Open Font License) options:

| Font | Notes | Download |
|---|---|---|
| **Sarasa Mono** | Latin and CJK built to the exact 1:2 grid. Pick the variant for your language: SC, TC, J or K | <https://github.com/be5invis/Sarasa-Gothic> |
| **Noto Sans Mono CJK** | Very complete coverage. Variants SC, TC, JP, KR | <https://fonts.google.com/noto> or <https://github.com/notofonts/noto-cjk> |
| **Maple Mono** | A programming font with CJK variants (look for the CN build) | <https://github.com/subframe7536/maple-font> |

Check each project's page for the current releases and variant names.

**Install, then select it in your terminal.** Install the font on the computer that draws the
terminal, not inside WSL or a remote server, and restart the terminal.

- **Windows Terminal** (also for WSL): Settings, then your profile, then Appearance, then Font face.
  It accepts several names separated by commas, and the later ones are used for characters the first
  one lacks, for example `Cascadia Mono, Microsoft YaHei UI`.
- **macOS Terminal or iTerm2**: Settings, Profiles, Text, Font. iTerm2 can also use a different font
  for non-ASCII text.
- **Linux, kitty, WezTerm, Alacritty**: set the font family in the terminal's settings or config file.

Pair the font with `BBILINGUAL_STYLE=gray` and the translation reads as a quiet second line under the
original. If you cannot or do not want to change fonts, nothing else needs to change.

## What is and is not translated

Translated: paragraphs, headings, bullets, numbered items, quotes, table cells that contain words.

Left alone: fenced code blocks, lines that are already in the target script (CJK targets), table
separator rows, cells without words such as numbers, and any line where the translator returns the
original unchanged. The translator itself decides what is worth translating, so a status line or
progress bar is translated or ignored depending on the model.

## Privacy and security

- **What is sent, and where.** The text of Claude's replies goes to the backend you configured, and to
  nowhere else. BBILINGUAL has no server, no telemetry and no analytics. A local backend (Ollama, LM
  Studio) keeps everything on your machine; a hosted API receives your text under its own terms.
- **What your replies may contain.** Replies can quote your code, file paths, error messages and
  secrets that Claude read. Choose a backend you trust with that, or better, a [local model](#use-a-local-model-recommended).
- **Temporary files.** While a message streams, a few small files holding recent text are kept in
  `$TMPDIR/bbilingual-<uid>` (mode 0700) and removed when the message ends; leftovers are pruned
  after an hour.
- **The log is off.** With `BBILINGUAL_LOG=1` every translated line is appended to
  `~/.cache/bbilingual/log.jsonl` (mode 0600, rotated at 5 MB) together with its original. That is
  your conversation text on disk: delete the file when you are done, and do not paste it in public
  issues.
- **API keys** are read from the environment and sent only to the configured API base. Do not commit
  a `settings.json` that contains a key.
- `BBILINGUAL_CMD` is run through the shell, with the same trust as anything else in your settings.

## Limitations

- **A line break inside a table cell is not possible** in Claude Code: `<br>` and the Unicode line
  separators are drawn literally or ignored. That is why the translation of a table is a second table.
- **Old messages are not translated.** The hook runs while a reply streams in. When you reopen a
  conversation with `claude -c` or `--resume`, earlier replies are redrawn from the transcript
  without it (checked with Claude Code 2.1.289).
- **Latency.** Each batch of lines appears after its translation is back, usually one to three
  seconds with a small model. A table is translated in one request when it ends.
- **A weak model can copy the English back** for a whole batch. BBilingual asks once more when most of
  a batch comes back unchanged, but a better model is the real fix.
- **Translation quality is your backend's.** Cheap models sometimes leave words untranslated or
  translate a term inconsistently. A better model, or `BBILINGUAL_PROMPT_EXTRA`, helps.
- Tested on Linux and WSL with Windows Terminal. Native Windows is untested.

## Troubleshooting

**Nothing is translated.** In the Claude Code window, run `! echo $BBILINGUAL_BACKEND`. It must print
a backend name. Settings are read when `claude` starts, so open a new session after changing them.
Run `/plugin` to check that BBILINGUAL is enabled.

**Try the hook by hand.** This prints the JSON Claude Code would receive back:

```bash
echo '{"index":0,"final":true,"message_id":"x","session_id":"s","delta":"Hello world.\n"}' \
  | BBILINGUAL_BACKEND=command BBILINGUAL_CMD="echo 你好世界" python3 scripts/bilingual.py
```

**Something looks wrong.** Start Claude Code with `BBILINGUAL_LOG=1`, reproduce it, then run
`python3 scripts/show_log.py --flagged` to see lines the plugin flagged (`no_translation`,
`same_as_english`, `no_cjk`, `english_left:...`). `python3 scripts/note.py "what looked wrong"` adds
a note next to the latest batch. When you open an issue, include only text you are happy to share.

## Development

```bash
python3 -m unittest discover -s tests -v     # about 25 seconds, no network
```

The hook is one file, [`scripts/bilingual.py`](scripts/bilingual.py), using only the standard
library. [`docs/how-it-works.md`](docs/how-it-works.md) explains the design and what was learned
about Claude Code's rendering. See [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

## Star history

<a href="https://star-history.com/#Ahorns/BBilingual&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=Ahorns/BBilingual&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=Ahorns/BBilingual&type=Date" />
    <img alt="Star history chart" src="https://api.star-history.com/svg?repos=Ahorns/BBilingual&type=Date" />
  </picture>
</a>

## License

[MIT](LICENSE)
