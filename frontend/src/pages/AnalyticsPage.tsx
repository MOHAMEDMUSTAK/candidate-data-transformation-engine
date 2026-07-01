import React, { useEffect, useState } from "react"
import { BarChart3, Database, Target, Clock, Zap, CheckCircle2, ShieldCheck, PieChart } from "lucide-react"

import { getLastResult } from "@/lib/api"
import type { PipelineResponse } from "@/types"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"

export default function AnalyticsPage() {
  const [result, setResult] = useState<PipelineResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getLastResult()
      .then((data) => {
        setResult(data)
        setLoading(false)
      })
      .catch((err) => {
        setError("Failed to load pipeline results. Have you run the pipeline yet?")
        setLoading(false)
      })
  }, [])

  if (loading) return <div className="p-8">Loading analytics...</div>
  if (error) return <div className="p-8 text-destructive">{error}</div>
  if (!result) return <div className="p-8">No data available.</div>

  const { analytics, total_time_ms, conflicts, rule_applications } = result
  
  // Calculate some derived metrics
  const totalRulesApplied = rule_applications.length
  const canonicalizedSkills = rule_applications.filter(r => r.rule_name === 'skill_canonicalize').length
  const conflictWinRate = analytics.conflicts_resolved > 0 
    ? (analytics.conflicts_resolved / analytics.conflicts_detected) * 100 
    : 100

  const statCards = [
    {
      title: "Total Processing Time",
      value: `${total_time_ms}ms`,
      description: "Extremely fast end-to-end execution",
      icon: Zap,
      color: "text-amber-500",
    },
    {
      title: "Data Sources Parsed",
      value: analytics.files_uploaded || 0,
      description: "Structured and unstructured inputs",
      icon: Database,
      color: "text-blue-500",
    },
    {
      title: "Average Confidence",
      value: `${analytics.average_confidence || 0}%`,
      description: "Across all canonicalized fields",
      icon: Target,
      color: "text-emerald-500",
    },
    {
      title: "Profile Quality",
      value: `${analytics.quality_score || 0}/100`,
      description: "Completeness and richness",
      icon: ShieldCheck,
      color: "text-indigo-500",
    },
  ]

  return (
    <div className="mx-auto max-w-6xl p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Pipeline Analytics</h1>
        <p className="text-muted-foreground mt-2">
          High-level metrics and performance analysis of the transformation engine.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {statCards.map((stat, idx) => {
          const Icon = stat.icon
          return (
            <Card key={idx} className="overflow-hidden">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-medium text-sm text-muted-foreground">{stat.title}</h3>
                  <div className={`p-2 bg-muted rounded-md ${stat.color}`}>
                    <Icon className="h-4 w-4" />
                  </div>
                </div>
                <div className="text-3xl font-bold mb-1">{stat.value}</div>
                <p className="text-xs text-muted-foreground">{stat.description}</p>
              </CardContent>
            </Card>
          )
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PieChart className="h-5 w-5 text-primary" />
              Transformation Metrics
            </CardTitle>
            <CardDescription>Volume of data transformed and cleaned.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="font-medium">Fields Parsed vs Transformed</span>
                <span>{analytics.fields_transformed || 0} / {analytics.fields_parsed || 0}</span>
              </div>
              <Progress 
                value={((analytics.fields_transformed || 0) / Math.max(analytics.fields_parsed || 1, 1)) * 100} 
                className="h-2"
              />
            </div>

            <div className="grid grid-cols-2 gap-4 mt-6">
              <div className="p-4 border rounded-lg bg-card">
                <div className="text-sm text-muted-foreground mb-1">Duplicates Removed</div>
                <div className="text-2xl font-semibold">{analytics.duplicates_removed || 0}</div>
              </div>
              <div className="p-4 border rounded-lg bg-card">
                <div className="text-sm text-muted-foreground mb-1">Skills Canonicalized</div>
                <div className="text-2xl font-semibold">{canonicalizedSkills}</div>
              </div>
              <div className="p-4 border rounded-lg bg-card col-span-2">
                <div className="text-sm text-muted-foreground mb-1">Total Rules Applied</div>
                <div className="text-2xl font-semibold">{totalRulesApplied}</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-primary" />
              Conflict Resolution Engine
            </CardTitle>
            <CardDescription>Deterministic resolution performance.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="font-medium">Conflicts Resolved</span>
                <span className="text-emerald-500 font-medium">{conflictWinRate}% Success</span>
              </div>
              <Progress value={conflictWinRate} indicatorColor="bg-emerald-500" className="h-2" />
            </div>

            <div className="flex gap-4 mt-6">
              <div className="flex-1 p-4 bg-muted/50 rounded-lg text-center">
                <div className="text-3xl font-bold text-amber-500 mb-1">{analytics.conflicts_detected || 0}</div>
                <div className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">Detected</div>
              </div>
              <div className="flex-1 p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-center">
                <div className="text-3xl font-bold text-emerald-600 dark:text-emerald-400 mb-1">{analytics.conflicts_resolved || 0}</div>
                <div className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">Resolved</div>
              </div>
            </div>

            {conflicts.length > 0 && (
              <div className="mt-6 pt-4 border-t">
                <h4 className="text-sm font-medium mb-3">Top Conflict Areas</h4>
                <div className="space-y-2">
                  {Object.entries(
                    conflicts.reduce((acc, c) => {
                      acc[c.field] = (acc[c.field] || 0) + 1;
                      return acc;
                    }, {} as Record<string, number>)
                  ).map(([field, count]) => (
                    <div key={field} className="flex justify-between items-center text-sm">
                      <span className="text-muted-foreground font-mono">{field}</span>
                      <Badge variant="secondary">{count as number} conflicts</Badge>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
