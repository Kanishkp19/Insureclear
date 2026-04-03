// === POLICY TREE PAGE ===
import { useState } from 'react'
import { motion } from 'framer-motion'
import { C } from '../../../constants'
import TreeNode from './TreeNode'
import ClauseInspector from './ClauseInspector'
import { TREE_DATA } from './treeData'

export default function PolicyTreePage() {
  const [activeNode, setActiveNode] = useState({ id: 'excl1', label: '2. Exclusions: Expected or Intended Injury' })
  const [inspectorOpen, setInspectorOpen] = useState(true)

  function handleSelect(node) {
    if (node.type === 'file') {
      setActiveNode(node)
      setInspectorOpen(true)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      style={{ display: 'flex', flex: 1, overflow: 'hidden', minWidth: 0 }}
    >
      {/* Left tree panel */}
      <div style={{
        width: 380,
        minWidth: 380,
        borderRight: `1px solid ${C.border}`,
        overflowY: 'auto',
        padding: 16,
      }}>
        <div style={{ fontSize: 14, fontWeight: 500, color: C.textPrimary, marginBottom: 4 }}>
          Policy Document
        </div>
        <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 16, fontFamily: 'monospace' }}>
          ROOT / COVERAGE / LIABILITY
        </div>

        {TREE_DATA.map(node => (
          <TreeNode
            key={node.id}
            node={node}
            activeId={activeNode?.id}
            onSelect={handleSelect}
            depth={0}
          />
        ))}
      </div>

      {/* Right clause inspector */}
      {inspectorOpen && activeNode ? (
        <ClauseInspector node={activeNode} onClose={() => setInspectorOpen(false)} />
      ) : (
        <div style={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: C.textMuted,
          fontSize: 13,
        }}>
          Select a clause to inspect
        </div>
      )}
    </motion.div>
  )
}
