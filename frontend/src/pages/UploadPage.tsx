import React, { useState } from "react"
import { useNavigate } from "react-router-dom"
import { UploadCloud, File, X, Play, Loader2, AlertCircle } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { runPipeline } from "@/lib/api"
import { cn } from "@/lib/utils"

export default function UploadPage() {
  const [files, setFiles] = useState<File[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  
  const navigate = useNavigate()

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFiles((prev) => [...prev, ...Array.from(e.dataTransfer.files)])
    }
  }

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFiles((prev) => [...prev, ...Array.from(e.target.files!)])
    }
  }

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const handleRunPipeline = async () => {
    if (files.length === 0) return

    setIsProcessing(true)
    setError(null)
    setProgress(0)

    // Simulate progress while waiting for backend
    const interval = setInterval(() => {
      setProgress((prev) => Math.min(prev + 10, 90))
    }, 200)

    try {
      await runPipeline(files)
      setProgress(100)
      clearInterval(interval)
      
      // Short delay for UX before redirecting
      setTimeout(() => {
        navigate("/explainability")
      }, 500)
    } catch (err: any) {
      clearInterval(interval)
      setError(err.response?.data?.detail || err.message || "Failed to process files")
      setIsProcessing(false)
    }
  }

  return (
    <div className="mx-auto max-w-4xl p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Data Ingestion</h1>
        <p className="text-muted-foreground mt-2">
          Upload structured and unstructured candidate data to begin the transformation pipeline.
        </p>
      </div>

      <div className="grid gap-8">
        <Card>
          <CardHeader>
            <CardTitle>Upload Sources</CardTitle>
            <CardDescription>
              Supported formats: CSV, JSON (ATS/LinkedIn), PDF, DOCX, TXT.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={cn(
                "flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-12 transition-colors",
                isDragging
                  ? "border-primary bg-primary/5"
                  : "border-muted-foreground/25 hover:border-primary/50 hover:bg-muted/50"
              )}
            >
              <div className="rounded-full bg-primary/10 p-4 mb-4">
                <UploadCloud className="h-8 w-8 text-primary" />
              </div>
              <h3 className="mb-1 text-lg font-semibold">Click or drag files to upload</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Upload multiple files from different sources to see conflict resolution in action.
              </p>
              
              <label htmlFor="file-upload">
                <Button variant="outline" asChild>
                  <span>Browse Files</span>
                </Button>
                <input
                  id="file-upload"
                  type="file"
                  multiple
                  className="hidden"
                  onChange={handleFileInput}
                />
              </label>
            </div>

            {files.length > 0 && (
              <div className="mt-8">
                <h4 className="mb-4 text-sm font-medium">Selected Files ({files.length})</h4>
                <div className="space-y-2">
                  {files.map((file, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between rounded-md border bg-card p-3 shadow-sm"
                    >
                      <div className="flex items-center gap-3">
                        <File className="h-5 w-5 text-blue-500" />
                        <div>
                          <p className="text-sm font-medium">{file.name}</p>
                          <p className="text-xs text-muted-foreground">
                            {(file.size / 1024).toFixed(1)} KB
                          </p>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="text-muted-foreground hover:text-destructive"
                        onClick={() => removeFile(i)}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {error && (
              <div className="mt-6 flex items-start gap-3 rounded-md bg-destructive/15 p-4 text-destructive">
                <AlertCircle className="mt-0.5 h-5 w-5" />
                <div className="text-sm">
                  <p className="font-medium">Pipeline Execution Failed</p>
                  <p className="mt-1 opacity-90">{error}</p>
                </div>
              </div>
            )}

            {isProcessing && (
              <div className="mt-6 space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium">Executing Transformation Pipeline...</span>
                  <span className="text-muted-foreground">{progress}%</span>
                </div>
                <Progress value={progress} />
              </div>
            )}
          </CardContent>
          <CardFooter className="flex justify-end gap-3 border-t bg-muted/20 px-6 py-4">
            <Button
              variant="outline"
              onClick={() => setFiles([])}
              disabled={files.length === 0 || isProcessing}
            >
              Clear
            </Button>
            <Button
              onClick={handleRunPipeline}
              disabled={files.length === 0 || isProcessing}
              className="gap-2"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4" />
                  Run Pipeline
                </>
              )}
            </Button>
          </CardFooter>
        </Card>
      </div>
    </div>
  )
}
