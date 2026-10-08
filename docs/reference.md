# BBilingual reference

**English** | [简体中文](reference.zh-CN.md)

Everything beyond the [quick start](../README.md#quick-start): installing, every setting, backends, local
models, languages, fonts, privacy, limitations and troubleshooting.

[Install](#install) · [Configure](#configure) · [Use a local model](#use-a-local-model-recommended) · [Backends](#backends) ·
[Write in your own language](#write-in-your-own-language) · [Languages](#languages) · [Appearance](#appearance) · [Fonts](#fonts-for-a-better-look) ·
[What is and is not translated](#what-is-and-is-not-translated) · [Privacy](#privacy-and-security) ·
[Limitations](#limitations) · [Troubleshooting](#troubleshooting) · [Development](#development)

## Install

Requirements: a Claude Code version that has the `MessageDisplay` hook (tested with 2.1.285 to
2.1.289), Python 3.9 or newer (standard library only; developed on 3.12, CI runs 3.9 to 3.12),
Linux, macOS, or Windows with WSL.

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
| `BBILINGUAL_BACKEND` | `openai`, `deepseek`, `deepl` or `command` | not set: the plugin does nothing |
| `BBILINGUAL_TARGET` | Target language: a code (`fr`, `ja`, `zh-CN`, `zh-TW`, `pt`, ...) or a name | `zh-CN` |
| `BBILINGUAL_MODEL` | Model name | needed for `openai`; `deepseek` has a default |
| `BBILINGUAL_API_BASE` | Base URL of the chat API | `https://api.openai.com/v1` |
| `BBILINGUAL_API_KEY` | API key (optional for local servers; DeepL also reads `DEEPL_API_KEY` and DeepSeek `DEEPSEEK_API_KEY`) | none |
| `BBILINGUAL_CMD` | Command for the `command` backend | needed for `command` |
| `BBILINGUAL_PROMPT_EXTRA` | Extra instructions for the model: domain, glossary, tone | none |
| `BBILINGUAL_TEMPERATURE` | Sent only if set (some models reject anything but their default) | not sent |
| `BBILINGUAL_EXTRA_BODY` | A JSON object merged into every chat request, for services that need an extra field, for example `{"thinking": {"type": "disabled"}}`. It cannot replace the model or the messages | none |
| `BBILINGUAL_STYLE` | Colour for the translated text: `dim`, `italic`, `gray`, `cyan`, `green`, `yellow` | plain |
| `BBILINGUAL_INPUT` | Starting value of [input translation](#write-in-your-own-language): `on`, `confirm` or `off` (`/bbinput` overrides it) | `off` |
| `BBILINGUAL_LOG` | `1` records English/translation pairs locally (see [Privacy](#privacy-and-security)) | off |
| `BBILINGUAL_DISABLE` | `1` switches the hook off, for one session or for good | off |

To switch BBILINGUAL off for a single conversation, start it with `BBILINGUAL_DISABLE=1 claude`. Inside Claude Code,
`/bbilingual off` switches the translation under Claude's replies off straight away (no restart) and
`/bbilingual on` switches it back on; the choice is remembered. `/bbilingual` alone shows the current setting.
The command needs Claude Code 2.1.287 or newer, like `/bbinput`.

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
| DeepSeek | `https://api.deepseek.com` (or use the [`deepseek`](#deepseek) preset) |
| Ollama (local) | `http://localhost:11434/v1` |
| LM Studio (local) | `http://localhost:1234/v1` |
| vLLM, llama.cpp server, ... | the server's `/v1` URL |

The base URLs above are the services' documented defaults. The protocol was tested against Poe and
against a local stand-in server; the others speak the same protocol but check their documentation.

Pick a small, fast model: each batch of text waits for the translation before it appears. Check
the service's own model list for names. See [`examples/`](../examples) for ready-made settings.

### `deepseek`

A preset for the DeepSeek API: set `BBILINGUAL_BACKEND=deepseek` and `DEEPSEEK_API_KEY` (or `BBILINGUAL_API_KEY`)
and nothing else. It uses `https://api.deepseek.com` and the model `deepseek-flash`, and switches thinking off:
DeepSeek's models think before they answer by default, which makes a translation slow and uses more tokens.
`BBILINGUAL_MODEL`, `BBILINGUAL_API_BASE` and `BBILINGUAL_EXTRA_BODY` still win when you set them. Model names
change, so check DeepSeek's documentation. Your text goes to DeepSeek's servers, under its terms. Ready-made
settings: [`examples/settings-deepseek.json`](../examples/settings-deepseek.json).

### `deepl`

One request per line to the DeepL API. Set `BBILINGUAL_API_KEY` (or `DEEPL_API_KEY`). Keys ending
in `:fx` use the free endpoint.

### `command`: your own backend

`BBILINGUAL_CMD` is run once per line, up to 8 at a time. The text arrives on standard input; print
the translation, and nothing else, on standard output. A non-zero exit status or empty output leaves
that line untranslated. The environment is inherited, so `BBILINGUAL_TARGET` tells your program the
language. [`examples/custom_backend.py`](../examples/custom_backend.py) is a complete example that talks
to a LibreTranslate server.

## Write in your own language

The display hook translates Claude's English into your language. The input feature does the opposite for
what you type: text that is not plain English is translated into English before Claude receives it, so
you can write your prompts in your own language. The conversation then shows the English that Claude
received; your original is not kept there.

It is off until you turn it on. Switch it with the `/bbinput` command, which remembers your choice
across sessions:

| Command | Effect |
|---|---|
| `/bbinput on` | translate and send the English straight away |
| `/bbinput confirm` | show the English first and ask Send / Cancel (text typed under "Other" is sent instead) |
| `/bbinput off` | do nothing (the default) |
| `/bbinput` | show the current setting |

`BBILINGUAL_INPUT` (`on`, `confirm` or `off`) sets the starting value, and `/bbinput` overrides it. In `on` mode there
is no pop-up and no question: you see your message in the chat as the English that Claude received.

- **What is translated:** text with letters that are not plain English: Chinese, Japanese, Korean,
  Cyrillic, Arabic, Hebrew, Indic scripts, Thai or accented Latin letters. The model is told to keep
  code, file paths, @-mentions, URLs and technical terms as written.
- **Pasted text:** only the lines that are not English are translated. A pasted English text, log or code stays word
  for word, and the translation of your own Chinese paragraph is put in its place.
- **What is not:** plain English, slash commands (`/...`), shell lines (`!...`) and pastes over 4000
  characters pass through unchanged.
- **When it fails:** if the translation fails or comes back unchanged, what you typed is sent as it is
  (in `confirm` mode you are asked first).
- **While Claude is still working:** a message you type then waits in Claude Code's queue exactly as you typed
  it (Claude Code shows that list itself and a plugin cannot change it). It is translated at once, and a line above
  the prompt, "Waiting to be sent, as English", shows the English until Claude's turn ends.
- **Backend:** it needs the `openai` backend (any OpenAI-compatible API or a local model), with the same
  model, key and base URL as the display hook. `deepl` and `command` cannot translate into English here.
- **Privacy:** what you type is sent to your translator, as Claude's replies are. A [local model](#use-a-local-model-recommended) keeps it on your machine.
- **Requirements:** Claude Code 2.1.287 or newer. It uses Claude Code's mods API, which Anthropic
  describes as early access and which may change. The display translation uses the regular hook API.

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
  whose cells contain colour codes (see [how it works](how-it-works.md)).

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
- **What you type.** With [input translation](#write-in-your-own-language) on, what you type (when it is not plain
  English) is also sent to the backend, and nothing else is. It is off by default.
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

**Input is not translated.** Type `/bbinput` to see the setting; it must say `on` or `confirm`. It only
acts on text with non-English letters, needs the `openai` backend, and needs Claude Code 2.1.287 or newer.
Try the translator by hand: `echo '你好' | python3 scripts/to_english.py`.

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

The hook is one file, [`scripts/bilingual.py`](../scripts/bilingual.py), using only the standard
library. [`docs/how-it-works.md`](how-it-works.md) explains the design and what was learned
about Claude Code's rendering. See [CONTRIBUTING.md](../CONTRIBUTING.md) before opening a pull request.
