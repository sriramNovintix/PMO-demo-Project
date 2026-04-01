'use client'

import { useState, useEffect } from 'react'
import { UserPlus, Loader2, CheckCircle, XCircle } from 'lucide-react'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Candidate {
  candidate_id: string
  name: string
  email: string
  skills: string[]
  experience_years: number
  status: string
  created_at: string
}

export default function CandidatesPage() {
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  useEffect(() => {
    loadCandidates()
  }, [])

  const loadCandidates = async () => {
    try {
      const response = await axios.get(`${API_URL}/candidates`)
      setCandidates(response.data.candidates || [])
    } catch (error) {
      console.error('Error loading candidates:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSelect = async (candidateId: string) => {
    if (!confirm('Select this candidate and move to employees?')) return
    
    setActionLoading(candidateId)
    try {
      await axios.post(`${API_URL}/candidates/${candidateId}/select`)
      alert('Candidate selected and moved to employees!')
      loadCandidates()
    } catch (error: any) {
      alert(`Error: ${error.response?.data?.detail || error.message}`)
    } finally {
      setActionLoading(null)
    }
  }

  const handleReject = async (candidateId: string) => {
    if (!confirm('Reject and delete this candidate?')) return
    
    setActionLoading(candidateId)
    try {
      await axios.post(`${API_URL}/candidates/${candidateId}/reject`)
      alert('Candidate rejected')
      loadCandidates()
    } catch (error: any) {
      alert(`Error: ${error.response?.data?.detail || error.message}`)
    } finally {
      setActionLoading(null)
    }
  }

  return (
    <div className="container mx-auto px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">Candidates</h1>
        <p className="text-gray-600">Upload resumes through chat to add candidates automatically</p>
      </div>

      {/* Candidates List */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold mb-6">All Candidates</h2>
        
        {loading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="animate-spin" size={32} />
          </div>
        ) : candidates.length === 0 ? (
          <div className="text-center py-12">
            <UserPlus className="mx-auto mb-4 text-gray-400" size={48} />
            <p className="text-gray-500 text-lg mb-2">No candidates yet</p>
            <p className="text-gray-400 text-sm">Upload resumes through chat to add candidates</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {candidates.map((candidate) => (
              <div key={candidate.candidate_id} className="border border-gray-200 rounded-lg p-5 hover:shadow-md transition-shadow">
                <div className="mb-3">
                  <h3 className="font-bold text-lg mb-1">👤 {candidate.name}</h3>
                  <p className="text-sm text-gray-500">{candidate.email || 'No email'}</p>
                  <p className="text-sm text-gray-500">{candidate.experience_years} years experience</p>
                </div>
                
                <div className="mb-4">
                  <p className="text-xs font-semibold text-gray-600 mb-2">SKILLS</p>
                  <div className="flex flex-wrap gap-1">
                    {candidate.skills.map(skill => (
                      <span
                        key={skill}
                        className="bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="flex gap-2 pt-3 border-t border-gray-200">
                  <button
                    onClick={() => handleSelect(candidate.candidate_id)}
                    disabled={actionLoading === candidate.candidate_id}
                    className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50 text-sm font-medium"
                  >
                    {actionLoading === candidate.candidate_id ? (
                      <Loader2 className="animate-spin" size={16} />
                    ) : (
                      <>
                        <CheckCircle size={16} />
                        Select
                      </>
                    )}
                  </button>
                  <button
                    onClick={() => handleReject(candidate.candidate_id)}
                    disabled={actionLoading === candidate.candidate_id}
                    className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 disabled:opacity-50 text-sm font-medium"
                  >
                    {actionLoading === candidate.candidate_id ? (
                      <Loader2 className="animate-spin" size={16} />
                    ) : (
                      <>
                        <XCircle size={16} />
                        Reject
                      </>
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
