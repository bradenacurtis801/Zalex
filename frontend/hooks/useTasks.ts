import { useState, useEffect } from 'react'
import { taskApi } from '@/api'
import { TaskSummaryResponse, TasksResponse, TaskEntry } from '@/generated'

export function useTasks() {
  // Task summary state (counts by status)
  const [taskSummary, setTaskSummary] = useState<TaskSummaryResponse | null>(null)
  const [summaryLoading, setSummaryLoading] = useState(false)
  const [summaryError, setSummaryError] = useState<string | null>(null)

  // Tasks list state
  const [tasks, setTasks] = useState<TaskEntry[]>([])
  const [tasksLoading, setTasksLoading] = useState(false)
  const [tasksError, setTasksError] = useState<string | null>(null)
  const [pagination, setPagination] = useState({
    page: 1,
    pageSize: 20,
    total: 0,
    totalPages: 0
  })

  const fetchTaskSummary = async () => {
    setSummaryLoading(true)
    setSummaryError(null)
    try {
      const response = await taskApi.getTaskSummaryApiTasksSummaryGet()
      setTaskSummary(response)
      return response
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch task summary'
      setSummaryError(errorMessage)
      console.error('Error fetching task summary:', err)
      throw err
    } finally {
      setSummaryLoading(false)
    }
  }

  const fetchTasks = async (page: number = 1, pageSize: number = 20) => {
    setTasksLoading(true)
    setTasksError(null)
    try {
      const response = await taskApi.getUserTasksApiTasksGet({ page, pageSize })
      setTasks(response.tasks || [])
      setPagination({
        page: response.page || page,
        pageSize: response.pageSize || pageSize,
        total: response.total || 0,
        totalPages: response.totalPages || 0
      })
      return response
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch tasks'
      setTasksError(errorMessage)
      console.error('Error fetching tasks:', err)
      throw err
    } finally {
      setTasksLoading(false)
    }
  }

  const deleteTask = async (taskId: number) => {
    try {
      await taskApi.deleteTaskApiTasksTaskIdDelete({ taskId })
      
      // Remove task from local state
      setTasks(prev => prev.filter(task => task.id !== taskId))
      // Refresh summary to update counts
      await fetchTaskSummary()
      return true
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete task'
      console.error('Error deleting task:', err)
      throw new Error(errorMessage)
    }
  }

  const deleteTasks = async (taskIds: number[]) => {
    try {
      await taskApi.deleteTasksApiTasksDelete({
        bulkDeleteTasksRequest: { taskIds }
      })
      
      // Remove tasks from local state
      setTasks(prev => prev.filter(task => !taskIds.includes(task.id)))
      // Refresh summary to update counts
      await fetchTaskSummary()
      return true
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete tasks'
      console.error('Error deleting tasks:', err)
      throw new Error(errorMessage)
    }
  }

  const refetch = async () => {
    await Promise.all([
      fetchTaskSummary(), 
      fetchTasks(pagination.page, pagination.pageSize)
    ])
  }

  useEffect(() => {
    // Fetch both summary and tasks on mount
    fetchTaskSummary()
    fetchTasks(1, 20)
  }, [])

  return {
    // Task summary
    taskSummary,
    summaryLoading,
    summaryError,
    
    // Tasks list
    tasks,
    tasksLoading,
    tasksError,
    pagination,
    
    // Functions
    fetchTaskSummary,
    fetchTasks,
    deleteTask,
    deleteTasks,
    refetch
  }
}

