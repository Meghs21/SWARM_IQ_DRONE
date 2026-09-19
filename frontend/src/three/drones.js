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

    // 1. Follower Drones Instanced Mesh
    const droneGeometry = this.createDroneGeometry()
    const droneMaterial = new THREE.MeshStandardMaterial({
      roughness: 0.3,
      metalness: 0.8,
      vertexColors: true,
    })
    this.instancedMesh = new THREE.InstancedMesh(droneGeometry, droneMaterial, maxDrones)
    this.instancedMesh.castShadow = true
    this.instancedMesh.receiveShadow = true
    this.instancedMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage)
    this.scene.add(this.instancedMesh)

    // 2. Leader Drone Mesh
    this.leaderGroup = new THREE.Group()
    const leaderBodyGeo = new THREE.OctahedronGeometry(0.85)
    const leaderMat = new THREE.MeshStandardMaterial({
      color: 0xf59e0b,
      emissive: 0xd97706,
      emissiveIntensity: 0.6,
      roughness: 0.2,
      metalness: 0.9,
    })
    this.leaderMesh = new THREE.Mesh(leaderBodyGeo, leaderMat)
    this.leaderMesh.castShadow = true
    this.leaderGroup.add(this.leaderMesh)

    // Rotating beacon ring for leader
    const ringGeo = new THREE.TorusGeometry(1.6, 0.06, 16, 64)
    const ringMat = new THREE.MeshBasicMaterial({ color: 0xfbbf24, wireframe: true })
    this.beaconRing = new THREE.Mesh(ringGeo, ringMat)
    this.beaconRing.rotation.x = Math.PI / 2
    this.leaderGroup.add(this.beaconRing)

    // Leader point light
    this.leaderLight = new THREE.PointLight(0xfbbf24, 2.0, 15)
    this.leaderGroup.add(this.leaderLight)

    this.leaderGroup.visible = false
    this.scene.add(this.leaderGroup)

    // Hide all instances initially
    for (let i = 0; i < maxDrones; i++) {
      this.tempScale.set(0, 0, 0)
      this.tempMatrix.compose(this.tempPos, this.tempQuat, this.tempScale)
      this.instancedMesh.setMatrixAt(i, this.tempMatrix)
    }
    this.instancedMesh.instanceMatrix.needsUpdate = true
  }

  createDroneGeometry() {
    // Quadcopter drone structure
    const droneGroup = new THREE.Group()

    // Center body
    const body = new THREE.Mesh(
      new THREE.BoxGeometry(0.6, 0.2, 0.6),
      new THREE.MeshStandardMaterial()
    )
    droneGroup.add(body)

    // 4 rotor arms
    const arm1 = new THREE.Mesh(
      new THREE.CylinderGeometry(0.04, 0.04, 1.2),
      new THREE.MeshStandardMaterial()
    )
    arm1.rotation.z = Math.PI / 2
    arm1.rotation.y = Math.PI / 4
    droneGroup.add(arm1)

    const arm2 = new THREE.Mesh(
      new THREE.CylinderGeometry(0.04, 0.04, 1.2),
      new THREE.MeshStandardMaterial()
    )
    arm2.rotation.z = Math.PI / 2
    arm2.rotation.y = -Math.PI / 4
    droneGroup.add(arm2)

    // Merge into single BufferGeometry for instancing
    // Or simplified cone/tetrahedron for high-efficiency rendering
    const geo = new THREE.ConeGeometry(0.5, 0.9, 5)
    geo.rotateX(Math.PI / 2) // Point forward along Z
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
          // Cyan gradient according to battery
          this.tempColor.setHex(drone.battery > 50 ? 0x06b6d4 : 0x3b82f6)
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

  cleanup() {
    this.scene.remove(this.instancedMesh)
    this.scene.remove(this.leaderGroup)
    this.instancedMesh.geometry.dispose()
    this.instancedMesh.material.dispose()
    this.droneInterpolations.clear()
  }
}
