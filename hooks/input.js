// BBilingual input (optional): write in your own language, Claude gets English.
//
// Before a prompt is sent, text that is not plain English is translated into English
// (scripts/to_english.py, with the same settings as the display hook) and sent in its place. Your
// message then shows as the English that Claude received.
//
// It is off until you turn it on. Switch it with /bbinput:
//   on        send the English straight away
//   confirm   show the English and ask "Send / Cancel" first
//   off       do nothing (the default)
// The choice is remembered across sessions. BBILINGUAL_INPUT (on | confirm | off) sets the starting
// value. Slash commands, shell lines (!), long pastes and plain English are never touched, and a
// failed translation sends what you typed.
//
// This uses Claude Code's mods API (Claude Code 2.1.287 or newer), which is early access.

// letters that are not plain English: CJK, Cyrillic, Arabic, Hebrew, Indic, Thai, accented Latin
const NOT_ENGLISH = /[À-ÖØ-öø-ɏЀ-ӿ֐-ۿऀ-෿฀-๿぀-ヿ㐀-鿿가-힯]/
const MAX_CHARS = 4000
const MODES = ['on', 'confirm', 'off']

async function currentMode($) {
  const mode = (await $.store.get('mode')) || (await $.env.get('BBILINGUAL_INPUT')) || 'off'
  return mode === 'auto' ? 'on' : mode
}

export function register(on) {
  on('session.start', async ($, e, next) => {
    await $.command.register({ name: 'bbinput', description: 'Translate what you type into English: on, confirm or off' })
    return next(e)
  })

  on('command.run', { command: 'bbinput' }, async ($, e) => {
    const asked = e.args.trim().toLowerCase()
    if (MODES.includes(asked)) await $.store.set('mode', asked)
    const mode = await currentMode($)
    const hint = asked && !MODES.includes(asked) ? ' ("' + asked + '" is not a mode)' : ''
    return { text: 'input translation is ' + mode + hint + '. /bbinput on, confirm or off changes it.' }
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
