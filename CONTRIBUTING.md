# Contributing

Thanks for helping. BBilingual is small on purpose: one hook file with no dependencies, so that anyone
who lets it see their conversations can read all of it in a few minutes.

## Ground rules

- **Fail open.** If anything goes wrong the hook must print nothing, so Claude Code shows the original
  text. Never raise, and never print partial output.
- **Private by default.** Nothing is sent anywhere or written to disk beyond temporary state unless the
  user turned it on. New features that store or send text need a switch that is off by default and a
  line in the README's privacy section.
- **No dependencies.** Standard library only, Python 3.9 or newer.
- **Backend-neutral.** The plugin must not assume one provider. Provider names appear only in
  documentation examples.
- **Language-neutral.** Anything specific to Chinese, Japanese or Korean is guarded by
  `TARGET_IS_CJK`.

## Development

```bash
python3 -m unittest discover -s tests -v
```

The tests start the hook as a subprocess, as Claude Code does. A fake OpenAI-compatible server stands
in for the network. Please add a test for every behaviour you change, and for every bug you fix.

To try changes in a real session:

```bash
claude --plugin-dir /path/to/your/clone
```

After editing a plugin that is installed from a marketplace, bump `version` in
`.claude-plugin/plugin.json` and run `claude plugin update`, because Claude Code runs a cached copy.

## Translating the README

`README.zh-CN.md` is the full Chinese README. Other languages live in `docs/translations/` as short
landing pages (what it is, why, quick start, things to know) that link to the English README for the
details. To add one, copy `docs/translations/README.es.md`, translate it, set `BBILINGUAL_TARGET` in the
quick start to your language code, and add the language to the switch line at the top of every README.
Say in the page whether it was translated by a person or by an AI, and have a native speaker read it if
you can.

## Reporting bugs

Use the issue template. The most useful report has the English text, what you expected and a screenshot
of what you saw. The log file contains your conversation: share only what you are comfortable with.

## Pull requests

- Keep them focused and explain the why.
- Run the tests. CI runs them on Python 3.9 to 3.12.
- Update `README.md` and `CHANGELOG.md` when behaviour or settings change.
