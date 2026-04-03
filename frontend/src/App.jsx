// === APP ROOT ===
import { AnimatePresence } from 'framer-motion'
import { useAppState } from './hooks/useAppState'
import Sidebar from './components/sidebar/Sidebar'
import TopBar from './components/topbar/TopBar'
import RightRailChat from './components/rightRail/RightRailChat'
import RightRailTree from './components/rightRail/RightRailTree'
import ChatPage from './components/pages/chat/ChatPage'
import PolicyTreePage from './components/pages/policyTree/PolicyTreePage'
import PlaceholderPage from './components/pages/PlaceholderPage'
import { C } from './constants'

function PageContent(props) {
  const { activePage, ...rest } = props
  switch (activePage) {
    case 'AI Chat':        return <ChatPage {...rest} />
    case 'Policy Tree':    return <PolicyTreePage />
    case 'Analyzer':       return <PlaceholderPage name="Analyzer" />
    case 'Recommendations':return <PlaceholderPage name="Recommendations" />
    case 'Insights':       return <PlaceholderPage name="Insights" />
    case 'Settings':       return <PlaceholderPage name="Settings" />
    case 'Help':           return <PlaceholderPage name="Help" />
    default:               return <PlaceholderPage name={activePage} />
  }
}

export default function App() {
  const state = useAppState()

  const {
    sessionId, messages, domain, confidence, clauseCount, riskFlags,
    activePage, setActivePage, fileName, isUploading, isLoading,
    handleUpload, handleQuery, resetSession,
  } = state

  const showTreeRail = activePage === 'Policy Tree'

  return (
    <div style={{
      display: 'flex',
      height: '100vh',
      width: '100vw',
      overflow: 'hidden',
      background: C.bgPage,
      fontFamily: "'Inter', 'SF Pro Display', system-ui, sans-serif",
      color: C.textPrimary,
    }}>
      {/* Left sidebar */}
      <Sidebar activePage={activePage} setActivePage={setActivePage} />

      {/* Main area */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        minWidth: 0,
        overflow: 'hidden',
      }}>
        <TopBar activePage={activePage} domain={domain} />

        {/* Page body */}
        <div style={{ flex: 1, display: 'flex', overflow: 'hidden', minWidth: 0 }}>
          <AnimatePresence mode="wait">
            <PageContent
              key={activePage}
              activePage={activePage}
              sessionId={sessionId}
              messages={messages}
              isUploading={isUploading}
              isLoading={isLoading}
              fileName={fileName}
              onUpload={handleUpload}
              onQuery={handleQuery}
              onReset={resetSession}
            />
          </AnimatePresence>
        </div>
      </div>

      {/* Right rail — swaps based on page */}
      <AnimatePresence mode="wait">
        {showTreeRail
          ? <RightRailTree key="tree-rail" />
          : <RightRailChat
              key="chat-rail"
              confidence={confidence}
              domain={domain}
              clauseCount={clauseCount}
              riskFlags={riskFlags}
            />
        }
      </AnimatePresence>
    </div>
  )
}
