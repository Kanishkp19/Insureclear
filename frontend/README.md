# InsureClear — AI-Powered Insurance Policy Analyzer

A production-grade React application for AI-assisted insurance policy analysis.

## Tech Stack

- **React 18** — UI framework
- **Framer Motion** — animations & transitions
- **Lucide React** — icons
- **Vite** — build tool & dev server
- Inline styles only — zero external CSS, zero UI libraries

## Project Structure

```
insureclear/
├── index.html                        # HTML shell, fonts
├── vite.config.js
├── package.json
└── src/
    ├── main.jsx                      # React root
    ├── App.jsx                       # Layout shell, page routing
    ├── constants.js                  # Design tokens (C), nav items, chip data
    ├── hooks/
    │   └── useAppState.js            # Global state + API calls
    ├── utils/
    │   ├── api.js                    # uploadPDF / queryPolicy fetch helpers
    │   └── icons.js                  # Lucide icon name → component resolver
    └── components/
        ├── sidebar/
        │   └── Sidebar.jsx           # Nav, brand, bottom nav
        ├── topbar/
        │   └── TopBar.jsx            # Page title, domain badge, avatar
        ├── rightRail/
        │   ├── RightRailChat.jsx     # Session Intelligence (metrics + risk flags)
        │   └── RightRailTree.jsx     # Policy Analytics (risk index + entities)
        ├── common/
        │   └── ClauseCard.jsx        # Reusable clause evidence card
        └── pages/
            ├── chat/
            │   ├── ChatPage.jsx      # Orchestrates upload hero ↔ chat active
            │   ├── UploadHero.jsx    # Drag-and-drop upload zone + chips
            │   ├── MessageBubbles.jsx# UserMessage / AssistantMessage
            │   └── ChatInput.jsx     # Text input + send button
            ├── policyTree/
            │   ├── PolicyTreePage.jsx # Split-panel layout
            │   ├── TreeNode.jsx       # Recursive tree node with collapse animation
            │   ├── ClauseInspector.jsx# Right panel: clause text, risk, AI rec
            │   └── treeData.js        # Hardcoded demo tree
            └── PlaceholderPage.jsx    # Analyzer / Recommendations / Insights stubs
```

## Getting Started

```bash
# Install dependencies
npm install

# Start dev server
npm run dev
# → http://localhost:5173

# Production build
npm run build
npm run preview
```

## Backend API

The app expects a FastAPI (or similar) server at `http://localhost:8000` with two endpoints:

### `POST /upload`
```
Content-Type: multipart/form-data
Body: file (PDF or DOCX)

Response: { session_id: string, node_count: number }
```

### `POST /query`
```json
{
  "question": "Is maternity covered?",
  "session_id": "abc123"
}

Response:
{
  "explanation": "...",
  "selected_clauses": [
    {
      "verdict": "COVERED",
      "confidence_score": 0.94,
      "text": "...",
      "breadcrumb": "Section IV › Clause 4.1",
      "keyword": "Maternity benefit"
    }
  ],
  "domain": "HEALTH",
  "refined_question": "..."
}
```

> **Demo mode**: If the backend is unavailable, the app falls back to hardcoded demo responses so the UI is fully explorable without a running server.

## Design System

All colors, spacing, and type scales live in `src/constants.js` as the `C` object.  
No external CSS — all styles are JS objects passed to `style` props.

| Token          | Value                      | Usage                    |
|----------------|----------------------------|--------------------------|
| `C.bgPage`     | `#080810`                  | Main canvas              |
| `C.bgSidebar`  | `#0d0d16`                  | Side panels              |
| `C.bgSurface`  | `#12121c`                  | Cards, message bubbles   |
| `C.bgElevated` | `#1a1a28`                  | Input fields, user msgs  |
| `C.amber`      | `#f0a500`                  | Active state, confidence |
| `C.teal`       | `#1d9e75`                  | Covered verdict, domain  |
| `C.red`        | `#e24b4a`                  | Excluded verdict, risks  |
| `C.blue`       | `#378add`                  | Info-level flags         |
