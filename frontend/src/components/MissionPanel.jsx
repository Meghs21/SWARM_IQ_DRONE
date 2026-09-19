import React from 'react'
import { Compass, Target, Clock, BatteryCharging, Crown } from 'lucide-react'

export default function MissionPanel({ mission, leaderId, metrics }) {
  const progress = mission?.progress || 0
  const elapsed = mission?.elapsed_time || 0
  const distance = mission?.distance_to_target || 0
  const target = mission?.target || { x: 0, y: 0, z: 0 }

  const formatTime = (secs) => {
    const m = Math.floor(secs / 60)
    const s = Math.floor(secs % 60)
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  }

  return (
    <div className="glass-panel p-4 rounded-xl shadow-2xl flex flex-col gap-3 text-sm w-80">
      <div className="flex items-center justify-between border-b border-gray-800 pb-2">
        <h3 className="font-semibold text-gray-200 flex items-center gap-2">
          <Compass className="w-4 h-4 text-emerald-400" /> Mission Telemetry
        </h3>
        <span className="text-xs px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800/60 text-emerald-400 font-mono">
          {mission?.formation || 'V'} FORMATION
        </span>
      </div>

      {/* Progress Bar */}
      <div className="flex flex-col gap-1.5">
        <div className="flex justify-between text-xs font-mono">
          <span className="text-gray-400">Progress</span>
          <span className="text-emerald-400 font-bold">{progress.toFixed(1)}%</span>
        </div>
        <div className="w-full bg-gray-800/80 rounded-full h-2.5 overflow-hidden p-0.5 border border-gray-700/50">
          <div
            className="bg-gradient-to-r from-emerald-500 to-accent h-full rounded-full transition-all duration-300 shadow-[0_0_10px_rgba(16,185,129,0.5)]"
            style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
          />
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-2 pt-1">
        <div className="bg-gray-800/40 p-2 rounded-lg border border-gray-800 flex flex-col gap-0.5">
          <span className="text-[11px] text-gray-400 flex items-center gap-1">
            <Target className="w-3 h-3 text-cyan-400" /> Distance to Goal
          </span>
          <span className="font-mono text-base font-bold text-gray-200">
            {distance.toFixed(1)} <span className="text-xs font-normal text-gray-400">m</span>
          </span>
        </div>

        <div className="bg-gray-800/40 p-2 rounded-lg border border-gray-800 flex flex-col gap-0.5">
          <span className="text-[11px] text-gray-400 flex items-center gap-1">
            <Clock className="w-3 h-3 text-amber-400" /> Mission Time
          </span>
          <span className="font-mono text-base font-bold text-gray-200">
            {formatTime(elapsed)}
          </span>
        </div>
      </div>

      {/* Leader Status */}
      <div className="bg-amber-950/20 border border-amber-800/40 p-2.5 rounded-lg flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Crown className="w-4 h-4 text-amber-400" />
          <div className="flex flex-col">
            <span className="text-[10px] text-amber-400/80 uppercase font-semibold">Active Leader</span>
            <span className="font-mono text-xs font-bold text-amber-200">{leaderId || 'None Elected'}</span>
          </div>
        </div>
        <div className="flex items-center gap-1 text-xs font-mono text-amber-300">
          <BatteryCharging className="w-3.5 h-3.5" />
          <span>{metrics?.leader_battery?.toFixed(0) ?? 100}%</span>
        </div>
      </div>

      {/* Target Coordinates */}
      <div className="text-[11px] font-mono text-gray-500 text-center">
        Destination: [{target.x.toFixed(0)}, {target.y.toFixed(0)}, {target.z.toFixed(0)}]
      </div>
    </div>
  )
}
