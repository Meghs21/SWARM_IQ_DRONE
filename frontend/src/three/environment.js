import * as THREE from 'three'

export class EnvironmentRenderer {
  constructor(scene) {
    this.scene = scene
    this.obstacleMeshes = new Map()

    // Waypoint Path Line
    this.pathLineMaterial = new THREE.LineBasicMaterial({
      color: 0x10b981,
      linewidth: 3,
      transparent: true,
      opacity: 0.8,
    })
    this.pathLineGeometry = new THREE.BufferGeometry()
    this.pathLine = new THREE.Line(this.pathLineGeometry, this.pathLineMaterial)
    this.scene.add(this.pathLine)

    // Destination Beacon
    this.beaconGroup = new THREE.Group()
    const targetRingGeo = new THREE.TorusGeometry(3.5, 0.15, 16, 64)
    const targetRingMat = new THREE.MeshBasicMaterial({ color: 0x10b981, wireframe: true })
    this.targetRing = new THREE.Mesh(targetRingGeo, targetRingMat)
    this.targetRing.rotation.x = Math.PI / 2
    this.beaconGroup.add(this.targetRing)

    const beamGeo = new THREE.CylinderGeometry(0.2, 0.2, 60, 16)
    const beamMat = new THREE.MeshBasicMaterial({
      color: 0x10b981,
      transparent: true,
      opacity: 0.4,
    })
    const beam = new THREE.Mesh(beamGeo, beamMat)
    beam.position.y = 30
    this.beaconGroup.add(beam)
    this.scene.add(this.beaconGroup)
  }

  update(obstacles, waypoints, target) {
    // 1. Update Destination Beacon
    if (target) {
      this.beaconGroup.visible = true
      this.beaconGroup.position.set(target.x, 0, target.z)
      this.targetRing.rotation.z += 0.02
    } else {
      this.beaconGroup.visible = false
    }

    // 2. Update A* Waypoint Line
    if (waypoints && waypoints.length > 1) {
      this.pathLine.visible = true
      const points = waypoints.map((w) => new THREE.Vector3(w.x, w.y, w.z))
      this.pathLineGeometry.setFromPoints(points)
    } else {
      this.pathLine.visible = false
    }

    // 3. Update Obstacles
    const activeIds = new Set()

    if (obstacles && Array.isArray(obstacles)) {
      for (const obs of obstacles) {
        activeIds.add(obs.id)
        let mesh = this.obstacleMeshes.get(obs.id)

        if (!mesh) {
          mesh = this.createObstacleMesh(obs)
          this.obstacleMeshes.set(obs.id, mesh)
          this.scene.add(mesh)
        }

        // Update position
        mesh.position.set(obs.position.x, obs.position.y, obs.position.z)

        // Dynamic obstacle animation
        if (obs.is_dynamic && mesh.halo) {
          mesh.halo.rotation.y += 0.05
          mesh.halo.rotation.x += 0.02
        }
      }
    }

    // Remove deleted obstacles
    for (const [id, mesh] of this.obstacleMeshes.entries()) {
      if (!activeIds.has(id)) {
        this.scene.remove(mesh)
        this.obstacleMeshes.delete(id)
      }
    }
  }

  createObstacleMesh(obs) {
    const group = new THREE.Group()
    let mainMesh

    if (obs.type === 'CYLINDER') {
      const radius = obs.size.x
      const height = obs.size.y
      const geo = new THREE.CylinderGeometry(radius, radius, height, 32)
      const mat = new THREE.MeshStandardMaterial({
        color: 0x334155,
        metalness: 0.8,
        roughness: 0.3,
      })
      mainMesh = new THREE.Mesh(geo, mat)
      // Offset so cylinder sits upright
      mainMesh.position.y = height / 2
      mainMesh.castShadow = true
      mainMesh.receiveShadow = true
      group.add(mainMesh)

      // Warning stripes ring
      const ringGeo = new THREE.TorusGeometry(radius + 0.3, 0.15, 16, 32)
      const ringMat = new THREE.MeshBasicMaterial({ color: 0xef4444 })
      const ring = new THREE.Mesh(ringGeo, ringMat)
      ring.rotation.x = Math.PI / 2
      ring.position.y = height * 0.7
      group.add(ring)

    } else if (obs.type === 'BOX') {
      const geo = new THREE.BoxGeometry(obs.size.x, obs.size.y, obs.size.z)
      const mat = new THREE.MeshStandardMaterial({
        color: 0x1e293b,
        metalness: 0.7,
        roughness: 0.4,
      })
      mainMesh = new THREE.Mesh(geo, mat)
      mainMesh.castShadow = true
      mainMesh.receiveShadow = true
      group.add(mainMesh)

    } else {
      // SPHERE
      const radius = obs.size.x
      const geo = new THREE.SphereGeometry(radius, 32, 32)
      const mat = new THREE.MeshStandardMaterial({
        color: obs.is_dynamic ? 0xd97706 : 0x475569,
        metalness: 0.6,
        roughness: 0.4,
      })
      mainMesh = new THREE.Mesh(geo, mat)
      mainMesh.castShadow = true
      mainMesh.receiveShadow = true
      group.add(mainMesh)
    }

    if (obs.is_dynamic) {
      // Pulsing wireframe halo
      const haloGeo = new THREE.IcosahedronGeometry(obs.size.x * 1.35, 1)
      const haloMat = new THREE.MeshBasicMaterial({
        color: 0xf59e0b,
        wireframe: true,
        transparent: true,
        opacity: 0.5,
      })
      const halo = new THREE.Mesh(haloGeo, haloMat)
      group.add(halo)
      group.halo = halo
    }

    return group
  }

  cleanup() {
    this.scene.remove(this.pathLine)
    this.scene.remove(this.beaconGroup)
    for (const mesh of this.obstacleMeshes.values()) {
      this.scene.remove(mesh)
    }
    this.obstacleMeshes.clear()
  }
}
