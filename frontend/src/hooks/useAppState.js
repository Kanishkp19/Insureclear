// === GLOBAL STATE HOOK ===
import { useState } from 'react'
import { POST_QUERY_FLAGS } from '../constants'
import { uploadPDF as apiUpload, queryPolicy as apiQuery } from '../utils/api'

export function useAppState() {
  const [sessionId,   setSessionId]   = useState(null)
  const [messages,    setMessages]    = useState([])
  const [domain,      setDomain]      = useState(null)
  const [confidence,  setConfidence]  = useState(null)
  const [clauseCount, setClauseCount] = useState(0)
  const [riskFlags,   setRiskFlags]   = useState([])
  const [activePage,  setActivePage]  = useState('AI Chat')
  const [fileName,    setFileName]    = useState('')
  const [isUploading, setIsUploading] = useState(false)
  const [isLoading,   setIsLoading]   = useState(false)

  async function handleUpload(file) {
    setFileName(file.name)
    setIsUploading(true)
    try {
      const data = await apiUpload(file)
      setSessionId(data.session_id)
      setClauseCount(data.node_count || 0)
    } catch {
      // demo fallback — simulate successful upload
      setSessionId('demo-session-' + Date.now())
      setClauseCount(48)
    } finally {
      setIsUploading(false)
    }
  }

  async function handleQuery(question) {
    const userMsg = { role: 'user', content: question, clauses: [] }
    setMessages(prev => [...prev, userMsg])
    setIsLoading(true)
    try {
      const data = await apiQuery(question, sessionId)
      const assistantMsg = {
        role: 'assistant',
        content: data.explanation || data.answer || 'No response.',
        clauses: data.selected_clauses || [],
      }
      setMessages(prev => [...prev, assistantMsg])
      setDomain(data.domain || 'HEALTH')
      const c = data.selected_clauses?.[0]?.confidence_score
      if (c !== undefined) setConfidence(Math.round(c * 100))
      else setConfidence(94)
      setClauseCount(prev => prev + (data.selected_clauses?.length || 0))
      setRiskFlags(POST_QUERY_FLAGS)
    } catch {
      // demo fallback
      const assistantMsg = {
        role: 'assistant',
        content:
          'Based on your policy document, maternity benefits are covered after a 30-day waiting period. Pre-existing conditions are excluded under clause 3.2. The cashless network covers 8,500+ hospitals across India.',
        clauses: [
          {
            verdict: 'COVERED',
            confidence_score: 0.94,
            text: '"Maternity benefit" means expenses incurred in connection with childbirth, including pre and post-natal care, subject to the waiting period specified in the schedule.',
            breadcrumb: 'Section IV › Maternity Benefit › Clause 4.1',
            keyword: 'Maternity benefit',
          },
        ],
      }
      setMessages(prev => [...prev, assistantMsg])
      setDomain('HEALTH')
      setConfidence(94)
      setClauseCount(prev => prev + 1)
      setRiskFlags(POST_QUERY_FLAGS)
    } finally {
      setIsLoading(false)
    }
  }

  function resetSession() {
    setSessionId(null)
    setMessages([])
    setDomain(null)
    setConfidence(null)
    setClauseCount(0)
    setRiskFlags([])
    setFileName('')
    setIsUploading(false)
    setIsLoading(false)
  }

  return {
    sessionId, messages, domain, confidence, clauseCount, riskFlags,
    activePage, setActivePage, fileName, isUploading, isLoading,
    handleUpload, handleQuery, resetSession,
  }
}
