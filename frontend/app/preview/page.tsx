'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Button } from '../../components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card'
import PreviewGrid from '../../components/preview/PreviewGrid'
import { ArrowLeft, CheckCircle, AlertCircle, FileText } from 'lucide-react'
import { apiService, type JobStatus, type ComposeResponse, type TaskResult } from '../../lib/api'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'

export default function PreviewPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [jobs, setJobs] = useState<JobStatus[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [reportGenerated, setReportGenerated] = useState<ComposeResponse | null>(null)
  const [uploadId, setUploadId] = useState<number | null>(null)

  useEffect(() => {
    loadJobs()
  }, [])

  const loadJobs = async () => {
    setLoading(true)
    try {
      // Get job results from URL parameters
      const jobResultsParam = searchParams.get('jobResults')
      const uploadIdParam = searchParams.get('uploadId')
      
      if (jobResultsParam && uploadIdParam) {
        const jobResults: TaskResult[] = JSON.parse(jobResultsParam)
        setUploadId(parseInt(uploadIdParam))
        
        // Convert TaskResult to JobStatus format
        const convertedJobs: JobStatus[] = jobResults.map(result => ({
          id: result.id,
          task_id: parseInt(result.task_id) || result.id,
          question_text: result.caption || `Task ${result.task_id}`,
          status: result.status,
          output_text: result.stdout || '',
          execution_time: 0, // We don't have this in TaskResult
          screenshot_url: result.screenshot_url ? `http://localhost:8000${result.screenshot_url}` : undefined,
          error_message: result.status === 'failed' ? (result.stdout || 'Execution failed') : undefined
        }))
        
        setJobs(convertedJobs)
      } else {
        // Fallback to mock data if no params
        const mockJobs: JobStatus[] = [
          {
            id: 1,
            task_id: 1,
            question_text: "Write a Python function to calculate the factorial of a number.",
            status: "completed",
            output_text: "Factorial function created successfully. Test with factorial(5) = 120",
            execution_time: 150,
            screenshot_url: "/screenshots/1/screenshot_abc123.png"
          },
          {
            id: 2,
            task_id: 2,
            question_text: "Create a list comprehension to generate squares of numbers 1 to 10.",
            status: "completed",
            output_text: "[1, 4, 9, 16, 25, 36, 49, 64, 81, 100]",
            execution_time: 89,
            screenshot_url: "/screenshots/2/screenshot_def456.png"
          }
        ]
        setJobs(mockJobs)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load jobs')
    } finally {
      setLoading(false)
    }
  }

  const handleRemoveJob = (jobId: number) => {
    setJobs(prev => prev.filter(job => job.id !== jobId))
  }

  const handlePreviewJob = (job: JobStatus) => {
    // Open screenshot in new tab or modal
    if (job.screenshot_url) {
      window.open(job.screenshot_url, '_blank')
    }
  }

  const handleGenerateReport = async (screenshotOrder: number[]) => {
    try {
      if (!uploadId) {
        throw new Error('Upload ID not found')
      }
      
      const response = await apiService.composeReport({
        upload_id: uploadId,
        screenshot_order: screenshotOrder
      })
      
      setReportGenerated(response)
      
      // Auto-download the report
      const blob = await apiService.downloadReport(response.report_id)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = response.filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate report')
    }
  }

  const handleReset = () => {
    setReportGenerated(null)
    router.push('/dashboard')
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center"
        >
          <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
          </div>
          <h2 className="text-xl font-semibold text-white">Loading preview...</h2>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-black">
      {/* Header */}
      <header className="bg-black/80 backdrop-blur-sm border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link href="/dashboard">
                <Button variant="ghost" size="sm" className="text-white hover:bg-white/10">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to Dashboard
                </Button>
              </Link>
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                  <FileText className="w-4 h-4 text-white" />
                </div>
                <span className="text-xl font-bold text-white">LabMate AI</span>
              </div>
            </div>
            <div className="text-sm text-white/60">
              Preview & Download
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Success Message */}
        {reportGenerated && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6"
          >
            <Card className="border-green-500/50 bg-green-500/10">
              <CardContent className="p-4">
                <div className="flex items-center space-x-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <div>
                    <h3 className="font-semibold text-green-400">Report Generated Successfully!</h3>
                    <p className="text-sm text-green-300">
                      Your report "{reportGenerated.filename}" has been generated and downloaded.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Error Display */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6"
          >
            <Card className="border-red-500/50 bg-red-500/10">
              <CardContent className="p-4">
                <div className="flex items-center space-x-3">
                  <AlertCircle className="w-5 h-5 text-red-400" />
                  <div>
                    <h3 className="font-semibold text-red-400">Error</h3>
                    <p className="text-sm text-red-300">{error}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Page Header */}
        <div className="text-center mb-8">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h1 className="text-4xl font-bold mb-4 text-white">
              Preview & Download
            </h1>
                <p className="text-xl text-white/80 max-w-2xl mx-auto">
                  Review your generated screenshots, reorder them as needed, and update your original document with the screenshots.
                </p>
          </motion.div>
        </div>

        {/* Preview Grid */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <PreviewGrid
            jobs={jobs}
            onRemoveJob={handleRemoveJob}
            onPreviewJob={handlePreviewJob}
            onGenerateReport={handleGenerateReport}
            onReset={handleReset}
          />
        </motion.div>

        {/* Instructions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="mt-12"
        >
          <Card className="bg-gray-900/50 border-white/10">
            <CardHeader>
              <CardTitle className="text-white">How to Use This Preview</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid md:grid-cols-3 gap-6">
                <div className="space-y-2">
                  <h4 className="font-semibold text-blue-400">1. Review Screenshots</h4>
                  <p className="text-sm text-white/80">
                    Click on any screenshot to preview it in full size. Check that the code output looks correct.
                  </p>
                </div>
                <div className="space-y-2">
                  <h4 className="font-semibold text-blue-400">2. Reorder if Needed</h4>
                  <p className="text-sm text-white/80">
                    Drag and drop screenshots to reorder them. The final report will maintain this order.
                  </p>
                </div>
                <div className="space-y-2">
                  <h4 className="font-semibold text-blue-400">3. Update Document</h4>
                  <p className="text-sm text-white/80">
                    Click "Update & Download Document" to add screenshots to your original assignment document.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </main>
    </div>
  )
}
