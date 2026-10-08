#!/usr/bin/env python3
"""BBilingual: a Claude Code MessageDisplay hook that shows a translation under English text.

The hook reads one MessageDisplay event on stdin and prints
{"hookSpecificOutput": {"hookEventName": "MessageDisplay", "displayContent": ...}}.
displayContent is the original text with the translation added. It changes only what is drawn on
screen: the transcript and Claude's context are never touched, so Claude keeps working in English.
If anything goes wrong the hook prints nothing and Claude Code shows the original text.

Nothing happens until a backend is configured (BBILINGUAL_BACKEND). Settings are environment
variables, so they can live in your shell or in the "env" block of ~/.claude/settings.json:

  BBILINGUAL_BACKEND    openai | deepseek | deepl | command        (required)
  BBILINGUAL_TARGET     target language, a code (fr, ja, zh-CN) or a name   (default zh-CN)
  BBILINGUAL_MODEL      model name                       (openai)
  BBILINGUAL_API_BASE   base URL                         (openai; default https://api.openai.com/v1)
  BBILINGUAL_API_KEY    API key                          (openai, deepseek, deepl; optional for local servers)
  BBILINGUAL_CMD        command: text on stdin, translation on stdout   (command)
  BBILINGUAL_PROMPT_EXTRA  extra instructions for the model (domain, glossary, tone)   (openai)
  BBILINGUAL_EXTRA_BODY    JSON object merged into every chat request, e.g. to switch thinking off   (openai)
  BBILINGUAL_STYLE      colour for the translated text: dim|italic|gray|cyan|green|yellow
  BBILINGUAL_LOG        1 to record English/translation pairs in ~/.cache/bbilingual/log.jsonl
  BBILINGUAL_DISABLE    1 to switch the hook off

See README.md for details and examples.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor


def env(name, default=""):
    return os.environ.get(name, default)


TARGET = env("BBILINGUAL_TARGET", "zh-CN")
BACKEND_TIMEOUT = 25   # seconds; the hook's own timeout is 60 (hooks/hooks.json)
FENCE_WAIT = 20        # seconds a batch waits for the previous batch's code-fence state
CTX_WAIT = 4           # seconds it waits for the previous batch's translations (context only)
CONTEXT_LINES = 6      # earlier (English, translation) pairs sent along for consistent terminology
STATE_DIR = os.path.join(tempfile.gettempdir(), "bbilingual-%d" % getattr(os, "getuid", lambda: 0)())
LOG_PATH = env("BBILINGUAL_LOG_FILE") or os.path.join(
    env("XDG_CACHE_HOME") or os.path.expanduser("~/.cache"), "bbilingual", "log.jsonl")

LANG_NAMES = {
    "zh-CN": "Simplified Chinese", "zh-TW": "Traditional Chinese", "ja": "Japanese", "ko": "Korean",
    "fr": "French", "de": "German", "es": "Spanish", "pt": "Portuguese", "it": "Italian",
    "ru": "Russian", "ar": "Arabic", "hi": "Hindi", "vi": "Vietnamese", "th": "Thai",
    "id": "Indonesian", "tr": "Turkish", "nl": "Dutch", "pl": "Polish",
}
CJK_RE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]")
# Chinese, Japanese and Korean need special care: no spaces between words, wide characters.
TARGET_IS_CJK = TARGET.lower()[:2] in ("zh", "ja", "ko") or any(
    n in TARGET.lower() for n in ("chinese", "japanese", "korean"))

FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
BULLET_RE = re.compile(r"^(\s*(?:[-*+•]|\d+[.)])\s+)(.*)$")
HEADING_RE = re.compile(r"^(#{1,6}\s+)(.*)$")
QUOTE_RE = re.compile(r"^(\s*>\s?)(.*)$")


# ------------------------------------------------------------------- logging
# Opt-in (BBILINGUAL_LOG=1). Each batch is recorded with its English/translation pairs and any
# problems found, so bugs can be reviewed later: python3 scripts/show_log.py [--flagged].

def plugin_version():
    try:
        manifest = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".claude-plugin", "plugin.json")
        with open(manifest, encoding="utf-8") as f:
            return json.load(f)["version"]
    except Exception:
        return "?"


def log(**kw):
    if env("BBILINGUAL_LOG") != "1":
        return
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        if os.path.exists(LOG_PATH) and os.path.getsize(LOG_PATH) > 5_000_000:
            os.replace(LOG_PATH, LOG_PATH + ".old")
        entry = dict(t=time.strftime("%Y-%m-%d %H:%M:%S"), v=plugin_version(), **kw)
        fd = os.open(LOG_PATH, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)   # private: it holds your text
        with os.fdopen(fd, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass


def problems(en, tr):
    """Cheap automatic checks on one translated line."""
    if not tr:
        return ["no_translation"]
    found = []
    if tr.strip() == en.strip():
        found.append("same_as_english")
    if TARGET_IS_CJK:
        if not CJK_RE.search(tr):
            found.append("no_cjk")
        plain = re.sub(r"`[^`]*`|\([^)]*\)|（[^）]*）", "", tr)        # ignore code and bracketed glosses
        left = re.findall(r"(?<![\w/])[a-z]{5,}(?![\w/])", plain)       # lowercase words only: names are fine
        if len(left) >= 3:
            found.append("english_left:" + ",".join(left[:5]))
    return found


# ------------------------------------------------------------------ backends
# openai   one request per batch to any OpenAI-compatible chat endpoint (OpenAI, OpenRouter, Poe,
#          Ollama, LM Studio, vLLM, ...). It sees the surrounding lines, so terms stay consistent.
# deepl    one request per line to the DeepL API.
# command  your own program, run once per line: text on stdin, translation on stdout.

def http_json(url, payload, headers=None):
    hdrs = {"Content-Type": "application/json"}
    hdrs.update(headers or {})
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=hdrs)
    with urllib.request.urlopen(req, timeout=BACKEND_TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8"))


def system_prompt():
    lang = LANG_NAMES.get(TARGET, TARGET)
    prompt = ("You translate technical text from English into %s for a reader who sees the English "
              "original right next to your translation. Use the standard terminology of the field and "
              "keep it consistent with the earlier lines you are shown. Keep code, file paths, "
              "identifiers, acronyms and technical terms in English, and keep markdown markers such "
              "as ** and backticks. Write math symbols and Greek letters as plain Unicode "
              "characters, never as LaTeX. The input is numbered lines like `[1] text`. Reply with one "
              "translated line per input line, using the same `[n]` numbers, and nothing else." % lang)
    extra = env("BBILINGUAL_PROMPT_EXTRA")
    return prompt + (" " + extra if extra else "")


def extra_body():
    """The JSON object in BBILINGUAL_EXTRA_BODY (extra request fields some services need), or {}."""
    raw = env("BBILINGUAL_EXTRA_BODY")
    value = json.loads(raw) if raw else {}
    if not isinstance(value, dict):
        raise ValueError("BBILINGUAL_EXTRA_BODY must be a JSON object")
    return value


# A service that speaks the OpenAI protocol can be a preset: BBILINGUAL_BACKEND=<name> and its key are enough.
# The preset only fills in what you leave unset: BBILINGUAL_API_BASE, BBILINGUAL_MODEL, BBILINGUAL_API_KEY and
# BBILINGUAL_EXTRA_BODY all still win.
PRESETS = {"deepseek": {"base": "https://api.deepseek.com", "model": "deepseek-flash", "key": "DEEPSEEK_API_KEY",
                        "extra": {"thinking": {"type": "disabled"}}}}   # thinking is on by default there: slow


def chat_openai(system, user, preset=None):
    p = PRESETS.get(preset, {})
    base = (env("BBILINGUAL_API_BASE") or p.get("base") or "https://api.openai.com/v1").rstrip("/")
    payload = dict(p.get("extra", {}), **extra_body())
    payload.update(model=env("BBILINGUAL_MODEL") or p.get("model"),
                   messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])
    if env("BBILINGUAL_TEMPERATURE"):    # some models reject anything but their default
        payload["temperature"] = float(env("BBILINGUAL_TEMPERATURE"))
    key = env("BBILINGUAL_API_KEY") or env(p.get("key", ""))
    resp = http_json(base + "/chat/completions", payload, {"Authorization": "Bearer " + key} if key else {})
    return resp["choices"][0]["message"]["content"].strip()


def chat_deepseek(system, user):
    return chat_openai(system, user, "deepseek")


def tr_deepl(text):
    key = env("BBILINGUAL_API_KEY") or env("DEEPL_API_KEY")
    host = "api-free.deepl.com" if key.endswith(":fx") else "api.deepl.com"
    target = {"zh-CN": "ZH-HANS", "zh-TW": "ZH-HANT"}.get(TARGET, TARGET.upper())
    resp = http_json("https://%s/v2/translate" % host,
                     {"text": [text], "source_lang": "EN", "target_lang": target},
                     {"Authorization": "DeepL-Auth-Key " + key})
    return resp["translations"][0]["text"].strip()


def tr_command(text):
    out = subprocess.run(env("BBILINGUAL_CMD"), shell=True, input=text, encoding="utf-8",
                         capture_output=True, timeout=BACKEND_TIMEOUT, check=True)
    return out.stdout.strip()


def tr_mock(text):    # for the test suite
    return "【译】" + text


LLM_BACKENDS = {"openai": chat_openai, "deepseek": chat_deepseek}            # one request per batch
LINE_BACKENDS = {"deepl": tr_deepl, "command": tr_command, "mock": tr_mock}   # one request per line


def configure():
    """Return (backend, problem). backend is None when the hook should do nothing."""
    name = env("BBILINGUAL_BACKEND").lower()
    if not name:
        return None, "BBILINGUAL_BACKEND is not set"
    if name not in LLM_BACKENDS and name not in LINE_BACKENDS:
        return None, "unknown backend '%s' (use openai, deepseek, deepl or command)" % name
    needs = {"openai": "BBILINGUAL_MODEL", "command": "BBILINGUAL_CMD"}.get(name)
    if needs and not env(needs):
        return None, "%s is not set" % needs
    if name == "deepl" and not (env("BBILINGUAL_API_KEY") or env("DEEPL_API_KEY")):
        return None, "BBILINGUAL_API_KEY is not set"
    if name in PRESETS and not (env("BBILINGUAL_API_KEY") or env(PRESETS[name]["key"])):
        return None, "%s is not set" % PRESETS[name]["key"]
    if name == "openai" or name in PRESETS:
        try:
            extra_body()
        except ValueError:      # includes json.JSONDecodeError
            return None, "BBILINGUAL_EXTRA_BODY is not a JSON object"
    return name, None


def translate_line(backend, text):
    try:
        return LINE_BACKENDS[backend](text) or None
    except Exception:
        return None


def parse_numbered(reply, count):
    """Read '[n] text' lines from a reply; a translation the model wrapped onto two lines is rejoined."""
    found, cur = {}, None
    for ln in (reply or "").splitlines():
        m = re.match(r"\s*\[(\d+)\]\s?(.*)$", ln)
        if m:
            cur = int(m.group(1))
            found[cur] = m.group(2).strip()
        elif cur and ln.strip():
            found[cur] += " " + ln.strip()
    return [found.get(i + 1) or None for i in range(count)]


def translate_llm(backend, lines, ctx):
    """One request for all lines of a batch, with earlier lines of the message as context."""
    user = ""
    if ctx:
        user += "Earlier lines of this message, for context and consistent terminology only (do not translate):\n"
        user += "\n".join("%s\n%s" % (en, tr) for en, tr in ctx) + "\n\n"
    user += "Translate these lines:\n" + "\n".join("[%d] %s" % (i + 1, l) for i, l in enumerate(lines))

    def ask(prompt):
        reply = LLM_BACKENDS[backend](system_prompt(), prompt)
        return parse_numbered(reply, len(lines)), reply

    def good(result):
        return sum(1 for en, tr in zip(lines, result) if tr and usable(en, tr))

    try:
        result, reply = ask(user)
    except Exception as e:
        log(event="error", backend=backend, error=repr(e)[:300])
        return [None] * len(lines)
    # Small models sometimes copy the English back for a whole batch (seen with a table). Ask once more.
    if len(lines) >= 3 and good(result) * 5 <= len(lines) * 2:
        log(event="retry", asked=len(lines), usable=good(result))
        try:
            again, _ = ask(user + "\n\nYour previous reply repeated the original text. Translate every line "
                           "into %s. Do not copy the English." % LANG_NAMES.get(TARGET, TARGET))
            if good(again) > good(result):
                result = again
        except Exception as e:
            log(event="error", backend=backend, error=repr(e)[:300])
    if not all(result):
        log(event="missing", asked=len(lines), got=sum(1 for r in result if r), reply=(reply or "")[:1000])
    return result


def translate_batch(backend, lines, ctx):
    """Translate prose lines; None for a line means 'leave it alone'."""
    if backend in LLM_BACKENDS:
        return translate_llm(backend, lines, ctx)
    with ThreadPoolExecutor(max_workers=min(8, len(lines))) as pool:
        return list(pool.map(lambda l: translate_line(backend, l), lines))


# ------------------------------------------------------------- message state
# Claude Code can start the hook for batch n+1 before batch n has finished, so batches hand state
# to each other through small files in a private temp directory (removed when the message ends):
#   fence: the open code fence and any table still open. It depends only on the text, so it is
#          saved straight after classifying and the next batch waits for it (fast), whatever the
#          translations take.
#   ctx:   the recent (English, translation) pairs. Saved after translating; the next batch waits
#          for it only briefly, because slightly stale context beats a slow display.

def state_path(message_id):
    return os.path.join(STATE_DIR, hashlib.sha1(message_id.encode()).hexdigest())


def read_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def write_json(path, data):
    try:
        os.makedirs(STATE_DIR, mode=0o700, exist_ok=True)
        tmp = "%s.%d" % (path, os.getpid())
        with open(tmp, "w") as f:
            json.dump(data, f)
        os.replace(tmp, path)   # atomic: a waiting batch never reads a half-written file
    except OSError:
        pass


def wait_for(path, key, want, timeout):
    """Wait until the state file says key == want (the previous batch has handed over)."""
    deadline = time.time() + timeout
    while True:
        st = read_json(path)
        if st.get(key) == want or time.time() > deadline:
            return st
        time.sleep(0.02)


def fence_path(message_id):
    return state_path(message_id) + ".fence"


def ctx_path(message_id):
    return state_path(message_id) + ".ctx"


def load_fence(message_id, index):
    """(open code fence, rows of a table still open) left by the previous batch."""
    if index == 0:
        return None, None
    st = wait_for(fence_path(message_id), "cls", index - 1, FENCE_WAIT)
    return st.get("fence"), st.get("table")


def save_fence(message_id, fence, table, index):
    write_json(fence_path(message_id), {"fence": fence, "table": table, "cls": index})


def load_ctx(message_id, index):
    if index == 0:
        return []
    st = wait_for(ctx_path(message_id), "tr", index - 1, CTX_WAIT)
    return [tuple(pair) for pair in st.get("ctx", [])]


def save_ctx(message_id, ctx, index):
    if read_json(ctx_path(message_id)).get("tr", -1) < index:   # never go back to older context
        write_json(ctx_path(message_id), {"tr": index, "ctx": ctx})


def finish_message(message_id):
    for p in (fence_path(message_id), ctx_path(message_id)):
        try:
            os.remove(p)
        except OSError:
            pass


def prune_state(max_age=3600):
    """Remove leftovers of messages that never got a final batch."""
    try:
        for name in os.listdir(STATE_DIR):
            path = os.path.join(STATE_DIR, name)
            if time.time() - os.path.getmtime(path) > max_age:
                os.remove(path)
    except OSError:
        pass


def first_notice(session_id):
    """True exactly once per session (used for the 'not configured' hint)."""
    p = os.path.join(STATE_DIR, "notice-" + hashlib.sha1(session_id.encode()).hexdigest())
    if os.path.exists(p):
        return False
    try:
        os.makedirs(STATE_DIR, mode=0o700, exist_ok=True)
        open(p, "w").close()
    except OSError:
        pass
    return True


# -------------------------------------------------------------------- render

def mostly_cjk(line):
    """Already in the target script: more CJK characters than Latin letters (CJK targets only)."""
    if not TARGET_IS_CJK:
        return False
    cjk = len(CJK_RE.findall(line))
    return cjk > 0 and cjk * 3 >= len(re.findall(r"[A-Za-z]", line))


def classify(lines, fence):
    """Yield (line, prefix_width, body, fence_after); body is translatable prose or None."""
    for raw in lines:
        line = raw.rstrip("\r\n")
        m = FENCE_RE.match(line)
        if fence:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) \
                    and line.strip() == m.group(1):
                fence = None
            yield line, 0, None, fence
            continue
        if m:
            fence = m.group(1)
            yield line, 0, None, fence
            continue
        if not line.strip() or mostly_cjk(line) or line.lstrip().startswith("|"):
            yield line, 0, None, fence
            continue
        for rx in (BULLET_RE, HEADING_RE, QUOTE_RE):
            b = rx.match(line)
            if b:
                yield line, len(b.group(1)), b.group(2), fence
                break
        else:
            yield line, len(line) - len(line.lstrip()), line.strip(), fence


STYLES = {"dim": ("\x1b[2m", "\x1b[22m"), "italic": ("\x1b[3m", "\x1b[23m"),
          "gray": ("\x1b[90m", "\x1b[39m"), "cyan": ("\x1b[36m", "\x1b[39m"),
          "green": ("\x1b[32m", "\x1b[39m"), "yellow": ("\x1b[33m", "\x1b[39m")}
SPAN_RE = re.compile(r"(`[^`]*`|\*\*|\*|~~)")   # code spans and markdown markers


def style(text):
    """Optional colour for the translated text (BBILINGUAL_STYLE).

    Claude Code resets the effect at the end of every bold/italic/code span, so the style is applied
    again to each piece of plain text between the markers (the markers themselves stay untouched).
    """
    codes = STYLES.get(env("BBILINGUAL_STYLE"))
    if not codes:
        return text
    on, off = codes
    parts = SPAN_RE.split(text)
    return "".join(p if i % 2 or not p.strip() else on + p + off for i, p in enumerate(parts))


# Claude Code wraps lines at normal spaces. A space in the middle of CJK text (translators put them
# around Latin words and numbers) makes the next stretch jump to the next line as one block, leaving
# a short line. Without such spaces long lines fill the whole width. So remove them, but keep a space
# next to a markdown marker (`**bold**` needs it to stay bold).
CJK = r"[\u3000-\u30ff\u3400-\u9fff\uac00-\ud7af\uff00-\uffef]"
NEXT_TO_CJK = re.compile(r"(?<=%s) +(?=[^\s*_`~])|(?<=[^\s*_`~]) +(?=%s)" % (CJK, CJK))


def tighten(text):
    return NEXT_TO_CJK.sub("", text) if TARGET_IS_CJK else text


def unbreakable(text):
    """Claude Code wraps only at ordinary spaces and moves a long chunk whole to the next line, so a
    space left inside a CJK line (between English words, in "87.0 %") makes an early break. A no-break
    space keeps the line in one piece. Code spans stay as they are, so copied commands still work."""
    if not TARGET_IS_CJK:
        return text
    return "".join(part if part.startswith("`") else part.replace(" ", "\u00a0")
                   for part in re.split(r"(`[^`]*`)", text))


def usable(en, tr):
    """A translation is shown only if it differs from the English (and is CJK for CJK targets)."""
    return bool(tr) and tr.strip() != en.strip() and (not TARGET_IS_CJK or bool(CJK_RE.search(tr)))


# ------------------------------------------------------------------- tables
# A table is shown as it arrives, in the original language. When it ends (a line that is not a table
# row, or the end of the message) a complete translated table follows it. Claude Code cannot put a
# line break inside a cell: <br> and the Unicode line separators were tested and are not honoured.

def split_cells(row):
    """Cells of a markdown table row; pipes inside code spans or escaped as \\| do not split."""
    row = row.strip()
    cells, cur, in_code, i = [], [], False, 0
    while i < len(row):
        ch = row[i]
        if ch == "\\" and row[i + 1:i + 2] == "|":
            cur.append("\\|")
            i += 2
            continue
        if ch == "`":
            in_code = not in_code
        if ch == "|" and not in_code:
            cells.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
        i += 1
    cells.append("".join(cur))
    if cells and not cells[0].strip():
        cells = cells[1:]
    if cells and not cells[-1].strip():
        cells = cells[:-1]
    return [c.strip() for c in cells]


def is_separator(cells):
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", c) for c in cells)


def cell_translatable(text):
    return bool(re.search(r"[A-Za-z]{2,}", text)) and not is_separator([text]) and not mostly_cjk(text)


def track_tables(items, table, final):
    """Follow tables through a batch. Returns the table still open at the end of the batch (its rows
    so far) and the tables that ended: [(position in items to insert before, rows)]."""
    ended = []
    for i, (line, _, body, fence_after) in enumerate(items):
        if body is None and fence_after is None and line.lstrip().startswith("|"):
            table = (table or []) + [split_cells(line)]
        elif table is not None:
            ended.append((i, table))
            table = None
    if final and table is not None:
        ended.append((len(items), table))
        table = None
    return table, [(pos, rows) for pos, rows in ended if len(rows) >= 2 and is_separator(rows[1])]


# No colour inside tables. Claude Code lays a table out from the text it receives, and colour codes in the
# cells confuse it: wide tables were printed as raw "| a | b |" text and narrow ones had their bars
# shifted. The translated table is plain; it is still a separate table under the original.
def translated_table(rows, results, tid):
    """The translated copy of a table: translated cells where there are any, the original elsewhere."""
    lines, any_tr = [], False
    for r, cells in enumerate(rows):
        shown = []
        for c, t in enumerate(cells):
            tr = results.get((tid, r, c))
            any_tr = any_tr or bool(tr)
            shown.append(tighten(tr) if tr else t)
        lines.append("| " + " | ".join(shown) + " |")
    return lines if any_tr else []


def render(delta, message_id, final, backend, index=0, session_id=""):
    fence, table = load_fence(message_id, index)
    items = list(classify(delta.splitlines(keepends=True), fence))
    table, ended = track_tables(items, table, final)
    save_fence(message_id, items[-1][3] if items else fence, table, index)   # hand over before the slow part
    ctx = load_ctx(message_id, index)
    t0 = time.time()

    # everything to translate in this batch: prose lines and the cells of tables that just ended
    jobs = [(i, body) for i, (_, _, body, _) in enumerate(items)
            if body is not None and re.search(r"[A-Za-z]{2,}", body)]
    for tid, (_, rows) in enumerate(ended):
        jobs += [((tid, r, c), t) for r, cells in enumerate(rows) if r != 1
                 for c, t in enumerate(cells) if cell_translatable(t)]
    raw = {}
    if jobs:
        raw = {key: tr for (key, _), tr in zip(jobs, translate_batch(backend, [t for _, t in jobs], ctx))}
    english = dict(jobs)
    results = {k: tr.replace("|", "/") for k, tr in raw.items() if usable(english[k], tr)}
    ctx = (ctx + [(english[k], tr) for k, tr in results.items()])[-CONTEXT_LINES:]

    blocks = {}                                  # position -> translated table lines to insert before it
    for tid, (pos, rows) in enumerate(ended):
        block = translated_table(rows, results, tid)
        if block:
            blocks[pos] = [""] + block + ([""] if pos < len(items) and items[pos][0].strip() else [])

    out_lines = []
    for i, (line, width, body, _) in enumerate(items):
        out_lines += blocks.get(i, [])
        out_lines.append(line)
        tr = results.get(i)
        if tr and HEADING_RE.match(line):       # headings get a blank line after them: keep it on one line
            out_lines[-1] = line + " / " + style(unbreakable(tighten(tr)))
        elif tr:
            indent = re.match(r"\s*", line).group(0)
            out_lines.append(indent + " " * max(0, width - len(indent)) + style(unbreakable(tighten(tr))))
    out_lines += blocks.get(len(items), [])

    if env("BBILINGUAL_LOG") == "1":
        pairs = [[t, raw[k], problems(t, raw[k])] for k, t in jobs]
        log(event="batch", session=session_id[:8], message=message_id[:8], index=index, final=final,
            backend=backend, model=env("BBILINGUAL_MODEL"), lines=len(items), prose=len(jobs),
            ctx=len(ctx), secs=round(time.time() - t0, 1), pairs=pairs)
    save_ctx(message_id, ctx, index)
    if final:
        finish_message(message_id)
    else:
        prune_state()
    text = "".join(l + "\n" for l in out_lines)   # every line keeps its own newline, blank lines included
    return text if delta.endswith("\n") or not delta else text[:-1]


def utf8_stdio():
    """Claude Code speaks UTF-8; Windows pipes default to the legacy code page and would crash on CJK."""
    for stream in (sys.stdin, sys.stdout):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


def emit(content):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "MessageDisplay",
                                             "displayContent": content}}, ensure_ascii=False))


def main():
    if env("BBILINGUAL_DISABLE") == "1":
        return
    utf8_stdio()
    try:
        event = json.load(sys.stdin)
        delta = event.get("delta") or ""
        backend, problem = configure()
        if backend is None:
            if event.get("index", 0) == 0 and first_notice(event.get("session_id") or ""):
                emit("[BBilingual is installed but not configured: %s. See the README.]\n%s" % (problem, delta))
            return
        display = render(delta, event.get("message_id") or "unknown", bool(event.get("final")), backend,
                         event.get("index", 0), event.get("session_id") or "")
    except Exception:
        return  # fail open: Claude Code shows the original text
    if display != delta:   # nothing added: Claude Code shows the original
        emit(display)


if __name__ == "__main__":
    main()
