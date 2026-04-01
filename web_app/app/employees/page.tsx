'use client'

import { useState, useEffect } from 'react'
import axios from 'axios'
import { Users, Loader2 } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Employee {
  name: string
  employee_name?: string
  skills: string[]
  capacity_hours: number
}

export default function EmployeesPage() {
  const [employees, setEmployees] = useState<Employee[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadEmployees()
  }, [])

  const loadEmployees = async () => {
    try {
      const response = await axios.get(`${API_URL}/employees`)
      setEmployees(response.data.employees || [])
    } catch (error) {
      console.error('Error loading employees:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container mx-auto px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">Employees</h1>
        <p className="text-gray-600">View your team members and their current tasks</p>
      </div>

      {/* Employees List */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        {loading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="animate-spin" size={32} />
          </div>
        ) : employees.length === 0 ? (
          <div className="text-center py-12">
            <Users className="mx-auto mb-4 text-gray-400" size={48} />
            <p className="text-gray-500 text-lg mb-2">No employees yet</p>
            <p className="text-gray-400 text-sm">Employees are added when candidates are selected through the chat</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {employees.map((emp, idx) => (
              <div key={idx} className="border border-gray-200 rounded-lg p-5 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="font-bold text-lg mb-1">👤 {emp.name || emp.employee_name}</h3>
                    <p className="text-sm text-gray-500">
                      {emp.capacity_hours} hrs/week
                    </p>
                  </div>
                </div>
                
                <div className="mb-3">
                  <p className="text-xs font-semibold text-gray-600 mb-2">SKILLS</p>
                  <div className="flex flex-wrap gap-1">
                    {emp.skills.map(skill => (
                      <span
                        key={skill}
                        className="bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="pt-3 border-t border-gray-200">
                  <p className="text-xs font-semibold text-gray-600 mb-1">CURRENT TASKS</p>
                  <p className="text-sm text-gray-500">No active tasks</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
