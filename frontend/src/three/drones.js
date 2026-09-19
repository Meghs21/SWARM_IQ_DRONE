import * as THREE from 'three'

export class DroneRenderer {
  constructor(scene, maxDrones = 150) {
    self.scene = scene
    this.scene = scene
    this.maxDrones = maxDrones

    // Temporary math objects for high-performance matrix updates
    this.tempMatrix = new THREE.Matrix4()
    this.tempPos = new THREE.Vector3()
    this.tempTargetPos = new THREE.Vector3()
    this.tempQuat = new THREE.Quaternion()
    this.tempScale = new THREE.Vector3(1, 1, 1)
    this.tempColor = new THREE.Color()

    // Map to track interpolated positions for smooth 60fps rendering
    this.droneInterpolations = new Map()
    this.colorTheme = 'emerald'

    // 1. Follower Drones Instanced Mesh
    const droneGeometry = this.createDroneGeometry()
    const droneMaterial = new THREE.MeshStandardMaterial({
      color: 0xffffff,
      roughness: 0.25,
      metalness: 0.1,
      emissive: 0x0a2f1d,
      emissiveIntensity: 0.35,
    })
    this.instancedMesh = new THREE.InstancedMesh(droneGeometry, droneMaterial, maxDrones)
    this.instancedMesh.castShadow = true
    this.instancedMesh.receiveShadow = true
    this.instancedMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage)

    // Pre-initialize instance colors so shader compiles with USE_INSTANCING_COLOR
    for (let i = 0; i < maxDrones; i++) {
      this.tempScale.set(0, 0, 0)
      this.tempMatrix.compose(this.tempPos, this.tempQuat, this.tempScale)
      this.instancedMesh.setMatrixAt(i, this.tempMatrix)
      this.instancedMesh.setColorAt(i, new THREE.Color(0x10b981))
    }
    this.instancedMesh.instanceMatrix.needsUpdate = true
    if (this.instancedMesh.instanceColor) {
      this.instancedMesh.instanceColor.needsUpdate = true
    }
    this.scene.add(this.instancedMesh)

    // 2. Leader Drone Mesh
    this.leaderGroup = new THREE.Group()
    const leaderBodyGeo = new THREE.OctahedronGeometry(1.1)
    const leaderMat = new THREE.MeshStandardMaterial({
      color: 0xfbbf24,
      emissive: 0xd97706,
      emissiveIntensity: 0.7,
      roughness: 0.2,
      metalness: 0.3,
    })
    this.leaderMesh = new THREE.Mesh(leaderBodyGeo, leaderMat)
    this.leaderMesh.castShadow = true
    this.leaderGroup.add(this.leaderMesh)

    // Rotating beacon ring for leader
    const ringGeo = new THREE.TorusGeometry(1.8, 0.08, 16, 64)
    const ringMat = new THREE.MeshBasicMaterial({ color: 0xfbbf24, wireframe: true })
    this.beaconRing = new THREE.Mesh(ringGeo, ringMat)
    this.beaconRing.rotation.x = Math.PI / 2
    this.leaderGroup.add(this.beaconRing)

    // Leader point light
    this.leaderLight = new THREE.PointLight(0xfbbf24, 2.5, 20)
    this.leaderGroup.add(this.leaderLight)

    this.leaderGroup.visible = false
    this.scene.add(this.leaderGroup)
  }

  createDroneGeometry() {
    // Sleek faceted delta-wing drone body:
    // Wide aerodynamic arrowhead with prominent wingtips
    const geo = new THREE.ConeGeometry(1.2, 1.8, 4)
    geo.rotateX(Math.PI / 2) // Point nose forward along +Z
    geo.scale(1.3, 0.45, 1.3) // Flatten vertically and widen
    return geo
  }

  update(drones, leaderId) {
    if (!drones || !Array.isArray(drones)) return

    let followerIndex = 0
    let leaderFound = false

    const defaultQuat = new THREE.Quaternion()

    for (let i = 0; i < drones.length; i++) {
      const drone = drones[i]
      const isLeader = drone.id === leaderId && drone.role === 'LEADER'

      // Interpolation setup
      let interp = this.droneInterpolations.get(drone.id)
      if (!interp) {
        interp = {
          currentPos: new THREE.Vector3(drone.position.x, drone.position.y, drone.position.z),
          targetPos: new THREE.Vector3(drone.position.x, drone.position.y, drone.position.z),
          currentQuat: new THREE.Quaternion(),
        }
        this.droneInterpolations.set(drone.id, interp)
      }

      interp.targetPos.set(drone.position.x, drone.position.y, drone.position.z)

      // Compute heading rotation
      const vel = new THREE.Vector3(drone.velocity.x, drone.velocity.y, drone.velocity.z)
      if (vel.lengthSq() > 0.1) {
        const forward = vel.clone().normalize()
        const rotMatrix = new THREE.Matrix4().lookAt(new THREE.Vector3(0, 0, 0), forward, new THREE.Vector3(0, 1, 0))
        interp.currentQuat.setFromRotationMatrix(rotMatrix)
      }

      // Smooth lerp (15% per frame)
      interp.currentPos.lerp(interp.targetPos, 0.22)

      if (isLeader) {
        leaderFound = true
        this.leaderGroup.visible = true
        this.leaderGroup.position.copy(interp.currentPos)
        this.leaderGroup.quaternion.copy(interp.currentQuat)
        this.beaconRing.rotation.z += 0.04
      } else if (followerIndex < this.maxDrones) {
        this.tempScale.set(1, 1, 1)
        this.tempMatrix.compose(interp.currentPos, interp.currentQuat, this.tempScale)
        this.instancedMesh.setMatrixAt(followerIndex, this.tempMatrix)

        // Color based on status
        if (drone.status === 'FAILED') {
          this.tempColor.setHex(0xef4444) // Red
        } else if (drone.status === 'RETURNING') {
          this.tempColor.setHex(0xf59e0b) // Amber
        } else {
          // Follower color theme
          if (this.colorTheme === 'violet') {
            this.tempColor.setHex(drone.battery > 50 ? 0xa855f7 : 0x7c3aed)
          } else if (this.colorTheme === 'white') {
            this.tempColor.setHex(drone.battery > 50 ? 0xf8fafc : 0x94a3b8)
          } else if (this.colorTheme === 'amber') {
            this.tempColor.setHex(drone.battery > 50 ? 0xf97316 : 0xd97706)
          } else if (this.colorTheme === 'cyan') {
            this.tempColor.setHex(drone.battery > 50 ? 0x06b6d4 : 0x0284c7)
          } else {
            // Default: Neon Emerald Green
            this.tempColor.setHex(drone.battery > 50 ? 0x10b981 : 0x059669)
          }
        }
        this.instancedMesh.setColorAt(followerIndex, this.tempColor)
        followerIndex++
      }
    }

    if (!leaderFound) {
      this.leaderGroup.visible = false
    }

    // Hide unused instances
    for (let i = followerIndex; i < this.maxDrones; i++) {
      this.tempScale.set(0, 0, 0)
      this.tempMatrix.compose(this.tempPos, defaultQuat, this.tempScale)
      this.instancedMesh.setMatrixAt(i, this.tempMatrix)
    }

    this.instancedMesh.instanceMatrix.needsUpdate = true
    if (this.instancedMesh.instanceColor) {
      this.instancedMesh.instanceColor.needsUpdate = true
    }
  }

  setColorTheme(theme) {
    this.colorTheme = theme
  }

  cleanup() {
    this.scene.remove(this.instancedMesh)
    this.scene.remove(this.leaderGroup)
    this.instancedMesh.geometry.dispose()
    this.instancedMesh.material.dispose()
    this.droneInterpolations.clear()
  }
}
