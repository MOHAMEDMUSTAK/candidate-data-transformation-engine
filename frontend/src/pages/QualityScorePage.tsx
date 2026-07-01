import React, { useEffect, useState } from "react"
import { CheckCircle, AlertCircle, TrendingUp, HelpCircle } from "lucide-react"

import { getLastResult } from "@/lib/api"
import type { PipelineResponse } from "@/types"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"

export default function QualityScorePage() {
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

  if (loading) return <div className="p-8">Loading quality score...</div>
  if (error) return <div className="p-8 text-destructive">{error}</div>
  if (!result || !result.quality_score) return <div className="p-8">No quality score data available.</div>

  const quality = result.quality_score
  const score = quality.overall_score

  const getScoreColor = (s: number) => {
    if (s >= 80) return "text-emerald-500"
    if (s >= 50) return "text-amber-500"
    return "text-destructive"
  }

  const getProgressColor = (s: number) => {
    if (s >= 80) return "bg-emerald-500"
    if (s >= 50) return "bg-amber-500"
    return "bg-destructive"
  }

  return (
    <div className="mx-auto max-w-5xl p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Candidate Profile Quality</h1>
        <p className="text-muted-foreground mt-2">
          Analyzes the completeness and richness of the final canonical candidate profile.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        
        {/* Overall Score */}
        <div className="col-span-1">
          <Card className="h-full flex flex-col justify-center items-center p-8 text-center border-primary/20">
            <h3 className="text-lg font-medium text-muted-foreground mb-4 uppercase tracking-wider">Overall Quality Score</h3>
            <div className={`text-7xl font-bold mb-4 ${getScoreColor(score)}`}>
              {score}
            </div>
            <Progress 
              value={score} 
              indicatorColor={getProgressColor(score)} 
              className="w-full max-w-[200px] h-3 mb-6" 
            />
            <p className="text-sm text-muted-foreground">
              Based on the presence and validity of critical profile fields weighted by importance.
            </p>
          </Card>
        </div>

        {/* Field Completeness Details */}
        <div className="col-span-1 md:col-span-2">
          <Card className="h-full">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-primary" />
                Completeness Breakdown
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-4">
                {Object.entries(quality.field_completeness).map(([field, isComplete]) => (
                  <div key={field} className="flex items-center justify-between p-3 rounded-lg border bg-muted/20">
                    <span className="font-medium text-sm">{field}</span>
                    {isComplete ? (
                      <Badge variant="success" className="gap-1">
                        <CheckCircle className="h-3 w-3" /> Complete
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="text-muted-foreground gap-1 border-muted-foreground/30">
                        <AlertCircle className="h-3 w-3" /> Missing
                      </Badge>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Improvement Suggestions */}
        <div className="col-span-1 md:col-span-3">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <HelpCircle className="h-5 w-5 text-amber-500" />
                Recommended Actions
              </CardTitle>
              <CardDescription>
                Suggestions to improve the candidate profile score.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {quality.suggestions.length > 0 ? (
                <ul className="space-y-3">
                  {quality.suggestions.map((suggestion, idx) => (
                    <li key={idx} className="flex items-start gap-3 bg-amber-500/5 p-4 rounded-md border border-amber-500/20">
                      <div className="mt-0.5 h-2 w-2 rounded-full bg-amber-500 shrink-0" />
                      <span className="text-sm font-medium">{suggestion}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="flex flex-col items-center justify-center p-8 text-center bg-emerald-500/5 border border-emerald-500/20 rounded-lg">
                  <CheckCircle className="h-10 w-10 text-emerald-500 mb-3" />
                  <h3 className="font-semibold text-emerald-700 dark:text-emerald-400">Excellent Profile!</h3>
                  <p className="text-sm text-emerald-600/80 dark:text-emerald-400/80 mt-1">
                    This candidate profile contains all highly-weighted information.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

      </div>
    </div>
  )
}
