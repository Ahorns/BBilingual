# Changelog

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
