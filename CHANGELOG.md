# Changelog

## Unreleased

- README: the demo on the English page now rotates through Chinese, Japanese, Korean and Spanish. The Chinese page has a
  Chinese banner and a Chinese how-it-works diagram, and a plainer tagline.

## 0.3.8 - 2026-10-06

- Input translation no longer loses a pasted text. Only the lines that are not English go to the model, and the rest
  of the message is kept exactly as written. (Some models returned just the translation of the foreign paragraph and
  dropped the pasted English.)
- The tests no longer pick up a real `DEEPSEEK_API_KEY` from the environment.

## 0.3.7 - 2026-10-06

- New `deepseek` backend (a preset of the OpenAI protocol): `BBILINGUAL_BACKEND=deepseek` and `DEEPSEEK_API_KEY` are
  enough. It uses `https://api.deepseek.com`, the model `deepseek-flash`, and switches DeepSeek's thinking off.
- `BBILINGUAL_EXTRA_BODY`: a JSON object merged into every request of the `openai` and `deepseek` backends, for
  services that need an extra field.

## 0.3.6 - 2026-10-05

- A message typed while Claude is still working is translated at once, and a line above the prompt shows its English
  while it waits in Claude Code's queue (the queue itself keeps showing what you typed).

## 0.3.5 - 2026-10-05

- Took back 0.3.4: fenced code blocks are never translated again, whatever their language tag.

## 0.3.3 - 2026-10-05

- `/bbinput confirm` is back as an optional mode: it shows the English and asks Send / Cancel before anything is sent.
  The default is unchanged (`on` sends at once; the public default is `off`).

## 0.3.2 - 2026-10-05

- `/bbilingual on | off` switches the translation under Claude's replies on or off inside Claude Code, without a
  restart, and remembers the choice (Claude Code 2.1.287 or newer).
- README: an animated demo of input translation (`assets/input-demo.svg`, and a Chinese-label version for the Chinese README).
- Repository: the generated `tsconfig.json` and `.claude-plugin/types/` that Claude Code writes next to a mod are ignored.

## 0.3.1 - 2026-10-05

- Input translation has no confirmation box any more: `/bbinput` is `on` or `off`. A message is sent as the English
  straight away, and a failed translation sends what you typed.

## 0.3.0 - 2026-10-05

- New, off by default: input translation. Type in your own language and Claude receives English
  (`/bbinput on | confirm | off`, `BBILINGUAL_INPUT`). It uses Claude Code's mods API (2.1.287 or newer),
  which is early access, and the `openai` backend. See `docs/reference.md`.
- README: a short front page; settings, backends, fonts, privacy and troubleshooting moved to
  `docs/reference.md` (and `docs/reference.zh-CN.md`).
- README: banner, animated demo, a real-session screenshot, how-it-works diagram, feature cards, quick start and a comparison table.
  Short README pages in Japanese, Korean and Spanish (`docs/translations/`) next to the Chinese one, each
  with a demo that shows its own language. A social preview image (`assets/social-preview.png`).
- CJK translations: spaces left inside a line become no-break spaces, so Claude Code no longer breaks the
  line early before a long chunk (code spans are left alone).

## 0.2.0 - first public release

- Display-only translation of Claude Code's assistant messages through the `MessageDisplay` hook.
  The transcript and Claude's context are never changed.
- Bring your own backend: any OpenAI-compatible chat endpoint (`openai`), DeepL (`deepl`), or your
  own program (`command`). Nothing is sent anywhere until a backend is configured.
- Any target language (`BBILINGUAL_TARGET`), with extra handling for Chinese, Japanese and Korean.
- Per-batch requests with the surrounding lines as context, so terminology stays consistent.
- Code blocks are never translated. Headings, bullets, quotes and tables keep their layout; a
  translated table follows the original one.
- Batches that Claude Code starts out of order are handled (code fences and tables are tracked
  across batches).
- Optional colour for the translated text (`BBILINGUAL_STYLE`); not applied inside tables, where it
  confuses Claude Code's table layout.
- A batch the model copies back unchanged is retried once.
- Optional local log of English/translation pairs with automatic problem flags (`BBILINGUAL_LOG=1`),
  plus `scripts/show_log.py` and `scripts/note.py`. Off by default.
