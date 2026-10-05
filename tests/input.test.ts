// Tests for hooks/input.js. Run from the repository root: claude plugin test
// (needs Claude Code 2.1.287 or newer; no session, sign-in or network is used)
import { expect, mock, test } from 'claude-code/testing'

const CHINESE = '我的 loss 在剪枝之后不稳定，怎么办？'
const SPANISH = '¿Por qué mi pérdida es inestable después de podar?'
const ENGLISH = 'Why is my loss unstable after pruning?'

// stubs: what scripts/to_english.py prints (and its exit code), and the answer to the "Send this to Claude?" question
function stubs(on: any, opts: { mode?: string; exitCode?: number; stdout?: string; answer?: string }) {
  mock.env(on, opts.mode ? { BBILINGUAL_INPUT: opts.mode } : {})
  mock.store(on, {})
  const seen = { ran: 0, question: '' }
  on('process.run', () => {
    seen.ran += 1
    return { value: { exitCode: opts.exitCode ?? 0, stdout: opts.stdout ?? ENGLISH, stderr: '' } }
  })
  on('tool.call', ($: any, e: any) => {
    seen.question = e.questions[0].question
    return { result: { answers: { [seen.question]: opts.answer ?? 'Send' } } }
  })
  on('prompt.submit', ($: any, e: any) => ({ text: e.text }))
  return seen
}

test('off is the default: nothing is translated', async ($, on) => {
  const seen = stubs(on, {})
  const out = await $.prompt.submit({ text: CHINESE })
  expect(out.text).toBe(CHINESE)
  expect(seen.ran).toBe(0)
})

test('on: text in another language is sent as English', async ($, on) => {
  stubs(on, { mode: 'on' })
  expect((await $.prompt.submit({ text: CHINESE })).text).toBe(ENGLISH)
  expect((await $.prompt.submit({ text: SPANISH })).text).toBe(ENGLISH)
})

test('English, slash commands and shell lines pass through untouched', async ($, on) => {
  const seen = stubs(on, { mode: 'on' })
  for (const text of ['Why is my loss unstable? It grew 2–4× after pruning.', '/help 帮助', '!ls 目录']) {
    expect((await $.prompt.submit({ text })).text).toBe(text)
  }
  expect(seen.ran).toBe(0)
})

test('on: a failed translation sends what was typed', async ($, on) => {
  stubs(on, { mode: 'on', exitCode: 1, stdout: '' })
  expect((await $.prompt.submit({ text: CHINESE })).text).toBe(CHINESE)
})

test('confirm: Send sends the English, after showing it', async ($, on) => {
  const seen = stubs(on, { mode: 'confirm', answer: 'Send' })
  expect((await $.prompt.submit({ text: CHINESE })).text).toBe(ENGLISH)
  expect(seen.question).toContain(ENGLISH)
})

test('confirm: Cancel sends nothing and returns the typed text', async ($, on) => {
  stubs(on, { mode: 'confirm', answer: 'Cancel' })
  const out = await $.prompt.submit({ text: CHINESE })
  expect(out.drop).toContain(CHINESE)
})

test('confirm: text typed under Other is sent instead', async ($, on) => {
  stubs(on, { mode: 'confirm', answer: 'Why does pruning make my loss unstable?' })
  expect((await $.prompt.submit({ text: CHINESE })).text).toBe('Why does pruning make my loss unstable?')
})

test('confirm: a failed translation asks before sending the original', async ($, on) => {
  stubs(on, { mode: 'confirm', exitCode: 1, stdout: '', answer: 'Send as typed' })
  expect((await $.prompt.submit({ text: CHINESE })).text).toBe(CHINESE)
})

test('/bbinput on, off: the switch is remembered', async ($, on) => {
  const seen = stubs(on, {})
  const turnedOn = await $.command.run({ command: 'bbinput', args: 'on' })
  expect(turnedOn.text).toContain('input translation is on')
  expect((await $.prompt.submit({ text: CHINESE })).text).toBe(ENGLISH)
  await $.command.run({ command: 'bbinput', args: 'off' })
  seen.ran = 0
  expect((await $.prompt.submit({ text: CHINESE })).text).toBe(CHINESE)
  expect(seen.ran).toBe(0)
})

test('/bbinput alone shows the state; a wrong word changes nothing', async ($, on) => {
  stubs(on, { mode: 'on' })
  expect((await $.command.run({ command: 'bbinput', args: '' })).text).toContain('input translation is on')
  const wrong = await $.command.run({ command: 'bbinput', args: 'maybe' })
  expect(wrong.text).toContain('"maybe" is not a mode')
  expect(wrong.text).toContain('input translation is on')
})
