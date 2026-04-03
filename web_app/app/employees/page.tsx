'use client'

import { useState, useEffect } from 'react'
import axios from 'axios'
import { Users, Loader2, Mail, Clock, CheckCircle, AlertCircle, Briefcase } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Employee {
  employee_id?: string
  name: string
  employee_name?: string
  email?: string
  skills: string[]
  capacity_hours: number
}

interface Task {
  task_id: string
  title: string
  status: string
  estimated_hours: number
  assigned_to: string
}

export default function EmployeesPage() {
  const [employees, setEmployees] = useState<Employee[]>([])
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [employeesRes, tasksRes] = await Promise.all([
        axios.get(`${API_URL}/employees`),
        axios.get(`${API_URL}/tasks`)
      ])
      const employeesData = employeesRes.data.employees || []
      const tasksData = tasksRes.data.tasks || []
      
      console.log('=== EMPLOYEES DATA ===')
      console.log('Employees:', employeesData)
      console.log('Employee names:', employeesData.map((e: any) => e.name || e.employee_name))
      
      console.log('=== TASKS DATA ===')
      console.log('Tasks:', tasksData)
      console.log('Assigned to:', tasksData.map((t: any) => t.assigned_to))
      
      setEmployees(employeesData)
      setTasks(tasksData)
    } catch (error) {
      console.error('Error loading data:', error)
    } finally {
      setLoading(false)
    }
  }

  const getEmployeeTasks = (employeeName: string) => {
    // Match tasks by employee name (case-insensitive and trim whitespace)
    const normalizedName = employeeName.trim().toLowerCase()
    const matchedTasks = tasks.filter(task => {
      const assignedTo = (task.assigned_to || '').trim().toLowerCase()
      return assignedTo === normalizedName
    })
    
    console.log(`Tasks for ${employeeName}:`, matchedTasks.length, matchedTasks)
    return matchedTasks
  }

  const getEmployeeStats = (employeeName: string) => {
    const empTasks = getEmployeeTasks(employeeName)
    const completedTasks = empTasks.filter(t => t.status === 'completed').length
    const inProgressTasks = empTasks.filter(t => t.status === 'in_progress').length
    const todoTasks = empTasks.filter(t => t.status === 'todo').length
    
    return { completedTasks, inProgressTasks, todoTasks, totalTasks: empTasks.length }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50">
      <div className="container mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-md">
              <Users className="text-white" size={24} />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Team Members</h1>
              <p className="text-gray-600">View your team and their workload</p>
            </div>
          </div>
        </div>

        {/* Employees Grid */}
        {loading ? (
          <div className="flex justify-center items-center py-20">
            <Loader2 className="animate-spin text-blue-600" size={40} />
          </div>
        ) : employees.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
            <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Users className="text-gray-400" size={40} />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">No Team Members Yet</h3>
            <p className="text-gray-500 mb-4">Employees are added when candidates are selected through the chat</p>
            <p className="text-sm text-gray-400">Try: "Show me the candidates" → Select a candidate</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {employees.map((emp, idx) => {
              const stats = getEmployeeStats(emp.name || emp.employee_name || '')
              
              return (
                <div 
                  key={emp.employee_id || idx} 
                  className="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-all overflow-hidden"
                >
                  {/* Header */}
                  <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-5 border-b border-gray-200">
                    <div className="flex items-start gap-3">
                      <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center text-white font-bold text-lg flex-shrink-0">
                        {(emp.name || emp.employee_name || 'U')[0].toUpperCase()}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="font-bold text-lg text-gray-900 truncate">
                          {emp.name || emp.employee_name}
                        </h3>
                        {emp.email && (
                          <div className="flex items-center gap-1 text-sm text-gray-600 mt-1">
                            <Mail size={14} />
                            <span className="truncate">{emp.email}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Body */}
                  <div className="p-5 space-y-4">
                    {/* Skills */}
                    <div>
                      <p className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                        <Briefcase size={16} />
                        Skills
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {emp.skills.length > 0 ? (
                          emp.skills.map(skill => (
                            <span
                              key={skill}
                              className="bg-blue-50 text-blue-700 text-xs px-2.5 py-1 rounded-md font-medium border border-blue-200"
                            >
                              {skill}
                            </span>
                          ))
                        ) : (
                          <span className="text-sm text-gray-400">No skills listed</span>
                        )}
                      </div>
                    </div>

                    {/* Tasks Summary */}
                    <div className="pt-4 border-t border-gray-200">
                      <p className="text-sm font-semibold text-gray-700 mb-3">Assigned Tasks</p>
                      {stats.totalTasks === 0 ? (
                        <p className="text-sm text-gray-400 italic">No tasks assigned</p>
                      ) : (
                        <div className="space-y-2">
                          <div className="flex items-center justify-between text-sm">
                            <div className="flex items-center gap-2">
                              <CheckCircle size={16} className="text-green-600" />
                              <span className="text-gray-600">Completed</span>
                            </div>
                            <span className="font-semibold text-gray-900">{stats.completedTasks}</span>
                          </div>
                          <div className="flex items-center justify-between text-sm">
                            <div className="flex items-center gap-2">
                              <Loader2 size={16} className="text-blue-600" />
                              <span className="text-gray-600">In Progress</span>
                            </div>
                            <span className="font-semibold text-gray-900">{stats.inProgressTasks}</span>
                          </div>
                          <div className="flex items-center justify-between text-sm">
                            <div className="flex items-center gap-2">
                              <AlertCircle size={16} className="text-gray-400" />
                              <span className="text-gray-600">To Do</span>
                            </div>
                            <span className="font-semibold text-gray-900">{stats.todoTasks}</span>
                          </div>
                          <div className="mt-3 pt-3 border-t border-gray-200">
                            <div className="flex items-center justify-between text-sm font-semibold">
                              <span className="text-gray-700">Total Tasks</span>
                              <span className="text-blue-600">{stats.totalTasks}</span>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
