// === PLACEHOLDER PAGE ===
import { motion } from 'framer-motion'
import { C } from '../../constants'

export default function PlaceholderPage({ name }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 48,
      }}
    >
      <div style={{ fontSize: 22, fontWeight: 400, color: C.textMuted, marginBottom: 8 }}>
        {name}
      </div>
      <div style={{ fontSize: 13, color: C.textMuted }}>Coming soon</div>
    </motion.div>
  )
}
