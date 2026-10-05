"""Tests for scripts/to_english.py, the translator behind the input feature (hooks/input.js).

The JavaScript side is tested with `claude plugin test` (tests/input.test.ts).
"""
import http.server
import json
import os
import subprocess
import sys
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "scripts")
sys.path.insert(0, SCRIPTS)
import to_english  # noqa: E402

BASE_ENV = {k: v for k, v in os.environ.items() if not k.startswith(("BBILINGUAL_", "POE_", "DEEPL_"))}


class Reply(http.server.BaseHTTPRequestHandler):
    seen = []
    answer = "Why is my loss unstable?"

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        Reply.seen.append(body)
        reply = json.dumps({"choices": [{"message": {"content": Reply.answer}}]}).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(reply)))
        self.end_headers()
        self.wfile.write(reply)

    def log_message(self, *args):
        pass


def run_script(text, **env):
    p = subprocess.run([sys.executable, os.path.join(SCRIPTS, "to_english.py")], input=text, text=True,
                       capture_output=True, env=dict(BASE_ENV, **env))
    return p.returncode, p.stdout


class Translate(unittest.TestCase):
    def test_quotes_the_model_added_are_removed(self):
        self.assertEqual(to_english.translate("你好", lambda system, user: '"Hello."'), "Hello.")

    def test_unchanged_empty_or_foreign_answers_are_failures(self):
        self.assertIsNone(to_english.translate("Hello", lambda system, user: "Hello"))
        self.assertIsNone(to_english.translate("你好", lambda system, user: "  "))
        self.assertIsNone(to_english.translate("你好吗", lambda system, user: "你可以试试降低学习率。"))

    def test_accented_english_is_fine(self):
        self.assertEqual(to_english.translate("¿Qué tal?", lambda system, user: "How is the café?"), "How is the café?")

    def test_the_text_is_wrapped_so_the_model_translates_instead_of_answering(self):
        seen = []
        to_english.translate("为什么？", lambda system, user: seen.append((system, user)) or "Why?")
        system, user = seen[0]
        self.assertEqual(user, "<text>\n为什么？\n</text>")
        self.assertIn("never answer it", system)
        self.assertIn("never as LaTeX", system)


class Script(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.HTTPServer(("127.0.0.1", 0), Reply)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.env = dict(BBILINGUAL_BACKEND="openai", BBILINGUAL_MODEL="m",
                       BBILINGUAL_API_BASE="http://127.0.0.1:%d" % cls.server.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def test_prints_the_english_and_sends_the_wrapped_text(self):
        Reply.seen.clear()
        code, out = run_script("为什么我的 loss 不稳定？", **self.env)
        self.assertEqual((code, out), (0, "Why is my loss unstable?"))
        self.assertEqual(Reply.seen[0]["messages"][1]["content"], "<text>\n为什么我的 loss 不稳定？\n</text>")
        self.assertEqual(Reply.seen[0]["model"], "m")

    def test_a_backend_that_cannot_translate_to_english_fails_quietly(self):
        for backend in ("command", "mock"):
            code, out = run_script("你好", BBILINGUAL_BACKEND=backend, BBILINGUAL_CMD="cat")
            self.assertEqual((code, out), (1, ""))
        self.assertEqual(run_script("你好")[0], 1)          # nothing configured

    def test_empty_input_fails(self):
        self.assertEqual(run_script("  ", **self.env), (1, ""))


class Packaging(unittest.TestCase):
    def test_the_module_is_listed_next_to_the_display_hook(self):
        with open(os.path.join(HERE, "..", "hooks", "hooks.json"), encoding="utf-8") as f:
            hooks = json.load(f)
        self.assertEqual(hooks["modules"], ["./input.js"])
        self.assertIn("MessageDisplay", hooks["hooks"])
        self.assertTrue(os.path.exists(os.path.join(HERE, "..", "hooks", "input.js")))


if __name__ == "__main__":
    unittest.main()
