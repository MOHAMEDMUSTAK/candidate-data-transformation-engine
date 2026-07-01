import React, { useEffect, useState } from "react"
import { CheckCircle2, Circle, Clock, Activity, AlertTriangle } from "lucide-react"

import { getLastResult } from "@/lib/api"
import type { PipelineResponse, StageResult } from "@/types"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"

export default function PipelinePage() {
  const [result, setResult] = useState<PipelineResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeStage, setActiveStage] = useState<number | null>(null)

  useEffect(() => {
    getLastResult()
      .then((data) => {
        setResult(data)
        setLoading(false)
        if (data.stage_results.length > 0) {
          setActiveStage(data.stage_results.length - 1)
        }
      })
      .catch((err) => {
        setError("Failed to load pipeline results. Have you run the pipeline yet?")
        setLoading(false)
      })
  }, [])

  if (loading) return <div className="p-8">Loading dashboard...</div>
  if (error) return <div className="p-8 text-destructive">{error}</div>
  if (!result) return <div className="p-8">No data available.</div>

  const stages = result.stage_results
  const selectedStage = activeStage !== null ? stages.find(s => s.stage_index === activeStage) : null

  return (
    <div className="mx-auto max-w-6xl p-8 h-[calc(100vh-4rem)] flex flex-col">
      <div className="mb-8 flex items-end justify-between shrink-0">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Transformation Replay</h1>
          <p className="text-muted-foreground mt-2">
            Interactive timeline of the deterministic 12-stage transformation pipeline.
          </p>
        </div>
        <div className="text-right">
          <Badge variant="outline" className="mb-2">
            {stages.length} Stages Executed
          </Badge>
          <div className="text-sm font-medium flex items-center justify-end gap-2 text-primary">
            <Activity className="h-4 w-4" />
            Total Time: {result.total_time_ms}ms
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 flex-1 min-h-0">
        
        {/* Timeline View */}
        <div className="col-span-1 border-r pr-6 overflow-y-auto pb-8 relative">
          <div className="absolute left-[27px] top-4 bottom-8 w-0.5 bg-border -z-10"></div>
          
          <div className="space-y-6">
            {stages.map((stage) => {
              const isSelected = activeStage === stage.stage_index
              const hasWarnings = stage.warnings.length > 0
              
              return (
                <button
                  key={stage.stage_index}
                  onClick={() => setActiveStage(stage.stage_index)}
                  className={`w-full flex items-start gap-4 text-left p-3 rounded-lg transition-all ${
                    isSelected ? "bg-primary/5 ring-1 ring-primary/20" : "hover:bg-muted"
                  }`}
                >
                  <div className="relative mt-1">
                    {stage.status === 'success' ? (
                      <CheckCircle2 className={`h-6 w-6 z-10 bg-background rounded-full ${isSelected ? 'text-primary' : 'text-emerald-500'}`} />
                    ) : hasWarnings ? (
                      <AlertTriangle className={`h-6 w-6 z-10 bg-background rounded-full ${isSelected ? 'text-primary' : 'text-amber-500'}`} />
                    ) : (
                      <Circle className={`h-6 w-6 z-10 bg-background rounded-full ${isSelected ? 'text-primary' : 'text-muted-foreground'}`} />
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="flex justify-between items-baseline mb-1">
                      <h4 className={`font-semibold text-sm ${isSelected ? 'text-primary' : ''}`}>
                        {stage.stage_index + 1}. {stage.stage_name}
                      </h4>
                      <span className="text-xs text-muted-foreground font-mono">
                        {stage.execution_time_ms}ms
                      </span>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground mt-1.5">
                      <span className="bg-background border rounded px-1.5 py-0.5">{stage.records_processed} Records</span>
                      <span className="bg-background border rounded px-1.5 py-0.5">{stage.fields_transformed} Fields</span>
                    </div>
                  </div>
                </button>
              )
            })}
          </div>
        </div>

        {/* Stage Details View */}
        <div className="col-span-2 overflow-y-auto pb-8">
          {selectedStage ? (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-300">
              <div className="flex items-center justify-between border-b pb-4">
                <div>
                  <h2 className="text-2xl font-bold">{selectedStage.stage_name}</h2>
                  <p className="text-muted-foreground mt-1 text-sm">Execution details and applied transformations.</p>
                </div>
                <div className="text-right">
                  <Badge variant={selectedStage.warnings.length > 0 ? "warning" : "success"}>
                    {selectedStage.status.toUpperCase()}
                  </Badge>
                  <div className="text-sm font-mono mt-2 text-muted-foreground">
                    <Clock className="inline h-3 w-3 mr-1" />
                    {selectedStage.execution_time_ms.toFixed(2)}ms
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm text-muted-foreground font-medium uppercase tracking-wider">Metrics</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm">Records Processed</span>
                      <span className="font-semibold text-lg">{selectedStage.records_processed}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Fields Transformed</span>
                      <span className="font-semibold text-lg text-primary">{selectedStage.fields_transformed}</span>
                    </div>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm text-muted-foreground font-medium uppercase tracking-wider">Errors & Warnings</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm">Errors</span>
                      <span className={`font-semibold text-lg ${selectedStage.errors.length > 0 ? 'text-destructive' : 'text-muted-foreground'}`}>
                        {selectedStage.errors.length}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Warnings</span>
                      <span className={`font-semibold text-lg ${selectedStage.warnings.length > 0 ? 'text-amber-500' : 'text-muted-foreground'}`}>
                        {selectedStage.warnings.length}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {selectedStage.changes.length > 0 && (
                <Card className="border-primary/20">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium uppercase tracking-wider flex items-center gap-2">
                      State Changes
                      <Badge variant="secondary" className="ml-2 bg-primary/10 text-primary">{selectedStage.changes.length}</Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {selectedStage.changes.map((change, idx) => (
                        <div key={idx} className="bg-muted/40 p-3 rounded-md border text-sm font-mono">
                          <pre className="whitespace-pre-wrap break-words">
                            {JSON.stringify(change, null, 2)}
                          </pre>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {selectedStage.warnings.length > 0 && (
                <Card className="border-amber-500/50 bg-amber-500/5">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-amber-500 uppercase tracking-wider">Warnings</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="list-disc list-inside text-sm text-amber-700/80 dark:text-amber-400 space-y-1">
                      {selectedStage.warnings.map((w, idx) => (
                        <li key={idx}>{w}</li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-muted-foreground">
              Select a stage from the timeline to view details.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
