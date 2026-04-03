// === AI CHAT PAGE ===
import { useRef, useEffect, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { C } from '../../../constants'
import UploadHero from './UploadHero'
import ChatInput from './ChatInput'
import { UserMessage, AssistantMessage } from './MessageBubbles'

export default function ChatPage({
  sessionId, messages, isUploading, isLoading,
  onUpload, onQuery, onReset, fileName,
}) {
  const threadRef = useRef(null)
  const [pendingQuestion, setPendingQuestion] = useState(null)

  // Auto-scroll
  useEffect(() => {
    if (threadRef.current) {
      threadRef.current.scrollTop = threadRef.current.scrollHeight
    }
  }, [messages, isLoading])

  // Send pending question once session exists
  useEffect(() => {
    if (sessionId && pendingQuestion) {
      onQuery(pendingQuestion)
      setPendingQuestion(null)
    }
  }, [sessionId])

  function handleChipClick(text) {
    if (sessionId) {
      onQuery(text)
    } else {
      setPendingQuestion(text)
      // Trigger file picker by dispatching click — caller handles that via UploadHero's own ref
    }
  }

  // Loading message shown while a response is in flight
  const showLoadingBubble = isLoading && messages[messages.length - 1]?.role === 'user'

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, height: '100%' }}>
      <AnimatePresence mode="wait">
        {!sessionId ? (
          <motion.div
            key="upload"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
            transition={{ duration: 0.2 }}
            style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}
          >
            <UploadHero
              onUpload={onUpload}
              isUploading={isUploading}
              onChipClick={handleChipClick}
            />
          </motion.div>
        ) : (
          <motion.div
            key="chat"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
            transition={{ duration: 0.2 }}
            style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, overflow: 'hidden' }}
          >
            {/* File status bar */}
            <div style={{
              height: 40,
              background: C.bgSurface,
              borderBottom: `1px solid ${C.border}`,
              padding: '0 20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexShrink: 0,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={{ width: 6, height: 6, borderRadius: '50%', background: C.teal }} />
                <span style={{ fontSize: 13, color: C.textSecondary }}>{fileName || 'policy.pdf'}</span>
                <span style={{ fontSize: 12, color: C.textMuted }}>· processing complete</span>
              </div>
              <span
                onClick={onReset}
                style={{ fontSize: 11, color: C.textMuted, cursor: 'pointer', transition: 'color 150ms' }}
                onMouseEnter={e => e.currentTarget.style.color = C.textPrimary}
                onMouseLeave={e => e.currentTarget.style.color = C.textMuted}
              >
                Clear session
              </span>
            </div>

            {/* Message thread */}
            <div
              ref={threadRef}
              style={{
                flex: 1,
                overflowY: 'auto',
                padding: 24,
                display: 'flex',
                flexDirection: 'column',
                gap: 16,
              }}
            >
              {messages.map((msg, i) =>
                msg.role === 'user'
                  ? <UserMessage key={i} content={msg.content} />
                  : <AssistantMessage key={i} content={msg.content} clauses={msg.clauses} />
              )}
              {showLoadingBubble && (
                <AssistantMessage content="" clauses={[]} isLoading={true} />
              )}
            </div>

            {/* Input bar */}
            <ChatInput onSend={onQuery} disabled={isLoading} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
