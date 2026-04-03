// === CLAUSE INSPECTOR ===
import { X } from 'lucide-react'
import { C } from '../../../constants'

const CLAUSE_TEXT =
  '"Bodily injury" or "property damage" expected or intended from the standpoint of the insured. This exclusion does not apply to "bodily injury" resulting from the use of reasonable force to protect persons or property.'

function HighlightPhrase({ text, phrase }) {
  if (!phrase) return <>{text}</>
  const parts = text.split(new RegExp(`(${phrase})`, 'gi'))
  return (
    <>
      {parts.map((p, i) =>
        p.toLowerCase() === phrase.toLowerCase()
          ? <span key={i} style={{ background: 'rgba(240,165,0,0.2)' }}>{p}</span>
          : p
      )}
    </>
  )
}

export default function ClauseInspector({ node, onClose }) {
  return (
    <div style={{ flex: 1, padding: 20, overflowY: 'auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
        <div>
          <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '2px', color: C.textMuted, marginBottom: 4 }}>
            Clause Inspector
          </div>
          <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '2px', color: C.textMuted, marginBottom: 4 }}>
            Selected Node
          </div>
          <div style={{ fontSize: 16, fontWeight: 500, color: C.textPrimary }}>
            {node?.label || '2. Exclusions: Expected or Intended Injury'}
          </div>
        </div>
        <X
          size={16}
          color={C.textMuted}
          style={{ cursor: 'pointer', marginTop: 4 }}
          onClick={onClose}
        />
      </div>

      {/* Clause text box */}
      <div style={{
        background: C.bgElevated,
        border: `1px solid ${C.border}`,
        borderRadius: 8,
        padding: 16,
        fontFamily: 'JetBrains Mono, monospace',
        fontSize: 13,
        lineHeight: 1.8,
        color: C.textPrimary,
      }}>
        <HighlightPhrase text={CLAUSE_TEXT} phrase="bodily injury" />
      </div>

      {/* Risk conflict */}
      <div style={{
        marginTop: 16,
        background: C.redDim,
        borderLeft: `3px solid ${C.red}`,
        borderRadius: '0 8px 8px 0',
        padding: '12px 16px',
      }}>
        <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '1px', color: C.red }}>
          ⚠ Risk Conflict Found
        </div>
        <div style={{ fontSize: 12, color: C.textSecondary, marginTop: 4 }}>
          Overlap detected with Umbrella Policy #881 under Intentional Acts provision.
        </div>
      </div>

      {/* AI recommendation */}
      <div style={{
        marginTop: 8,
        background: C.tealDim,
        borderLeft: `3px solid ${C.teal}`,
        borderRadius: '0 8px 8px 0',
        padding: '12px 16px',
      }}>
        <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '1px', color: C.teal }}>
          ✦ AI Recommendation
        </div>
        <div style={{ fontSize: 12, color: C.textSecondary, marginTop: 4 }}>
          Suggest adding rider SF-102 to mitigate exposure for security personnel force usage.
        </div>
      </div>

      {/* Buttons */}
      <div style={{ display: 'flex', gap: 8, marginTop: 24 }}>
        <button
          style={{
            flex: 1,
            height: 38,
            background: 'transparent',
            border: `1px solid ${C.border}`,
            borderRadius: 8,
            fontSize: 12,
            letterSpacing: '1px',
            color: C.textSecondary,
            cursor: 'pointer',
            transition: 'background 150ms',
          }}
          onMouseEnter={e => e.currentTarget.style.background = C.bgHover}
          onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
        >
          COMPARE
        </button>
        <button
          style={{
            flex: 1,
            height: 38,
            background: C.bgElevated,
            border: `1px solid ${C.borderHover}`,
            borderRadius: 8,
            fontSize: 12,
            letterSpacing: '1px',
            color: C.textPrimary,
            cursor: 'pointer',
            transition: 'background 150ms',
          }}
          onMouseEnter={e => e.currentTarget.style.background = C.bgHover}
          onMouseLeave={e => e.currentTarget.style.background = C.bgElevated}
        >
          EDIT CLAUSE
        </button>
      </div>
    </div>
  )
}
