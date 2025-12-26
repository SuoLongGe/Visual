<template>
  <div class="industry-nebula" ref="containerRef">
    <canvas ref="terrainCanvas" class="layer terrain"></canvas>
    <canvas ref="heatCanvas" class="layer heat"></canvas>
    <canvas ref="fogCanvas" class="layer fog"></canvas>
    <canvas ref="entitiesCanvas" class="layer entities"></canvas>
    <!-- 控制提示 -->
    <div class="controls">
      <div class="hint">WASD / 方向键 移动，双击跳转</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, reactive } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  industries: {
    type: Array,
    required: true,
    default: () => []
  },
  width: { type: Number, default: 900 },
  height: { type: Number, default: 560 },
  // 外部过滤传入 industry id/name
  filterIndustry: { type: [String, Number], default: null },
  interactive: { type: Boolean, default: true },
  // visuals control
  fogEnabled: { type: Boolean, default: false },
  heatIntensity: { type: Number, default: 1.4 }, // multiplier for heat stamp alpha/size
  footprintDecay: { type: Number, default: 0.03 } // amount to fade heat canvas each frame (0-1)
  ,
  // terrain heatmap mode
  terrainMode: { type: Boolean, default: false },
  terrainSmooth: { type: Number, default: 0.6 } // 0-1 smoothing for gradient influence falloff
})

const emit = defineEmits(['industryEnter', 'selectJob', 'filter', 'hoverIndustry'])

const containerRef = ref(null)
const terrainCanvas = ref(null)
const heatCanvas = ref(null)
const fogCanvas = ref(null)
const entitiesCanvas = ref(null)

let terrainCtx, heatCtx, fogCtx, entitiesCtx

let points = []
let delaunay = null
let voronoi = null
let logicalWidth = props.width
let logicalHeight = props.height

const player = reactive({ x: props.width / 2, y: props.height / 2, r: 8 })
const keys = {}
let animFrame = null
let lastFrameTime = null

// footprints heat accumulation
const heatMap = []

// job nodes (stars)
let jobNodes = []
let particles = []
function spawnEnterParticles(x,y) {
  for (let i = 0; i < 40; i++) {
    particles.push({
      x: x + (Math.random()-0.5) * 20,
      y: y + (Math.random()-0.5) * 20,
      vx: (Math.random()-0.5) * 4,
      vy: (Math.random()-0.5) * 4,
      life: 300 + Math.random() * 400,
      maxLife: 700,
      size: 1 + Math.random() * 3,
      c: { r: 255, g: 220, b: 140 }
    })
  }
}
let hoverIdx = null
let hoverRadius = 0

function initPoints() {
  const w = logicalWidth, h = logicalHeight
  points = props.industries.map((d, i) => ({
    id: d.id ?? i,
    industryName: d.industry_name ?? d.company_type ?? `行业 ${i}`,
    x: Math.random() * (w - 120) + 60,
    y: Math.random() * (h - 120) + 60,
    raw: d
  }))
}

function buildVoronoi() {
  const coords = points.map(p => [p.x, p.y])
  try {
    delaunay = d3.Delaunay.from(coords)
    voronoi = delaunay.voronoi([0, 0, logicalWidth, logicalHeight])
  } catch (e) {
    console.warn('Voronoi build failed', e)
  }
}

function getIndustryCount(raw) {
  return Number(raw?.national_job_count ?? raw?.count ?? raw?.records ?? raw?.job_count ?? 0) || 0
}
function getIndustrySalary(raw) {
  return Number(raw?.avg_median_salary ?? raw?.median_salary ?? raw?.salary ?? 0) || 0
}

function getInnerColorScale(value, min, max) {
  const v = Number(value) || 0
  const mi = Number.isFinite(Number(min)) ? Number(min) : 0
  const ma = Number.isFinite(Number(max)) && Number(max) !== mi ? Number(max) : mi + 1
  const t = (v - mi) / (ma - mi || 1)
  const clamped = Math.max(0, Math.min(1, t))
  const r = 255
  const g = Math.round(200 - 120 * clamped)
  const b = Math.round(200 - 120 * clamped)
  return `rgb(${r},${g},${b})`
}

function setupCanvases() {
  // responsive canvas sizing: fit to container
  const dpr = window.devicePixelRatio || 1
  const resizeAll = () => {
    const container = containerRef.value
    const cw = Math.max(200, Math.floor(container.clientWidth))
    const ch = Math.max(200, Math.floor(container.clientHeight || props.height))
    ;[terrainCanvas, heatCanvas, fogCanvas, entitiesCanvas].forEach(cRef => {
      const c = cRef.value
      c.width = cw * dpr
      c.height = ch * dpr
      c.style.width = cw + 'px'
      c.style.height = ch + 'px'
      const ctx = c.getContext('2d')
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    })
    terrainCtx = terrainCanvas.value.getContext('2d')
    heatCtx = heatCanvas.value.getContext('2d')
    fogCtx = fogCanvas.value.getContext('2d')
    entitiesCtx = entitiesCanvas.value.getContext('2d')
    // ensure canvases start transparent / cleared
    terrainCtx.clearRect(0, 0, cw, ch)
    heatCtx.clearRect(0, 0, cw, ch)
    fogCtx.clearRect(0, 0, cw, ch)
    entitiesCtx.clearRect(0, 0, cw, ch)
    // set pointer-events according to prop
    if (entitiesCanvas.value) {
      entitiesCanvas.value.style.pointerEvents = props.interactive ? 'auto' : 'none'
    }
    // update logical width/height used by the component
    // (we don't reassign props directly; store into local vars if needed)
    // keep logical width/height in sync for voronoi/rendering use
    // NOTE: props are readonly in Vue; use internal variables instead
    logicalWidth = cw
    logicalHeight = ch
    buildVoronoi()
    drawTerrain()
  }
  // initial resize
  resizeAll()
  // observe container resize
  const ro = new ResizeObserver(resizeAll)
  ro.observe(containerRef.value)
  // store observer for cleanup
  setupCanvases._ro = ro
}

function drawTerrain() {
  terrainCtx.clearRect(0,0,logicalWidth,logicalHeight)
  if (props.terrainMode) {
    // additive radial-gradient-based terrain height field
    terrainCtx.clearRect(0,0,logicalWidth,logicalHeight)
    terrainCtx.save()
    // do NOT paint a solid background (it drowns other layers) — keep very subtle base only
    terrainCtx.fillStyle = 'rgba(11,12,15,0.02)'
    terrainCtx.fillRect(0,0,logicalWidth,logicalHeight)
    // composite add gradients per industry: radius ~ count, intensity ~ salary
    const counts = points.map(p => getIndustryCount(p.raw))
    const maxCount = Math.max(1, ...counts)
    const sals = points.map(p => getIndustrySalary(p.raw))
    const minSal = Math.min(...sals)
    const maxSal = Math.max(...sals) || 1
    // debug: if counts are all zero or points empty, draw a visible test gradient so user sees rendering is working
    const totalCount = counts.reduce((s, v) => s + v, 0)
    if (!points.length || totalCount <= 0) {
      terrainCtx.save()
      const cx = logicalWidth / 2, cy = logicalHeight / 2
      const rg = terrainCtx.createRadialGradient(cx, cy, 0, cx, cy, Math.max(logicalWidth, logicalHeight) * 0.3)
      rg.addColorStop(0, 'rgba(255,80,30,1)')
      rg.addColorStop(0.4, 'rgba(255,160,60,0.8)')
      rg.addColorStop(1, 'rgba(0,0,0,0)')
      terrainCtx.globalCompositeOperation = 'lighter'
      terrainCtx.fillStyle = rg
      terrainCtx.beginPath()
      terrainCtx.arc(cx, cy, Math.max(logicalWidth, logicalHeight) * 0.3, 0, Math.PI*2)
      terrainCtx.fill()
      terrainCtx.restore()
      return
    }
    // debug logging to help diagnose invisible terrain
    try {
      console.debug('terrainMode active', { pointsLen: points.length, totalCount, logicalWidth, logicalHeight, sampleCounts: counts.slice(0,6), sampleSals: sals.slice(0,6) })
    } catch (e) {}
    points.forEach((p, i) => {
      const count = getIndustryCount(p.raw)
      const sal = getIndustrySalary(p.raw)
      const countNorm = Math.min(1, count / maxCount)
      // map area proportional to count: area ~ count => radius ~ sqrt(countNorm)
      const areaNorm = Math.sqrt(countNorm)
      const salNorm = (maxSal > minSal) ? Math.max(0, Math.min(1, (sal - minSal) / (maxSal - minSal))) : 0.5
      // reduce max radius so heat spots don't dominate the entire map
      const maxRadius = Math.max(logicalWidth, logicalHeight) * 0.22
      const minRadius = 14
      const radius = Math.round(minRadius + (maxRadius - minRadius) * areaNorm)
      // stronger intensity mapping to ensure visible heat contrast
      const intensity = 0.8 + salNorm * 1.0
      // color by salary using d3 sequential colormap (magma): low->high
      const salNormSafe = Number.isFinite(salNorm) ? salNorm : 0
      const colHex = d3.interpolateMagma(salNormSafe)
      const col = d3.color(colHex)
      // create radial gradient with alpha based on intensity and terrainSmooth falloff
      terrainCtx.globalCompositeOperation = 'lighter'
      const g = terrainCtx.createRadialGradient(p.x, p.y, 0, p.x, p.y, radius * 1.6)
      const smooth = Math.max(0, Math.min(1, Number(props.terrainSmooth)))
      const a0 = Math.min(1, 0.95 * intensity)
      const a1 = Math.min(0.85, 0.55 * intensity)
      const a2 = Math.min(0.45, 0.18 * intensity)
      const c0 = `rgba(${col.r},${col.g},${col.b},${a0})`
      const c1 = `rgba(${col.r},${col.g},${col.b},${a1})`
      const c2 = `rgba(${col.r},${col.g},${col.b},${a2})`
      g.addColorStop(0, c0)
      g.addColorStop(Math.max(0.12, 0.12 * (1 - smooth)), c1)
      g.addColorStop(Math.max(0.45, 0.45 * (1 - smooth)), c2)
      g.addColorStop(1, 'rgba(0,0,0,0)')
      terrainCtx.fillStyle = g
      terrainCtx.beginPath()
      terrainCtx.arc(p.x, p.y, radius, 0, Math.PI*2)
      terrainCtx.fill()
    })
    terrainCtx.restore()
    // draw extra bright overlays for top counts for visibility/debug
    try {
      const indexed = points.map((p, i) => ({ i, c: getIndustryCount(p.raw) }))
      indexed.sort((a,b) => b.c - a.c)
      const topN = Math.min(6, indexed.length)
      terrainCtx.save()
      terrainCtx.globalCompositeOperation = 'lighter'
      for (let t=0; t<topN; t++) {
        const p = points[indexed[t].i]
        const cx = p.x, cy = p.y
        // top overlays: smaller and more transparent
        const rr = Math.max(28, Math.min(Math.max(logicalWidth, logicalHeight)*0.22, 60 + indexed[t].c * 0.00025))
        const g2 = terrainCtx.createRadialGradient(cx, cy, 0, cx, cy, rr)
        g2.addColorStop(0, 'rgba(255,240,180,0.95)')
        g2.addColorStop(0.25, 'rgba(255,180,80,0.6)')
        g2.addColorStop(0.6, 'rgba(255,120,40,0.28)')
        g2.addColorStop(1, 'rgba(0,0,0,0)')
        terrainCtx.fillStyle = g2
        terrainCtx.beginPath()
        terrainCtx.arc(cx, cy, rr, 0, Math.PI*2)
        terrainCtx.fill()
        // stroke center
        terrainCtx.strokeStyle = 'rgba(255,255,255,0.85)'
        terrainCtx.lineWidth = 1
        terrainCtx.beginPath()
        terrainCtx.arc(cx, cy, 6, 0, Math.PI*2)
        terrainCtx.stroke()
      }
      terrainCtx.restore()
    } catch (e) {}
    // draw an always-visible debug indicator on entities layer so user can see terrain drawing occurred
    try {
      if (entitiesCtx) {
        entitiesCtx.save()
        entitiesCtx.globalCompositeOperation = 'source-over'
        const cx = logicalWidth / 2, cy = logicalHeight / 2
        const rg2 = entitiesCtx.createRadialGradient(cx, cy, 0, cx, cy, Math.min(logicalWidth, logicalHeight) * 0.08)
        rg2.addColorStop(0, 'rgba(255,255,255,0.95)')
        rg2.addColorStop(1, 'rgba(255,200,100,0.0)')
        entitiesCtx.fillStyle = rg2
        entitiesCtx.beginPath()
        entitiesCtx.arc(cx, cy, Math.min(logicalWidth, logicalHeight) * 0.08, 0, Math.PI*2)
        entitiesCtx.fill()
        entitiesCtx.restore()
      }
    } catch (e) {}
    // draw voronoi boundaries lightly and labels
    terrainCtx.strokeStyle = 'rgba(255,255,255,0.06)'
    terrainCtx.lineWidth = 0.8
    points.forEach((p, i) => {
      const pathStr = voronoi.renderCell(i)
      if (!pathStr) return
      const path = new Path2D(pathStr)
      terrainCtx.stroke(path)
      terrainCtx.fillStyle = 'rgba(255,255,255,0.85)'
      terrainCtx.font = '12px "Microsoft YaHei", Arial'
      terrainCtx.textAlign = 'center'
      terrainCtx.fillText(p.industryName, p.x, p.y)
    })
    return
  }
  // default: draw each voronoi cell with a color based on industry heat / salary
  points.forEach((p, i) => {
    const pathStr = voronoi.renderCell(i)
    if (!pathStr) return
    const path = new Path2D(pathStr)
    // color mapping: use salary and count to produce terrain color
    const sal = Number(p.raw?.avg_median_salary) || 0
    const salNorm = Math.min(1, Math.max(0, (sal - 5) / 40))
    const green = Math.round(180 - salNorm * 80)
    const red = Math.round(100 + salNorm * 120)
    terrainCtx.fillStyle = `rgb(${red},${green},${100})`
    terrainCtx.fill(path)
    terrainCtx.strokeStyle = 'rgba(255,255,255,0.08)'
    terrainCtx.lineWidth = 1
    terrainCtx.stroke(path)
    // draw label
    terrainCtx.fillStyle = 'rgba(255,255,255,0.9)'
    terrainCtx.font = '12px "Microsoft YaHei", Arial'
    terrainCtx.textAlign = 'center'
    terrainCtx.fillText(p.industryName, p.x, p.y)
  })
}

function initJobNodes() {
  jobNodes = []
  points.forEach(p => {
    const topJobs = Array.isArray(p.raw?.top_jobs) ? p.raw.top_jobs : []
    topJobs.slice(0,5).forEach((j, idx) => {
      const angle = (idx / 5) * Math.PI * 2
      const radius = 20 + Math.random() * 40
      const node = {
        id: `${p.id}::${j.name || j.job_title || idx}`,
        x: p.x + Math.cos(angle) * radius + (Math.random()-0.5)*10,
        y: p.y + Math.sin(angle) * radius + (Math.random()-0.5)*10,
        r: Math.max(3, Math.min(10, (Number(j.count)||1) ** 0.4)),
        raw: j,
        industryId: p.id,
        industryName: p.industryName,
        // mark emerging: explicit flag or heuristic by count/some score
        isEmerging: Boolean(j.is_emerging) || (Number(j.count) || 0) > 200 || (Number(j.score) || 0) > 0.8
      }
      jobNodes.push(node)
    })
  })
}

function drawEntities() {
  entitiesCtx.clearRect(0,0,logicalWidth,logicalHeight)
  const now = performance.now()
  // draw job nodes (stars) with optional pulsing for emerging nodes
  jobNodes.forEach((n, idx) => {
    if (n.isEmerging) {
      const pulse = 0.6 + 0.6 * Math.sin(now / 400 + idx)
      entitiesCtx.beginPath()
      entitiesCtx.strokeStyle = `rgba(255,200,100,${0.12 * pulse})`
      entitiesCtx.lineWidth = 2
      entitiesCtx.arc(n.x, n.y, n.r + 6 + pulse * 6, 0, Math.PI*2)
      entitiesCtx.stroke()
    }
    entitiesCtx.beginPath()
    // draw with radial gradient for nicer glow
    const grad = entitiesCtx.createRadialGradient(n.x, n.y, 0, n.x, n.y, n.r * 3)
    if (n.isEmerging) {
      grad.addColorStop(0, 'rgba(255,240,200,1)')
      grad.addColorStop(0.2, 'rgba(255,210,120,0.9)')
      grad.addColorStop(0.6, 'rgba(255,160,60,0.45)')
      grad.addColorStop(1, 'rgba(255,120,20,0)')
    } else {
      grad.addColorStop(0, 'rgba(255,255,255,0.95)')
      grad.addColorStop(0.5, 'rgba(200,220,255,0.25)')
      grad.addColorStop(1, 'rgba(200,220,255,0)')
    }
    entitiesCtx.globalCompositeOperation = 'lighter'
    entitiesCtx.fillStyle = grad
    entitiesCtx.beginPath()
    entitiesCtx.arc(n.x, n.y, n.r * 2.2, 0, Math.PI*2)
    entitiesCtx.fill()
    // core
    entitiesCtx.beginPath()
    entitiesCtx.fillStyle = n.isEmerging ? 'rgba(255,230,140,1)' : 'rgba(255,255,255,0.95)'
    entitiesCtx.arc(n.x, n.y, n.r, 0, Math.PI*2)
    entitiesCtx.fill()
  })

  // update and draw particles
  if (particles.length) {
    for (let i = particles.length - 1; i >= 0; i--) {
      const p = particles[i]
      p.x += p.vx; p.y += p.vy; p.life -= 16
      entitiesCtx.beginPath()
      entitiesCtx.fillStyle = `rgba(${p.c.r},${p.c.g},${p.c.b},${Math.max(0, p.life / p.maxLife)})`
      entitiesCtx.arc(p.x, p.y, p.size, 0, Math.PI*2)
      entitiesCtx.fill()
      if (p.life <= 0) particles.splice(i,1)
    }
  }

  // draw player
  entitiesCtx.beginPath()
  entitiesCtx.fillStyle = '#FFD27A'
  entitiesCtx.shadowColor = 'rgba(255,210,122,0.6)'
  entitiesCtx.shadowBlur = 12
  entitiesCtx.arc(player.x, player.y, player.r, 0, Math.PI*2)
  entitiesCtx.fill()
  entitiesCtx.shadowBlur = 0
  // draw hover outline if present
  if (hoverIdx != null && points[hoverIdx]) {
    const h = points[hoverIdx]
    entitiesCtx.save()
    entitiesCtx.beginPath()
    entitiesCtx.strokeStyle = 'rgba(255,255,255,0.9)'
    entitiesCtx.lineWidth = 2
    entitiesCtx.setLineDash([6,6])
    entitiesCtx.arc(h.x, h.y, hoverRadius, 0, Math.PI*2)
    entitiesCtx.stroke()
    entitiesCtx.restore()
  }
}

function drawFog() {
  // fog is dark overlay with cleared circle around player and slight trail
  fogCtx.clearRect(0,0,logicalWidth,logicalHeight)
  if (!props.fogEnabled) return
  // draw fog overlay with a softened clear around player
  // when terrainMode is active, make fog very transparent so terrain colors remain visible
  const baseFogAlpha = 0.85
  const fogAlpha = props.terrainMode ? 0.06 : baseFogAlpha
  fogCtx.fillStyle = `rgba(10,12,18,${fogAlpha})`
  fogCtx.fillRect(0,0,logicalWidth,logicalHeight)
  fogCtx.globalCompositeOperation = 'destination-out'
  const minDim = Math.min(logicalWidth, logicalHeight)
  const holeRadius = Math.max(120, Math.round(minDim * 0.16))
  const grad = fogCtx.createRadialGradient(player.x, player.y, 0, player.x, player.y, holeRadius)
  // inner should be opaque to clear fully; outer transparent to leave fog beyond
  grad.addColorStop(0, 'rgba(0,0,0,1.0)')
  grad.addColorStop(0.6, 'rgba(0,0,0,0.6)')
  grad.addColorStop(1, 'rgba(0,0,0,0.0)')
  fogCtx.fillStyle = grad
  fogCtx.beginPath()
  fogCtx.arc(player.x, player.y, holeRadius, 0, Math.PI*2)
  fogCtx.fill()
  fogCtx.globalCompositeOperation = 'source-over'
}

function heatStamp(x,y) {
  // apply intensity and draw a soft radial gradient 'heat' stamp using additive blending
  const rawIntensity = Number(props.heatIntensity)
  const intensity = Number.isFinite(rawIntensity) ? Math.max(0.2, rawIntensity) : 1
  const baseRadius = 24 * Math.max(0.9, intensity)
  heatCtx.save()
  heatCtx.globalCompositeOperation = 'lighter'
  const g = heatCtx.createRadialGradient(x, y, 0, x, y, baseRadius * 2.6)
  // stronger center alpha to make heat visible even at low intensity settings
  const cen = Math.min(1, intensity)
  g.addColorStop(0, `rgba(255,220,130,${cen})`)
  g.addColorStop(0.2, `rgba(255,170,80,${0.7 * cen})`)
  g.addColorStop(0.55, `rgba(255,110,50,${0.35 * cen})`)
  g.addColorStop(1, 'rgba(255,110,50,0)')
  heatCtx.fillStyle = g
  heatCtx.beginPath()
  heatCtx.arc(x, y, baseRadius * 2.6, 0, Math.PI * 2)
  heatCtx.fill()
  heatCtx.restore()
}

function findIndustryAt(x,y) {
  if (!delaunay) return null
  const idx = delaunay.find(x,y)
  return points[idx] ?? null
}

function handleMovement() {
  // legacy: use dt-based smooth movement; keys: up/down/left/right boolean flags
  const speedPxPerSec = 220 // pixels per second
  const now = performance.now()
  const dt = lastFrameTime ? Math.min(50, now - lastFrameTime) / 1000 : 0
  lastFrameTime = now
  if (!dt) return
  let dx = 0, dy = 0
  if (keys.up) dy -= 1
  if (keys.down) dy += 1
  if (keys.left) dx -= 1
  if (keys.right) dx += 1
  if (dx !== 0 || dy !== 0) {
    const len = Math.sqrt(dx*dx + dy*dy) || 1
    const move = speedPxPerSec * dt
    player.x = Math.max(8, Math.min(logicalWidth-8, player.x + (dx/len) * move))
    player.y = Math.max(8, Math.min(logicalHeight-8, player.y + (dy/len) * move))
  }
}

let lastIndustry = null
function frame() {
  handleMovement()
  drawEntities()
  drawFog()
  // decay heat canvas slightly to create footprint fading (use destination-out to fade, not darken)
  if (heatCtx) {
    // accept explicit 0 value from props; don't use || fallback which treats 0 as falsy
    const raw = Number(props.footprintDecay)
    const decay = Number.isFinite(raw) ? Math.max(0, Math.min(0.5, raw)) : 0.03
    if (decay > 0) {
      heatCtx.save()
      heatCtx.globalCompositeOperation = 'destination-out'
      heatCtx.fillStyle = `rgba(0,0,0,${decay})`
      heatCtx.fillRect(0,0,logicalWidth,logicalHeight)
      heatCtx.restore()
    }
  }
  heatStamp(player.x, player.y)
  const found = findIndustryAt(player.x, player.y)
  // 当玩家进入新的行业区域时触发行业进入事件（键盘或移动均应触发）
  if (found && (!lastIndustry || lastIndustry.id !== found.id)) {
    lastIndustry = found
    emit('industryEnter', found.raw)
    spawnEnterParticles(found.x, found.y)
  }
  animFrame = requestAnimationFrame(frame)
}

// teleport animation
let teleporting = false
function teleportTo(x,y) {
  if (teleporting) return
  teleporting = true
  const start = { x: player.x, y: player.y }
  const dur = 700
  const t0 = performance.now()
  function step(ts) {
    const p = Math.min(1, (ts - t0) / dur)
    const ease = d3.easeCubicInOut(p)
    player.x = start.x + (x - start.x) * ease
    player.y = start.y + (y - start.y) * ease
    if (p < 1) requestAnimationFrame(step)
    else teleporting = false
  }
  requestAnimationFrame(step)
  // spawn particles at target for visual effect
  for (let i = 0; i < 28; i++) {
    particles.push({
      x, y,
      vx: (Math.random()-0.5) * 6,
      vy: (Math.random()-0.5) * 6,
      life: 600 + Math.random() * 400,
      maxLife: 1000,
      size: 1 + Math.random() * 2,
      c: { r: 255, g: 200 + Math.round(Math.random()*55), b: 120 }
    })
  }
}

function onKeyDown(e) {
  // prevent page scrolling for movement keys and set direction flags using e.code for stability
  const preventCodes = ['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','KeyW','KeyA','KeyS','KeyD']
  if (preventCodes.includes(e.code)) {
    e.preventDefault()
  }
  switch (e.code) {
    case 'ArrowUp':
    case 'KeyW':
      keys.up = true; break
    case 'ArrowDown':
    case 'KeyS':
      keys.down = true; break
    case 'ArrowLeft':
    case 'KeyA':
      keys.left = true; break
    case 'ArrowRight':
    case 'KeyD':
      keys.right = true; break
    default:
      // preserve old behavior for other keys
      keys[e.key] = true
  }
  // compatibility: also set the raw key name (some code or older logic may read it)
  keys[e.key] = true
}
function onKeyUp(e) {
  switch (e.code) {
    case 'ArrowUp':
    case 'KeyW':
      keys.up = false; break
    case 'ArrowDown':
    case 'KeyS':
      keys.down = false; break
    case 'ArrowLeft':
    case 'KeyA':
      keys.left = false; break
    case 'ArrowRight':
    case 'KeyD':
      keys.right = false; break
    default:
      keys[e.key] = false
  }
  // compatibility
  keys[e.key] = false
}

function onDblClick(ev) {
  const rect = entitiesCanvas.value.getBoundingClientRect()
  const x = (ev.clientX - rect.left)
  const y = (ev.clientY - rect.top)
  // find nearest industry and teleport near its center
  const idx = delaunay.find(x,y)
  const p = points[idx]
  if (p) {
    teleportTo(p.x + (Math.random()-0.5)*20, p.y + (Math.random()-0.5)*20)
    emit('filter', p.raw)
  }
}

function onPointerDown(ev) {
  const rect = entitiesCanvas.value.getBoundingClientRect()
  const x = (ev.clientX - rect.left)
  const y = (ev.clientY - rect.top)
  // enable dragging control
  pointerActive = true
  ev.preventDefault()
  // detect click on job node
  for (const n of jobNodes) {
    const dx = n.x - x, dy = n.y - y
    if (Math.sqrt(dx*dx + dy*dy) <= n.r + 2) {
      // 明确的点击选中职位：发射 selectJob 事件（用于反向联动至玫瑰图）
      emit('selectJob', n.raw)
      return
    }
  }
  // also on pointer down, update lastIndustry immediately (so click/drag updates info)
  const idx = delaunay?.find(x, y)
  if (typeof idx === 'number') {
    const p = points[idx]
    if (p) {
      lastIndustry = p
      emit('industryEnter', p.raw)
    }
  }
}

// touch support: allow dragging player by touch
let pointerActive = false
function onPointerMove(ev) {
  if (!pointerActive) return
  const rect = entitiesCanvas.value.getBoundingClientRect()
  player.x = Math.max(8, Math.min(logicalWidth-8, ev.clientX - rect.left))
  player.y = Math.max(8, Math.min(logicalHeight-8, ev.clientY - rect.top))
}
function onPointerUp() {
  pointerActive = false
}

// hover handler for terrain detection (uses delaunay.find)
function onCanvasPointerMove(ev) {
  if (!delaunay || !entitiesCanvas.value) return
  const rect = entitiesCanvas.value.getBoundingClientRect()
  const x = ev.clientX - rect.left
  const y = ev.clientY - rect.top
  const idx = delaunay.find(x, y)
  const p = points[idx]
  if (!p) {
    if (hoverIdx !== null) {
      hoverIdx = null
      hoverRadius = 0
      emit('hoverIndustry', null)
    }
    return
  }
  if (hoverIdx !== idx) {
    hoverIdx = idx
    // compute radius for hover outline using same mapping as drawTerrain
    const counts = points.map(pp => getIndustryCount(pp.raw))
    const maxCount = Math.max(1, ...counts)
    const count = getIndustryCount(p.raw)
    const countNorm = Math.min(1, count / maxCount)
    const areaNorm = Math.sqrt(countNorm)
    const maxRadius = Math.max(logicalWidth, logicalHeight) * 0.22
    const minRadius = 14
    hoverRadius = Math.round(minRadius + (maxRadius - minRadius) * areaNorm)
    emit('hoverIndustry', p.raw)
  }
}

onMounted(() => {
  initPoints()
  buildVoronoi()
  setupCanvases()
  initJobNodes()
  drawTerrain()
  drawEntities()
  drawFog()
  window.addEventListener('keydown', onKeyDown, { passive: false })
  window.addEventListener('keyup', onKeyUp)
  entitiesCanvas.value.addEventListener('dblclick', onDblClick)
  entitiesCanvas.value.addEventListener('pointerdown', onPointerDown)
  entitiesCanvas.value.addEventListener('pointermove', onPointerMove)
  entitiesCanvas.value.addEventListener('pointermove', onCanvasPointerMove)
  entitiesCanvas.value.addEventListener('pointerup', onPointerUp)
  animFrame = requestAnimationFrame(frame)
})
  // add hover pointermove listener for terrain hover detection (registered in onMounted)
// re-render terrain when visual props change
watch(() => [props.terrainMode, props.terrainSmooth, props.heatIntensity, props.footprintDecay, props.fogEnabled], () => {
  // redraw static terrain layer when mode or smooth changes
  try { drawTerrain() } catch (e) { /* ignore */ }
})
// 为了确保键盘事件在元素捕获或其他组件阻断时仍然可用，额外在 document 上做捕获注册
const _docKeyHandlers = {
  attached: false
}
function attachDocumentKeyHandlers() {
  if (_docKeyHandlers.attached) return
  document.addEventListener('keydown', onKeyDown, { passive: false, capture: true })
  document.addEventListener('keyup', onKeyUp, { capture: true })
  _docKeyHandlers.attached = true
}
function detachDocumentKeyHandlers() {
  if (!_docKeyHandlers.attached) return
  document.removeEventListener('keydown', onKeyDown, { capture: true })
  document.removeEventListener('keyup', onKeyUp, { capture: true })
  _docKeyHandlers.attached = false
}
attachDocumentKeyHandlers()

// 当 interactive prop 改变时，调整 entities 层的 pointer-events
watch(() => props.interactive, (val) => {
  if (entitiesCanvas.value) entitiesCanvas.value.style.pointerEvents = val ? 'auto' : 'none'
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeyDown, { passive: false })
  window.removeEventListener('keyup', onKeyUp)
  entitiesCanvas.value.removeEventListener('dblclick', onDblClick)
  entitiesCanvas.value.removeEventListener('pointerdown', onPointerDown)
  entitiesCanvas.value.removeEventListener('pointermove', onPointerMove)
  entitiesCanvas.value && entitiesCanvas.value.removeEventListener('pointermove', onCanvasPointerMove)
  entitiesCanvas.value.removeEventListener('pointerup', onPointerUp)
  detachDocumentKeyHandlers()
  cancelAnimationFrame(animFrame)
  // disconnect resize observer if present
  if (setupCanvases._ro) setupCanvases._ro.disconnect()
})

watch(() => props.industries, (v) => {
  initPoints(); buildVoronoi(); initJobNodes(); drawTerrain()
}, { deep: true })

watch(() => props.filterIndustry, (id) => {
  if (!id) return
  // find corresponding point and teleport to it
  const p = points.find(x => x.id === id || x.industryName === id || x.raw?.id === id)
  if (p) teleportTo(p.x, p.y)
})

</script>

<style scoped>
.industry-nebula { position: relative; width: 100%; height: 100%; max-width: 100%; display: block; z-index: 50; }
.industry-nebula .layer { position: absolute; inset: 0; pointer-events: none; z-index: 10; }
.industry-nebula .layer.terrain { z-index: 11; }
.industry-nebula .layer.heat { z-index: 12; }
.industry-nebula .layer.fog { z-index: 13; }
.industry-nebula .layer.entities { pointer-events: auto; z-index: 14; } /* allow interaction on entities layer */
.industry-nebula .controls { position: absolute; left: 12px; bottom: 12px; color: #fff; font-size:12px; background: rgba(0,0,0,0.25); padding:6px 8px; border-radius:6px; z-index:3 }
.industry-nebula canvas { display:block; width:100%; height:100%; border-radius:8px; }
.layer.terrain, .layer.entities, .layer.fog, .layer.heat { width: 100%; height: 100%; }
</style>


