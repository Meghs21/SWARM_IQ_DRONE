import React, { useState, useEffect } from 'react'
import { Play, Pause, RotateCcw, ShieldAlert, Cpu, Layers, Palette } from 'lucide-react'

export default function Controls({ mission, leaderId, totalDrones, onRefresh, colorTheme = 'emerald', onColorThemeChange }) {
  const [droneCount, setDroneCount] = useState(totalDrones || 50)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (totalDrones) {
      setDroneCount(totalDrones)
    }
  }, [totalDrones])

  const isRunning = mission?.status === 'RUNNING'
  const isPaused = mission?.status === 'PAUSED'

  const callApi = async (endpoint, options = {}) => {
    setLoading(true)
    try {
      await fetch(`http://localhost:8000/api/${endpoint}`, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
      })
      if (onRefresh) onRefresh()
    } catch (err) {
      console.error(`API Error on ${endpoint}:`, err)
    } finally {
      setLoading(false)
    }
  }

  const handleStartResume = () => {
    if (isPaused) {
      callApi('mission/resume', { method: 'POST' })
    } else {
      callApi('mission/start', { method: 'POST' })
    }
  }

  const handlePause = () => {
    callApi('mission/pause', { method: 'POST' })
  }

  const handleReset = () => {
    callApi('mission/reset', { method: 'POST' })
  }

  const handleFormationChange = (formation) => {
    callApi('config/formation', {
      method: 'POST',
      body: JSON.stringify({ formation }),
    })
  }

  const handleFleetSizeChange = (count) => {
    setDroneCount(count)
    callApi('config/fleet-size', {
      method: 'POST',
      body: JSON.stringify({ drone_count: count }),
    })
  }

  const handleFailLeader = () => {
    if (!leaderId) return
    callApi(`drone/${leaderId}/fail`, { method: 'POST' })
  }

  return (
    <div className="glass-panel p-4 rounded-xl shadow-2xl flex flex-col gap-4 text-sm w-80">
      <div className="flex items-center justify-between border-b border-gray-800 pb-2">
        <h3 className="font-semibold text-gray-200 flex items-center gap-2">
          <Cpu className="w-4 h-4 text-accent" /> Swarm Controls
        </h3>
        <span className="text-xs px-2 py-0.5 rounded bg-gray-800 text-gray-300 font-mono">
          {mission?.status || 'IDLE'}
        </span>
      </div>

      {/* Primary Actions */}
      <div className="grid grid-cols-3 gap-2">
        {!isRunning ? (
          <button
            onClick={handleStartResume}
            disabled={loading}
            className="flex items-center justify-center gap-1.5 bg-accent hover:bg-accent-hover text-background font-medium py-2 px-3 rounded-lg transition-all"
          >
            <Play className="w-4 h-4 fill-current" /> Start
          </button>
        ) : (
          <button
            onClick={handlePause}
            disabled={loading}
            className="flex items-center justify-center gap-1.5 bg-warning hover:bg-amber-600 text-background font-medium py-2 px-3 rounded-lg transition-all"
          >
            <Pause className="w-4 h-4 fill-current" /> Pause
          </button>
        )}

        <button
          onClick={handleReset}
          disabled={loading}
          className="flex items-center justify-center gap-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 font-medium py-2 px-3 rounded-lg border border-gray-700 transition-all col-span-2"
        >
          <RotateCcw className="w-4 h-4" /> Reset Swarm
        </button>
      </div>

      {/* Formation Selector */}
      <div className="flex flex-col gap-1.5">
        <label className="text-xs text-gray-400 flex items-center gap-1.5">
          <Layers className="w-3.5 h-3.5" /> Swarm Formation
        </label>
        <div className="grid grid-cols-4 gap-1">
          {['V', 'LINE', 'GRID', 'CIRCLE'].map((fmt) => (
            <button
              key={fmt}
              onClick={() => handleFormationChange(fmt)}
              className={`py-1.5 rounded text-xs font-mono transition-all ${
                mission?.formation === fmt
                  ? 'bg-accent/20 border border-accent text-accent font-bold'
                  : 'bg-gray-800/60 hover:bg-gray-800 text-gray-400 border border-gray-700/50'
              }`}
            >
              {fmt}
            </button>
          ))}
        </div>
      </div>

      {/* Fleet Size Selector */}
      <div className="flex flex-col gap-1.5">
        <div className="flex justify-between text-xs text-gray-400">
          <span>Fleet Size</span>
          <span className="font-mono text-accent font-bold">{droneCount} Drones</span>
        </div>
        <div className="grid grid-cols-3 gap-1">
          {[20, 50, 100].map((count) => (
            <button
              key={count}
              onClick={() => handleFleetSizeChange(count)}
              className={`py-1 rounded text-xs font-mono transition-all ${
                droneCount === count
                  ? 'bg-cyan-950 border border-cyan-500 text-cyan-300 font-bold shadow-[0_0_8px_rgba(6,182,212,0.3)]'
                  : 'bg-gray-800/60 hover:bg-gray-800 text-gray-400 border border-gray-700/50'
              }`}
            >
              {count}
            </button>
          ))}
        </div>
      </div>

      {/* Follower Drone Color Palette */}
      <div className="flex flex-col gap-1.5">
        <div className="flex justify-between text-xs text-gray-400">
          <span className="flex items-center gap-1.5">
            <Palette className="w-3.5 h-3.5 text-emerald-400" /> Drone Color
          </span>
          <span className="capitalize font-mono text-xs text-emerald-400 font-bold">{colorTheme}</span>
        </div>
        <div className="grid grid-cols-5 gap-1">
          {[
            { id: 'emerald', bg: 'bg-emerald-500', label: 'Emerald' },
            { id: 'violet', bg: 'bg-purple-500', label: 'Violet' },
            { id: 'white', bg: 'bg-slate-200', label: 'White' },
            { id: 'amber', bg: 'bg-orange-500', label: 'Amber' },
            { id: 'cyan', bg: 'bg-cyan-400', label: 'Cyan' },
          ].map((theme) => (
            <button
              key={theme.id}
              onClick={() => onColorThemeChange && onColorThemeChange(theme.id)}
              className={`h-7 rounded flex items-center justify-center transition-all border ${
                colorTheme === theme.id
                  ? 'border-white ring-2 ring-emerald-400/50 scale-105 shadow-md'
                  : 'border-gray-700 hover:border-gray-500 opacity-70 hover:opacity-100'
              }`}
              title={theme.label}
            >
              <span className={`w-3.5 h-3.5 rounded-full ${theme.bg}`} />
            </button>
          ))}
        </div>
      </div>

      {/* Fault Injection: Kill Leader */}
      <div className="pt-2 border-t border-gray-800">
        <button
          onClick={handleFailLeader}
          disabled={!leaderId}
          className="w-full flex items-center justify-center gap-2 bg-red-950/40 hover:bg-red-900/60 text-red-400 border border-red-800/60 py-2 px-3 rounded-lg text-xs font-medium transition-all group"
        >
          <ShieldAlert className="w-4 h-4 text-red-500 group-hover:animate-pulse" />
          Inject Fault: Kill Leader ({leaderId || 'N/A'})
        </button>
      </div>
    </div>
  )
}
