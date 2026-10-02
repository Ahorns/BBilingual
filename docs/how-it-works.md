# How BBilingual works

This page explains the design and records what was learned about how Claude Code draws text. The
findings come from using the plugin for real and from driving Claude Code in a pseudo-terminal while
reading the screen through a terminal emulator.

## 1. Display only

Claude Code's `MessageDisplay` hook runs while an assistant message streams in. It receives the new
text and may return `displayContent`, which replaces that text on screen. The transcript, the saved
history and what Claude sees keep the original. So:

- Claude answers in English throughout; it is never asked to translate or to write bilingual text.
- The translation can never leak back into the conversation.
- A failing hook is harmless: if it prints nothing, Claude Code shows the original.

The plugin therefore treats "do nothing" as the answer to every error.

## 2. Batches

The hook does not receive a whole message. Claude Code calls it for each batch of newly completed
lines, with `index` (position in the message) and `final` (last batch). In `claude -p` it is called
once per message with the full text.

Observed in practice (a day of normal use, about 220 batches):

- Batches are small: the median is one or two lines, and some carry thirty or more.
- The hook for batch *n + 1* can start before batch *n* has finished, and batches can finish out of
  order. State that depends on earlier batches (an open code fence, an open table) must therefore be
  handed over explicitly.

BBilingual does this with two small files per message in a private temp directory:

| State | Depends on | Saved | Next batch waits |
|---|---|---|---|
| open code fence, rows of an open table | the text only | right after classifying, before translating | up to 20 s (normally milliseconds) |
| recent (original, translation) pairs | translations | after translating | up to 4 s, then continues with older context |

Splitting them matters: a slow translation must never make a later batch lose track of a code fence,
and a late context update must never make the display wait.

## 3. What gets translated

Each line is classified before anything is sent: fenced code, blank lines, table rows, lines that are
already in the target script, and prose (with its bullet, number, quote or heading prefix split off, so
the translation can be indented to match).

All prose lines of a batch go to the model in one request, numbered `[1] ...`, together with up to six
earlier pairs from the same message as context. The reply is parsed by number: a translation the
model wrapped onto two lines is rejoined, and a number the model skipped leaves that line untranslated.
A translation that is identical to its original, or that is not in the target script for CJK targets,
is dropped, so lines like `PROGRESS ████ 85%` do not show up twice.

## 4. Layout

- **Bullets and numbered items:** the translation goes on the next line, indented to the text.
- **Headings:** Claude Code draws a blank line after a heading, so a translation on its own line would
  float away from it. It goes on the heading line instead: `## Results / 结果`.
- **Tables:** a table is shown as it arrives. When it ends, a complete translated table follows it.
  Putting both languages in one cell works, but Claude Code cannot break a line inside a cell (see 6).
- **Colour:** `BBILINGUAL_STYLE` wraps the translation of paragraphs, bullets and headings in ANSI codes. Claude Code ends bold, italic and
  code spans with a reset that also switches off dim and colour, so the style is applied again to each
  stretch of plain text between markers. The markers themselves are left outside the colour codes so
  markdown still parses (checked with a markdown parser).

## 5. Line wrapping for CJK

Claude Code wraps long lines itself, before the terminal sees them, and it breaks at ordinary spaces.
Translators put spaces around Latin words and numbers inside Chinese text (`与 VPR 的区别`). Each such
space turns the stretch after it into a "word" that jumps to the next line as a whole when it does not
fit, leaving a short line. Text with no spaces at all is cut at the full width instead.

Measured on one sample paragraph (width in terminal cells of each Chinese line):

| Terminal width | As the translator wrote it | Spaces next to CJK removed |
|---|---|---|
| 60 | 57, 45, 35, 57, 57, 42 | 58, 58, 57, 58, 54 |
| 100 | 98, 39, 93, 62 | 98, 97, 90 |

BBilingual removes spaces next to CJK characters, except next to markdown markers (`**bold** text`
needs the space to stay bold). Inserting spaces after Chinese punctuation, as an earlier version did,
made things worse.

## 6. What does not work in Claude Code (tested)

| Idea | Result |
|---|---|
| `<br>`, `<br/>`, `<br />` inside a table cell | drawn literally |
| `&#10;`, U+2028, U+2029, vertical tab, U+0085 inside a table cell | drawn literally or ignored; the cell stays one line |
| zero-width space, word joiner, soft hyphen as a wrap point | not a break point; wrapping happens at ASCII spaces only |
| colour codes inside table cells | Claude Code mis-draws the table: a wide one is printed as raw `\| a \| b \|` text, a narrow one has its bars shifted. Tables are therefore left uncoloured |
| a long CJK table cell with no spaces | fine: the cell is cut at the column width and the table stays a table |
| a table wider than the terminal | Claude Code switches to a vertical layout (`header: value` per row), which is readable |

## 7. Models that copy the English back

Small models occasionally return the original text for a whole batch (seen with a ten-row table).
Nothing useful can be shown, so when most lines of a batch of three or more come back unchanged the
request is repeated once with an explicit reminder, and the better of the two replies is used.

## 8. Method

The checks above were made by starting `claude` in a pseudo-terminal at a fixed size, sending a prompt
that makes it print the text under test, and reading the final screen with a terminal emulator
(`pyte`). That shows exactly which cell each character lands in. It reproduces Claude Code's layout, but
not a particular terminal's font or width rules; those can differ.
