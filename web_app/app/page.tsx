'use client'

import { useState, useEffect, useRef, Suspense } from 'react'
import { Send, Loader2, CheckCircle, XCircle, Sparkles, Target, Users, UserPlus, Paperclip, X } from 'lucide-react'
import axios from 'axios'
import { useSearchParams } from 'next/navigation'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Message {
  role: 'user' | 'agent'
  content: string
  timestamp: Date
  data?: any
}

function HomeContent() {
  const searchParams = useSearchParams()
  const urlSessionId = searchParams.get('session')
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string>('')
  const [pendingApproval, setPendingApproval] = useState<any>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadingFile, setUploadingFile] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Initialize session ID only once
  useEffect(() => {
    if (urlSessionId) {
      setSessionId(urlSessionId)
    } else {
      // Check if there's a default session in localStorage
      const defaultSession = localStorage.getItem('default_session_id')
      if (defaultSession) {
        setSessionId(defaultSession)
      } else {
        // Create new session only if none exists
        const newSessionId = `manager_${Math.random().toString(36).substr(2, 9)}`
        setSessionId(newSessionId)
        localStorage.setItem('default_session_id', newSessionId)
      }
    }
  }, [urlSessionId])

  useEffect(() => {
    if (!sessionId) return
    
    // Load session from backend (MongoDB)
    const loadSessionFromBackend = async () => {
      try {
        const response = await axios.get(`${API_URL}/session/${sessionId}`)
        if (response.data.success && response.data.session) {
          const sessionData = response.data.session
          
          // Build messages from conversation history
          const loadedMessages: Message[] = []
          
          // Add conversation history if exists
          if (sessionData.conversation_history && sessionData.conversation_history.length > 0) {
            sessionData.conversation_history.forEach((msg: any) => {
              loadedMessages.push({
                role: msg.role,
                content: msg.content,
                timestamp: new Date(msg.timestamp),
                data: msg.data
              })
            })
          } else {
            // Welcome message for new session
            loadedMessages.push({
              role: 'agent',
              content: 'Hello! I\'m your task orchestrator. Tell me what you\'d like to do:\n\n• Set weekly goals\n• Upload candidate resumes\n• Search candidates by skills\n• Assign tasks to team',
              timestamp: new Date()
            })
          }
          
          setMessages(loadedMessages)
          
          // Also save to localStorage as backup
          localStorage.setItem(`session_${sessionId}`, JSON.stringify(loadedMessages))
        }
      } catch (error: any) {
        console.error('Error loading session from backend:', error)
        // If session not found in backend, show welcome message
        const welcomeMessage: Message = {
          role: 'agent',
          content: 'Hello! I\'m your task orchestrator. Tell me what you\'d like to do:\n\n• Set weekly goals\n• Upload candidate resumes\n• Search candidates by skills\n• Assign tasks to team',
          timestamp: new Date()
        }
        setMessages([welcomeMessage])
        localStorage.setItem(`session_${sessionId}`, JSON.stringify([welcomeMessage]))
      }
    }
    
    loadSessionFromBackend()
  }, [sessionId])

  useEffect(() => {
    // Save messages to localStorage
    if (messages.length > 0) {
      localStorage.setItem(`session_${sessionId}`, JSON.stringify(messages))
    }
  }, [messages, sessionId])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async () => {
    if ((!input.trim() && !selectedFile) || loading) return

    // Handle file upload if file is selected
    if (selectedFile) {
      await handleFileUpload()
      return
    }

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await axios.post(`${API_URL}/chat`, {
        session_id: sessionId,
        message: input
      })

      const data = response.data

      let agentContent = data.response || 'Task completed'
      
      if (data.project_name) {
        agentContent += `\n\n📋 Project: ${data.project_name}`
      }
      
      if (data.weekly_goal) {
        agentContent += `\n🎯 Goal: ${data.weekly_goal}`
      }
      
      if (data.generated_tasks && data.generated_tasks.length > 0) {
        agentContent += `\n\n✅ Generated ${data.generated_tasks.length} tasks`
      }

      if (data.candidates && data.candidates.length > 0) {
        agentContent += `\n\n👥 Found ${data.candidates.length} matching candidates`
      }

      if (data.pending_approval) {
        agentContent += `\n\n⚠️ Approval Required`
        setPendingApproval(data.assignment_plan)
      }

      const agentMessage: Message = {
        role: 'agent',
        content: agentContent,
        timestamp: new Date(),
        data
      }

      setMessages(prev => [...prev, agentMessage])
    } catch (error: any) {
      const errorMessage: Message = {
        role: 'agent',
        content: `Error: ${error.response?.data?.error || error.message}`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = async () => {
    if (!selectedFile) return

    setUploadingFile(true)
    setLoading(true)

    // Add user message showing file upload
    const userMessage: Message = {
      role: 'user',
      content: `${input || 'Uploading resume'}: ${selectedFile.name}`,
      timestamp: new Date()
    }
    setMessages(prev => [...prev, userMessage])

    try {
      const formData = new FormData()
      formData.append('file', selectedFile)

      const response = await axios.post(`${API_URL}/candidates/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      const data = response.data

      if (data.success) {
        const candidate = data.candidate
        let agentContent = `✅ Resume uploaded successfully!\n\n`
        agentContent += `📄 Candidate: ${candidate.name}\n`
        agentContent += `📧 Email: ${candidate.email || 'Not provided'}\n`
        agentContent += `💼 Experience: ${candidate.experience_years || 0} years\n`
        agentContent += `🔧 Skills: ${candidate.skills.join(', ')}\n\n`
        agentContent += `Candidate has been added to the database.`

        const agentMessage: Message = {
          role: 'agent',
          content: agentContent,
          timestamp: new Date(),
          data: data
        }

        setMessages(prev => [...prev, agentMessage])
      } else {
        throw new Error(data.error || 'Upload failed')
      }
    } catch (error: any) {
      const errorMessage: Message = {
        role: 'agent',
        content: `❌ Error uploading resume: ${error.response?.data?.detail?.error || error.message}`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setSelectedFile(null)
      setInput('')
      setUploadingFile(false)
      setLoading(false)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      if (file.type === 'application/pdf') {
        setSelectedFile(file)
        if (!input.trim()) {
          setInput('This is a candidate resume')
        }
      } else {
        alert('Please select a PDF file')
      }
    }
  }

  const removeSelectedFile = () => {
    setSelectedFile(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleApproval = async (approved: boolean) => {
    setLoading(true)
    try {
      const response = await axios.post(`${API_URL}/approval`, {
        session_id: sessionId,
        approved
      })

      const message: Message = {
        role: 'agent',
        content: approved 
          ? '✅ Assignment approved and executed!' 
          : '❌ Assignment rejected',
        timestamp: new Date(),
        data: response.data
      }

      setMessages(prev => [...prev, message])
      setPendingApproval(null)
    } catch (error: any) {
      const errorMessage: Message = {
        role: 'agent',
        content: `Error: ${error.message}`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const quickActions = [
    'Set weekly goal: Build authentication system',
    'Search candidates with Python and AWS skills',
    'Assign tasks to the team',
    'Show current task status',
    'Update weekly goal: Implement payment integration'
  ]

  // Check if user has sent any messages (excluding the initial agent welcome message)
  const userHasSentMessage = messages.some(msg => msg.role === 'user')

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50">
      <div className="container mx-auto px-4 py-6 max-w-7xl h-screen flex flex-col">
        {!userHasSentMessage ? (
          // Welcome Screen - Cleaner Design
          <div className="max-w-5xl mx-auto flex-1 flex flex-col justify-center">
            {/* Header */}
            <div className="text-center mb-10 pt-8">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl mb-4 shadow-md">
                <Sparkles className="text-white" size={32} />
              </div>
              <h1 className="text-4xl font-bold text-gray-900 mb-3">
                TaskFlow
              </h1>
              <p className="text-lg text-gray-600">
                AI-powered task orchestration and team management
              </p>
            </div>

            {/* Feature Cards - Simplified */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
              <div className="bg-white rounded-lg shadow-sm p-5 hover:shadow-md transition-shadow border border-gray-100">
                <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center mb-3">
                  <Target className="text-blue-600" size={20} />
                </div>
                <h3 className="text-base font-semibold text-gray-900 mb-1">Set Goals</h3>
                <p className="text-gray-600 text-sm">
                  Define goals and generate tasks automatically
                </p>
              </div>

              <div className="bg-white rounded-lg shadow-sm p-5 hover:shadow-md transition-shadow border border-gray-100">
                <div className="w-10 h-10 bg-purple-50 rounded-lg flex items-center justify-center mb-3">
                  <UserPlus className="text-purple-600" size={20} />
                </div>
                <h3 className="text-base font-semibold text-gray-900 mb-1">Find Talent</h3>
                <p className="text-gray-600 text-sm">
                  Search and match candidates by skills
                </p>
              </div>

              <div className="bg-white rounded-lg shadow-sm p-5 hover:shadow-md transition-shadow border border-gray-100">
                <div className="w-10 h-10 bg-green-50 rounded-lg flex items-center justify-center mb-3">
                  <Users className="text-green-600" size={20} />
                </div>
                <h3 className="text-base font-semibold text-gray-900 mb-1">Assign Tasks</h3>
                <p className="text-gray-600 text-sm">
                  Distribute work intelligently across team
                </p>
              </div>
            </div>

            {/* Quick Start - Cleaner */}
            <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-100">
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Sparkles className="text-blue-600" size={20} />
                Quick Start
              </h2>
              <div className="space-y-2 mb-5">
                {quickActions.map((action, idx) => (
                  <button
                    key={idx}
                    onClick={() => setInput(action)}
                    className="w-full text-left px-4 py-3 bg-gray-50 hover:bg-blue-50 rounded-lg transition-colors border border-gray-200 hover:border-blue-300 text-sm"
                  >
                    <span className="text-gray-700">{action}</span>
                  </button>
                ))}
              </div>
              
              {/* Input - Simplified */}
              <div className="flex gap-2">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      sendMessage()
                    }
                  }}
                  placeholder="Or type your message here..."
                  className="flex-1 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-sm"
                  rows={2}
                  disabled={loading}
                />
                <button
                  onClick={sendMessage}
                  disabled={loading || !input.trim()}
                  className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-sm hover:shadow transition-all"
                >
                  {loading ? <Loader2 className="animate-spin" size={20} /> : <Send size={20} />}
                </button>
              </div>
            </div>
          </div>
        ) : (
          // Chat Interface - Cleaner Design
          <div className="max-w-4xl mx-auto flex-1 flex flex-col h-full">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 flex flex-col h-full">
              {/* Header - Simplified */}
              <div className="flex items-center gap-3 px-5 py-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50">
                <div className="w-9 h-9 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center">
                  <Sparkles className="text-white" size={18} />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">TaskFlow</h2>
                  <p className="text-xs text-gray-600">{sessionId.substring(0, 20)}...</p>
                </div>
              </div>
              
              {/* Messages - Cleaner */}
              <div className="flex-1 overflow-y-auto p-5 space-y-3 bg-gray-50">
                {messages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[75%] rounded-lg px-4 py-3 shadow-sm ${
                        msg.role === 'user'
                          ? 'bg-blue-600 text-white'
                          : 'bg-white border border-gray-200 text-gray-900'
                      }`}
                    >
                      <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</p>
                      <p className={`text-xs mt-1.5 ${msg.role === 'user' ? 'text-blue-100' : 'text-gray-400'}`}>
                        {msg.timestamp.toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                ))}
                {loading && (
                  <div className="flex justify-start">
                    <div className="bg-white border border-gray-200 rounded-lg px-4 py-3 shadow-sm">
                      <Loader2 className="animate-spin text-blue-600" size={20} />
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Approval Section - Cleaner */}
              {pendingApproval && (
                <div className="mx-5 mb-4 bg-amber-50 border border-amber-200 rounded-lg p-4">
                  <h3 className="font-semibold text-amber-900 mb-2 flex items-center gap-2 text-sm">
                    <CheckCircle size={16} />
                    Approval Required
                  </h3>
                  {pendingApproval.assignments && (
                    <div className="mb-3 text-xs space-y-1">
                      {Object.entries(pendingApproval.assignments).map(([employee, data]: [string, any]) => (
                        <p key={employee} className="text-gray-700 bg-white rounded px-2 py-1">
                          <strong>{employee}:</strong> {data.tasks.length} tasks ({data.total_hours}h)
                        </p>
                      ))}
                    </div>
                  )}
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleApproval(true)}
                      disabled={loading}
                      className="flex items-center gap-1.5 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 text-sm shadow-sm transition-all"
                    >
                      <CheckCircle size={16} />
                      Approve
                    </button>
                    <button
                      onClick={() => handleApproval(false)}
                      disabled={loading}
                      className="flex items-center gap-1.5 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 text-sm shadow-sm transition-all"
                    >
                      <XCircle size={16} />
                      Reject
                    </button>
                  </div>
                </div>
              )}

              {/* Input - Cleaner */}
              <div className="p-4 border-t border-gray-200 bg-white">
                <div className="flex gap-2">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    disabled={loading}
                    className="p-3 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 transition-colors"
                    title="Upload Resume (PDF)"
                  >
                    <Paperclip size={20} className="text-gray-600" />
                  </button>
                  <div className="flex-1 relative">
                    {selectedFile && (
                      <div className="absolute -top-9 left-0 right-0 bg-blue-50 border border-blue-200 rounded-lg px-3 py-1.5 flex items-center justify-between">
                        <span className="text-xs text-blue-800 truncate flex-1">
                          📄 {selectedFile.name}
                        </span>
                        <button
                          onClick={removeSelectedFile}
                          className="ml-2 text-blue-600 hover:text-blue-800"
                        >
                          <X size={14} />
                        </button>
                      </div>
                    )}
                    <textarea
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault()
                          sendMessage()
                        }
                      }}
                      placeholder={selectedFile ? "Add a message..." : "Type your message..."}
                      className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-sm"
                      rows={2}
                      disabled={loading}
                    />
                  </div>
                  <button
                    onClick={sendMessage}
                    disabled={loading || (!input.trim() && !selectedFile)}
                    className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-sm hover:shadow transition-all"
                  >
                    {loading ? <Loader2 className="animate-spin" size={20} /> : <Send size={20} />}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default function Home() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50 flex items-center justify-center">
        <Loader2 className="animate-spin text-blue-600" size={48} />
      </div>
    }>
      <HomeContent />
    </Suspense>
  )
}
