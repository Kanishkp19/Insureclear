// === CLAUSE CARD ===
import { useState } from 'react'
import { motion } from 'framer-motion'
import { C } from '../../constants'

const VERDICT_COLOR = {
  COVERED:  C.teal,
  EXCLUDED: C.red,
  PARTIAL:  C.amber,
}

function HighlightedText({ text, keyword }) {
  if (!keyword || !text) return <>{text}</>
  const parts = text.split(new RegExp(`(${keyword})`, 'gi'))
  return (
    <>
      {parts.map((part, i) =>
        part.toLowerCase() === keyword.toLowerCase()
          ? <span key={i} style={{ background: 'rgba(240,165,0,0.2)' }}>{part}</span>
          : part
      )}
    </>
  )
}

export default function ClauseCard({ clause }) {
  const [copied, setCopied] = useState(false)
  const verdict = clause.verdict || 'COVERED'
  const color   = VERDICT_COLOR[verdict] || C.teal
  const conf    = clause.confidence_score !== undefined
    ? Math.round(clause.confidence_score * 100)
    : 94
  const confPct = conf + '%'
  const text    = clause.text || ''
  const crumb   = clause.breadcrumb || 'Section I › Clause 1.1'
  const keyword = clause.keyword || ''

  function handleCopy() {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    })
  }

  return (
    <motion.div
      initial={{ y: 8, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ delay: 0.1, duration: 0.2 }}
      style={{
        background: C.bgSurface,
        border: `1px solid ${C.border}`,
        borderRadius: 8,
        marginTop: 8,
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 14px',
        height: 32,
        borderBottom: `1px solid ${C.border}`,
      }}>
        <span style={{
          fontSize: 10,
          textTransform: 'uppercase',
          letterSpacing: '1.5px',
          color,
          fontWeight: 600,
        }}>
          {verdict}
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 12, color: C.amber }}>{confPct}</span>
          <div style={{
            width: 60,
            height: 3,
            borderRadius: 2,
            background: 'rgba(255,255,255,0.08)',
            overflow: 'hidden',
          }}>
            <div style={{ width: confPct, height: '100%', background: color, borderRadius: 2 }} />
          </div>
        </div>
      </div>

      {/* Clause text */}
      <div style={{
        padding: '12px 14px',
        fontFamily: 'JetBrains Mono, monospace',
        fontSize: 12,
        lineHeight: 1.8,
        color: C.textPrimary,
      }}>
        <HighlightedText text={text} keyword={keyword} />
      </div>

      {/* Breadcrumb */}
      <div style={{
        padding: '8px 14px',
        fontFamily: 'monospace',
        fontSize: 11,
        color: C.textMuted,
        borderTop: `1px solid ${C.border}`,
      }}>
        {crumb}
      </div>

      {/* Actions */}
      <div style={{
        padding: '6px 14px',
        display: 'flex',
        gap: 12,
        borderTop: `1px solid ${C.border}`,
      }}>
        <span
          style={{ fontSize: 11, color: C.textMuted, cursor: 'pointer', transition: 'color 150ms' }}
          onMouseEnter={e => e.currentTarget.style.color = C.textPrimary}
          onMouseLeave={e => e.currentTarget.style.color = C.textMuted}
        >
          View in tree
        </span>
        <span
          onClick={handleCopy}
          style={{
            fontSize: 11,
            color: copied ? C.teal : C.textMuted,
            cursor: 'pointer',
            transition: 'color 150ms',
          }}
          onMouseEnter={e => { if (!copied) e.currentTarget.style.color = C.textPrimary }}
          onMouseLeave={e => { if (!copied) e.currentTarget.style.color = C.textMuted }}
        >
          {copied ? 'Copied ✓' : 'Copy clause'}
        </span>
      </div>
    </motion.div>
  )
}
