'use client'

import Link from 'next/link'
import { usePathname, useRouter, useSearchParams } from 'next/navigation'
import { Target, Users, UserPlus, MessageSquare, Edit2, Trash2, Plus, MoreVertical } from 'lucide-react'
import { useState, useEffect, useRef } from 'react'

interface Session {
  id: string
  name: string
  created_at: string
}

export default function Sidebar() {
  const pathname = usePathname()
  const router = useRouter()
  const searchParams = useSearchParams()
  const [sessions, setSessions] = useState<Session[]>([])
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editName, setEditName] = useState('')
  const [menuOpenId, setMenuOpenId] = useState<string | null>(null)
  const currentSessionId = searchParams.get('session')
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    loadSessions()
  }, [])

  const loadSessions = async () => {
    try {
      // Try to load from backend first
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/sessions`)
      if (response.ok) {
        const data = await response.json()
        if (data.success && data.sessions) {
          // Convert backend sessions to frontend format
          const backendSessions: Session[] = data.sessions.map((s: any) => ({
            id: s.session_id || s.id,
            name: s.project_name || s.name || `Session ${(s.session_id || s.id).slice(-8)}`,
            created_at: s.created_at
          }))
          
          setSessions(backendSessions)
          // Also save to localStorage as backup
          localStorage.setItem('sessions', JSON.stringify(backendSessions))
          return
        }
      }
    } catch (error) {
      console.error('Error loading sessions from backend:', error)
    }
    
    // Fallback to localStorage
    const stored = localStorage.getItem('sessions')
    if (stored) {
      try {
        setSessions(JSON.parse(stored))
      } catch (e) {
        console.error('Error parsing localStorage sessions:', e)
        setSessions([])
      }
    }
  }

  const createNewSession = async () => {
    const newSession: Session = {
      id: `manager_${Math.random().toString(36).substr(2, 9)}`,
      name: `Session ${sessions.length + 1}`,
      created_at: new Date().toISOString()
    }
    
    // Save to backend first
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/session/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: newSession.id,
          project_name: newSession.name
        })
      })
      
      if (response.ok) {
        const updated = [...sessions, newSession]
        setSessions(updated)
        localStorage.setItem('sessions', JSON.stringify(updated))
        router.push(`/?session=${newSession.id}`)
      }
    } catch (error) {
      console.error('Error creating session:', error)
      // Fallback: create locally
      const updated = [...sessions, newSession]
      setSessions(updated)
      localStorage.setItem('sessions', JSON.stringify(updated))
      router.push(`/?session=${newSession.id}`)
    }
  }

  const renameSession = (id: string) => {
    if (!editName.trim()) return
    const updated = sessions.map(s => 
      s.id === id ? { ...s, name: editName } : s
    )
    setSessions(updated)
    localStorage.setItem('sessions', JSON.stringify(updated))
    setEditingId(null)
    setEditName('')
  }

  const deleteSession = (id: string) => {
    if (confirm('Are you sure you want to delete this session?')) {
      // Remove from sessions list
      const updated = sessions.filter(s => s.id !== id)
      setSessions(updated)
      localStorage.setItem('sessions', JSON.stringify(updated))
      
      // Remove session data
      localStorage.removeItem(`session_${id}`)
      
      // If deleting current session, redirect to home
      if (currentSessionId === id) {
        router.push('/')
      }
    }
  }

  const navLinks = [
    { href: '/', label: 'Dashboard', icon: Target },
    { href: '/tasks', label: 'Tasks', icon: Users },
    { href: '/employees', label: 'Employees', icon: Users },
    { href: '/candidates', label: 'Candidates', icon: UserPlus },
  ]

  return (
    <aside className="w-64 bg-gray-900 text-white h-screen flex flex-col fixed">
      {/* Logo */}
      <div className="p-6 border-b border-gray-800 flex-shrink-0">
        <div className="flex items-center gap-2">
          <Target className="text-blue-400" size={28} />
          <h1 className="text-base font-bold">TaskFlow</h1>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="p-4 border-b border-gray-800 flex-shrink-0">
        <div className="space-y-1">
          {navLinks.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                pathname === href
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-300 hover:bg-gray-800'
              }`}
            >
              <Icon size={20} />
              <span>{label}</span>
            </Link>
          ))}
        </div>
      </nav>

      {/* Sessions - Scrollable */}
      <div className="flex-1 p-4 overflow-y-auto min-h-0">
        <div className="flex items-center justify-between mb-3 flex-shrink-0">
          <h3 className="text-sm font-semibold text-gray-400 uppercase">Sessions</h3>
          <button
            onClick={createNewSession}
            className="p-1 hover:bg-gray-800 rounded transition-colors"
            title="New Session"
          >
            <Plus size={16} />
          </button>
        </div>
        
        <div className="space-y-2">
          {sessions.length === 0 ? (
            <p className="text-sm text-gray-500 px-2">No sessions yet</p>
          ) : (
            sessions.map(session => (
              <div
                key={session.id}
                className={`group rounded-lg p-3 transition-colors ${
                  currentSessionId === session.id 
                    ? 'bg-blue-600' 
                    : 'bg-gray-800 hover:bg-gray-750'
                }`}
              >
                {editingId === session.id ? (
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') renameSession(session.id)
                        if (e.key === 'Escape') setEditingId(null)
                      }}
                      className="flex-1 px-2 py-1 bg-gray-700 text-white text-sm rounded border border-gray-600 focus:outline-none focus:border-blue-500"
                      autoFocus
                    />
                    <button
                      onClick={() => renameSession(session.id)}
                      className="text-green-400 hover:text-green-300"
                    >
                      ✓
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <Link 
                      href={`/?session=${session.id}`}
                      className="flex-1 min-w-0"
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <MessageSquare size={14} className="text-gray-400 flex-shrink-0" />
                        <span className="text-sm font-medium truncate">
                          {session.name}
                        </span>
                      </div>
                      <span className="text-xs text-gray-500">
                        {new Date(session.created_at).toLocaleDateString()}
                      </span>
                    </Link>
                    <div className="relative" ref={menuOpenId === session.id ? menuRef : null}>
                      <button
                        onClick={(e) => {
                          e.preventDefault()
                          e.stopPropagation()
                          setMenuOpenId(menuOpenId === session.id ? null : session.id)
                        }}
                        className="p-1 hover:bg-gray-700 rounded transition-colors"
                        title="Options"
                      >
                        <MoreVertical size={16} />
                      </button>
                      {menuOpenId === session.id && (
                        <div className="absolute right-0 top-8 bg-gray-800 border border-gray-700 rounded-lg shadow-lg py-1 z-10 min-w-[120px]">
                          <button
                            onClick={(e) => {
                              e.preventDefault()
                              setEditingId(session.id)
                              setEditName(session.name)
                              setMenuOpenId(null)
                            }}
                            className="w-full text-left px-3 py-2 hover:bg-gray-700 flex items-center gap-2 text-sm"
                          >
                            <Edit2 size={14} />
                            Rename
                          </button>
                          <button
                            onClick={(e) => {
                              e.preventDefault()
                              deleteSession(session.id)
                              setMenuOpenId(null)
                            }}
                            className="w-full text-left px-3 py-2 hover:bg-gray-700 flex items-center gap-2 text-sm text-red-400"
                          >
                            <Trash2 size={14} />
                            Delete
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-800 text-xs text-gray-500 flex-shrink-0">
        <p>© 2024 TaskFlow</p>
      </div>
    </aside>
  )
}
