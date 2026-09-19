import React, { useState } from 'react'
import SceneView from './SceneView'
import Controls from './Controls'
import MissionPanel from './MissionPanel'
import MetricsPanel from './MetricsPanel'
import PresetScenarios from './PresetScenarios'
import { Radio, Wifi, WifiOff } from 'lucide-react'

export default function Dashboard({ snapshot, isConnected }) {
  const [activeScenario, setActiveScenario] = useState(1)

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-background">
      {/* 1. Fullscreen Three.js Simulation Canvas */}
      <SceneView snapshot={snapshot} />

      {/* 2. Floating Command Center Overlay UI (pointer-events-none on backdrop, pointer-events-auto on cards) */}
      <div className="absolute inset-0 pointer-events-none flex flex-col justify-between p-4 z-10">
        {/* Top Header Bar */}
        <header className="flex items-center justify-between pointer-events-auto">
          <div className="glass-panel px-4 py-2 rounded-xl flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-accent/20 border border-accent/40 flex items-center justify-center text-accent font-mono font-bold text-lg">
              IQ
            </div>
            <div>
              <h1 className="text-sm font-bold tracking-wider text-gray-100 uppercase flex items-center gap-2">
                SwarmIQ <span className="text-accent font-normal text-xs">Autonomous Drone Simulator</span>
              </h1>
              <p className="text-[11px] text-gray-400">
                Hierarchical Boids • 3D A* Path • Potential Fields • Dynamic Leader Election
              </p>
            </div>
          </div>

          <div className="glass-panel px-3 py-1.5 rounded-xl flex items-center gap-2 text-xs">
            {isConnected ? (
              <span className="flex items-center gap-1.5 text-emerald-400 font-mono">
                <Wifi className="w-3.5 h-3.5 animate-pulse" />
                <span>ONLINE (25 Hz)</span>
              </span>
            ) : (
              <span className="flex items-center gap-1.5 text-red-400 font-mono">
                <WifiOff className="w-3.5 h-3.5" />
                <span>BACKEND OFFLINE</span>
              </span>
            )}
          </div>
        </header>

        {/* Middle Area: Left Controls & Right Telemetry Panels */}
        <div className="flex justify-between items-start my-auto w-full">
          {/* Left HUD Panel */}
          <div className="flex flex-col gap-3 pointer-events-auto max-h-[75vh] overflow-y-auto pr-1">
            <Controls
              mission={snapshot?.mission}
              leaderId={snapshot?.leader_id}
            />
            <MissionPanel
              mission={snapshot?.mission}
              leaderId={snapshot?.leader_id}
              metrics={snapshot?.metrics}
            />
          </div>

          {/* Right HUD Panel */}
          <div className="flex flex-col gap-3 pointer-events-auto max-h-[75vh] overflow-y-auto pl-1">
            <MetricsPanel metrics={snapshot?.metrics} />
          </div>
        </div>

        {/* Bottom Preset Scenarios Selector */}
        <footer className="pointer-events-auto">
          <PresetScenarios
            activeScenario={activeScenario}
            onSelectScenario={(id) => setActiveScenario(id)}
          />
        </footer>
      </div>
    </div>
  )
}
