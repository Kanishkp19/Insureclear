// === SIDEBAR ===
import { motion, AnimatePresence } from 'framer-motion'
import { C, NAV_ITEMS, BOTTOM_NAV } from '../../constants'
import { getIcon } from '../../utils/icons'

function NavItem({ item, active, onClick }) {
  const Icon = getIcon(item.icon)
  return (
    <motion.div
      whileHover={{ scale: 1.01 }}
      transition={{ duration: 0.15 }}
      onClick={() => onClick(item.id)}
      style={{
        height: 36,
        borderRadius: 8,
        padding: '0 12px',
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        cursor: 'pointer',
        background: active ? C.amberDim : 'transparent',
        borderLeft: active ? `2px solid ${C.amber}` : '2px solid transparent',
        color: active ? C.textPrimary : C.textSecondary,
        position: 'relative',
        marginBottom: 2,
        transition: 'background 150ms, color 150ms',
      }}
      onMouseEnter={e => { if (!active) e.currentTarget.style.background = C.bgHover }}
      onMouseLeave={e => { if (!active) e.currentTarget.style.background = 'transparent' }}
    >
      {active && (
        <motion.div
          layoutId="activeNav"
          style={{
            position: 'absolute',
            inset: 0,
            borderRadius: 8,
            background: C.amberDim,
            borderLeft: `2px solid ${C.amber}`,
          }}
          transition={{ type: 'spring', stiffness: 400, damping: 35 }}
        />
      )}
      <Icon size={14} style={{ position: 'relative', zIndex: 1 }} />
      <span style={{ fontSize: 13, position: 'relative', zIndex: 1 }}>{item.id}</span>
    </motion.div>
  )
}

export default function Sidebar({ activePage, setActivePage }) {
  return (
    <div style={{
      width: 240,
      minWidth: 240,
      background: C.bgSidebar,
      borderRight: `1px solid ${C.border}`,
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      padding: '20px 12px 16px',
      boxSizing: 'border-box',
    }}>
      {/* Brand */}
      <div style={{ paddingLeft: 4, marginBottom: 28 }}>
        <div style={{ fontSize: 16, fontWeight: 500, color: C.textPrimary, letterSpacing: '-0.2px' }}>
          InsureClear
        </div>
        <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '2px', color: C.textMuted, marginTop: 3 }}>
          AI Underwriter
        </div>
      </div>

      {/* Main nav */}
      <nav style={{ flex: 1 }}>
        {NAV_ITEMS.map(item => (
          <NavItem
            key={item.id}
            item={item}
            active={activePage === item.id}
            onClick={setActivePage}
          />
        ))}
      </nav>

      {/* Bottom nav */}
      <div style={{ borderTop: `1px solid ${C.border}`, paddingTop: 12 }}>
        {BOTTOM_NAV.map(item => (
          <NavItem
            key={item.id}
            item={item}
            active={activePage === item.id}
            onClick={setActivePage}
          />
        ))}
      </div>
    </div>
  )
}
