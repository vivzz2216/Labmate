'use client'

import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Card, CardContent } from '@/components/ui/card'
import { Upload, FileText, CheckCircle, AlertCircle } from 'lucide-react'
import { apiService, type UploadResponse } from '@/lib/api'
import { formatFileSize } from '@/lib/utils'

interface FileUploadProps {
  onUploadComplete: (upload: UploadResponse) => void
  onError: (error: string) => void
}

export default function FileUpload({ onUploadComplete, onError }: FileUploadProps) {
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

      const upload = await apiService.uploadFile(file)
      
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
        <Card className="border-green-200 bg-green-50">
          <CardContent className="p-6">
            <div className="flex items-center space-x-3">
              <CheckCircle className="w-8 h-8 text-green-600" />
              <div>
                <h3 className="font-semibold text-green-800">File Uploaded Successfully!</h3>
                <p className="text-sm text-green-600">
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
    <Card>
      <CardContent className="p-8">
        <div
          {...getRootProps()}
          className={`
            border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
            ${isDragActive ? 'border-indigo-500 bg-indigo-50' : 'border-gray-300 hover:border-gray-400'}
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
              <div className="w-16 h-16 mx-auto bg-indigo-100 rounded-full flex items-center justify-center">
                <Upload className="w-8 h-8 text-indigo-600 animate-pulse" />
              </div>
              <div className="space-y-2">
                <h3 className="text-lg font-semibold">Uploading...</h3>
                <Progress value={uploadProgress} className="w-full max-w-xs mx-auto" />
                <p className="text-sm text-gray-600">{uploadProgress}% complete</p>
              </div>
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-4"
            >
              <div className="w-16 h-16 mx-auto bg-gray-100 rounded-full flex items-center justify-center">
                <FileText className="w-8 h-8 text-gray-600" />
              </div>
              <div className="space-y-2">
                <h3 className="text-lg font-semibold">
                  {isDragActive ? 'Drop your file here' : 'Upload Assignment'}
                </h3>
                <p className="text-sm text-gray-600">
                  Drag and drop your DOCX or PDF file here, or click to browse
                </p>
                <p className="text-xs text-gray-500">
                  Supported formats: .docx, .pdf (max 50MB)
                </p>
              </div>
              <Button variant="outline" className="mt-4">
                Choose File
              </Button>
            </motion.div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
