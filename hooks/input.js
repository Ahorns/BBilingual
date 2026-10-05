// BBilingual input (optional): write in your own language, Claude gets English.
//
// Before a prompt is sent, text that is not plain English is translated into English
// (scripts/to_english.py, with the same settings as the display hook) and sent in its place. Your
// message then shows as the English that Claude received. There is no question and no pop-up.
//
// It is off until you turn it on. Switch it with /bbinput on or /bbinput off; the choice is
// remembered across sessions. BBILINGUAL_INPUT (on | off) sets the starting value. Slash commands,
// shell lines (!), long pastes and plain English are never touched, and a failed translation sends
// what you typed.
//
// This uses Claude Code's mods API (Claude Code 2.1.287 or newer), which is early access.

// letters that are not plain English: CJK, Cyrillic, Arabic, Hebrew, Indic, Thai, accented Latin
const NOT_ENGLISH = /[\u00c0-\u00d6\u00d8-\u00f6\u00f8-\u024f\u0400-\u04ff\u0590-\u06ff\u0900-\u0dff\u0e00-\u0e7f\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]/
const MAX_CHARS = 4000
const MODES = ['on', 'off']

async function currentMode($) {
  const mode = (await $.store.get('mode')) || (await $.env.get('BBILINGUAL_INPUT')) || 'off'
  return mode === 'on' || mode === 'auto' || mode === 'confirm' ? 'on' : 'off'
}

export function register(on) {
  on('session.start', async ($, e, next) => {
    await $.command.register({ name: 'bbinput', description: 'Translate what you type into English: on or off' })
    return next(e)
  })

  on('command.run', { command: 'bbinput' }, async ($, e) => {
    const asked = e.args.trim().toLowerCase()
    if (MODES.includes(asked)) await $.store.set('mode', asked)
    const mode = await currentMode($)
    const hint = asked && !MODES.includes(asked) ? ' ("' + asked + '" is not a mode)' : ''
    return { text: 'input translation is ' + mode + hint + '. /bbinput on or off changes it.' }
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
      // no translation: send what was typed
    }
    return english ? next({ ...e, text: english }) : next(e)
  })
}
