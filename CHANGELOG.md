# Changelog

## 0.3.4 - 2026-10-05

- Plain-text blocks are translated: a fenced block with no language (or `text`), such as a diagram, gets a translation
  under each line that reads like an English sentence. Blocks with a language tag are still never translated.

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
