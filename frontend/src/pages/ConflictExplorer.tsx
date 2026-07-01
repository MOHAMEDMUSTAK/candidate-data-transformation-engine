import React, { useEffect, useState } from "react"
import { GitPullRequest, ShieldCheck, ShieldAlert, Check, X } from "lucide-react"

import { getLastResult } from "@/lib/api"
import type { PipelineResponse } from "@/types"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export default function ConflictExplorer() {
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

  if (loading) return <div className="p-8">Loading conflict explorer...</div>
  if (error) return <div className="p-8 text-destructive">{error}</div>
  if (!result) return <div className="p-8">No data available.</div>

  const { conflicts, analytics } = result

  return (
    <div className="mx-auto max-w-5xl p-8">
      <div className="mb-8 flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Conflict Resolution Explorer</h1>
          <p className="text-muted-foreground mt-2">
            Analyze deterministic merge decisions when sources disagree.
          </p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-emerald-500">
            {analytics.conflicts_resolved || 0}
          </div>
          <div className="text-sm text-muted-foreground font-medium uppercase tracking-wider">
            Conflicts Resolved
          </div>
        </div>
      </div>

      {conflicts.length === 0 ? (
        <Card className="border-dashed bg-muted/20">
          <CardContent className="flex flex-col items-center justify-center p-12 text-center">
            <ShieldCheck className="h-12 w-12 text-emerald-500 mb-4" />
            <h3 className="text-xl font-semibold mb-2">No Conflicts Detected</h3>
            <p className="text-muted-foreground max-w-sm">
              All data sources were in agreement or only single sources provided values for fields.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-6">
          {conflicts.map((conflict, idx) => (
            <Card key={idx} className="border-primary/20 shadow-sm overflow-hidden">
              <div className="bg-primary/5 px-6 py-4 border-b flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <GitPullRequest className="h-5 w-5 text-primary" />
                  <h3 className="font-semibold font-mono text-lg">{conflict.field}</h3>
                </div>
                <Badge variant="outline" className="bg-background">
                  {conflict.candidates.length} sources competing
                </Badge>
              </div>
              
              <CardContent className="p-6">
                <p className="text-sm text-muted-foreground mb-6 bg-muted/50 p-3 rounded-md border">
                  <strong>Resolution Strategy:</strong> {conflict.explanation}
                </p>

                <div className="grid md:grid-cols-2 gap-8">
                  {/* Winner */}
                  <div>
                    <h4 className="flex items-center gap-2 font-semibold text-emerald-600 dark:text-emerald-400 mb-3">
                      <Check className="h-4 w-4" /> Selected Value
                    </h4>
                    <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-4">
                      <div className="text-xl font-bold mb-3">{String(conflict.winner.value)}</div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Source:</span>
                        <Badge variant="outline" className="font-mono bg-background text-emerald-700 dark:text-emerald-300 border-emerald-500/30">
                          {conflict.winner.source}
                        </Badge>
                      </div>
                      <div className="flex items-center justify-between text-sm mt-1">
                        <span className="text-muted-foreground">Priority (lower=better):</span>
                        <span className="font-mono font-semibold">{conflict.winner.priority}</span>
                      </div>
                    </div>
                  </div>

                  {/* Rejected */}
                  <div>
                    <h4 className="flex items-center gap-2 font-semibold text-destructive mb-3">
                      <X className="h-4 w-4" /> Rejected Values
                    </h4>
                    <div className="space-y-3">
                      {conflict.rejected.map((rej, ridx) => (
                        <div key={ridx} className="bg-destructive/5 border border-destructive/10 rounded-lg p-3">
                          <div className="font-medium line-through opacity-80 mb-2">{String(rej.value)}</div>
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-muted-foreground">Source:</span>
                            <span className="font-mono text-destructive/80">{rej.source}</span>
                          </div>
                          <div className="flex items-center justify-between text-xs mt-1">
                            <span className="text-muted-foreground">Priority:</span>
                            <span className="font-mono opacity-80">{rej.priority}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
