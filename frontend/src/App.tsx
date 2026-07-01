import React from "react"
import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom"
import { 
  LayoutDashboard, 
  Upload, 
  Settings, 
  GitMerge, 
  BarChart3, 
  FileJson, 
  List, 
  BookOpen, 
  Activity,
  GitPullRequest,
  CheckCircle,
  Eye
} from "lucide-react"

import { cn } from "@/lib/utils"

// Import actual pages
import UploadPage from "@/pages/UploadPage"
import ExplainabilityPage from "@/pages/ExplainabilityPage"
import PipelinePage from "@/pages/PipelinePage"
import RuleInspector from "@/pages/RuleInspector"
import ConflictExplorer from "@/pages/ConflictExplorer"
import QualityScorePage from "@/pages/QualityScorePage"
import AnalyticsPage from "@/pages/AnalyticsPage"

// Placeholders for pages not yet implemented fully as separate components
const Dashboard = () => <div className="p-8"><h1 className="text-3xl font-bold">Dashboard</h1><p className="mt-4 text-muted-foreground">System Overview</p></div>
const ConfigPage = () => <div className="p-8"><h1 className="text-3xl font-bold">Configuration</h1><p className="mt-4 text-muted-foreground">Runtime projection config.</p></div>
const OutputPage = () => <div className="p-8"><h1 className="text-3xl font-bold">JSON Output</h1><p className="mt-4 text-muted-foreground">Final generated canonical profile.</p></div>
const LogsPage = () => <div className="p-8"><h1 className="text-3xl font-bold">Structured Logs</h1><p className="mt-4 text-muted-foreground">Pipeline execution logs.</p></div>

const navItems = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard, section: "Overview" },
  { name: "Upload Data", href: "/upload", icon: Upload, section: "Overview" },
  
  { name: "Transformation Replay", href: "/pipeline", icon: Activity, section: "Enhancements" },
  { name: "Explainability", href: "/explainability", icon: Eye, section: "Enhancements" },
  { name: "Rule Inspector", href: "/rules", icon: List, section: "Enhancements" },
  { name: "Conflict Explorer", href: "/conflicts", icon: GitPullRequest, section: "Enhancements" },
  { name: "Profile Quality", href: "/quality", icon: CheckCircle, section: "Enhancements" },
  { name: "Analytics", href: "/analytics", icon: BarChart3, section: "Enhancements" },
  
  { name: "Configuration", href: "/config", icon: Settings, section: "System" },
  { name: "Pipeline", href: "/legacy-pipeline", icon: GitMerge, section: "System" },
  { name: "JSON Output", href: "/output", icon: FileJson, section: "System" },
  { name: "Logs", href: "/logs", icon: List, section: "System" },
  { name: "Documentation", href: "/docs", icon: BookOpen, section: "System" },
]

function Sidebar() {
  const location = useLocation()
  
  const sections = Array.from(new Set(navItems.map(item => item.section)))

  return (
    <div className="flex h-full w-64 flex-col border-r bg-card px-3 py-4">
      <div className="mb-8 px-4">
        <h2 className="text-lg font-bold tracking-tight text-primary">Eightfold AI</h2>
        <p className="text-xs text-muted-foreground">Data Transformation Engine</p>
      </div>
      
      <div className="flex-1 space-y-6 overflow-y-auto">
        {sections.map(section => (
          <div key={section} className="space-y-1">
            <h3 className="mb-2 px-4 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              {section}
            </h3>
            {navItems.filter(item => item.section === section).map(item => {
              const Icon = item.icon
              const isActive = location.pathname === item.href
              
              return (
                <Link
                  key={item.href}
                  to={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-md px-4 py-2 text-sm font-medium transition-colors",
                    isActive 
                      ? "bg-primary text-primary-foreground" 
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {item.name}
                </Link>
              )
            })}
          </div>
        ))}
      </div>
    </div>
  )
}

function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/upload" element={<UploadPage />} />
          
          {/* Enhancement Pages */}
          <Route path="/explainability" element={<ExplainabilityPage />} />
          <Route path="/pipeline" element={<PipelinePage />} />
          <Route path="/rules" element={<RuleInspector />} />
          <Route path="/conflicts" element={<ConflictExplorer />} />
          <Route path="/quality" element={<QualityScorePage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          
          {/* System Pages */}
          <Route path="/config" element={<ConfigPage />} />
          <Route path="/legacy-pipeline" element={<PipelinePage />} />
          <Route path="/output" element={<OutputPage />} />
          <Route path="/logs" element={<LogsPage />} />
          <Route path="/docs" element={<div className="p-8"><h1 className="text-3xl font-bold">Documentation</h1></div>} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}

export default App
