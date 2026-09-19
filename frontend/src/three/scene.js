import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

export function createSimulationScene(container) {
  const scene = new THREE.Scene()
  scene.background = new THREE.Color(0x0a0e17)
  scene.fog = new THREE.FogExp2(0x0a0e17, 0.0035)

  // Camera
  const camera = new THREE.PerspectiveCamera(
    55,
    container.clientWidth / container.clientHeight,
    0.1,
    1000
  )
  camera.position.set(-60, 45, -30)

  // Renderer
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: "high-performance" })
  renderer.setSize(container.clientWidth, container.clientHeight)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.shadowMap.enabled = true
  renderer.shadowMap.type = THREE.PCFSoftShadowMap
  container.appendChild(renderer.domElement)

  // Controls
  const controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.08
  controls.maxDistance = 350
  controls.minDistance = 5
  controls.maxPolarAngle = Math.PI / 2 - 0.01 // Don't clip under ground
  controls.target.set(0, 10, 0)

  // Lighting
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.8)
  scene.add(ambientLight)

  const dirLight = new THREE.DirectionalLight(0x06b6d4, 1.2)
  dirLight.position.set(60, 120, 50)
  dirLight.castShadow = true
  dirLight.shadow.mapSize.width = 2048
  dirLight.shadow.mapSize.height = 2048
  dirLight.shadow.camera.near = 10
  dirLight.shadow.camera.far = 300
  dirLight.shadow.camera.left = -120
  dirLight.shadow.camera.right = 120
  dirLight.shadow.camera.top = 120
  dirLight.shadow.camera.bottom = -120
  scene.add(dirLight)

  const secondaryLight = new THREE.DirectionalLight(0x3b82f6, 0.6)
  secondaryLight.position.set(-80, 60, -80)
  scene.add(secondaryLight)

  // Ground Grid & Floor
  const gridHelper = new THREE.GridHelper(240, 60, 0x06b6d4, 0x1e293b)
  gridHelper.position.y = 0.0
  scene.add(gridHelper)

  const floorGeo = new THREE.PlaneGeometry(300, 300)
  const floorMat = new THREE.MeshStandardMaterial({
    color: 0x0a0f1d,
    roughness: 0.9,
    metalness: 0.1,
  })
  const floor = new THREE.Mesh(floorGeo, floorMat)
  floor.rotation.x = -Math.PI / 2
  floor.position.y = -0.05
  floor.receiveShadow = true
  scene.add(floor)

  // Resize handler
  const handleResize = () => {
    if (!container) return
    const width = container.clientWidth
    const height = container.clientHeight
    camera.aspect = width / height
    camera.updateProjectionMatrix()
    renderer.setSize(width, height)
  }
  window.addEventListener('resize', handleResize)

  return {
    scene,
    camera,
    renderer,
    controls,
    cleanup: () => {
      window.removeEventListener('resize', handleResize)
      controls.dispose()
      renderer.dispose()
      if (renderer.domElement && container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement)
      }
    }
  }
}
