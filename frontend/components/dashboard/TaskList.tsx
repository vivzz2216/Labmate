'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Switch } from '@/components/ui/switch'
import { Progress } from '@/components/ui/progress'
import { CheckCircle, XCircle, Clock, Code, Play, Eye } from 'lucide-react'
import { apiService, type Task, type JobStatus } from '@/lib/api'
import { truncateText } from '@/lib/utils'

interface TaskListProps {
  tasks: Task[]
  onExecutionComplete: (jobs: JobStatus[]) => void
  onError: (error: string) => void
  onPreview: () => void
}

export default function TaskList({ tasks, onExecutionComplete, onError, onPreview }: TaskListProps) {
  const [selectedTasks, setSelectedTasks] = useState<number[]>([])
  const [theme, setTheme] = useState<'idle' | 'vscode'>('idle')
  const [executing, setExecuting] = useState(false)
  const [executionProgress, setExecutionProgress] = useState(0)
  const [jobResults, setJobResults] = useState<JobStatus[]>([])

  const handleTaskToggle = (taskId: number) => {
    setSelectedTasks(prev => 
      prev.includes(taskId) 
        ? prev.filter(id => id !== taskId)
        : [...prev, taskId]
    )
  }

  const handleSelectAll = () => {
    if (selectedTasks.length === tasks.length) {
      setSelectedTasks([])
    } else {
      setSelectedTasks(tasks.map(task => task.id))
    }
  }

  const handleExecute = async () => {
    if (selectedTasks.length === 0) {
      onError('Please select at least one task to execute')
      return
    }

    setExecuting(true)
    setExecutionProgress(0)

    try {
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setExecutionProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval)
            return 90
          }
          return prev + 10
        })
      }, 300)

      // Get upload ID from first task (assuming all tasks belong to same upload)
      const uploadId = 1 // This should come from props or context
      const response = await apiService.runTasks({
        upload_id: uploadId,
        task_ids: selectedTasks,
        theme
      })

      clearInterval(progressInterval)
      setExecutionProgress(100)
      setJobResults(response.jobs)
      
      setTimeout(() => {
        onExecutionComplete(response.jobs)
        setExecuting(false)
        setExecutionProgress(0)
      }, 500)

    } catch (error) {
      setExecuting(false)
      setExecutionProgress(0)
      onError(error instanceof Error ? error.message : 'Execution failed')
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-600" />
      default:
        return <Clock className="w-5 h-5 text-yellow-600" />
    }
  }

  return (
    <div className="space-y-6">
      {/* Theme Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Code className="w-5 h-5" />
            <span>Screenshot Theme</span>
          </CardTitle>
          <CardDescription>
            Choose the editor theme for generated screenshots
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <span className={theme === 'idle' ? 'font-semibold' : ''}>IDLE</span>
              <Switch
                checked={theme === 'vscode'}
                onCheckedChange={(checked) => setTheme(checked ? 'vscode' : 'idle')}
              />
              <span className={theme === 'vscode' ? 'font-semibold' : ''}>VS Code</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Task Selection */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Select Tasks to Execute</CardTitle>
              <CardDescription>
                Choose which code blocks to run and generate screenshots for
              </CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleSelectAll}
              disabled={executing}
            >
              {selectedTasks.length === tasks.length ? 'Deselect All' : 'Select All'}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <AnimatePresence>
            {tasks.map((task, index) => (
              <motion.div
                key={task.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ delay: index * 0.1 }}
              >
                <Card className={`cursor-pointer transition-colors ${
                  selectedTasks.includes(task.id) ? 'ring-2 ring-indigo-500 bg-indigo-50' : 'hover:bg-gray-50'
                }`}>
                  <CardContent className="p-4">
                    <div className="flex items-start space-x-3">
                      <input
                        type="checkbox"
                        checked={selectedTasks.includes(task.id)}
                        onChange={() => handleTaskToggle(task.id)}
                        className="mt-1 h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                        disabled={executing}
                      />
                      <div className="flex-1 space-y-2">
                        <div className="flex items-center space-x-2">
                          <h4 className="font-medium">Task {task.id}</h4>
                          {task.requires_screenshot && (
                            <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
                              Screenshot Required
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-600">
                          {truncateText(task.question_text, 150)}
                        </p>
                        {task.code_snippet && (
                          <div className="bg-gray-100 p-3 rounded-md">
                            <pre className="text-xs text-gray-700 whitespace-pre-wrap">
                              {truncateText(task.code_snippet, 200)}
                            </pre>
                          </div>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </AnimatePresence>
        </CardContent>
      </Card>

      {/* Execution Controls */}
      <Card>
        <CardContent className="p-6">
          {executing ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="space-y-4"
            >
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center">
                  <Play className="w-4 h-4 text-indigo-600 animate-pulse" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold">Executing Code...</h3>
                  <Progress value={executionProgress} className="mt-2" />
                  <p className="text-sm text-gray-600 mt-1">{executionProgress}% complete</p>
                </div>
              </div>
            </motion.div>
          ) : (
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold">
                  {selectedTasks.length} task{selectedTasks.length !== 1 ? 's' : ''} selected
                </h3>
                <p className="text-sm text-gray-600">
                  Ready to execute code and generate screenshots
                </p>
              </div>
              <div className="flex space-x-3">
                <Button
                  onClick={handleExecute}
                  disabled={selectedTasks.length === 0}
                  className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700"
                >
                  <Play className="w-4 h-4 mr-2" />
                  Run Code
                </Button>
                {jobResults.length > 0 && (
                  <Button
                    onClick={onPreview}
                    variant="outline"
                  >
                    <Eye className="w-4 h-4 mr-2" />
                    Preview & Download
                  </Button>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Results */}
      {jobResults.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Execution Results</CardTitle>
            <CardDescription>
              Status of code execution and screenshot generation
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {jobResults.map((job) => (
              <div key={job.id} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                {getStatusIcon(job.status)}
                <div className="flex-1">
                  <p className="font-medium">Task {job.task_id}</p>
                  <p className="text-sm text-gray-600">
                    {job.status === 'completed' ? 'Successfully executed' : 
                     job.status === 'failed' ? job.error_message : 'In progress...'}
                  </p>
                </div>
                {job.screenshot_url && (
                  <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
                    Screenshot Ready
                  </span>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
