'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
// Using basic HTML elements since UI components are not available
import { 
  Brain, 
  Code, 
  Camera, 
  MessageSquare, 
  Edit3, 
  CheckCircle, 
  AlertCircle,
  Play,
  Settings
} from 'lucide-react'
import { type AITaskCandidate, type TaskSubmission } from '@/lib/api'

interface AISuggestionsPanelProps {
  candidates: AITaskCandidate[]
  onSubmit: (submissions: TaskSubmission[], theme: string, insertionPreference: string) => void
  onError: (error: string) => void
}

export default function AISuggestionsPanel({ candidates, onSubmit, onError }: AISuggestionsPanelProps) {
  const [selectedTasks, setSelectedTasks] = useState<Set<string>>(new Set())
  const [taskSubmissions, setTaskSubmissions] = useState<Map<string, TaskSubmission>>(new Map())
  const [theme, setTheme] = useState<string>('idle')
  const [insertionPreference, setInsertionPreference] = useState<string>('below_question')
  const [followUpAnswers, setFollowUpAnswers] = useState<Map<string, string>>(new Map())
  const [editingCode, setEditingCode] = useState<Set<string>>(new Set())

  const getTaskIcon = (taskType: string) => {
    switch (taskType) {
      case 'screenshot_request':
        return <Camera className="w-4 h-4" />
      case 'answer_request':
        return <MessageSquare className="w-4 h-4" />
      case 'code_execution':
        return <Code className="w-4 h-4" />
      default:
        return <Brain className="w-4 h-4" />
    }
  }

  const getTaskTypeLabel = (taskType: string) => {
    switch (taskType) {
      case 'screenshot_request':
        return 'Screenshot Request'
      case 'answer_request':
        return 'AI Answer'
      case 'code_execution':
        return 'Code Execution'
      default:
        return 'AI Task'
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'bg-green-500/20 text-green-400'
    if (confidence >= 0.6) return 'bg-yellow-500/20 text-yellow-400'
    return 'bg-red-500/20 text-red-400'
  }

  const handleTaskSelection = (taskId: string, selected: boolean) => {
    const newSelectedTasks = new Set(selectedTasks)
    if (selected) {
      newSelectedTasks.add(taskId)
      // Initialize task submission
      const candidate = candidates.find(c => c.task_id === taskId)
      if (candidate) {
        taskSubmissions.set(taskId, {
          task_id: taskId,
          selected: true,
          user_code: candidate.suggested_code || candidate.extracted_code,
          follow_up_answer: followUpAnswers.get(taskId),
          insertion_preference: candidate.suggested_insertion
        })
      }
    } else {
      newSelectedTasks.delete(taskId)
      taskSubmissions.delete(taskId)
    }
    setSelectedTasks(newSelectedTasks)
    setTaskSubmissions(new Map(taskSubmissions))
  }

  const handleCodeEdit = (taskId: string, code: string) => {
    const submission = taskSubmissions.get(taskId)
    if (submission) {
      submission.user_code = code
      taskSubmissions.set(taskId, submission)
      setTaskSubmissions(new Map(taskSubmissions))
    }
  }

  const handleFollowUpAnswer = (taskId: string, answer: string) => {
    followUpAnswers.set(taskId, answer)
    setFollowUpAnswers(new Map(followUpAnswers))
    
    const submission = taskSubmissions.get(taskId)
    if (submission) {
      submission.follow_up_answer = answer
      taskSubmissions.set(taskId, submission)
      setTaskSubmissions(new Map(taskSubmissions))
    }
  }

  const handleSubmit = () => {
    if (selectedTasks.size === 0) {
      onError('Please select at least one task to execute')
      return
    }

    const submissions = Array.from(taskSubmissions.values())
    onSubmit(submissions, theme, insertionPreference)
  }

  return (
    <div className="space-y-6">
      <Card className="bg-gray-900/50 border-white/10">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-white">
            <Brain className="w-5 h-5" />
            AI Suggestions
          </CardTitle>
          <CardDescription className="text-white/60">
            Review and customize AI-generated task suggestions. Select tasks you want to execute.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Global Settings */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-white/5 rounded-lg border border-white/10">
            <div>
              <label className="text-sm font-medium mb-2 block text-white">Editor Theme</label>
              <select 
                value={theme} 
                onChange={(e) => setTheme(e.target.value)}
                className="w-full p-2 border border-white/20 rounded bg-gray-800 text-white"
              >
                <option value="idle">IDLE</option>
                <option value="vscode">VS Code</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block text-white">Insertion Preference</label>
              <select 
                value={insertionPreference} 
                onChange={(e) => setInsertionPreference(e.target.value)}
                className="w-full p-2 border border-white/20 rounded bg-gray-800 text-white"
              >
                <option value="below_question">Below Question</option>
                <option value="bottom_of_page">Bottom of Page</option>
              </select>
            </div>
          </div>

          {/* Task Candidates */}
          <div className="space-y-4">
            {candidates.map((candidate, index) => (
              <motion.div
                key={candidate.task_id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <Card className={`transition-all duration-200 bg-gray-900/50 border-white/10 ${
                  selectedTasks.has(candidate.task_id) ? 'ring-2 ring-blue-500' : ''
                }`}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={selectedTasks.has(candidate.task_id)}
                          onChange={(e) => 
                            handleTaskSelection(candidate.task_id, e.target.checked)
                          }
                          className="w-4 h-4 text-blue-600 bg-gray-800 border-gray-600 rounded focus:ring-blue-500"
                        />
                        <div className="flex items-center gap-2">
                          {getTaskIcon(candidate.task_type)}
                          <span className="font-medium text-white">{getTaskTypeLabel(candidate.task_type)}</span>
                          <span className={`px-2 py-1 text-xs rounded-full ${getConfidenceColor(candidate.confidence)}`}>
                            {Math.round(candidate.confidence * 100)}% confidence
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Question Context */}
                    <div className="mb-3">
                      <p className="text-sm text-white/80 bg-white/5 p-3 rounded border-l-4 border-blue-400">
                        {candidate.question_context}
                      </p>
                    </div>

                    {/* Brief Description */}
                    <p className="text-sm text-white/70 mb-3">
                      {candidate.brief_description}
                    </p>

                    {/* Code Preview/Edit */}
                    {(candidate.suggested_code || candidate.extracted_code) && (
                      <div className="mb-3">
                        <div className="flex items-center justify-between mb-2">
                          <label className="text-sm font-medium text-white">Code</label>
                          <Button
                            variant="outline"
                            size="sm"
                            className="border-white/20 text-white hover:bg-white/10"
                            onClick={() => {
                              const newEditing = new Set(editingCode)
                              if (editingCode.has(candidate.task_id)) {
                                newEditing.delete(candidate.task_id)
                              } else {
                                newEditing.add(candidate.task_id)
                              }
                              setEditingCode(newEditing)
                            }}
                          >
                            <Edit3 className="w-3 h-3 mr-1" />
                            {editingCode.has(candidate.task_id) ? 'Done' : 'Edit'}
                          </Button>
                        </div>
                        
                        {editingCode.has(candidate.task_id) ? (
                          <textarea
                            value={taskSubmissions.get(candidate.task_id)?.user_code || candidate.suggested_code || candidate.extracted_code || ''}
                            onChange={(e) => handleCodeEdit(candidate.task_id, e.target.value)}
                            className="w-full p-3 border border-white/20 rounded font-mono text-sm min-h-[100px] bg-gray-800 text-white"
                            placeholder="Edit code here..."
                          />
                        ) : (
                          <pre className="bg-gray-800 p-3 rounded text-sm font-mono overflow-x-auto border border-white/20 text-white">
                            {candidate.suggested_code || candidate.extracted_code}
                          </pre>
                        )}
                      </div>
                    )}

                    {/* Follow-up Question */}
                    {candidate.follow_up && (
                      <div className="mb-3">
                        <label className="text-sm font-medium block mb-2 text-white">
                          <AlertCircle className="w-4 h-4 inline mr-1" />
                          Follow-up Question
                        </label>
                        <p className="text-sm text-white/80 mb-2">{candidate.follow_up}</p>
                        <textarea
                          value={followUpAnswers.get(candidate.task_id) || ''}
                          onChange={(e) => handleFollowUpAnswer(candidate.task_id, e.target.value)}
                          placeholder="Your answer..."
                          className="w-full p-3 border border-white/20 rounded text-sm bg-gray-800 text-white"
                        />
                      </div>
                    )}

                    {/* Insertion Preference */}
                    <div className="mb-3">
                      <label className="text-sm font-medium block mb-2 text-white">Insertion Location</label>
                      <select
                        value={taskSubmissions.get(candidate.task_id)?.insertion_preference || candidate.suggested_insertion}
                        onChange={(e) => {
                          const submission = taskSubmissions.get(candidate.task_id)
                          if (submission) {
                            submission.insertion_preference = e.target.value
                            taskSubmissions.set(candidate.task_id, submission)
                            setTaskSubmissions(new Map(taskSubmissions))
                          }
                        }}
                        className="w-full p-2 border border-white/20 rounded bg-gray-800 text-white"
                      >
                        <option value="below_question">Below Question</option>
                        <option value="bottom_of_page">Bottom of Page</option>
                      </select>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>

          {/* Submit Button */}
          <div className="flex justify-end pt-4 border-t border-white/10">
            <Button 
              onClick={handleSubmit}
              disabled={selectedTasks.size === 0}
              className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700"
            >
              <Play className="w-4 h-4" />
              Execute {selectedTasks.size} Selected Task{selectedTasks.size !== 1 ? 's' : ''}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Safety Notice */}
      <Card className="border-amber-500/50 bg-amber-500/10">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <Settings className="w-5 h-5 text-amber-400 mt-0.5" />
            <div>
              <h4 className="font-medium text-amber-400 mb-1">Safety Notice</h4>
              <p className="text-sm text-amber-300">
                All code execution happens in a sandboxed environment with no internet access or file system access. 
                Your code cannot access your computer's files or make network requests.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
