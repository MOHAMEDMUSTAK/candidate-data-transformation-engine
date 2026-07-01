import React, { useEffect, useState } from "react"
import { Info, CheckCircle2, AlertTriangle, ShieldCheck, History } from "lucide-react"

import { getLastResult } from "@/lib/api"
import type { PipelineResponse, ProvenanceEntry } from "@/types"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export default function ExplainabilityPage() {
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

  if (loading) return <div className="p-8">Loading dashboard...</div>
  if (error) return <div className="p-8 text-destructive">{error}</div>
  if (!result || !result.candidate) return <div className="p-8">No candidate data available.</div>

  const candidate = result.candidate

  // Helper to render a field block
  const renderField = (label: string, fieldKey: string, value: any) => {
    // Find the winning provenance for this field
    const fieldProv = result.field_provenance[fieldKey] || {}
    const winner: ProvenanceEntry | undefined = fieldProv.winning_entry
    const rejected: ProvenanceEntry[] = fieldProv.rejected_entries || []
    
    // Find confidence if available
    const confidence = candidate.field_confidences?.find(c => c.field === fieldKey)?.confidence

    return (
      <Card className="mb-6 overflow-hidden border-l-4 border-l-primary">
        <div className="grid grid-cols-1 md:grid-cols-3">
          
          {/* Left Col: Final Value */}
          <div className="bg-muted/30 p-6 md:border-r">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-sm uppercase tracking-wider text-muted-foreground">{label}</h3>
              {confidence !== undefined && (
                <Badge variant={confidence > 0.8 ? "success" : confidence > 0.5 ? "warning" : "destructive"}>
                  {Math.round(confidence * 100)}% Conf
                </Badge>
              )}
            </div>
            
            <div className="mt-4">
              <div className="text-2xl font-bold break-words">
                {Array.isArray(value) ? value.join(", ") : 
                 typeof value === 'object' && value !== null ? JSON.stringify(value) : 
                 String(value || "N/A")}
              </div>
            </div>
          </div>

          {/* Right Col: Explainability */}
          <div className="p-6 md:col-span-2 space-y-4">
            <h4 className="flex items-center gap-2 font-semibold text-sm">
              <Info className="h-4 w-4 text-primary" /> 
              Why was this value selected?
            </h4>
            
            {winner ? (
              <div className="space-y-4 text-sm">
                <div className="rounded-md bg-secondary/50 p-4 border border-border/50">
                  <p className="font-medium mb-1">Explanation:</p>
                  <p className="text-muted-foreground">{winner.explanation}</p>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="text-muted-foreground block text-xs mb-1">Winning Source</span>
                    <Badge variant="outline" className="font-mono bg-background">
                      {winner.source_type} (Priority: {winner.source_priority})
                    </Badge>
                  </div>
                  <div>
                    <span className="text-muted-foreground block text-xs mb-1">Original Extracted Value</span>
                    <span className="font-mono text-xs px-2 py-1 bg-muted rounded">
                      {String(winner.original_value)}
                    </span>
                  </div>
                </div>

                {rejected.length > 0 && (
                  <div className="mt-4 border-t pt-4">
                    <span className="text-muted-foreground block text-xs mb-2">Rejected Values ({rejected.length})</span>
                    <div className="space-y-2">
                      {rejected.map((rej, i) => (
                        <div key={i} className="flex items-center justify-between text-xs bg-destructive/5 rounded px-3 py-2 border border-destructive/10 text-destructive/80">
                          <span className="line-through">{String(rej.original_value)}</span>
                          <span className="flex items-center gap-1">
                            from {rej.source_type} 
                            <span className="opacity-50">(Priority {rej.source_priority})</span>
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-sm text-muted-foreground italic">No provenance available for this field.</div>
            )}
          </div>
        </div>
      </Card>
    )
  }

  return (
    <div className="mx-auto max-w-5xl p-8">
      <div className="mb-8 flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Explainability Dashboard</h1>
          <p className="text-muted-foreground mt-2">
            Inspect every transformed field, its provenance, and the deterministic rules applied.
          </p>
        </div>
        <div className="text-right">
          <Badge variant="outline" className="mb-2">
            ID: {candidate.candidate_id}
          </Badge>
          <div className="text-sm text-muted-foreground flex items-center gap-2">
            <History className="h-4 w-4" />
            Processed in {result.total_time_ms}ms
          </div>
        </div>
      </div>

      <div className="space-y-1">
        {renderField("Full Name", "full_name", candidate.full_name)}
        {renderField("Email Addresses", "emails", candidate.emails)}
        {renderField("Phone Numbers", "phones", candidate.phones)}
        {renderField("Headline", "headline", candidate.headline)}
      </div>
    </div>
  )
}
