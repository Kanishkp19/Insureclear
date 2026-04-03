// === MESSAGE BUBBLES ===
import { motion } from 'framer-motion'
import { C } from '../../../constants'
import ClauseCard from '../../common/ClauseCard'

export function UserMessage({ content }) {
  return (
    <motion.div
      initial={{ y: 10, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      style={{
        alignSelf: 'flex-end',
        maxWidth: '65%',
        background: C.bgElevated,
        borderRadius: '12px 12px 2px 12px',
        padding: '10px 14px',
        fontSize: 14,
        color: C.textPrimary,
      }}
    >
      {content}
    </motion.div>
  )
}

export function AssistantMessage({ content, clauses, isLoading }) {
  return (
    <motion.div
      initial={{ y: 10, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      style={{ alignSelf: 'flex-start', maxWidth: '80%' }}
    >
      <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
        {/* IC badge */}
        <div style={{
          width: 20,
          height: 20,
          borderRadius: '50%',
          background: C.amberDim,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 10,
          color: C.amber,
          flexShrink: 0,
          marginTop: 4,
          fontWeight: 600,
        }}>
          IC
        </div>

        <div style={{
          background: C.bgSurface,
          border: `1px solid ${C.border}`,
          borderRadius: '2px 12px 12px 12px',
          padding: '12px 16px',
          fontSize: 14,
          color: C.textPrimary,
          lineHeight: 1.7,
        }}>
          {content}
          {isLoading && (
            <motion.span
              animate={{ opacity: [1, 0] }}
              transition={{ repeat: Infinity, duration: 0.6 }}
              style={{ marginLeft: 2, color: C.amber }}
            >
              |
            </motion.span>
          )}
        </div>
      </div>

      {/* Clause cards */}
      {clauses && clauses.map((clause, i) => (
        <div key={i} style={{ paddingLeft: 30 }}>
          <ClauseCard clause={clause} />
        </div>
      ))}
    </motion.div>
  )
}
