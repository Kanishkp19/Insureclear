// === RIGHT RAIL — POLICY ANALYTICS ===
import { C } from '../../constants'

function SectionHeader({ label }) {
  return (
    <div style={{ padding: '14px 16px 6px', fontSize: 10, textTransform: 'uppercase', letterSpacing: '2px', color: C.textMuted }}>
      {label}
    </div>
  )
}

function Row({ label, value, valueColor }) {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '8px 16px',
    }}>
      <span style={{ fontSize: 12, color: C.textSecondary }}>{label}</span>
      <span style={{ fontSize: 12, fontWeight: 500, color: valueColor || C.textSecondary }}>{value}</span>
    </div>
  )
}

function StatusRow({ label, active }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 16px' }}>
      <div style={{
        width: 6, height: 6, borderRadius: '50%',
        background: active ? C.teal : C.textMuted,
        flexShrink: 0,
      }} />
      <span style={{ fontSize: 13, color: active ? C.textPrimary : C.textSecondary }}>{label}</span>
    </div>
  )
}

export default function RightRailTree() {
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
          Policy Analytics
        </div>
      </div>

      {/* Risk Index */}
      <div style={{ padding: '14px 16px', borderBottom: `1px solid ${C.border}` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 8 }}>
          <span style={{ fontSize: 12, color: C.textSecondary }}>Risk Index</span>
          <span style={{ fontSize: 20, fontWeight: 500, color: C.amber }}>42.8</span>
        </div>
        {/* Segmented bar */}
        <div style={{ display: 'flex', height: 4, borderRadius: 2, overflow: 'hidden', gap: 2 }}>
          <div style={{ flex: 40, background: C.red }} />
          <div style={{ flex: 35, background: C.amber }} />
          <div style={{ flex: 25, background: C.teal }} />
        </div>
        <div style={{ fontSize: 11, color: C.textMuted, marginTop: 6 }}>
          Calculated based on 12 identified exclusions
        </div>
      </div>

      {/* Active Entities */}
      <SectionHeader label="Active Entities" />
      <Row label="Named Insured"  value="ACME CORP"       valueColor={C.teal} />
      <Row label="Jurisdiction"   value="NEW YORK, US"    valueColor={C.blue} />
      <Row label="Effective Date" value="JAN 01 2024"     valueColor={C.textSecondary} />

      <div style={{ borderTop: `1px solid ${C.border}`, marginTop: 4 }} />

      {/* Intelligence Status */}
      <SectionHeader label="Intelligence Status" />
      <StatusRow label="Real-time Vector Analysis"  active={true}  />
      <StatusRow label="Cross-policy Validation"    active={true}  />
      <StatusRow label="Historical Benchmarking"    active={false} />

      {/* Footer */}
      <div style={{ flex: 1 }} />
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
