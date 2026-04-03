// === TREE NODE ===
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronRight, Folder, FileText } from 'lucide-react'
import { C } from '../../../constants'

export default function TreeNode({ node, activeId, onSelect, depth = 0 }) {
  const [expanded, setExpanded] = useState(node.defaultExpanded || false)
  const isActive   = activeId === node.id
  const hasChildren = node.children && node.children.length > 0

  function toggle() {
    if (hasChildren) setExpanded(e => !e)
    onSelect(node)
  }

  return (
    <div>
      <motion.div
        whileHover={!isActive ? { backgroundColor: C.bgHover } : {}}
        onClick={toggle}
        style={{
          height: 32,
          paddingLeft: depth * 16 + 8,
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          cursor: 'pointer',
          background: isActive ? C.amberDim : 'transparent',
          borderLeft: isActive ? `2px solid ${C.amber}` : '2px solid transparent',
          marginLeft: isActive ? -2 : 0,
          borderRadius: isActive ? '0 4px 4px 0' : 0,
          userSelect: 'none',
        }}
      >
        {/* Chevron */}
        <motion.span
          animate={{ rotate: expanded ? 90 : 0 }}
          transition={{ duration: 0.15 }}
          style={{ display: 'flex', alignItems: 'center', opacity: hasChildren ? 1 : 0 }}
        >
          <ChevronRight size={12} color={C.textMuted} />
        </motion.span>

        {/* Icon */}
        {hasChildren
          ? <Folder size={14} color={C.textMuted} />
          : <FileText size={14} color={C.textMuted} />
        }

        {/* Label */}
        <span style={{
          fontSize: 13,
          color: isActive ? C.textPrimary : C.textSecondary,
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
        }}>
          {node.label}
        </span>
      </motion.div>

      {/* Children */}
      <AnimatePresence initial={false}>
        {expanded && hasChildren && (
          <motion.div
            key="children"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            style={{ overflow: 'hidden' }}
          >
            {node.children.map(child => (
              <TreeNode
                key={child.id}
                node={child}
                activeId={activeId}
                onSelect={onSelect}
                depth={depth + 1}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
