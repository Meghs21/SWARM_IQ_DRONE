import React from 'react'
import { Activity, ShieldCheck, AlertTriangle, Battery, Gauge } from 'lucide-react'

export default function MetricsPanel({ metrics }) {
  const warnings = metrics?.collision_warnings || 0
  const nearMisses = metrics?.near_misses || 0
  const actualCollisions = metrics?.actual_collisions || 0
  const active = metrics?.active_drones || 0
  const total = metrics?.total_drones || 0
  const failed = metrics?.failed_drones || 0
  const avgBattery = metrics?.average_battery || 100
  const fps = metrics?.fps || 0

  return (
    <div className="glass-panel p-4 rounded-xl shadow-2xl flex flex-col gap-3 text-sm w-80">
      <div className="flex items-center justify-between border-b border-gray-800 pb-2">
        <h3 className="font-semibold text-gray-200 flex items-center gap-2">
          <Activity className="w-4 h-4 text-cyan-400" /> Swarm Telemetry & Safety
        </h3>
        <span className="text-xs px-2 py-0.5 rounded bg-gray-800 text-cyan-400 font-mono flex items-center gap-1">
          <Gauge className="w-3 h-3" /> {fps.toFixed(0)} Hz
        </span>
      </div>

      {/* Fleet Status */}
      <div className="grid grid-cols-3 gap-2">
        <div className="bg-gray-800/40 p-2 rounded-lg border border-gray-800 flex flex-col items-center">
          <span className="text-[10px] text-gray-400">Total</span>
          <span className="font-mono text-sm font-bold text-gray-200">{total}</span>
        </div>
        <div className="bg-emerald-950/20 p-2 rounded-lg border border-emerald-800/40 flex flex-col items-center">
          <span className="text-[10px] text-emerald-400">Active</span>
          <span className="font-mono text-sm font-bold text-emerald-300">{active}</span>
        </div>
        <div className="bg-red-950/20 p-2 rounded-lg border border-red-800/40 flex flex-col items-center">
          <span className="text-[10px] text-red-400">Failed</span>
          <span className="font-mono text-sm font-bold text-red-400">{failed}</span>
        </div>
      </div>

      {/* Safety Incident Counters */}
      <div className="flex flex-col gap-1.5 pt-1">
        <span className="text-xs text-gray-400 font-medium flex items-center gap-1">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> Collision Avoidance
        </span>
        <div className="grid grid-cols-3 gap-2">
          <div className="bg-gray-800/40 p-2 rounded-lg border border-gray-800 flex flex-col items-center">
            <span className="text-[10px] text-amber-400">Warnings</span>
            <span className="font-mono text-sm font-bold text-amber-300">{warnings}</span>
          </div>
          <div className="bg-gray-800/40 p-2 rounded-lg border border-gray-800 flex flex-col items-center">
            <span className="text-[10px] text-orange-400">Near Miss</span>
            <span className="font-mono text-sm font-bold text-orange-300">{nearMisses}</span>
          </div>
          <div
            className={`p-2 rounded-lg border flex flex-col items-center transition-all ${
              actualCollisions > 0
                ? 'bg-red-950/40 border-red-700/60 text-red-400'
                : 'bg-gray-800/40 border-gray-800 text-gray-300'
            }`}
          >
            <span className="text-[10px]">Collisions</span>
            <span className="font-mono text-sm font-bold">{actualCollisions}</span>
          </div>
        </div>
      </div>

      {/* Battery Status */}
      <div className="pt-2 border-t border-gray-800 flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-xs text-gray-400">
          <Battery className="w-4 h-4 text-cyan-400" /> Fleet Avg Battery
        </div>
        <div className="flex items-center gap-2">
          <div className="w-24 bg-gray-800 rounded-full h-2 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${
                avgBattery > 50 ? 'bg-cyan-500' : avgBattery > 20 ? 'bg-amber-500' : 'bg-red-500'
              }`}
              style={{ width: `${avgBattery}%` }}
            />
          </div>
          <span className="font-mono text-xs font-bold text-gray-200">{avgBattery.toFixed(0)}%</span>
        </div>
      </div>
    </div>
  )
}
