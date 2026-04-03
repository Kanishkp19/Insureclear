// === CHAT INPUT BAR ===
import { useState } from 'react'
import { motion } from 'framer-motion'
import { Send } from 'lucide-react'
import { C } from '../../../constants'

export default function ChatInput({ onSend, disabled }) {
  const [text, setText] = useState('')

  function submit() {
    const trimmed = text.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setText('')
  }

  return (
    <div style={{
      height: 64,
      flexShrink: 0,
      background: C.bgSidebar,
      borderTop: `1px solid ${C.border}`,
      padding: '0 16px',
      display: 'flex',
      alignItems: 'center',
      gap: 10,
    }}>
      <input
        value={text}
        onChange={e => setText(e.target.value)}
        onKeyDown={e => e.key === 'Enter' && submit()}
        placeholder="Ask about your policy..."
        disabled={disabled}
        style={{
          flex: 1,
          height: 40,
          background: C.bgElevated,
          border: `1px solid ${C.border}`,
          borderRadius: 10,
          padding: '0 14px',
          fontSize: 14,
          color: C.textPrimary,
          outline: 'none',
          fontFamily: 'inherit',
          caretColor: C.amber,
          transition: 'border-color 200ms',
        }}
        onFocus={e => e.target.style.borderColor = 'rgba(240,165,0,0.4)'}
        onBlur={e => e.target.style.borderColor = C.border}
      />
      <motion.button
        whileTap={{ scale: 0.95 }}
        onClick={submit}
        style={{
          width: 36,
          height: 36,
          borderRadius: 8,
          border: 'none',
          background: text.trim() ? C.amber : C.bgHover,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: 'background 200ms',
          flexShrink: 0,
        }}
      >
        <Send size={16} color={text.trim() ? '#080810' : C.textMuted} />
      </motion.button>
    </div>
  )
}
