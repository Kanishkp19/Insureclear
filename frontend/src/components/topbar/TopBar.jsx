// === TOP BAR ===
import { Bell } from 'lucide-react'
import { C } from '../../constants'

export default function TopBar({ activePage, domain }) {
  const showDomain = domain || (activePage === 'Policy Tree' ? 'COMMERCIAL' : null)
  return (
    <div style={{
      height: 52,
      minHeight: 52,
      background: C.bgPage,
      borderBottom: `1px solid ${C.border}`,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 20px',
      position: 'sticky',
      top: 0,
      zIndex: 10,
      boxSizing: 'border-box',
    }}>
      <span style={{ fontSize: 14, fontWeight: 500, color: C.textPrimary }}>
        {activePage}
      </span>

      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        {showDomain && (
          <div style={{
            background: C.tealDim,
            color: C.teal,
            border: '1px solid rgba(29,158,117,0.25)',
            borderRadius: 6,
            padding: '3px 10px',
            fontSize: 11,
            fontWeight: 500,
            letterSpacing: '0.5px',
          }}>
            {showDomain}
          </div>
        )}
        <Bell size={16} color={C.textSecondary} style={{ cursor: 'pointer' }} />
        <div style={{
          width: 28,
          height: 28,
          borderRadius: '50%',
          background: C.amberDim,
          border: `1px solid rgba(240,165,0,0.3)`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 11,
          fontWeight: 600,
          color: C.amber,
          cursor: 'pointer',
        }}>
          U
        </div>
      </div>
    </div>
  )
}
