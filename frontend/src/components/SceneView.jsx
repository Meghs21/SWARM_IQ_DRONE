import React, { useEffect, useRef } from 'react'
import { createSimulationScene } from '../three/scene'
import { DroneRenderer } from '../three/drones'
import { EnvironmentRenderer } from '../three/environment'

export default function SceneView({ snapshot, colorTheme = 'emerald' }) {
  const containerRef = useRef(null)
  const droneRendererRef = useRef(null)
  const envRendererRef = useRef(null)
  const sceneContextRef = useRef(null)

  useEffect(() => {
    if (!containerRef.current) return

    // 1. Initialize Scene, Camera, Controls, Lights
    const ctx = createSimulationScene(containerRef.current)
    sceneContextRef.current = ctx

    // 2. Initialize Renderers
    const droneRenderer = new DroneRenderer(ctx.scene, 150)
    droneRenderer.setColorTheme(colorTheme)
    droneRendererRef.current = droneRenderer

    const envRenderer = new EnvironmentRenderer(ctx.scene)
    envRendererRef.current = envRenderer

    // 3. Render Loop (60 FPS)
    let animationFrameId
    const animate = () => {
      animationFrameId = requestAnimationFrame(animate)
      ctx.controls.update()
      ctx.renderer.render(ctx.scene, ctx.camera)
    }
    animate()

    return () => {
      cancelAnimationFrame(animationFrameId)
      droneRenderer.cleanup()
      envRenderer.cleanup()
      ctx.cleanup()
    }
  }, [])

  // Update color theme when changed
  useEffect(() => {
    if (droneRendererRef.current) {
      droneRendererRef.current.setColorTheme(colorTheme)
    }
  }, [colorTheme])

  // Update 3D renderers on each WebSocket snapshot
  useEffect(() => {
    if (!snapshot) return

    if (droneRendererRef.current) {
      droneRendererRef.current.update(snapshot.drones, snapshot.leader_id)
    }

    if (envRendererRef.current) {
      envRendererRef.current.update(
        snapshot.obstacles,
        snapshot.waypoints,
        snapshot.mission ? snapshot.mission.target : null
      )
    }
  }, [snapshot])

  return (
    <div
      ref={containerRef}
      className="absolute inset-0 w-full h-full cursor-grab active:cursor-grabbing"
    />
  )
}
