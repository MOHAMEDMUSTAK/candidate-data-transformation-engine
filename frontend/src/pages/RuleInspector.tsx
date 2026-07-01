import React, { useEffect, useState } from "react"
import { Search, ListFilter, SlidersHorizontal } from "lucide-react"

import { getLastResult } from "@/lib/api"
import type { PipelineResponse, RuleApplication } from "@/types"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export default function RuleInspector() {
  const [result, setResult] = useState<PipelineResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState("")
  const [filterCategory, setFilterCategory] = useState<string | null>(null)

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

  if (loading) return <div className="p-8">Loading rules...</div>
  if (error) return <div className="p-8 text-destructive">{error}</div>
  if (!result) return <div className="p-8">No data available.</div>

  const { rule_applications } = result

  // Extract unique categories for filtering
  const categories = Array.from(new Set(rule_applications.map(r => r.rule_category)))

  // Filter rules
  const filteredRules = rule_applications.filter(rule => {
    const matchesSearch = 
      rule.rule_name.toLowerCase().includes(search.toLowerCase()) ||
      rule.description.toLowerCase().includes(search.toLowerCase()) ||
      rule.field.toLowerCase().includes(search.toLowerCase())
    
    const matchesCategory = filterCategory ? rule.rule_category === filterCategory : true

    return matchesSearch && matchesCategory
  })

  return (
    <div className="mx-auto max-w-6xl p-8 h-[calc(100vh-4rem)] flex flex-col">
      <div className="mb-8 flex-shrink-0">
        <h1 className="text-3xl font-bold tracking-tight">Rule Inspector</h1>
        <p className="text-muted-foreground mt-2">
          Audit every transformation rule applied to the data.
        </p>
      </div>

      <Card className="flex-1 flex flex-col overflow-hidden min-h-0 border-primary/20">
        <CardHeader className="bg-muted/30 border-b pb-4 pt-6 shrink-0">
          <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <SlidersHorizontal className="h-5 w-5 text-primary" />
              Applied Rules ({filteredRules.length} of {rule_applications.length})
            </CardTitle>
            
            <div className="flex items-center gap-3 w-full md:w-auto">
              <div className="relative flex-1 md:w-64">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Search rules..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full bg-background rounded-md border border-input pl-9 pr-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                />
              </div>
              
              <div className="flex gap-2">
                <Badge 
                  variant={filterCategory === null ? "default" : "outline"} 
                  className="cursor-pointer"
                  onClick={() => setFilterCategory(null)}
                >
                  All
                </Badge>
                {categories.map(cat => (
                  <Badge 
                    key={cat}
                    variant={filterCategory === cat ? "default" : "outline"}
                    className="cursor-pointer capitalize"
                    onClick={() => setFilterCategory(cat)}
                  >
                    {cat}
                  </Badge>
                ))}
              </div>
            </div>
          </div>
        </CardHeader>
        
        <CardContent className="flex-1 overflow-y-auto p-0">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-muted-foreground uppercase bg-muted/50 sticky top-0 backdrop-blur-sm shadow-sm">
              <tr>
                <th className="px-6 py-4 font-medium">Rule Name & Category</th>
                <th className="px-6 py-4 font-medium">Field</th>
                <th className="px-6 py-4 font-medium">Transformation</th>
                <th className="px-6 py-4 font-medium">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {filteredRules.length > 0 ? (
                filteredRules.map((rule, idx) => (
                  <tr key={idx} className="hover:bg-muted/30 transition-colors">
                    <td className="px-6 py-4">
                      <div className="font-mono font-semibold text-primary">{rule.rule_name}</div>
                      <Badge variant="secondary" className="mt-1 text-[10px] uppercase">
                        {rule.rule_category}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 font-mono text-xs">{rule.field}</td>
                    <td className="px-6 py-4">
                      <div className="flex flex-col gap-1 text-xs font-mono bg-background p-2 rounded border">
                        <div className="flex">
                          <span className="text-muted-foreground w-10">In:</span> 
                          <span className="text-destructive truncate max-w-[200px]" title={String(rule.original_value)}>
                            {String(rule.original_value) || 'null'}
                          </span>
                        </div>
                        <div className="flex">
                          <span className="text-muted-foreground w-10">Out:</span> 
                          <span className="text-emerald-600 dark:text-emerald-400 font-semibold truncate max-w-[200px]" title={String(rule.transformed_value)}>
                            {String(rule.transformed_value) || 'null'}
                          </span>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-muted-foreground max-w-sm">
                      {rule.description}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={4} className="px-6 py-12 text-center text-muted-foreground">
                    No rules match your filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  )
}
