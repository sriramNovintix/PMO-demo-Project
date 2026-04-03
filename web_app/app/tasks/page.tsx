'use client'

import { useState, useEffect } from 'react'
import axios from 'axios'
import { Loader2, CheckCircle, Clock, ListTodo, Filter, X, UserPlus } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Task {
  task_id: string
  title: string
  description: string
  assigned_to: string | null
  assigned_to_email: string | null
  estimated_hours: number
  status: 'todo' | 'in_progress' | 'completed'
  created_at: string
  updated_at: string
  completed_at?: string
}

interface Employee {
  name: string
  email: string
  skills: string[]
}

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)
  const [draggedTask, setDraggedTask] = useState<Task | null>(null)
  const [filterEmployee, setFilterEmployee] = useState<string>('all')
  const [employees, setEmployees] = useState<Employee[]>([])
  const [assigningTask, setAssigningTask] = useState<string | null>(null)
  const [selectedEmployee, setSelectedEmployee] = useState<string>('')

  useEffect(() => {
    loadTasks()
    loadEmployees()
  }, [])

  const loadTasks = async () => {
    try {
      const response = await axios.get(`${API_URL}/tasks`)
      setTasks(response.data.tasks || [])
    } catch (error) {
      console.error('Error loading tasks:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadEmployees = async () => {
    try {
      const response = await axios.get(`${API_URL}/employees`)
      setEmployees(response.data.employees || [])
    } catch (error) {
      console.error('Error loading employees:', error)
    }
  }

  const assignTaskToEmployee = async (taskId: string, employeeName: string) => {
    try {
      const response = await axios.post(`${API_URL}/tasks/${taskId}/assign?employee_name=${employeeName}`)
      
      if (response.data.success) {
        alert(`Task assigned to ${employeeName} successfully!`)
        loadTasks()
        setAssigningTask(null)
        setSelectedEmployee('')
      } else {
        alert(response.data.message || 'Failed to assign task')
      }
    } catch (error: any) {
      console.error('Error assigning task:', error)
      alert(error.response?.data?.detail || 'Failed to assign task')
    }
  }

  const updateTaskStatus = async (taskId: string, newStatus: string) => {
    try {
      await axios.post(`${API_URL}/tasks/${taskId}/status?status=${newStatus}`)
      loadTasks() // Reload tasks
    } catch (error) {
      console.error('Error updating task:', error)
      alert('Failed to update task status')
    }
  }

  const handleDragStart = (task: Task) => {
    setDraggedTask(task)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
  }

  const handleDrop = (newStatus: string) => {
    if (draggedTask && draggedTask.status !== newStatus) {
      updateTaskStatus(draggedTask.task_id, newStatus)
    }
    setDraggedTask(null)
  }

  const getFilteredTasks = () => {
    if (filterEmployee === 'all') {
      return tasks
    } else if (filterEmployee === 'unassigned') {
      return tasks.filter(task => !task.assigned_to)
    } else {
      return tasks.filter(task => task.assigned_to === filterEmployee)
    }
  }

  const getTasksByStatus = (status: string) => {
    return getFilteredTasks().filter(task => task.status === status)
  }

  const columns = [
    {
      id: 'todo',
      title: 'To Do',
      icon: ListTodo,
      color: 'bg-gray-100 border-gray-300',
      headerColor: 'bg-gray-200 text-gray-800'
    },
    {
      id: 'in_progress',
      title: 'In Progress',
      icon: Clock,
      color: 'bg-blue-50 border-blue-300',
      headerColor: 'bg-blue-500 text-white'
    },
    {
      id: 'completed',
      title: 'Completed',
      icon: CheckCircle,
      color: 'bg-green-50 border-green-300',
      headerColor: 'bg-green-500 text-white'
    }
  ]

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50">
        <div className="container mx-auto px-6 py-8">
          <div className="flex justify-center items-center h-[600px]">
            <div className="text-center">
              <Loader2 className="animate-spin text-blue-600 mx-auto mb-4" size={48} />
              <p className="text-gray-600">Loading tasks...</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50">
      <div className="container mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-md">
              <ListTodo className="text-white" size={24} />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Task Board</h1>
              <p className="text-gray-600">Drag and drop tasks to update their status</p>
            </div>
          </div>
        </div>

        {/* Filter Section */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 mb-6">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2">
              <Filter size={20} className="text-gray-600" />
              <span className="font-medium text-gray-700">Filter by:</span>
            </div>
            
            <select
              value={filterEmployee}
              onChange={(e) => setFilterEmployee(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            >
              <option value="all">All Tasks</option>
              <option value="unassigned">Unassigned Tasks</option>
              {employees.map(emp => (
                <option key={emp.name} value={emp.name}>{emp.name}</option>
              ))}
            </select>

            {filterEmployee !== 'all' && (
              <button
                onClick={() => setFilterEmployee('all')}
                className="flex items-center gap-1 px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
              >
                <X size={16} />
                Clear
              </button>
            )}

            <div className="ml-auto text-sm text-gray-600 font-medium">
              {getFilteredTasks().length} of {tasks.length} tasks
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {columns.map(column => {
            const columnTasks = getTasksByStatus(column.id)
            const Icon = column.icon

            return (
              <div
                key={column.id}
                className="rounded-xl border-2 border-gray-200 bg-white shadow-sm min-h-[600px] flex flex-col"
                onDragOver={handleDragOver}
                onDrop={() => handleDrop(column.id)}
              >
                {/* Column Header */}
                <div className={`${column.headerColor} p-4 rounded-t-xl flex items-center justify-between`}>
                  <div className="flex items-center gap-2">
                    <Icon size={20} />
                    <h2 className="font-bold text-lg">{column.title}</h2>
                  </div>
                  <span className="bg-white bg-opacity-30 px-3 py-1 rounded-full text-sm font-semibold">
                    {columnTasks.length}
                  </span>
                </div>

                {/* Tasks */}
                <div className="p-4 space-y-3 flex-1">
                  {columnTasks.length === 0 ? (
                    <div className="flex items-center justify-center h-full">
                      <p className="text-gray-400 text-sm">No tasks</p>
                    </div>
                  ) : (
                    columnTasks.map(task => (
                      <div
                        key={task.task_id}
                        draggable
                        onDragStart={() => handleDragStart(task)}
                        className="bg-white rounded-lg p-4 shadow-sm hover:shadow-md transition-all cursor-move border border-gray-200 hover:border-blue-300"
                      >
                        <h3 className="font-semibold text-gray-900 mb-2 leading-tight">
                          {task.title}
                        </h3>
                        
                        {task.description && (
                          <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                            {task.description}
                          </p>
                        )}

                        <div className="space-y-2">
                          <div className="flex items-center justify-between text-xs">
                            <div>
                              {task.assigned_to ? (
                                <div className="space-y-1">
                                  <p className="font-medium text-gray-700 flex items-center gap-1">
                                    <span className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center text-blue-700 text-xs font-bold">
                                      {task.assigned_to[0].toUpperCase()}
                                    </span>
                                    {task.assigned_to}
                                  </p>
                                  <p className="text-gray-500 flex items-center gap-1">
                                    <Clock size={12} />
                                    {task.estimated_hours}h
                                  </p>
                                </div>
                              ) : (
                                <p className="font-medium text-orange-600 flex items-center gap-1">
                                  <span className="w-2 h-2 bg-orange-500 rounded-full"></span>
                                  Unassigned
                                </p>
                              )}
                            </div>
                            
                            {task.completed_at && (
                              <div className="text-green-600 font-medium flex items-center gap-1">
                                <CheckCircle size={14} />
                                Done
                              </div>
                            )}
                          </div>

                          {/* Manual Assignment Button */}
                          {assigningTask === task.task_id ? (
                            <div className="flex gap-2 mt-3 pt-3 border-t border-gray-200">
                              <select
                                value={selectedEmployee}
                                onChange={(e) => setSelectedEmployee(e.target.value)}
                                className="flex-1 px-2 py-1.5 text-xs border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                              >
                                <option value="">Select Employee</option>
                                {employees.map(emp => (
                                  <option key={emp.name} value={emp.name}>
                                    {emp.name}
                                  </option>
                                ))}
                              </select>
                              <button
                                onClick={() => {
                                  if (selectedEmployee) {
                                    assignTaskToEmployee(task.task_id, selectedEmployee)
                                  }
                                }}
                                disabled={!selectedEmployee}
                                className="px-3 py-1.5 text-xs bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                              >
                                ✓
                              </button>
                              <button
                                onClick={() => {
                                  setAssigningTask(null)
                                  setSelectedEmployee('')
                                }}
                                className="px-3 py-1.5 text-xs bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                              >
                                ✕
                              </button>
                            </div>
                          ) : (
                            <button
                              onClick={() => setAssigningTask(task.task_id)}
                              className="w-full mt-3 pt-3 border-t border-gray-200 flex items-center justify-center gap-1.5 px-3 py-2 text-xs bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 border border-blue-200 transition-colors font-medium"
                            >
                              <UserPlus size={14} />
                              {task.assigned_to ? 'Reassign' : 'Assign'}
                            </button>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
