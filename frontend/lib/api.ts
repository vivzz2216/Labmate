import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 150000, // Increased to 150 seconds for React projects (npm install + Vite startup)
  headers: {
    'X-Beta-Key': 'your_beta_key_here', // This should be configurable
  },
})

// Types
export interface UploadResponse {
  id: number
  filename: string
  original_filename: string
  file_type: string
  file_size: number
  uploaded_at: string
}

export interface Task {
  id: number
  question_text: string
  code_snippet: string
  requires_screenshot: boolean
}

export interface ParseResponse {
  tasks: Task[]
}

export interface JobStatus {
  id: number
  task_id: number
  question_text: string
  status: string
  output_text?: string
  error_message?: string
  execution_time?: number
  screenshot_url?: string
}

export interface RunResponse {
  jobs: JobStatus[]
}

export interface ComposeResponse {
  report_id: number
  filename: string
  download_url: string
}

export interface RunRequest {
  upload_id: number
  task_ids: number[]
  theme: 'idle' | 'vscode'
}

export interface ComposeRequest {
  upload_id: number
  screenshot_order?: number[]
}

// AI Analysis types
export interface AITaskCandidate {
  task_id: string
  question_context: string
  task_type: string // screenshot_request, answer_request, code_execution, react_project
  suggested_code?: string
  extracted_code?: string
  confidence: number
  suggested_insertion: string
  brief_description: string
  follow_up?: string
  project_files?: Record<string, string> // For React projects
  routes?: string[] // For React projects
}

export interface AnalyzeResponse {
  candidates: AITaskCandidate[]
}

export interface TaskSubmission {
  task_id: string
  selected: boolean
  user_code?: string
  follow_up_answer?: string
  insertion_preference: string
  task_type?: string // For react_project
  question_context?: string
  project_files?: Record<string, string> // For React projects
  routes?: string[] // For React projects
}

export interface TasksSubmitRequest {
  file_id: number
  tasks: TaskSubmission[]
  theme: string
  insertion_preference: string
}

export interface TasksSubmitResponse {
  job_id: number
  status: string
}

export interface TaskResult {
  id: number
  task_id: string
  task_type: string
  status: string
  screenshot_url?: string
  stdout?: string
  exit_code?: number
  caption?: string
  assistant_answer?: string
}

export interface JobStatusResponse {
  job_id: number
  status: string
  tasks: TaskResult[]
}

// API functions
export const apiService = {
  // Upload file
  async uploadFile(file: File, userId?: number): Promise<UploadResponse> {
    const formData = new FormData()
    formData.append('file', file)
    if (userId) {
      formData.append('user_id', String(userId))
    }
    
    const response = await api.post('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    
    return response.data
  },

  // Parse uploaded file
  async parseFile(fileId: number): Promise<ParseResponse> {
    const response = await api.get(`/api/parse/${fileId}`)
    return response.data
  },

  // Run code execution
  async runTasks(request: RunRequest): Promise<RunResponse> {
    const response = await api.post('/api/run', request)
    return response.data
  },

  // Compose final report
  async composeReport(request: ComposeRequest): Promise<ComposeResponse> {
    const response = await api.post('/api/compose', request)
    return response.data
  },

  // Download report
  async downloadReport(docId: number): Promise<Blob> {
    const response = await api.get(`/api/download/${docId}`, {
      responseType: 'blob',
    })
    return response.data
  },

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    const response = await api.get('/health')
    return response.data
  },

  // AI Analysis
  async analyzeDocument(fileId: number, language?: string): Promise<AnalyzeResponse> {
    const response = await api.post('/api/analyze', { file_id: fileId, language })
    return response.data
  },

  // Submit AI tasks
  async submitTasks(request: TasksSubmitRequest): Promise<TasksSubmitResponse> {
    const response = await api.post('/api/tasks/submit', request)
    return response.data
  },

  // Get job status
  async getJobStatus(jobId: number): Promise<JobStatusResponse> {
    const response = await api.get(`/api/tasks/${jobId}`)
    return response.data
  },

  // Get user assignments
  async getUserAssignments(userId: number): Promise<any[]> {
    const response = await api.get(`/api/assignments/?user_id=${userId}`)
    return response.data
  },

  // Set custom filename for uploaded file
  async setFilename(uploadId: number, filename: string): Promise<{ message: string; filename: string }> {
    // Append the correct extension if missing, based on current selection heuristics in UI
    const response = await api.post('/api/set-filename', {
      upload_id: uploadId,
      filename
    })
    return response.data
  },

  // Basic authentication methods
  async signup(email: string, name: string, password: string): Promise<any> {
    const response = await api.post('/api/basic-auth/signup', {
      email,
      name,
      password
    })
    return response.data
  },

  async login(email: string, password: string): Promise<any> {
    const response = await api.post('/api/basic-auth/login', {
      email,
      password
    })
    return response.data
  },

  async getCurrentUser(userId: number): Promise<any> {
    const response = await api.get(`/api/basic-auth/me?user_id=${userId}`)
    return response.data
  },
}

export default api

