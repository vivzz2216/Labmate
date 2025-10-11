'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Trash2, GripVertical, Eye, Download } from 'lucide-react'
import { JobStatus } from '@/lib/api'
import { truncateText } from '@/lib/utils'

interface ScreenshotCardProps {
  job: JobStatus
  index: number
  onRemove: (jobId: number) => void
  onPreview: (job: JobStatus) => void
  isDragging?: boolean
}

export default function ScreenshotCard({ 
  job, 
  index, 
  onRemove, 
  onPreview,
  isDragging = false 
}: ScreenshotCardProps) {
  const [imageLoaded, setImageLoaded] = useState(false)
  const [imageError, setImageError] = useState(false)

  const handleImageLoad = () => {
    setImageLoaded(true)
  }

  const handleImageError = () => {
    setImageError(true)
    setImageLoaded(true)
  }

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={`${isDragging ? 'opacity-50' : ''}`}
    >
      <Card className="overflow-hidden hover:shadow-lg transition-shadow duration-300">
        <CardContent className="p-0">
          {/* Drag Handle */}
          <div className="absolute top-2 left-2 z-10">
            <div className="w-8 h-8 bg-white/80 backdrop-blur-sm rounded-lg flex items-center justify-center cursor-grab active:cursor-grabbing shadow-sm">
              <GripVertical className="w-4 h-4 text-gray-600" />
            </div>
          </div>

          {/* Remove Button */}
          <div className="absolute top-2 right-2 z-10">
            <Button
              size="sm"
              variant="destructive"
              className="w-8 h-8 p-0 bg-red-500/80 hover:bg-red-600"
              onClick={() => onRemove(job.id)}
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>

          {/* Screenshot Image */}
          <div className="relative w-full h-48 bg-gray-100 flex items-center justify-center">
            {job.screenshot_url && !imageError ? (
              <>
                {!imageLoaded && (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                  </div>
                )}
                <img
                  src={job.screenshot_url}
                  alt={`Screenshot for Task ${job.task_id}`}
                  className={`w-full h-full object-cover transition-opacity duration-300 ${
                    imageLoaded ? 'opacity-100' : 'opacity-0'
                  }`}
                  onLoad={handleImageLoad}
                  onError={handleImageError}
                />
              </>
            ) : (
              <div className="flex flex-col items-center justify-center text-gray-500">
                <div className="w-12 h-12 bg-gray-200 rounded-lg flex items-center justify-center mb-2">
                  <Eye className="w-6 h-6" />
                </div>
                <p className="text-sm">No screenshot available</p>
              </div>
            )}
          </div>

          {/* Job Info */}
          <div className="p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="text-xs font-medium bg-indigo-100 text-indigo-800 px-2 py-1 rounded-full">
                  Task {job.task_id}
                </span>
                <span className={`text-xs px-2 py-1 rounded-full ${
                  job.status === 'completed' 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {job.status}
                </span>
              </div>
              {job.execution_time && (
                <span className="text-xs text-gray-500">
                  {job.execution_time}ms
                </span>
              )}
            </div>

            <div className="space-y-2">
              <h4 className="font-medium text-sm line-clamp-2">
                {truncateText(job.question_text, 80)}
              </h4>
              
              {job.output_text && (
                <div className="bg-gray-50 p-2 rounded text-xs">
                  <pre className="whitespace-pre-wrap text-gray-700 line-clamp-3">
                    {truncateText(job.output_text, 100)}
                  </pre>
                </div>
              )}

              {job.error_message && (
                <div className="bg-red-50 p-2 rounded text-xs">
                  <p className="text-red-700 line-clamp-2">
                    {truncateText(job.error_message, 100)}
                  </p>
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex space-x-2">
              <Button
                size="sm"
                variant="outline"
                className="flex-1 text-xs"
                onClick={() => onPreview(job)}
              >
                <Eye className="w-3 h-3 mr-1" />
                Preview
              </Button>
              {job.screenshot_url && (
                <Button
                  size="sm"
                  variant="outline"
                  className="flex-1 text-xs"
                  onClick={() => window.open(job.screenshot_url, '_blank')}
                >
                  <Download className="w-3 h-3 mr-1" />
                  Download
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}
