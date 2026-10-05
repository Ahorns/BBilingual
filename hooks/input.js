// BBilingual input (optional): write in your own language, Claude gets English.
//
// Before a prompt is sent, text that is not plain English is translated into English
// (scripts/to_english.py, with the same settings as the display hook) and sent in its place. Your
// message then shows as the English that Claude received.
//
// Also here: /bbilingual on or off switches the display translation (the text under Claude's replies).
//
// It is off until you turn it on. Switch it with /bbinput; the choice is remembered across sessions:
//   on        send the English straight away, with no question
//   confirm   show the English first and ask Send / Cancel (text typed under "Other" is sent instead)
//   off       do nothing (the default)
// BBILINGUAL_INPUT (on | confirm | off) sets the starting value. Slash commands, shell lines (!), long
// pastes and plain English are never touched, and a failed translation sends what you typed (confirm
// asks first).
//
// This uses Claude Code's mods API (Claude Code 2.1.287 or newer), which is early access.

// letters that are not plain English: CJK, Cyrillic, Arabic, Hebrew, Indic, Thai, accented Latin
const NOT_ENGLISH = /[\u00c0-\u00d6\u00d8-\u00f6\u00f8-\u024f\u0400-\u04ff\u0590-\u06ff\u0900-\u0dff\u0e00-\u0e7f\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]/
const MAX_CHARS = 4000
const MODES = ['on', 'confirm', 'off']
const DEFAULT = 'off'

async function currentMode($) {
  const mode = (await $.store.get('mode')) || (await $.env.get('BBILINGUAL_INPUT')) || DEFAULT
  const known = mode === 'auto' ? 'on' : mode // an old 'auto' just means on
  return MODES.includes(known) ? known : DEFAULT
}

async function displayIsOff($) {
  const saved = await $.store.get('display')
  if (saved === 'off') return true
  if (saved === 'on') return false
  return (await $.env.get('BBILINGUAL_DISABLE')) === '1'
}

export function register(on) {
  on('session.start', async ($, e, next) => {
    await $.command.register({ name: 'bbinput', description: 'Translate what you type into English: on, confirm or off' })
    await $.command.register({ name: 'bbilingual', description: "Show a translation under Claude's replies: on or off" })
    // the display hook is a separate process that obeys BBILINGUAL_DISABLE; re-apply a saved "off"
    if ((await $.store.get('display')) === 'off') await $.env.set('BBILINGUAL_DISABLE', '1')
    return next(e)
  })

  on('command.run', { command: 'bbinput' }, async ($, e) => {
    const asked = e.args.trim().toLowerCase()
    if (MODES.includes(asked)) await $.store.set('mode', asked)
    const mode = await currentMode($)
    const hint = asked && !MODES.includes(asked) ? ' ("' + asked + '" is not a mode)' : ''
    return { text: 'input translation is ' + mode + hint + '. /bbinput on, confirm or off changes it.' }
  })

  on('command.run', { command: 'bbilingual' }, async ($, e) => {
    const asked = e.args.trim().toLowerCase()
    if (asked === 'off') {
      await $.store.set('display', 'off')
      await $.env.set('BBILINGUAL_DISABLE', '1')
    }
    if (asked === 'on') {
      await $.store.set('display', 'on')
      await $.env.set('BBILINGUAL_DISABLE', undefined)
    }
    const state = (await displayIsOff($)) ? 'off' : 'on'
    const hint = asked && asked !== 'on' && asked !== 'off' ? ' ("' + asked + '" is not a mode)' : ''
    return { text: "translation under Claude's replies is " + state + hint + '. /bbilingual on or off changes it.' }
  })

  on('prompt.submit', async ($, e, next) => {
    const mode = await currentMode($)
    const text = e.text
    // only what the person typed (a test fires the event without an origin)
    if (mode === 'off' || (e.origin && e.origin.kind !== 'composer')) return next(e)
    if (!NOT_ENGLISH.test(text) || /^\s*[/!]/.test(text) || text.length > MAX_CHARS) return next(e)

    let english = ''
    try {
      const out = await $.process.run(['python3', $.plugin.root + '/scripts/to_english.py'], {
        stdin: text,
        timeoutMs: 40000,
      })
      if (out.exitCode === 0) english = out.stdout.trim()
    } catch (err) {
      // no translation: handled below
    }

    if (!english) {
      if (mode === 'on') return next(e)
      let answer = 'Cancel'
      try {
        answer = await $.ui.ask('Could not translate. Send what you typed?', ['Send as typed', 'Cancel'])
      } catch (err) {
        // dismissed: do not send
      }
      return answer === 'Send as typed' ? next(e) : { drop: 'Not sent. You typed: ' + text }
    }

    if (mode === 'confirm') {
      let answer = 'Cancel'
      try {
        answer = await $.ui.ask(english + '\n\nSend this to Claude?', { options: ['Send', 'Cancel'], header: 'English' })
      } catch (err) {
        // dismissed: do not send
      }
      if (answer === 'Cancel') return { drop: 'Not sent. You typed: ' + text }
      if (answer !== 'Send') english = answer.trim() || english // typed under "Other": send that instead
    }
    return next({ ...e, text: english })
  })
}
