'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import FileUpload from '@/components/dashboard/FileUpload'
import TaskList from '@/components/dashboard/TaskList'
import AISuggestionsPanel from '@/components/dashboard/AISuggestionsPanel'
import { ArrowLeft, AlertCircle, CheckCircle, FileText } from 'lucide-react'
import { apiService, type UploadResponse, type Task, type JobStatus, type AITaskCandidate, type TaskSubmission, type TaskResult } from '@/lib/api'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/BasicAuthContext'

export default function DashboardPage() {
  const router = useRouter()
  const { user, loading } = useAuth()
  const [currentStep, setCurrentStep] = useState<'upload' | 'ai_suggestions' | 'tasks' | 'results'>('upload')
  const [upload, setUpload] = useState<UploadResponse | null>(null)
  const [tasks, setTasks] = useState<Task[]>([])
  const [aiCandidates, setAICandidates] = useState<AITaskCandidate[]>([])
  const [jobResults, setJobResults] = useState<TaskResult[]>([])
  const [currentJobId, setCurrentJobId] = useState<number | null>(null)
  const [loadingState, setLoadingState] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showLanguageModal, setShowLanguageModal] = useState(false)
  const [selectedLanguage, setSelectedLanguage] = useState<string | null>(null)
  const [showFilenameModal, setShowFilenameModal] = useState(false)
  const [customFilename, setCustomFilename] = useState('')

  // Redirect to homepage if not authenticated
  useEffect(() => {
    if (!loading && !user) {
      router.push('/')
    }
  }, [user, loading, router])

  // Show loading while checking authentication
  if (loading) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center mr-3 mx-auto mb-4">
            <FileText className="w-4 h-4 text-white" />
          </div>
          <p className="text-white/80">Loading...</p>
        </div>
      </div>
    )
  }

  // Don't render anything if not authenticated (will redirect)
  if (!user) {
    return null
  }

  const handleUploadComplete = async (uploadResponse: UploadResponse) => {
    setUpload(uploadResponse)
    setShowLanguageModal(true)
  }

  const handleLanguageSelect = async (language: string) => {
    setSelectedLanguage(language)
    setShowLanguageModal(false)
    
    // Skip filename modal for Java, HTML, React, Node since we extract names from code or use defaults
    if (['java', 'html', 'react', 'node'].includes(language)) {
      setLoadingState(true)
      setError(null)

      try {
        // Set a default filename (will be overridden by automatic extraction)
        const defaultFilenames: Record<string, string> = {
          java: 'Main',
          html: 'index.html',
          react: 'App.jsx',
          node: 'server.js'
        }
        await apiService.setFilename(upload!.id, defaultFilenames[language] || 'Main')
        
        // Now proceed with AI analysis
        const analyzeResponse = await apiService.analyzeDocument(upload!.id, language)
        setAICandidates(analyzeResponse.candidates)
        setCurrentStep('ai_suggestions')
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to analyze document. Please check your OpenAI API key and billing.')
      } finally {
        setLoadingState(false)
      }
    } else {
      // Show filename modal for Python and C
      setShowFilenameModal(true)
    }
  }

  const handleFilenameSubmit = async () => {
    if (!customFilename.trim()) {
      setError('Please enter a filename')
      return
    }

    setLoading(true)
    setError(null)

    try {
      // Set the custom filename
      await apiService.setFilename(upload!.id, customFilename.trim())
      
      // Now proceed with AI analysis
      const analyzeResponse = await apiService.analyzeDocument(upload!.id, selectedLanguage!)
      setAICandidates(analyzeResponse.candidates)
      setCurrentStep('ai_suggestions')
      setShowFilenameModal(false)
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
            setLoadingState(false)
            setCurrentStep('results')
          } else {
            // Continue polling
            setTimeout(pollJobStatus, 2000)
          }
        } catch (err) {
          setLoadingState(false)
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
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
      <header className="bg-black/80 backdrop-blur-sm border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link href="/">
                <Button variant="ghost" size="sm" className="text-white hover:bg-white/10">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to Home
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
            <div className={`flex items-center space-x-2 ${currentStep === 'upload' ? 'text-blue-400' : 'text-green-400'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                currentStep === 'upload' ? 'bg-blue-500/20' : 'bg-green-500/20'
              }`}>
                {currentStep === 'upload' ? '1' : <CheckCircle className="w-4 h-4" />}
              </div>
              <span className="font-medium text-sm">Upload</span>
            </div>
            <div className={`w-12 h-1 rounded ${
              ['ai_suggestions', 'results'].includes(currentStep) ? 'bg-green-500' : 'bg-gray-600'
            }`} />
            <div className={`flex items-center space-x-2 ${
              currentStep === 'ai_suggestions' ? 'text-blue-400' : 
              currentStep === 'results' ? 'text-green-400' : 'text-gray-400'
            }`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                currentStep === 'ai_suggestions' ? 'bg-blue-500/20' : 
                currentStep === 'results' ? 'bg-green-500/20' : 'bg-gray-600/20'
              }`}>
                {currentStep === 'ai_suggestions' ? '2' : 
                 currentStep === 'results' ? <CheckCircle className="w-4 h-4" /> : '2'}
              </div>
              <span className="font-medium text-sm">AI Review</span>
            </div>
            <div className={`w-12 h-1 rounded ${
              currentStep === 'results' ? 'bg-green-500' : 'bg-gray-600'
            }`} />
            <div className={`flex items-center space-x-2 ${
              currentStep === 'results' ? 'text-blue-400' : 'text-gray-400'
            }`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                currentStep === 'results' ? 'bg-blue-500/20' : 'bg-gray-600/20'
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
                <h1 className="text-4xl font-bold mb-4 text-white">
                  Upload Your Assignment
                </h1>
                <p className="text-xl text-white/80 max-w-2xl mx-auto">
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
                <h1 className="text-4xl font-bold mb-4 text-white">
                  AI Suggestions
                </h1>
                <p className="text-xl text-white/80 max-w-2xl mx-auto">
                  Review AI-generated task suggestions and customize them before execution.
                </p>
              </div>
              <AISuggestionsPanel
                candidates={aiCandidates}
                onSubmit={handleAITaskSubmit}
                onError={handleError}
                initialTheme={selectedLanguage === 'c' ? 'codeblocks' : selectedLanguage === 'java' ? 'notepad' : 'idle'}
              />
            </div>
          )}


          {currentStep === 'results' && (
            <div className="space-y-6">
              <div className="text-center">
                <h1 className="text-4xl font-bold mb-4 text-white">
                  Execution Complete!
                </h1>
                <p className="text-xl text-white/80 max-w-2xl mx-auto">
                  Your code has been executed and screenshots have been generated. You can now preview and download your report.
                </p>
              </div>
              <Card className="bg-gray-900/50 border-white/10">
                <CardHeader>
                  <CardTitle className="text-white">Results Summary</CardTitle>
                  <CardDescription className="text-white/60">
                    Overview of code execution and screenshot generation
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid md:grid-cols-3 gap-4">
                    <div className="text-center p-4 bg-green-500/10 rounded-lg">
                      <div className="text-2xl font-bold text-green-400">
                        {jobResults.filter(job => job.status === 'completed').length}
                      </div>
                      <div className="text-sm text-green-400">Successfully Executed</div>
                    </div>
                    <div className="text-center p-4 bg-red-500/10 rounded-lg">
                      <div className="text-2xl font-bold text-red-400">
                        {jobResults.filter(job => job.status === 'failed').length}
                      </div>
                      <div className="text-sm text-red-400">Failed</div>
                    </div>
                    <div className="text-center p-4 bg-blue-500/10 rounded-lg">
                      <div className="text-2xl font-bold text-blue-400">
                        {jobResults.filter(job => job.screenshot_url).length}
                      </div>
                      <div className="text-sm text-blue-400">Screenshots Generated</div>
                    </div>
                  </div>
                  <div className="flex justify-center space-x-4">
                    <Button
                      onClick={handlePreview}
                      className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700"
                    >
                      Preview & Download Report
                    </Button>
                    <Button
                      onClick={resetWorkflow}
                      variant="outline"
                      className="border-white/20 text-white hover:bg-white/10"
                    >
                      Start New Assignment
                    </Button>
                  </div>
                </CardContent>
              </Card>

              {/* Individual Results */}
              {jobResults.length > 0 && (
                <div className="space-y-4">
                  <h2 className="text-2xl font-bold text-center text-white">Execution Results</h2>
                  {jobResults.map((result, index) => (
                    <Card key={result.id} className="border-l-4 border-l-blue-500 bg-gray-900/50 border-white/10">
                      <CardHeader>
                        <CardTitle className="flex items-center space-x-2 text-white">
                          <span>Task {index + 1}</span>
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            result.status === 'completed' 
                              ? 'bg-green-500/20 text-green-400' 
                              : 'bg-red-500/20 text-red-400'
                          }`}>
                            {result.status}
                          </span>
                        </CardTitle>
                        <CardDescription className="text-white/60">
                          {result.caption || `Code execution ${result.status}`}
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        {/* Screenshot */}
                        {result.screenshot_url && (
                          <div>
                            <h4 className="font-semibold mb-2 text-white">Screenshot:</h4>
                            <div className="border border-white/20 rounded-lg overflow-hidden">
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
                            <h4 className="font-semibold mb-2 text-white">Output:</h4>
                            <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm whitespace-pre-wrap border border-white/20">
                              {result.stdout}
                            </div>
                          </div>
                        )}
                        
                        {/* AI Answer */}
                        {result.assistant_answer && (
                          <div>
                            <h4 className="font-semibold mb-2 text-white">AI Answer:</h4>
                            <div className="bg-blue-500/10 p-4 rounded-lg border border-white/20">
                              <p className="text-white/80">{result.assistant_answer}</p>
                            </div>
                          </div>
                        )}
                        
                        {/* Exit Code */}
                        <div className="text-sm text-white/60">
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

      {/* Language Selection Modal */}
      {showLanguageModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="bg-gray-900 rounded-2xl p-8 max-w-md w-full border border-white/10"
          >
            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-6">
                <FileText className="w-8 h-8 text-white" />
              </div>
              
              <h2 className="text-2xl font-bold text-white mb-2">
                Select Programming Language
              </h2>
              <p className="text-white/80 mb-8">
                Choose the programming language for your assignment to get the appropriate IDE theme
              </p>
              
              <div className="space-y-3">
                <button
                  onClick={() => handleLanguageSelect('python')}
                  className="w-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white px-6 py-4 rounded-xl font-semibold transition-all duration-300"
                >
                  Python (IDLE)
                </button>
                
                <button
                  onClick={() => handleLanguageSelect('java')}
                  className="w-full bg-gradient-to-r from-orange-500 to-red-600 hover:from-orange-600 hover:to-red-700 text-white px-6 py-4 rounded-xl font-semibold transition-all duration-300"
                >
                  Java (Notepad)
                </button>
                
                <button
                  onClick={() => handleLanguageSelect('c')}
                  className="w-full bg-gradient-to-r from-green-500 to-teal-600 hover:from-green-600 hover:to-teal-700 text-white px-6 py-4 rounded-xl font-semibold transition-all duration-300"
                >
                  C Programming (CodeBlocks)
                </button>
                
                <button
                  onClick={() => handleLanguageSelect('html')}
                  className="w-full bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-600 hover:to-orange-600 text-white px-6 py-4 rounded-xl font-semibold transition-all duration-300"
                >
                  HTML/CSS/JS (VS Code)
                </button>
                
                <button
                  onClick={() => handleLanguageSelect('react')}
                  className="w-full bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white px-6 py-4 rounded-xl font-semibold transition-all duration-300"
                >
                  React (VS Code)
                </button>
                
                <button
                  onClick={() => handleLanguageSelect('node')}
                  className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white px-6 py-4 rounded-xl font-semibold transition-all duration-300"
                >
                  Node.js/Express (VS Code)
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      )}

      {/* Filename Input Modal */}
      {showFilenameModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="bg-gray-900 rounded-2xl p-8 max-w-md w-full border border-white/10"
          >
            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-6">
                <FileText className="w-8 h-8 text-white" />
              </div>
              
              <h2 className="text-2xl font-bold text-white mb-2">
                {selectedLanguage === 'c' ? 'Enter C Filename' : selectedLanguage === 'java' ? 'Enter Java Filename' : 'Enter Python Filename'}
              </h2>
              <p className="text-white/80 mb-6">
                {selectedLanguage === 'c'
                  ? 'What would you like to name your C file? (e.g., exp5, assignment1, lab3)'
                  : selectedLanguage === 'java'
                  ? 'What would you like to name your Java file? (e.g., exp5, assignment1, lab3)'
                  : 'What would you like to name your Python file? (e.g., exp5, assignment1, lab3)'}
              </p>
              
              <div className="mb-6">
                <input
                  type="text"
                  value={customFilename}
                  onChange={(e) => setCustomFilename(e.target.value)}
                  placeholder={selectedLanguage === 'c' ? 'Enter filename (without .c)'
                    : selectedLanguage === 'java' ? 'Enter filename (without .java)'
                    : 'Enter filename (without .py)'}
                  className="w-full px-4 py-3 bg-gray-800 border border-white/20 rounded-xl text-white placeholder-white/60 focus:outline-none focus:border-blue-500 transition-colors"
                  autoFocus
                />
                <p className="text-sm text-white/60 mt-2">
                  {selectedLanguage === 'c' ? 'The .c extension will be added automatically'
                    : selectedLanguage === 'java' ? 'The .java extension will be added automatically'
                    : 'The .py extension will be added automatically'}
                </p>
              </div>
              
              <div className="flex space-x-3">
                <button
                  onClick={() => setShowFilenameModal(false)}
                  className="flex-1 bg-gray-700 hover:bg-gray-600 text-white px-6 py-3 rounded-xl font-semibold transition-all duration-300"
                >
                  Cancel
                </button>
                <button
                  onClick={handleFilenameSubmit}
                  disabled={loadingState || !customFilename.trim()}
                  className="flex-1 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 disabled:from-gray-600 disabled:to-gray-700 text-white px-6 py-3 rounded-xl font-semibold transition-all duration-300"
                >
                  {loadingState ? 'Processing...' : 'Continue'}
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}
