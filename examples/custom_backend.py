#!/usr/bin/env python3
"""Example of your own translation backend for BBilingual (BBILINGUAL_BACKEND=command).

The contract is small:
  * BBilingual runs the command once per line of text, up to 8 at a time.
  * The English text arrives on standard input.
  * Print the translation, and nothing else, on standard output.
  * Exit with a non-zero status (or print nothing) and that line is simply shown untranslated.
  * The environment is inherited, so BBILINGUAL_TARGET tells you the target language.

This example talks to a LibreTranslate server (https://libretranslate.com). Replace the body of
translate() with whatever you like: another API, a local model, a glossary lookup, a cache.
"""
import json
import os
import sys
import urllib.request

SERVER = os.environ.get("LIBRETRANSLATE_URL", "http://localhost:5000")
CODES = {"zh-CN": "zh", "zh-TW": "zt"}          # LibreTranslate's names for a few codes


def translate(text, target):
    payload = {"q": text, "source": "en", "target": CODES.get(target, target), "format": "text"}
    request = urllib.request.Request(SERVER + "/translate", data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))["translatedText"]


if __name__ == "__main__":
    print(translate(sys.stdin.read().strip(), os.environ.get("BBILINGUAL_TARGET", "zh-CN")))
