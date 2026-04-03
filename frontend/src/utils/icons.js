// === ICON RESOLVER ===
import {
  MessageSquare, BarChart2, GitBranch, Star, TrendingUp,
  Settings, HelpCircle, Info, Clock, AlertTriangle, GitCompare,
  UploadCloud, Send, ChevronRight, Folder, FileText, X, Copy,
  Bell,
} from 'lucide-react'

const MAP = {
  MessageSquare, BarChart2, GitBranch, Star, TrendingUp,
  Settings, HelpCircle, Info, Clock, AlertTriangle, GitCompare,
  UploadCloud, Send, ChevronRight, Folder, FileText, X, Copy, Bell,
}

export function getIcon(name) {
  return MAP[name] || Info
}
