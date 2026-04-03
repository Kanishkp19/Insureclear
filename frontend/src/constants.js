// === DESIGN SYSTEM ===
export const C = {
  bgPage: '#080810',
  bgSidebar: '#0d0d16',
  bgSurface: '#12121c',
  bgElevated: '#1a1a28',
  bgHover: '#1e1e2e',
  border: 'rgba(255,255,255,0.08)',
  borderHover: 'rgba(255,255,255,0.16)',
  textPrimary: '#ededf5',
  textSecondary: '#8b8b9e',
  textMuted: '#3d3d52',
  amber: '#f0a500',
  amberDim: 'rgba(240,165,0,0.1)',
  teal: '#1d9e75',
  tealDim: 'rgba(29,158,117,0.1)',
  red: '#e24b4a',
  redDim: 'rgba(226,75,74,0.1)',
  blue: '#378add',
  blueDim: 'rgba(55,138,221,0.1)',
}

export const NAV_ITEMS = [
  { id: 'AI Chat',          icon: 'MessageSquare' },
  { id: 'Analyzer',         icon: 'BarChart2'     },
  { id: 'Policy Tree',      icon: 'GitBranch'     },
  { id: 'Recommendations',  icon: 'Star'          },
  { id: 'Insights',         icon: 'TrendingUp'    },
]

export const BOTTOM_NAV = [
  { id: 'Settings',  icon: 'Settings'    },
  { id: 'Help',      icon: 'HelpCircle'  },
]

export const SAMPLE_CHIPS = [
  { icon: 'Info',          text: 'Is maternity covered?'         },
  { icon: 'Clock',         text: 'What is my waiting period?'    },
  { icon: 'AlertTriangle', text: 'Any earthquake exclusions?'    },
  { icon: 'GitCompare',    text: 'Compare with HDFC Shield'      },
]

export const POST_QUERY_FLAGS = [
  { severity: 'red',   title: 'Pre-existing Condition',  desc: 'Exclusion detected in clause 3.2'   },
  { severity: 'amber', title: 'Maternity Waiting Period', desc: '30-day waiting period applies'       },
  { severity: 'blue',  title: 'Cashless Network',         desc: '8,500+ hospitals covered'            },
]
