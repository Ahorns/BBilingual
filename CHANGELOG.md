# Changelog

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
