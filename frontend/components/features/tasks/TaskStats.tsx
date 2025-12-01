'use client'

import { useState, useEffect, useCallback } from 'react'
import { useTasks } from '@/hooks/useTasks'
import { useLanguage } from '@/contexts/LanguageContext'
import { Button } from '@/components/ui'
import { StatusMessage } from '@/components/ui'
import { TaskEntry } from '@/generated'
import { useWebSocket } from '@/contexts/WebSocketContext'
import { WebSocketMessageType } from '@/websocket-protocol'
import { FileCompleteMessage, FileStartMessage, UploadProgressEvent } from '@/websocket-protocol'

type TaskStatusFilter = 'all' | 'pending' | 'processing' | 'completed' | 'failed'

export default function TaskStats() {
  const { t } = useLanguage()
  const { 
    taskSummary, 
    summaryLoading, 
    summaryError,
    tasks,
    tasksLoading,
    tasksError,
    pagination,
    deleteTask,
    deleteTasks,
    fetchTasks,
    refetch
  } = useTasks()
  
  const [deletingTaskId, setDeletingTaskId] = useState<number | null>(null)
  const [deleteError, setDeleteError] = useState<string | null>(null)
  
  // Filter and selection state
  const [statusFilter, setStatusFilter] = useState<TaskStatusFilter>('all')
  const [selectedTaskIds, setSelectedTaskIds] = useState<Set<number>>(new Set())
  const [isDeletingBulk, setIsDeletingBulk] = useState(false)

  // WebSocket context for real-time task updates
  const { register } = useWebSocket()

  // Handle file start - update task status to processing
  const handleFileStart = useCallback((data: FileStartMessage) => {
    // Update task status to processing if it exists
    // We'll need to find the task by filename and update it
    fetchTasks(pagination.page, pagination.pageSize) // Refresh current page
  }, [fetchTasks, pagination.page, pagination.pageSize])

  // Handle file complete - update task status to completed
  const handleFileComplete = useCallback((data: FileCompleteMessage) => {
    // Update task status to completed when file processing finishes
    // Refresh tasks to get updated status
    fetchTasks(pagination.page, pagination.pageSize) // Refresh current page
  }, [fetchTasks, pagination.page, pagination.pageSize])

  // Handle upload progress messages that contain nested file events
  const handleUploadProgress = useCallback((data: UploadProgressEvent) => {
    if (data.type === 'file_start') {
      handleFileStart(data)
    } else if (data.type === 'file_complete') {
      handleFileComplete(data)
    }
  }, [handleFileStart, handleFileComplete])

  // Register for WebSocket events
  useEffect(() => {
    const unsubscribeUploadProgress = register(
      WebSocketMessageType.UPLOAD_PROGRESS, 
      handleUploadProgress as (data: Record<string, any>) => void
    )
    
    return () => {
      unsubscribeUploadProgress()
    }
  }, [register, handleUploadProgress])


  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      case 'processing':
        return 'bg-blue-100 text-blue-800 border-blue-300'
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-300'
      case 'failed':
        return 'bg-red-100 text-red-800 border-red-300'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'pending':
        return '⏳'
      case 'processing':
        return (
          <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        )
      case 'completed':
        return '✓'
      case 'failed':
        return '✗'
      default:
        return '•'
    }
  }

  const formatDate = (date: Date | string) => {
    const d = typeof date === 'string' ? new Date(date) : date
    return d.toLocaleString()
  }

  // Filter tasks based on status
  const filteredTasks = tasks.filter(task => {
    if (statusFilter === 'all') return true
    return task.status.toLowerCase() === statusFilter.toLowerCase()
  })

  // Handle individual task selection
  const handleTaskSelect = (taskId: number, checked: boolean) => {
    setSelectedTaskIds(prev => {
      const newSet = new Set(prev)
      if (checked) {
        newSet.add(taskId)
      } else {
        newSet.delete(taskId)
      }
      return newSet
    })
  }

  // Handle select all in filtered list
  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      const allFilteredIds = new Set(filteredTasks.map(task => task.id))
      setSelectedTaskIds(allFilteredIds)
    } else {
      setSelectedTaskIds(new Set())
    }
  }

  // Check if all filtered tasks are selected
  const allFilteredSelected = filteredTasks.length > 0 && filteredTasks.every(task => selectedTaskIds.has(task.id))
  const someFilteredSelected = filteredTasks.some(task => selectedTaskIds.has(task.id))

  const handleDeleteTask = async (taskId: number) => {
    if (!confirm(t('tasks.confirmDeleteTask'))) {
      return
    }

    setDeletingTaskId(taskId)
    setDeleteError(null)
    
    try {
      await deleteTask(taskId)
      // Task is already removed from state by deleteTask
      // Also remove from selection if it was selected
      setSelectedTaskIds(prev => {
        const newSet = new Set(prev)
        newSet.delete(taskId)
        return newSet
      })
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : t('tasks.deleteTaskError')
      setDeleteError(errorMessage)
      console.error('Error deleting task:', err)
    } finally {
      setDeletingTaskId(null)
    }
  }

  const handleBulkDelete = async () => {
    const selectedIds = Array.from(selectedTaskIds)
    if (selectedIds.length === 0) return

    if (!confirm(t('tasks.confirmDeleteTasks', { count: selectedIds.length }))) {
      return
    }

    setIsDeletingBulk(true)
    setDeleteError(null)

    try {
      await deleteTasks(selectedIds)
      // Tasks are already removed from state by deleteTasks
      setSelectedTaskIds(new Set())
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : t('tasks.deleteTasksError')
      setDeleteError(errorMessage)
      console.error('Error deleting tasks:', err)
    } finally {
      setIsDeletingBulk(false)
    }
  }

  if (summaryLoading && !taskSummary) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="loader mx-auto mb-4"></div>
          <p className="text-gray-600">{t('tasks.loadingStatistics')}</p>
        </div>
      </div>
    )
  }

  if (summaryError) {
    return (
      <div className="text-center p-6">
        <StatusMessage message={summaryError} type="error" />
        <Button onClick={refetch} className="mt-4">
          {t('tasks.tryAgain')}
        </Button>
      </div>
    )
  }

  return (
    <div className="flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 border-b pb-2">
        <h2 className="text-xl font-semibold text-violet-800">
          {t('tasks.title')}
        </h2>
        <div className="flex gap-2 items-center">
          <Button 
            variant="secondary" 
            onClick={refetch}
            size="sm"
            isLoading={summaryLoading || tasksLoading}
          >
            {t('tasks.refresh')}
          </Button>
        </div>
      </div>

      {/* Task Summary Stats */}
      {taskSummary && (
        <div className="grid grid-cols-5 gap-4 mb-6">
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="text-2xl font-bold text-gray-900">{taskSummary.totalTasks}</div>
            <div className="text-sm text-gray-500 mt-1">{t('tasks.totalTasks')}</div>
          </div>
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="text-2xl font-bold text-yellow-700">{taskSummary.pending}</div>
            <div className="text-sm text-yellow-600 mt-1">{t('tasks.pending')}</div>
          </div>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="text-2xl font-bold text-blue-700">{taskSummary.processing}</div>
            <div className="text-sm text-blue-600 mt-1">{t('tasks.processing')}</div>
          </div>
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="text-2xl font-bold text-green-700">{taskSummary.completed}</div>
            <div className="text-sm text-green-600 mt-1">{t('tasks.completed')}</div>
          </div>
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="text-2xl font-bold text-red-700">{taskSummary.failed}</div>
            <div className="text-sm text-red-600 mt-1">{t('tasks.failed')}</div>
          </div>
        </div>
      )}

      {/* Delete Error Message */}
      {deleteError && (
        <div className="mb-4">
          <StatusMessage message={deleteError} type="error" />
        </div>
      )}

      {/* Filter and Bulk Actions */}
      <div className="mb-4 flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
            {t('tasks.filterByStatus')}
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value as TaskStatusFilter)
                setSelectedTaskIds(new Set()) // Clear selection when filter changes
              }}
              className="px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent"
            >
              <option value="all">{t('tasks.allTasks')}</option>
              <option value="pending">{t('tasks.pending')}</option>
              <option value="processing">{t('tasks.processing')}</option>
              <option value="completed">{t('tasks.completed')}</option>
              <option value="failed">{t('tasks.failed')}</option>
            </select>
          </label>
        </div>
        
        {selectedTaskIds.size > 0 && (
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">
              {t('tasks.tasksSelected', { count: selectedTaskIds.size })}
            </span>
            <Button
              variant="secondary"
              size="sm"
              onClick={handleBulkDelete}
              disabled={isDeletingBulk}
              isLoading={isDeletingBulk}
              className="text-xs text-red-600 hover:text-red-800"
            >
              {isDeletingBulk ? t('tasks.deleting') : `${t('tasks.deleteSelected')} (${selectedTaskIds.size})`}
            </Button>
          </div>
        )}
      </div>

      {/* Tasks List */}
      <div className="overflow-hidden flex flex-col" style={{ maxHeight: '400px' }}>
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">
            {t('tasks.taskList', { filtered: filteredTasks.length, total: tasks.length })}
          </span>
        </div>
        
        {tasksLoading && tasks.length === 0 ? (
          <div className="flex items-center justify-center h-32">
            <div className="text-center">
              <div className="loader mx-auto mb-2"></div>
              <p className="text-gray-600">{t('tasks.loadingTasks')}</p>
            </div>
          </div>
        ) : tasksError ? (
          <div className="text-center p-6">
            <StatusMessage message={tasksError} type="error" />
            <Button onClick={refetch} className="mt-4" size="sm">
              {t('tasks.tryAgain')}
            </Button>
          </div>
        ) : tasks.length === 0 ? (
          <div className="text-center p-8 text-gray-500">
            <div className="text-4xl mb-4">📋</div>
            <h3 className="text-lg font-medium mb-2">{t('tasks.noTasksFound')}</h3>
            <p className="text-sm">{t('tasks.noTasksDescription')}</p>
          </div>
        ) : filteredTasks.length === 0 ? (
          <div className="text-center p-8 text-gray-500">
            <div className="text-4xl mb-4">🔍</div>
            <h3 className="text-lg font-medium mb-2">{t('tasks.noTasksFound')}</h3>
            <p className="text-sm">{t('tasks.noTasksWithStatus', { status: statusFilter })}</p>
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto space-y-2 border border-gray-200 rounded-lg p-2">
            {/* Select All Checkbox */}
            <div className="sticky top-0 bg-gray-50 border-b border-gray-200 p-2 -mx-2 -mt-2 mb-2 z-10">
              <label className="flex items-center gap-2 text-sm font-medium text-gray-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={allFilteredSelected}
                  ref={(input) => {
                    if (input) input.indeterminate = someFilteredSelected && !allFilteredSelected
                  }}
                  onChange={(e) => handleSelectAll(e.target.checked)}
                  className="rounded border-gray-300 text-violet-600 focus:ring-violet-500"
                />
                <span>{t('tasks.selectAll')} ({filteredTasks.length})</span>
              </label>
            </div>

            {filteredTasks.map((task: TaskEntry) => (
              <div
                key={task.id}
                className={`bg-white border rounded-lg p-4 hover:shadow-md transition-shadow ${
                  selectedTaskIds.has(task.id) ? 'border-violet-500 bg-violet-50' : 'border-gray-200'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  {/* Checkbox */}
                  <div className="flex-shrink-0 pt-1">
                    <input
                      type="checkbox"
                      checked={selectedTaskIds.has(task.id)}
                      onChange={(e) => handleTaskSelect(task.id, e.target.checked)}
                      className="rounded border-gray-300 text-violet-600 focus:ring-violet-500 cursor-pointer"
                    />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(task.status)}`}>
                        {task.status.toUpperCase()}
                      </span>
                      <span className="text-sm text-gray-500">
                        {getStatusIcon(task.status)}
                      </span>
                    </div>
                    <h4 className="font-medium text-gray-900 truncate max-w-xs" title={task.filename}>
                      {task.filename}
                    </h4>
                    <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                      <span>{t('tasks.id')} {task.documentId.substring(0, 8)}...</span>
                      <span>{t('tasks.created')} {formatDate(task.createdAt)}</span>
                      {task.updatedAt && (
                        <span>{t('tasks.updated')} {formatDate(task.updatedAt)}</span>
                      )}
                    </div>
                    {task.error && (
                      <div className="mt-2 text-xs text-red-600 bg-red-50 border border-red-200 rounded p-2">
                        <strong>{t('tasks.error')}</strong> {task.error}
                      </div>
                    )}
                  </div>
                  
                  <div className="flex-shrink-0 flex items-center gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => handleDeleteTask(task.id)}
                      disabled={deletingTaskId === task.id || isDeletingBulk}
                      isLoading={deletingTaskId === task.id}
                      className="text-xs text-red-600 hover:text-red-800"
                    >
                      {deletingTaskId === task.id ? t('tasks.deleting') : t('tasks.delete')}
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pagination Controls */}
        {pagination.totalPages > 1 && (
          <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200">
            <div className="flex items-center gap-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => fetchTasks(pagination.page - 1, pagination.pageSize)}
                disabled={pagination.page <= 1 || tasksLoading}
              >
                {t('tasks.previous')}
              </Button>
              <span className="text-sm text-gray-600">
                {t('tasks.page', { current: pagination.page, total: pagination.totalPages })}
              </span>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => fetchTasks(pagination.page + 1, pagination.pageSize)}
                disabled={pagination.page >= pagination.totalPages || tasksLoading}
              >
                {t('tasks.next')}
              </Button>
            </div>
            <div className="text-sm text-gray-600">
              {t('tasks.showingTasks', {
                start: ((pagination.page - 1) * pagination.pageSize) + 1,
                end: Math.min(pagination.page * pagination.pageSize, pagination.total),
                total: pagination.total
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

