'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import FileUpload from '@/components/dashboard/FileUpload'
import TaskList from '@/components/dashboard/TaskList'
import AISuggestionsPanel from '@/components/dashboard/AISuggestionsPanel'
import { ArrowLeft, AlertCircle, CheckCircle } from 'lucide-react'
import { apiService, type UploadResponse, type Task, type JobStatus, type AITaskCandidate, type TaskSubmission, type TaskResult } from '@/lib/api'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

export default function DashboardPage() {
  const router = useRouter()
  const [currentStep, setCurrentStep] = useState<'upload' | 'ai_suggestions' | 'tasks' | 'results'>('upload')
  const [upload, setUpload] = useState<UploadResponse | null>(null)
  const [tasks, setTasks] = useState<Task[]>([])
  const [aiCandidates, setAICandidates] = useState<AITaskCandidate[]>([])
  const [jobResults, setJobResults] = useState<TaskResult[]>([])
  const [currentJobId, setCurrentJobId] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleUploadComplete = async (uploadResponse: UploadResponse) => {
    setUpload(uploadResponse)
    setLoading(true)
    setError(null)

    try {
      // Use AI analysis workflow
      const analyzeResponse = await apiService.analyzeDocument(uploadResponse.id)
      setAICandidates(analyzeResponse.candidates)
      setCurrentStep('ai_suggestions')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze document. Please check your OpenAI API key and billing.')
    } finally {
      setLoading(false)
    }
  }

  const handleAITaskSubmit = async (submissions: TaskSubmission[], theme: string, insertionPreference: string) => {
    if (!upload) return
    
    setLoading(true)
    setError(null)

    try {
      const submitResponse = await apiService.submitTasks({
        file_id: upload.id,
        tasks: submissions,
        theme,
        insertion_preference: insertionPreference
      })
      
      setCurrentJobId(submitResponse.job_id)
      
      // Poll for job completion
      const pollJobStatus = async () => {
        try {
          const statusResponse = await apiService.getJobStatus(submitResponse.job_id)
          setJobResults(statusResponse.tasks)
          
          if (statusResponse.status === 'completed' || statusResponse.status === 'failed') {
            setLoading(false)
            setCurrentStep('results')
          } else {
            // Continue polling
            setTimeout(pollJobStatus, 2000)
          }
        } catch (err) {
          setLoading(false)
          setError(err instanceof Error ? err.message : 'Failed to get job status')
        }
      }
      
      // Start polling
      setTimeout(pollJobStatus, 1000)
      
    } catch (err) {
      setLoading(false)
      setError(err instanceof Error ? err.message : 'Failed to submit tasks')
    }
  }

  const handleExecutionComplete = (jobs: JobStatus[]) => {
    // Convert JobStatus to TaskResult format
    const taskResults: TaskResult[] = jobs.map(job => ({
      id: job.id,
      task_id: job.task_id?.toString() || '',
      task_type: 'code_execution', // Default type for legacy jobs
      status: job.status,
      screenshot_url: job.screenshot_url,
      stdout: job.output_text,
      exit_code: job.execution_time ? 0 : 1, // Simple heuristic
      caption: job.error_message ? `Error: ${job.error_message}` : 'Code execution completed',
      assistant_answer: undefined
    }))
    setJobResults(taskResults)
    setCurrentStep('results')
  }

  const handleError = (errorMessage: string) => {
    setError(errorMessage)
  }

  const handlePreview = () => {
    // Pass the job results to the preview page
    const queryParams = new URLSearchParams({
      jobResults: JSON.stringify(jobResults),
      uploadId: upload?.id.toString() || ''
    })
    router.push(`/preview?${queryParams.toString()}`)
  }

  const resetWorkflow = () => {
    setCurrentStep('upload')
    setUpload(null)
    setTasks([])
    setAICandidates([])
    setJobResults([])
    setCurrentJobId(null)
    setError(null)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link href="/">
                <Button variant="ghost" size="sm">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to Home
                </Button>
              </Link>
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">LM</span>
                </div>
                <span className="text-xl font-bold gradient-text">LabMate AI</span>
              </div>
            </div>
            <div className="text-sm text-gray-600">
              Step {currentStep === 'upload' ? '1' : currentStep === 'ai_suggestions' ? '2' : currentStep === 'results' ? '3' : '4'} of 4
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Progress Indicator */}
        <div className="mb-8">
          <div className="flex items-center justify-center space-x-2">
            <div className={`flex items-center space-x-2 ${currentStep === 'upload' ? 'text-indigo-600' : 'text-green-600'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                currentStep === 'upload' ? 'bg-indigo-100' : 'bg-green-100'
              }`}>
                {currentStep === 'upload' ? '1' : <CheckCircle className="w-4 h-4" />}
              </div>
              <span className="font-medium text-sm">Upload</span>
            </div>
            <div className={`w-12 h-1 rounded ${
              ['ai_suggestions', 'results'].includes(currentStep) ? 'bg-green-500' : 'bg-gray-300'
            }`} />
            <div className={`flex items-center space-x-2 ${
              currentStep === 'ai_suggestions' ? 'text-indigo-600' : 
              currentStep === 'results' ? 'text-green-600' : 'text-gray-400'
            }`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                currentStep === 'ai_suggestions' ? 'bg-indigo-100' : 
                currentStep === 'results' ? 'bg-green-100' : 'bg-gray-100'
              }`}>
                {currentStep === 'ai_suggestions' ? '2' : 
                 currentStep === 'results' ? <CheckCircle className="w-4 h-4" /> : '2'}
              </div>
              <span className="font-medium text-sm">AI Review</span>
            </div>
            <div className={`w-12 h-1 rounded ${
              currentStep === 'results' ? 'bg-green-500' : 'bg-gray-300'
            }`} />
            <div className={`flex items-center space-x-2 ${
              currentStep === 'results' ? 'text-indigo-600' : 'text-gray-400'
            }`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                currentStep === 'results' ? 'bg-indigo-100' : 'bg-gray-100'
              }`}>
                3
              </div>
              <span className="font-medium text-sm">Execute & Report</span>
            </div>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6"
          >
            <Card className="border-red-200 bg-red-50">
              <CardContent className="p-4">
                <div className="flex items-center space-x-3">
                  <AlertCircle className="w-5 h-5 text-red-600" />
                  <div>
                    <h3 className="font-semibold text-red-800">Error</h3>
                    <p className="text-sm text-red-600">{error}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Step Content */}
        <motion.div
          key={currentStep}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
        >
          {currentStep === 'upload' && (
            <div className="space-y-6">
              <div className="text-center">
                <h1 className="text-4xl font-bold mb-4 gradient-text">
                  Upload Your Assignment
                </h1>
                <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                  Upload your DOCX or PDF lab assignment and let AI analyze which parts need screenshots and which need AI-generated answers.
                </p>
              </div>
              <FileUpload
                onUploadComplete={handleUploadComplete}
                onError={handleError}
              />
            </div>
          )}

          {currentStep === 'ai_suggestions' && (
            <div className="space-y-6">
              <div className="text-center">
                <h1 className="text-4xl font-bold mb-4 gradient-text">
                  AI Suggestions
                </h1>
                <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                  Review AI-generated task suggestions and customize them before execution.
                </p>
              </div>
              <AISuggestionsPanel
                candidates={aiCandidates}
                onSubmit={handleAITaskSubmit}
                onError={handleError}
              />
            </div>
          )}


          {currentStep === 'results' && (
            <div className="space-y-6">
              <div className="text-center">
                <h1 className="text-4xl font-bold mb-4 gradient-text">
                  Execution Complete!
                </h1>
                <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                  Your code has been executed and screenshots have been generated. You can now preview and download your report.
                </p>
              </div>
              <Card>
                <CardHeader>
                  <CardTitle>Results Summary</CardTitle>
                  <CardDescription>
                    Overview of code execution and screenshot generation
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid md:grid-cols-3 gap-4">
                    <div className="text-center p-4 bg-green-50 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">
                        {jobResults.filter(job => job.status === 'completed').length}
                      </div>
                      <div className="text-sm text-green-600">Successfully Executed</div>
                    </div>
                    <div className="text-center p-4 bg-red-50 rounded-lg">
                      <div className="text-2xl font-bold text-red-600">
                        {jobResults.filter(job => job.status === 'failed').length}
                      </div>
                      <div className="text-sm text-red-600">Failed</div>
                    </div>
                    <div className="text-center p-4 bg-blue-50 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">
                        {jobResults.filter(job => job.screenshot_url).length}
                      </div>
                      <div className="text-sm text-blue-600">Screenshots Generated</div>
                    </div>
                  </div>
                  <div className="flex justify-center space-x-4">
                    <Button
                      onClick={handlePreview}
                      className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700"
                    >
                      Preview & Download Report
                    </Button>
                    <Button
                      onClick={resetWorkflow}
                      variant="outline"
                    >
                      Start New Assignment
                    </Button>
                  </div>
                </CardContent>
              </Card>

              {/* Individual Results */}
              {jobResults.length > 0 && (
                <div className="space-y-4">
                  <h2 className="text-2xl font-bold text-center">Execution Results</h2>
                  {jobResults.map((result, index) => (
                    <Card key={result.id} className="border-l-4 border-l-indigo-500">
                      <CardHeader>
                        <CardTitle className="flex items-center space-x-2">
                          <span>Task {index + 1}</span>
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            result.status === 'completed' 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {result.status}
                          </span>
                        </CardTitle>
                        <CardDescription>
                          {result.caption || `Code execution ${result.status}`}
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        {/* Screenshot */}
                        {result.screenshot_url && (
                          <div>
                            <h4 className="font-semibold mb-2">Screenshot:</h4>
                            <div className="border rounded-lg overflow-hidden">
                              <img 
                                src={`http://localhost:8000${result.screenshot_url}`}
                                alt={`Execution result for task ${index + 1}`}
                                className="w-full max-w-2xl mx-auto"
                                onError={(e) => {
                                  console.error('Screenshot load error:', result.screenshot_url);
                                  e.currentTarget.style.display = 'none';
                                }}
                              />
                            </div>
                          </div>
                        )}
                        
                        {/* Output */}
                        {result.stdout && (
                          <div>
                            <h4 className="font-semibold mb-2">Output:</h4>
                            <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm whitespace-pre-wrap">
                              {result.stdout}
                            </div>
                          </div>
                        )}
                        
                        {/* AI Answer */}
                        {result.assistant_answer && (
                          <div>
                            <h4 className="font-semibold mb-2">AI Answer:</h4>
                            <div className="bg-blue-50 p-4 rounded-lg">
                              {result.assistant_answer}
                            </div>
                          </div>
                        )}
                        
                        {/* Exit Code */}
                        <div className="text-sm text-gray-600">
                          Exit Code: {result.exit_code !== null ? result.exit_code : 'N/A'}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          )}
        </motion.div>
      </main>
    </div>
  )
}
