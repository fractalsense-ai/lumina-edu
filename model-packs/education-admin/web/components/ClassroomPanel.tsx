/**
 * ClassroomPanel - Teacher sidebar showing colour-coded student status.
 *
 * Fetches roster-status from the education-admin dashboard API and renders
 * each assigned student as a card with a risk-colour indicator, active module
 * badge, and key risk factors.
 */

import { useState, useEffect, useCallback } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

interface AuthState {
  token: string
  userId: string
  username: string
  role: string
}

interface StudentStatus {
  student_id: string
  username: string
  active_module: string
  risk_score: number
  color: 'green' | 'yellow' | 'orange' | 'red'
  factors: {
    consecutive_incorrect: number
    hint_count: number
    outside_pct: number
    frustration: boolean
    valence: number
  }
  mastery: Record<string, number> | null
  fluency_tier: string | null
}

interface RosterStatusResponse {
  view: string
  teacher_id: string
  students: StudentStatus[]
}

const COLOR_CLASSES: Record<string, string> = {
  green: 'bg-green-500',
  yellow: 'bg-yellow-400',
  orange: 'bg-orange-500',
  red: 'bg-red-500',
}

const COLOR_BORDER: Record<string, string> = {
  green: 'border-l-green-500',
  yellow: 'border-l-yellow-400',
  orange: 'border-l-orange-500',
  red: 'border-l-red-500',
}

function getApiBase(): string {
  return (import.meta as any).env?.VITE_LUMINA_API_BASE_URL ?? 'http://localhost:8000'
}

function moduleLabel(moduleId: string): string {
  const parts = moduleId.split('/')
  return parts[parts.length - 1]?.replace(/\/v\d+$/, '') ?? moduleId
}

export function ClassroomPanel({ auth }: { auth: AuthState }) {
  const [data, setData] = useState<RosterStatusResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setError(null)
    setLoading(true)
    try {
      const res = await fetch(`${getApiBase()}/api/dashboard/education-admin/roster-status`, {
        headers: { Authorization: `Bearer ${auth.token}` },
      })
      if (res.ok) {
        setData(await res.json())
      } else {
        setError('Failed to load roster status.')
      }
    } catch {
      setError('Could not reach API.')
    } finally {
      setLoading(false)
    }
  }, [auth.token])

  useEffect(() => { load() }, [load])

  if (loading) {
    return <p className="text-sm text-muted-foreground p-4">Loading roster...</p>
  }

  const students = data?.students ?? []

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
          My Students
        </h3>
        <Button variant="outline" size="sm" onClick={load}>Refresh</Button>
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      {students.length === 0 && !error && (
        <p className="text-sm text-muted-foreground">No students assigned.</p>
      )}

      {students.map((student) => (
        <Card
          key={student.student_id}
          className={`p-3 border-l-4 ${COLOR_BORDER[student.color] ?? 'border-l-gray-400'}`}
        >
          <div className="flex items-center gap-2 mb-1">
            <span className={`inline-block w-2.5 h-2.5 rounded-full ${COLOR_CLASSES[student.color] ?? 'bg-gray-400'}`} />
            <span className="font-medium text-sm text-foreground">{student.username}</span>
            {student.active_module && (
              <span className="ml-auto text-xs px-1.5 py-0.5 rounded bg-muted text-muted-foreground">
                {moduleLabel(student.active_module)}
              </span>
            )}
          </div>

          <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-muted-foreground">
            {student.factors.consecutive_incorrect > 0 && (
              <span>{student.factors.consecutive_incorrect} incorrect</span>
            )}
            {student.factors.hint_count > 0 && (
              <span>{student.factors.hint_count} hints</span>
            )}
            {student.factors.outside_pct > 0 && (
              <span>{Math.round(student.factors.outside_pct * 100)}% outside ZPD</span>
            )}
            {student.factors.frustration && (
              <span className="text-red-500 font-medium">frustrated</span>
            )}
          </div>

          {student.fluency_tier && (
            <p className="text-xs text-muted-foreground mt-0.5">Fluency: {student.fluency_tier}</p>
          )}
        </Card>
      ))}
    </div>
  )
}