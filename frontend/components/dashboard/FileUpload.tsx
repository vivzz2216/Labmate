'use client'

import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Card, CardContent } from '@/components/ui/card'
import { Upload, FileText, CheckCircle, AlertCircle } from 'lucide-react'
import { apiService, type UploadResponse } from '@/lib/api'
import { useAuth } from '@/contexts/BasicAuthContext'
import { formatFileSize } from '@/lib/utils'

interface FileUploadProps {
  onUploadComplete: (upload: UploadResponse) => void
  onError: (error: string) => void
}

export default function FileUpload({ onUploadComplete, onError }: FileUploadProps) {
  const { user } = useAuth()
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadedFile, setUploadedFile] = useState<UploadResponse | null>(null)

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return

    setUploading(true)
    setUploadProgress(0)

    try {
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval)
            return 90
          }
          return prev + 10
        })
      }, 200)

      const upload = await apiService.uploadFile(file, user?.id)
      
      clearInterval(progressInterval)
      setUploadProgress(100)
      setUploadedFile(upload)
      
      setTimeout(() => {
        onUploadComplete(upload)
        setUploading(false)
        setUploadProgress(0)
      }, 500)

    } catch (error) {
      setUploading(false)
      setUploadProgress(0)
      onError(error instanceof Error ? error.message : 'Upload failed')
    }
  }, [onUploadComplete, onError])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/pdf': ['.pdf']
    },
    maxFiles: 1,
    disabled: uploading
  })

  if (uploadedFile) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="space-y-4"
      >
        <Card className="border-green-500/50 bg-green-500/10">
          <CardContent className="p-6">
            <div className="flex items-center space-x-3">
              <CheckCircle className="w-8 h-8 text-green-400" />
              <div>
                <h3 className="font-semibold text-green-400">File Uploaded Successfully!</h3>
                <p className="text-sm text-green-300">
                  {uploadedFile.original_filename} ({formatFileSize(uploadedFile.file_size)})
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    )
  }

  return (
    <Card className="bg-gray-900/50 border-white/10">
      <CardContent className="p-8">
        <div
          {...getRootProps()}
          className={`
            border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
            ${isDragActive ? 'border-blue-500 bg-blue-500/10' : 'border-white/20 hover:border-white/40'}
            ${uploading ? 'cursor-not-allowed opacity-50' : ''}
          `}
        >
          <input {...getInputProps()} />
          
          {uploading ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="space-y-4"
            >
              <div className="w-16 h-16 mx-auto bg-blue-500/20 rounded-full flex items-center justify-center">
                <Upload className="w-8 h-8 text-blue-400 animate-pulse" />
              </div>
              <div className="space-y-2">
                <h3 className="text-lg font-semibold text-white">Uploading...</h3>
                <Progress value={uploadProgress} className="w-full max-w-xs mx-auto" />
                <p className="text-sm text-white/60">{uploadProgress}% complete</p>
              </div>
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-4"
            >
              <div className="w-16 h-16 mx-auto bg-white/10 rounded-full flex items-center justify-center">
                <FileText className="w-8 h-8 text-white" />
              </div>
              <div className="space-y-2">
                <h3 className="text-lg font-semibold text-white">
                  {isDragActive ? 'Drop your file here' : 'Upload Assignment'}
                </h3>
                <p className="text-sm text-white/80">
                  Drag and drop your DOCX or PDF file here, or click to browse
                </p>
                <p className="text-xs text-white/60">
                  Supported formats: .docx, .pdf (max 50MB)
                </p>
              </div>
              <Button variant="outline" className="mt-4 border-white/20 text-white hover:bg-white/10">
                Choose File
              </Button>
            </motion.div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
