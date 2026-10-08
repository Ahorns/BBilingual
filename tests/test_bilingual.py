"""Tests for the BBilingual hook. Run: python3 -m unittest discover -s tests -v

The hook is started as a real subprocess, the way Claude Code starts it. No network is used: the
"mock" backend marks translations with 【译】, and a small local HTTP server stands in for an
OpenAI-compatible API.
"""
import http.server
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "scripts")
SCRIPT = os.path.join(SCRIPTS, "bilingual.py")

BASE_ENV = {k: v for k, v in os.environ.items() if not k.startswith(("BBILINGUAL_", "POE_", "DEEPL_", "DEEPSEEK_"))}
BASE_ENV.update(XDG_CACHE_HOME=tempfile.mkdtemp(), TMPDIR=tempfile.mkdtemp())
LOG_FILE = os.path.join(BASE_ENV["XDG_CACHE_HOME"], "bbilingual", "log.jsonl")


def event(delta, mid=None, index=0, final=False, session="s"):
    return {"hook_event_name": "MessageDisplay", "session_id": session, "message_id": mid or uuid.uuid4().hex,
            "index": index, "final": final, "delta": delta}


def hook(delta, extra=None, **kw):
    """Run the hook once and return the displayContent, or None if it printed nothing."""
    env = dict(BASE_ENV, BBILINGUAL_BACKEND="mock")
    env.update(extra or {})
    p = subprocess.run([sys.executable, SCRIPT], input=json.dumps(event(delta, **kw)), text=True,
                       capture_output=True, env=env)
    assert p.returncode == 0, p.stderr
    return json.loads(p.stdout)["hookSpecificOutput"]["displayContent"] if p.stdout else None


def command(cmd, **extra):
    return dict(BBILINGUAL_BACKEND="command", BBILINGUAL_CMD=cmd, **extra)


def finish(proc):
    """Read everything a subprocess printed, then reap it."""
    out = proc.stdout.read()
    proc.stdout.close()
    proc.wait()
    return out


class FakeOpenAI(http.server.BaseHTTPRequestHandler):
    """A stand-in for an OpenAI-compatible /chat/completions endpoint."""
    seen = []
    echo_first = False      # pretend to be a weak model that copies the English back on the first try

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        FakeOpenAI.seen.append({"path": self.path, "auth": self.headers.get("Authorization"), "body": body})
        lines = body["messages"][1]["content"].split("Translate these lines:\n")[1].splitlines()
        retry = "repeated the original text" in body["messages"][1]["content"]
        mark = "" if FakeOpenAI.echo_first and not retry else "译："
        content = "\n".join(l.replace("] ", "] " + mark, 1) for l in lines)
        reply = json.dumps({"choices": [{"message": {"content": content}}]}).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(reply)))
        self.end_headers()
        self.wfile.write(reply)

    def log_message(self, *args):
        pass


class Basics(unittest.TestCase):
    def test_translation_is_indented_under_a_bullet(self):
        out = hook("• Local fix idea: use pruning itself as the stabiliser.\n")
        self.assertEqual(out.splitlines()[1], "  【译】Local\u00a0fix\u00a0idea:\u00a0use\u00a0pruning\u00a0itself\u00a0as\u00a0the\u00a0stabiliser.")

    def test_speaks_utf8_even_when_the_console_code_page_is_not(self):
        # a native Windows pipe uses the legacy code page (cp1252 here), which cannot hold Chinese
        env = dict(BASE_ENV, BBILINGUAL_BACKEND="mock", PYTHONIOENCODING="cp1252")
        raw = json.dumps(event("Naïve “quotes” here.\n"), ensure_ascii=False).encode("utf-8")
        p = subprocess.run([sys.executable, SCRIPT], input=raw, capture_output=True, env=env)
        self.assertEqual(p.returncode, 0, p.stderr)
        out = json.loads(p.stdout.decode("utf-8"))["hookSpecificOutput"]["displayContent"]
        self.assertIn("【译】Naïve", out)

    def test_disable_switch(self):
        self.assertIsNone(hook("hello\n", {"BBILINGUAL_DISABLE": "1"}))

    def test_failing_backend_falls_back_to_the_original(self):
        self.assertIsNone(hook("Some text\n", command("exit 1")))

    def test_translation_identical_to_the_original_is_not_repeated(self):
        self.assertIsNone(hook("It stays English.\n", command("cat")))
        self.assertIsNone(hook("PROGRESS  █████░░ 85.0%\nCURRENT   M3.3 - Timing guard   in_progress\n", command("cat")))

    def test_mostly_chinese_line_is_left_alone(self):
        self.assertIsNone(hook("我们正在测试一个首个脉冲到达时间 (TTFS) Fast head 是否能在系统中占有一席之地。\n"))

    def test_english_line_containing_chinese_words_is_translated(self):
        out = hook("The heading `阶段一` is bold and the rest of this sentence is English.\n")
        self.assertIn("【译】", out)

    def test_double_space_inside_a_sentence_is_still_prose(self):
        self.assertIn("【译】", hook("For example, use the heading Where things stand: TTFS  当前进度 today.\n"))

    def test_heading_translation_stays_on_the_heading_line(self):
        out = hook("# A heading here\n\nSome text.\n")
        self.assertEqual(out.splitlines()[0], "# A heading here / 【译】A\u00a0heading\u00a0here")


class Configuration(unittest.TestCase):
    def test_nothing_happens_until_a_backend_is_configured(self):
        env = {"BBILINGUAL_BACKEND": ""}
        first = hook("Hello there.\n", env, session="fresh-session")
        self.assertIn("not configured", first)
        self.assertTrue(first.endswith("Hello there.\n"))
        self.assertIsNone(hook("Hello again.\n", env, session="fresh-session"))   # the hint shows once

    def test_misconfigured_backend_explains_what_is_missing(self):
        out = hook("Hello.\n", {"BBILINGUAL_BACKEND": "openai"}, session="misconfigured")
        self.assertIn("BBILINGUAL_MODEL is not set", out)
        out = hook("Hello.\n", {"BBILINGUAL_BACKEND": "nonsense"}, session="unknown-backend")
        self.assertIn("unknown backend", out)


class OpenAICompatible(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.HTTPServer(("127.0.0.1", 0), FakeOpenAI)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.env = dict(BBILINGUAL_BACKEND="openai", BBILINGUAL_MODEL="test-model", BBILINGUAL_API_KEY="k123",
                       BBILINGUAL_API_BASE="http://127.0.0.1:%d/v1" % cls.server.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        FakeOpenAI.seen.clear()

    def test_request_shape(self):
        out = hook("Use pruning as a stabiliser.\n", self.env)
        self.assertEqual(out.splitlines()[1], "译：Use\u00a0pruning\u00a0as\u00a0a\u00a0stabiliser.")
        seen = FakeOpenAI.seen[0]
        self.assertEqual(seen["path"], "/v1/chat/completions")
        self.assertEqual(seen["auth"], "Bearer k123")
        self.assertEqual(seen["body"]["model"], "test-model")
        self.assertNotIn("temperature", seen["body"])
        self.assertIn("Simplified Chinese", seen["body"]["messages"][0]["content"])
        self.assertIn("never as LaTeX", seen["body"]["messages"][0]["content"])

    def test_no_key_sends_no_authorization_header(self):
        env = dict(self.env, BBILINGUAL_API_KEY="")
        hook("A local model needs no key.\n", env)
        self.assertIsNone(FakeOpenAI.seen[0]["auth"])

    def test_all_prose_lines_of_a_batch_go_in_one_request(self):
        hook("First line.\nSecond line.\nThird line.\n", self.env)
        self.assertEqual(len(FakeOpenAI.seen), 1)
        self.assertIn("[3]", FakeOpenAI.seen[0]["body"]["messages"][1]["content"])

    def test_earlier_lines_are_sent_as_context_in_later_batches(self):
        mid = uuid.uuid4().hex
        hook("First line.\n", self.env, mid=mid, index=0)
        hook("Third line.\n", self.env, mid=mid, index=1, final=True)
        sent = FakeOpenAI.seen[-1]["body"]["messages"][1]["content"]
        self.assertIn("Earlier lines of this message", sent)
        self.assertIn("First line.", sent)

    def test_target_language_and_extra_instructions_reach_the_prompt(self):
        env = dict(self.env, BBILINGUAL_TARGET="fr", BBILINGUAL_PROMPT_EXTRA="Keep 'spike' untranslated.")
        hook("A spike train.\n", env)
        system = FakeOpenAI.seen[0]["body"]["messages"][0]["content"]
        self.assertIn("French", system)
        self.assertTrue(system.endswith("Keep 'spike' untranslated."))

    def test_a_batch_copied_back_unchanged_is_retried_once(self):
        FakeOpenAI.echo_first = True
        try:
            out = hook("Line one here.\nLine two here.\nLine three here.\n", self.env)
        finally:
            FakeOpenAI.echo_first = False
        self.assertEqual(len(FakeOpenAI.seen), 2)
        self.assertIn("repeated the original text", FakeOpenAI.seen[1]["body"]["messages"][1]["content"])
        self.assertEqual(out.splitlines()[1], "译：Line\u00a0one\u00a0here.")

    def test_the_deepseek_preset_needs_only_a_key(self):
        env = dict(BBILINGUAL_BACKEND="deepseek", DEEPSEEK_API_KEY="k456", BBILINGUAL_API_BASE=self.env["BBILINGUAL_API_BASE"])
        out = hook("Use pruning as a stabiliser.\n", env)
        self.assertEqual(out.splitlines()[1], "译：Use\u00a0pruning\u00a0as\u00a0a\u00a0stabiliser.")
        seen = FakeOpenAI.seen[0]
        self.assertEqual(seen["auth"], "Bearer k456")
        self.assertEqual(seen["body"]["model"], "deepseek-flash")
        self.assertEqual(seen["body"]["thinking"], {"type": "disabled"})

    def test_everything_the_preset_fills_in_can_be_overridden(self):
        env = dict(self.env, BBILINGUAL_BACKEND="deepseek", DEEPSEEK_API_KEY="from-the-preset",
                   BBILINGUAL_MODEL="deepseek-v4-pro", BBILINGUAL_EXTRA_BODY='{"thinking": {"type": "enabled"}}')
        hook("Override the preset.\n", env)
        seen = FakeOpenAI.seen[0]
        self.assertEqual(seen["auth"], "Bearer k123")                  # BBILINGUAL_API_KEY wins over DEEPSEEK_API_KEY
        self.assertEqual(seen["body"]["model"], "deepseek-v4-pro")
        self.assertEqual(seen["body"]["thinking"], {"type": "enabled"})

    def test_the_deepseek_preset_points_at_deepseek(self):
        sys.path.insert(0, SCRIPTS)
        import bilingual
        self.assertEqual(bilingual.PRESETS["deepseek"]["base"], "https://api.deepseek.com")

    def test_deepseek_without_a_key_explains_what_is_missing(self):
        out = hook("Hello.\n", {"BBILINGUAL_BACKEND": "deepseek"}, session="deepseek-no-key")
        self.assertIn("DEEPSEEK_API_KEY is not set", out)

    def test_extra_body_fields_are_merged_into_the_request(self):
        env = dict(self.env, BBILINGUAL_EXTRA_BODY='{"thinking": {"type": "disabled"}, "model": "ignored"}')
        hook("A line for a thinking model.\n", env)
        body = FakeOpenAI.seen[0]["body"]
        self.assertEqual(body["thinking"], {"type": "disabled"})
        self.assertEqual(body["model"], "test-model")                  # the extra fields cannot replace the model
        self.assertEqual(body["messages"][0]["role"], "system")

    def test_extra_body_that_is_not_a_json_object_is_reported(self):
        for bad in ("{oops", "[1, 2]"):
            out = hook("Hello.\n", dict(self.env, BBILINGUAL_EXTRA_BODY=bad), session="bad-extra-" + str(len(bad)))
            self.assertIn("BBILINGUAL_EXTRA_BODY is not a JSON object", out)
        self.assertEqual(FakeOpenAI.seen, [])

    def test_temperature_is_sent_only_when_asked(self):
        hook("Warm line.\n", dict(self.env, BBILINGUAL_TEMPERATURE="0"))
        self.assertEqual(FakeOpenAI.seen[0]["body"]["temperature"], 0.0)


class Languages(unittest.TestCase):
    def test_non_cjk_target_needs_no_cjk_and_keeps_its_spaces(self):
        out = hook("Hello world.\n", command("echo 'Bonjour le monde.'", BBILINGUAL_TARGET="fr"))
        self.assertEqual(out.splitlines()[1], "Bonjour le monde.")

    def test_cjk_target_must_answer_in_cjk(self):
        self.assertIsNone(hook("Hello world.\n", command("echo 'Bonjour le monde.'", BBILINGUAL_TARGET="ja")))

    def test_japanese_target_is_tightened_like_chinese(self):
        out = hook("Hello.\n", command("echo 'こんにちは， 世界 OK です'", BBILINGUAL_TARGET="ja"))
        self.assertEqual(out.splitlines()[1], "こんにちは，世界OKです")


class CodeFences(unittest.TestCase):
    def test_code_is_not_translated_across_batches(self):
        mid = uuid.uuid4().hex
        a = hook("Here is the code:\n```python\ndef prune_synapse(x):\n", mid=mid)
        b = hook("    return x > threshold\n```\nDone with the code block.\n", mid=mid, index=1, final=True)
        self.assertNotIn("【译】def", a)
        self.assertNotIn("【译】    return", b)
        self.assertIn("【译】Done", b)

    def test_batches_that_start_out_of_order_still_see_the_open_fence(self):
        env = dict(BASE_ENV, **command("sleep 1; echo 慢速翻译"))
        mid = uuid.uuid4().hex

        def spawn(delta, index, final=False):
            p = subprocess.Popen([sys.executable, SCRIPT], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 text=True, env=env)
            return p, json.dumps(event(delta, mid=mid, index=index, final=final))

        p0, e0 = spawn("A sentence before the code.\n```\n", 0)
        p1, e1 = spawn("rm -rf build\n```\n", 1, True)
        p0.stdin.write(e0)
        p0.stdin.close()
        time.sleep(0.15)                      # batch 1 starts while batch 0 is still translating
        p1.stdin.write(e1)
        p1.stdin.close()
        out1 = finish(p1)
        self.assertNotIn("慢速翻译", out1)
        self.assertIn("慢速翻译", finish(p0))

    def test_slow_translations_in_a_chain_do_not_break_code_detection(self):
        env = dict(BASE_ENV, **command("sleep 5; echo 慢速翻译"))
        mid = uuid.uuid4().hex
        procs = []
        for delta, index, final in (("Intro line.\n```\n", 0, False), ("Middle line.\n", 1, False),
                                    ("rm -rf x\n```\nTail line.\n", 2, True)):
            p = subprocess.Popen([sys.executable, SCRIPT], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 text=True, env=env)
            p.stdin.write(json.dumps(event(delta, mid=mid, index=index, final=final)))
            p.stdin.close()
            procs.append(p)
            time.sleep(0.1)
        shown = json.loads(finish(procs[2]))["hookSpecificOutput"]["displayContent"]
        for p in procs[:2]:
            finish(p)
        self.assertIn("rm -rf x\n", shown)
        self.assertEqual(shown.count("慢速翻译"), 1)       # only "Tail line." is translated

    def test_an_empty_batch_does_not_make_the_next_one_wait(self):
        mid = uuid.uuid4().hex
        hook("\n", mid=mid, index=0)
        t0 = time.time()
        hook("Hello there.\n", mid=mid, index=1, final=True)
        self.assertLess(time.time() - t0, 3)


class Tables(unittest.TestCase):
    ZH_TABLE = ["| 【译】Item | 【译】Cost |", "| --- | --- |", "| 【译】Fast head | 12.5% |"]

    def test_translated_table_follows_the_original(self):
        out = hook("| Item | Cost |\n|---|---|\n| Fast head | 12.5% |\n\nAfter text here.\n")
        self.assertEqual(out.splitlines(), ["| Item | Cost |", "|---|---|", "| Fast head | 12.5% |", ""]
                         + self.ZH_TABLE + ["", "After text here.", "【译】After\u00a0text\u00a0here."])

    def test_table_arriving_in_several_batches(self):
        mid = uuid.uuid4().hex
        self.assertIsNone(hook("| Item | Cost |\n|---|---|\n", mid=mid, index=0))
        self.assertIsNone(hook("| Fast head | 12.5% |\n", mid=mid, index=1))
        out = hook("\nNext paragraph.\n", mid=mid, index=2)
        self.assertEqual(out.splitlines(), [""] + self.ZH_TABLE + ["", "Next paragraph.", "【译】Next\u00a0paragraph."])

    def test_table_at_the_end_of_a_message(self):
        mid = uuid.uuid4().hex
        self.assertIsNone(hook("| Item | Cost |\n|---|---|\n| Fast head | 12.5% |\n", mid=mid, index=0))
        out = hook("", mid=mid, index=1, final=True)
        self.assertEqual(out.splitlines(), [""] + self.ZH_TABLE)

    def test_final_batch_without_a_trailing_newline(self):
        out = hook("| Item | Cost |\n|---|---|\n| Fast head | 12.5% |", index=0, final=True)
        self.assertTrue(out.endswith("| 【译】Fast head | 12.5% |"))
        self.assertIn("\n\n| 【译】Item", out)

    def test_rows_without_a_separator_row_are_not_a_table(self):
        out = hook("| not | a table |\n\nText.\n")
        self.assertEqual(out.splitlines()[:3], ["| not | a table |", "", "Text."])

    def test_table_inside_a_code_block_is_left_alone(self):
        self.assertIsNone(hook("```\n| Item | Cost |\n```\n"))

    def test_translated_table_has_no_colour_codes(self):
        out = hook("| Item | Cost |\n|---|---|\n| Fast head | 12.5% |\n", {"BBILINGUAL_STYLE": "gray"}, final=True)
        self.assertNotIn("\x1b", out.split("\n\n")[-1])      # colour codes make Claude Code mis-draw tables
        self.assertEqual(out.splitlines()[-1], "| 【译】Fast head | 12.5% |")

    def test_long_translated_cells_stay_unbroken_for_the_terminal_to_wrap(self):
        long_cell = "真正的目标是电路性能，但对其进行测量需要进行仿真，每次尝试都要耗费数分钟。"
        out = hook("| A | B |\n|---|---|\n| One | Two |\n", command("echo '%s'" % long_cell), final=True)
        self.assertEqual(out.splitlines()[-1], "| %s | %s |" % (long_cell, long_cell))


class StyleAndSpacing(unittest.TestCase):
    def test_style_wraps_the_translated_line(self):
        out = hook("Styled line.\n", {"BBILINGUAL_STYLE": "dim"})
        self.assertTrue(out.splitlines()[1].startswith("\x1b[2m") and out.splitlines()[1].endswith("\x1b[22m"))
        self.assertEqual(out.splitlines()[0], "Styled line.")     # the original is never styled

    def test_style_is_reapplied_after_a_bold_span(self):
        out = hook("A styled bold line.\n", command("echo '**粗体** 之后继续'", BBILINGUAL_STYLE="dim"))
        self.assertEqual(out.splitlines()[1], "**\x1b[2m粗体\x1b[22m**\x1b[2m\u00a0之后继续\x1b[22m")

    def test_spaces_next_to_cjk_are_removed(self):
        out = hook("Some text\n", command("echo 你好， 世界。 再见 OK 吧"))
        self.assertEqual(out.splitlines()[1], "你好，世界。再见OK吧")

    def test_space_next_to_a_markdown_marker_is_kept_so_bold_still_closes(self):
        out = hook("Bold line.\n", command("echo '**阶段一，粗调：** 像 VPR 的，规则（“引号”）。完'"))
        self.assertEqual(out.splitlines()[1], "**阶段一，粗调：**\u00a0像VPR的，规则（“引号”）。完")

    def test_spaces_left_in_a_cjk_line_cannot_break_it_early(self):
        out = hook("Some text\n", command("echo '与 VPR 的区别在于 fine tuning 和 80.8 % 的 `a b` 值'"))
        self.assertEqual(out.splitlines()[1],
                         "与VPR的区别在于fine\u00a0tuning和80.8\u00a0%的\u00a0`a b`\u00a0值")
        self.assertNotIn(" ", out.splitlines()[1].replace("`a b`", ""))


class Logging(unittest.TestCase):
    def read_log(self):
        with open(LOG_FILE, encoding="utf-8") as f:
            return [json.loads(line) for line in f]

    def test_log_is_off_by_default(self):
        hook("Nothing is recorded by default.\n")
        self.assertFalse(os.path.exists(LOG_FILE))

    def test_log_records_pairs_flags_and_notes(self):
        env = {"BBILINGUAL_LOG": "1"}
        hook("Log this line.\n", env)
        hook("This one fails.\n", dict(command("exit 1"), **env))
        entries = self.read_log()
        pairs = [p for e in entries if e["event"] == "batch" for p in e["pairs"]]
        self.assertTrue(any(p[0] == "Log this line." and p[1] == "【译】Log this line." for p in pairs))
        self.assertTrue(any("no_translation" in p[2] for p in pairs))

        note = subprocess.run([sys.executable, os.path.join(SCRIPTS, "note.py"), "demo bug"],
                              env=dict(BASE_ENV, **env), capture_output=True, text=True)
        self.assertEqual(note.returncode, 0, note.stderr)
        last = self.read_log()[-1]
        self.assertEqual((last["event"], last["note"]), ("note", "demo bug"))
        self.assertTrue(last["last_batch"])

        shown = subprocess.run([sys.executable, os.path.join(SCRIPTS, "show_log.py"), "--flagged"],
                               env=BASE_ENV, capture_output=True, text=True).stdout
        self.assertIn("no_translation", shown)


if __name__ == "__main__":
    unittest.main()
