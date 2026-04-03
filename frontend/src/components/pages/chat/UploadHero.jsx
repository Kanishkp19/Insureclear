// === UPLOAD HERO ===
import { useState, useRef } from 'react'
import { motion } from 'framer-motion'
import { UploadCloud, Info, Clock, AlertTriangle, GitCompare } from 'lucide-react'
import { C, SAMPLE_CHIPS } from '../../../constants'

const CHIP_ICONS = { Info, Clock, AlertTriangle, GitCompare }

export default function UploadHero({ onUpload, isUploading, onChipClick }) {
  const [dragOver, setDragOver] = useState(false)
  const [hovered,  setHovered]  = useState(false)
  const inputRef = useRef(null)

  function handleFile(file) {
    if (!file) return
    onUpload(file)
  }

  function onDrop(e) {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  return (
    <div style={{
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 48,
    }}>
      {/* Upload zone */}
      <div
        onClick={() => !isUploading && inputRef.current?.click()}
        onDragOver={e => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        style={{
          width: '100%',
          maxWidth: 600,
          height: 200,
          borderRadius: 12,
          border: dragOver
            ? `1px solid ${C.amber}`
            : hovered
              ? '1px solid rgba(240,165,0,0.5)'
              : '1px solid rgba(255,255,255,0.1)',
          background: hovered ? 'rgba(240,165,0,0.02)' : C.bgSurface,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 8,
          cursor: 'pointer',
          transition: 'border 200ms, background 200ms',
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx"
          style={{ display: 'none' }}
          onChange={e => handleFile(e.target.files[0])}
        />
        {isUploading ? (
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
            style={{
              width: 28,
              height: 28,
              borderRadius: '50%',
              border: `2px solid ${C.textMuted}`,
              borderTopColor: C.amber,
            }}
          />
        ) : (
          <>
            <UploadCloud size={32} color={C.textMuted} />
            <span style={{ fontSize: 13, color: C.textSecondary }}>Drag and drop your PDF policy here</span>
            <span style={{ fontSize: 11, color: C.textMuted }}>PDF, DOCX · Max 25MB</span>
          </>
        )}
      </div>

      {/* Sample question chips — 2x2 grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: 8,
        marginTop: 24,
        width: '100%',
        maxWidth: 600,
      }}>
        {SAMPLE_CHIPS.map(chip => {
          const Icon = CHIP_ICONS[chip.icon] || Info
          return (
            <motion.div
              key={chip.text}
              whileHover={{ y: -1 }}
              transition={{ duration: 0.15 }}
              onClick={() => onChipClick(chip.text)}
              style={{
                background: C.bgSurface,
                border: `1px solid ${C.border}`,
                borderRadius: 8,
                height: 38,
                padding: '0 14px',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                cursor: 'pointer',
                transition: 'border-color 150ms, background 150ms, color 150ms',
              }}
              onMouseEnter={e => {
                e.currentTarget.style.borderColor = C.borderHover
                e.currentTarget.style.background = C.bgHover
              }}
              onMouseLeave={e => {
                e.currentTarget.style.borderColor = C.border
                e.currentTarget.style.background = C.bgSurface
              }}
            >
              <Icon size={14} color={C.textMuted} />
              <span style={{ fontSize: 13, color: C.textSecondary }}>{chip.text}</span>
            </motion.div>
          )
        })}
      </div>

      {/* Compatible providers */}
      <div style={{ marginTop: 48, textAlign: 'center' }}>
        <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '2px', color: C.textMuted }}>
          Compatible Providers
        </div>
        <div style={{ fontSize: 11, color: C.textMuted, marginTop: 8 }}>
          ICICI Lombard · HDFC ERGO · Star Health · Bajaj Allianz · Niva Bupa
        </div>
      </div>
    </div>
  )
}
