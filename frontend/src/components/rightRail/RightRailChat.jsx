// === RIGHT RAIL — SESSION INTELLIGENCE ===
import { motion, AnimatePresence } from 'framer-motion'
import { C } from '../../constants'

const SEVERITY_COLOR = { red: C.red, amber: C.amber, blue: C.blue }

function MetricRow({ label, value, valueColor }) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '10px 16px',
      borderBottom: `1px solid ${C.border}`,
    }}>
      <span style={{ fontSize: 12, color: C.textSecondary }}>{label}</span>
      <span style={{ fontSize: 13, fontWeight: 500, color: valueColor || C.textPrimary }}>
        {value}
      </span>
    </div>
  )
}

function RiskFlag({ flag, index }) {
  return (
    <motion.div
      initial={{ x: -10, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ delay: index * 0.08, duration: 0.2 }}
      style={{
        background: C.bgSurface,
        borderLeft: `2px solid ${SEVERITY_COLOR[flag.severity]}`,
        borderRadius: '0 6px 6px 0',
        padding: '8px 12px',
        marginBottom: 6,
      }}
    >
      <div style={{ fontSize: 12, fontWeight: 500, color: C.textPrimary }}>{flag.title}</div>
      <div style={{ fontSize: 11, color: C.textSecondary, marginTop: 2 }}>{flag.desc}</div>
    </motion.div>
  )
}

export default function RightRailChat({ confidence, domain, clauseCount, riskFlags }) {
  return (
    <div style={{
      width: 260,
      minWidth: 260,
      background: C.bgSidebar,
      borderLeft: `1px solid ${C.border}`,
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      overflowY: 'auto',
      boxSizing: 'border-box',
    }}>
      {/* Header */}
      <div style={{ padding: '16px 16px 8px', borderBottom: `1px solid ${C.border}` }}>
        <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '2px', color: C.textMuted }}>
          Session Intelligence
        </div>
      </div>

      {/* Metrics */}
      <MetricRow
        label="Confidence Score"
        value={confidence !== null ? `${confidence}%` : '--'}
        valueColor={confidence !== null ? C.amber : C.textMuted}
      />
      <MetricRow
        label="Domain"
        value={domain || 'None'}
        valueColor={domain ? C.teal : C.textMuted}
      />
      <MetricRow
        label="Clauses Found"
        value={clauseCount}
        valueColor={clauseCount > 0 ? C.textPrimary : C.textMuted}
      />

      {/* Risk Flags */}
      <div style={{ padding: '16px 16px 8px' }}>
        <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '2px', color: C.textMuted }}>
          Risk Flags
        </div>
      </div>

      <div style={{ padding: '0 12px', flex: 1 }}>
        <AnimatePresence>
          {riskFlags.length === 0 ? (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              style={{ fontSize: 12, color: C.textMuted, textAlign: 'center', paddingTop: 16 }}
            >
              No risks identified.<br />Upload a document.
            </motion.div>
          ) : (
            riskFlags.map((f, i) => <RiskFlag key={f.title} flag={f} index={i} />)
          )}
        </AnimatePresence>
      </div>

      {/* Footer */}
      <div style={{ padding: '12px 16px', borderTop: `1px solid ${C.border}` }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
          <div style={{ width: 6, height: 6, borderRadius: '50%', background: C.teal }} />
          <span style={{ fontSize: 11, color: C.textMuted }}>SYSTEM READY</span>
        </div>
        <div style={{ fontSize: 10, color: C.textMuted }}>Engine: V4.2-Obsidian-Analyst</div>
      </div>
    </div>
  )
}
