import React, { useState } from 'react'
import { Sparkles, Navigation, Mountain, Radio, ShieldX, Users } from 'lucide-react'

const SCENARIOS = [
  {
    id: 1,
    title: '1. Open Field',
    desc: '20 drones, V-formation, direct waypoint tracking',
    icon: Navigation,
    color: 'text-cyan-400',
    border: 'hover:border-cyan-500/60',
  },
  {
    id: 2,
    title: '2. Obstacle Course',
    desc: '50 drones, static pillars & boxes, 3D A* navigation',
    icon: Mountain,
    color: 'text-emerald-400',
    border: 'hover:border-emerald-500/60',
  },
  {
    id: 3,
    title: '3. Dynamic Hazards',
    desc: '50 drones, oscillating hazards, potential-field evasion',
    icon: Radio,
    color: 'text-amber-400',
    border: 'hover:border-amber-500/60',
  },
  {
    id: 4,
    title: '4. Leader Failover',
    desc: '50 drones, automatic dynamic leader re-election',
    icon: ShieldX,
    color: 'text-purple-400',
    border: 'hover:border-purple-500/60',
  },
  {
    id: 5,
    title: '5. 100-Drone Swarm',
    desc: '100 drones, high density, complex field & circular flock',
    icon: Users,
    color: 'text-pink-400',
    border: 'hover:border-pink-500/60',
  },
]

export default function PresetScenarios({ activeScenario, onSelectScenario }) {
  const [loadingId, setLoadingId] = useState(null)

  const handleSelect = async (id) => {
    setLoadingId(id)
    try {
      await fetch(`http://localhost:8000/api/mission/scenario/${id}`, { method: 'POST' })
      if (onSelectScenario) onSelectScenario(id)
    } catch (err) {
      console.error('Failed to load scenario:', err)
    } finally {
      setLoadingId(null)
    }
  }

  return (
    <div className="glass-panel px-4 py-3 rounded-xl shadow-2xl flex flex-col gap-2 max-w-5xl mx-auto w-full">
      <div className="flex items-center gap-2 text-xs font-semibold text-gray-300 uppercase tracking-wider">
        <Sparkles className="w-3.5 h-3.5 text-accent" /> Preset Scenarios
      </div>

      <div className="grid grid-cols-5 gap-2">
        {SCENARIOS.map((sc) => {
          const Icon = sc.icon
          const isSelected = activeScenario === sc.id

          return (
            <button
              key={sc.id}
              onClick={() => handleSelect(sc.id)}
              disabled={loadingId === sc.id}
              className={`p-2.5 rounded-lg border text-left flex flex-col gap-1 transition-all ${
                isSelected
                  ? 'bg-accent/15 border-accent shadow-[0_0_12px_rgba(6,182,212,0.25)]'
                  : `bg-gray-800/40 border-gray-800 ${sc.border}`
              }`}
            >
              <div className="flex items-center gap-1.5 font-medium text-xs text-gray-200">
                <Icon className={`w-3.5 h-3.5 ${sc.color}`} />
                <span className="truncate">{sc.title}</span>
              </div>
              <p className="text-[11px] text-gray-400 line-clamp-2 leading-tight">
                {sc.desc}
              </p>
            </button>
          )
        })}
      </div>
    </div>
  )
}
