import fs from 'node:fs/promises'
import * as THREE from 'three'
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'

const filename = process.argv[2]
if (!filename) throw new Error('Usage: npm run validate -- <path-to.glb>')
globalThis.self = globalThis
globalThis.ProgressEvent ??= class ProgressEvent { constructor(type, init = {}) { this.type = type; Object.assign(this, init) } }
globalThis.createImageBitmap ??= async () => ({ width: 1, height: 1, close() {} })
const bytes = await fs.readFile(filename)
const buffer = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength)
const gltf = await new Promise((resolve, reject) => new GLTFLoader().parse(buffer, '', resolve, reject))
let meshes = 0
gltf.scene.traverse((node) => {
  if (!node.isMesh) return
  meshes += 1
  if (!node.geometry?.attributes?.position) throw new Error('Mesh has no position attribute')
  node.geometry.computeBoundingBox()
  const box = node.geometry.boundingBox
  if (![box.min.x, box.min.y, box.min.z, box.max.x, box.max.y, box.max.z].every(Number.isFinite)) throw new Error('Mesh bounds are invalid')
})
if (!meshes || new THREE.Box3().setFromObject(gltf.scene).isEmpty()) throw new Error('No renderable Three.js mesh')
console.log(`Three.js/WebXR compatible: ${meshes} mesh(es), finite bounds`)
