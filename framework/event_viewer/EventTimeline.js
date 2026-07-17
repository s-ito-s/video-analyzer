const TIMELINE_BAR_HEIGHT = 12
const TIMELINE_SCALE_LINE_HEIGHT = 8
const TIMELINE_SCALE_TEXT_AREA_HEIGHT = 36
const TIMELINE_SCALE_TEXT_HEIGHT = 14
const TIMELINE_BACKGROUND_COLOR = '#ffffff'
const TIMELINE_BAR_BLANK_COLOR = '#d3d3d3'
const TIMELINE_BAR_COLOR = '#e3ecfc'
const TIMELINE_CURRENT_TIME_LINE_COLOR = '#32a4ef'
const TIMELINE_SCALE_LINE_COLOR = '#a0a0a0'
const TIMELINE_SCALE_TEXT_COLOR = '#a0a0a0'
const EVENT_MARKER_MAX_WIDTH = 12
const EVENT_MARKER_HEIGHT = 12
const EVENT_MARKER_GAP_Y = 12
const EVENT_MARKER_SELECTED_BORDER_COLOR = '#ff0000'
const MIN_TIME_MS_PER_PIX = 3

class EventTimeline {
  // DOM elements
  parentDom = null
  canvas = document.createElement('canvas')

  // Timeline state
  durationMs = 1000000
  currentTimeMs = 0
  timeMsPerPix = 30

  // EventTimelines
  eventTimelines = []
  eventMarkerRects = []
  selectedEventMarkerId = null

  // Mouse & Touch interaction
  isMouseDown = false
  mousePosX = 0
  // touches = []

  // callbacks
  onTimeChange = null
  onClickEventMarker = null

  constructor(dom) {
    this.parentDom = dom
    this.parentDom.appendChild(this.canvas)

    this.canvas.addEventListener('mousedown', this.mouseDown)
    this.canvas.addEventListener('mousemove', this.mouseMove)
    this.canvas.addEventListener('mouseup', this.mouseUp)
    this.canvas.addEventListener('mouseleave', this.mouseLeave)
    this.canvas.addEventListener('wheel', this.mouseWheel)
    window.addEventListener('resize', this.resize)

    this.resize()
  }

  destroy() {
    this.parentDom?.removeChild(this.canvas)
    this.canvas.removeEventListener('mousedown', this.mouseDown)
    this.canvas.removeEventListener('mousemove', this.mouseMove)
    this.canvas.removeEventListener('mouseup', this.mouseUp)
    this.canvas.removeEventListener('mouseleave', this.mouseLeave)
    this.canvas.removeEventListener('wheel', this.mouseWheel)
    window.removeEventListener('resize', this.resize)
  }

  setDuration(durationMs) {
    this.durationMs = durationMs
    this.draw()
  }

  setCurrentTime(currentTimeMs) {
    if (this.isMouseDown) {
      return // Do not update current time while dragging
    }
    this.currentTimeMs = currentTimeMs
    this.draw()
  }

  getCurrentTime() {
    return this.currentTimeMs
  }

  setEventTimelines(eventTimelines) {
    this.eventTimelines = JSON.parse(JSON.stringify(eventTimelines))
    this.resize()
  }

  getEventTimelines() {
    return JSON.parse(JSON.stringify(this.eventTimelines))
  }

  selectEventMarker(eventMarkerId) {
    this.selectedEventMarkerId = eventMarkerId
    this.draw()
  }

  resize = () => {
    if (!this.parentDom) {
      return
    }

    const timelineHeight =
      EVENT_MARKER_GAP_Y +
      (EVENT_MARKER_HEIGHT + EVENT_MARKER_GAP_Y) * Object.keys(this.eventTimelines).length +
      TIMELINE_BAR_HEIGHT +
      TIMELINE_SCALE_LINE_HEIGHT +
      TIMELINE_SCALE_TEXT_AREA_HEIGHT
    this.canvas.style.width = '100%'
    this.canvas.style.height = timelineHeight + 'px'
    this.canvas.width = this.parentDom.clientWidth
    this.canvas.height = timelineHeight
    this.draw()
  }

  mouseDown = (e) => {
    this.isMouseDown = true
    this.mousePosX = e.offsetX

    for (const rect of this.eventMarkerRects) {
      if (rect.rect.isInside(e.offsetX, e.offsetY)) {
        if (this.onClickEventMarker) {
          this.onClickEventMarker(rect.timelineName, { ...rect.eventMarker })
        }
        break
      }
    }
  }

  mouseMove = (e) => {
    if (this.isMouseDown) {
      const prevMousePosX = this.mousePosX
      this.mousePosX = e.offsetX
      const diffX = prevMousePosX - this.mousePosX
      const newCurrentTime = this.currentTimeMs + diffX * this.timeMsPerPix
      this.currentTimeMs = Math.max(0, Math.min(this.durationMs - 0.1, newCurrentTime))
      this.draw()
    }

    this.canvas.style.cursor = 'ew-resize'
    for (const rect of this.eventMarkerRects) {
      if (rect.rect.isInside(e.offsetX, e.offsetY)) {
        this.canvas.style.cursor = 'pointer'
      }
    }
  }

  mouseUp = () => {
    if (this.onTimeChange) {
      this.onTimeChange(this.currentTimeMs)
    }
    this.isMouseDown = false
  }

  mouseLeave = () => {
    this.isMouseDown = false
    this.canvas.style.cursor = 'default'
  }

  mouseWheel = (e) => {
    e.preventDefault()
    let newTimeMsPerPix = this.timeMsPerPix
    if (e.deltaY > 0) {
      newTimeMsPerPix *= 1.1
    } else {
      newTimeMsPerPix *= 0.9
    }
    const maxTimeMsPerPix = this.durationMs / 500
    this.timeMsPerPix = Math.min(Math.max(MIN_TIME_MS_PER_PIX, newTimeMsPerPix), maxTimeMsPerPix)
    this.draw()
  }

  draw = () => {
    if (!this.canvas) return
    const ctx = this.canvas.getContext('2d')
    if (!ctx) return

    // Clear
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height)
    this.eventMarkerRects = []

    // Draw background
    ctx.fillStyle = TIMELINE_BACKGROUND_COLOR
    ctx.fillRect(0, 0, this.canvas.width, this.canvas.height)

    // Draw timeline bar
    const barHeight = TIMELINE_BAR_HEIGHT
    const barPosY =
      EVENT_MARKER_GAP_Y +
      (EVENT_MARKER_GAP_Y + EVENT_MARKER_HEIGHT) * Object.keys(this.eventTimelines).length
    const videoStartPosX = this.time2pix(0)
    const videoEndPosX = this.time2pix(this.durationMs)
    ctx.fillStyle = TIMELINE_BAR_COLOR
    ctx.fillRect(videoStartPosX, barPosY, videoEndPosX - videoStartPosX, barHeight)
    const barWidth = this.canvas.width
    const timeLineScalePosY = barPosY + barHeight
    ctx.fillStyle = TIMELINE_BAR_BLANK_COLOR
    ctx.fillRect(0, timeLineScalePosY, barWidth, 2)

    // Draw scale lines and text
    ctx.font = TIMELINE_SCALE_TEXT_HEIGHT + 'px Arial'
    const { scaleInterval, textInterval } = this.adjustScale(this.timeMsPerPix)
    const leftEndTime = this.pix2time(0)
    const rightEndTime = this.pix2time(this.canvas.width)
    const firstScaleTime = Math.floor(leftEndTime / scaleInterval) * scaleInterval
    let i = 0
    while (1) {
      const scaleTime = firstScaleTime + i * scaleInterval
      if (scaleTime > rightEndTime || scaleTime > this.durationMs) {
        break
      }

      if (scaleTime < 0) {
        i++
        continue
      }

      // Draw scale line
      const scalePosX = this.time2pix(scaleTime)
      const scaleLineStartY = timeLineScalePosY
      const scaleLineEndY =
        scaleTime % textInterval === 0
          ? scaleLineStartY + TIMELINE_SCALE_LINE_HEIGHT * 2
          : scaleLineStartY + TIMELINE_SCALE_LINE_HEIGHT
      ctx.fillStyle = TIMELINE_SCALE_LINE_COLOR
      ctx.fillRect(scalePosX, scaleLineStartY, 1, scaleLineEndY - scaleLineStartY)

      // Draw scale text
      if (scaleTime % textInterval === 0) {
        const scaleTextPosY = scaleLineEndY + 5
        ctx.textAlign = 'center'
        ctx.textBaseline = 'top'
        ctx.fillStyle = TIMELINE_SCALE_TEXT_COLOR
        ctx.fillText(this.time2str(scaleTime), scalePosX, scaleTextPosY)
      }

      i++
    }

    // Draw event markers
    const eventMarkerGapY = EVENT_MARKER_GAP_Y
    let eventMarkerPosY = eventMarkerGapY
    for (const timeline of this.eventTimelines) {
      for (const marker of timeline.eventMarkers) {
        let markerPosX = this.time2pix(marker.timeMs)
        let markerWidth = EVENT_MARKER_MAX_WIDTH

        if (marker.durationMs) {
          markerWidth = marker.durationMs / this.timeMsPerPix
          if (
            this.pix2time(markerPosX + markerWidth) < leftEndTime ||
            rightEndTime < this.pix2time(markerPosX)
          ) {
            continue // Skip if the marker is out of visible range
          }
        } else {
          markerPosX = markerPosX - EVENT_MARKER_MAX_WIDTH / 2
          if (
            this.pix2time(markerPosX + EVENT_MARKER_MAX_WIDTH) < leftEndTime ||
            rightEndTime < this.pix2time(markerPosX)
          ) {
            continue // Skip if the marker is out of visible range
          }
        }

        ctx.fillStyle = marker.color
        ctx.fillRect(markerPosX, eventMarkerPosY, markerWidth, EVENT_MARKER_HEIGHT)
        if (this.selectedEventMarkerId === marker.id) {
          ctx.strokeStyle = EVENT_MARKER_SELECTED_BORDER_COLOR
          ctx.lineWidth = 2
          ctx.strokeRect(markerPosX, eventMarkerPosY, markerWidth, EVENT_MARKER_HEIGHT)
        }
        this.eventMarkerRects.push({
          timelineName: timeline.name,
          eventMarker: marker,
          rect: new Rect(markerPosX, eventMarkerPosY, markerWidth, EVENT_MARKER_HEIGHT),
        })
      }
      eventMarkerPosY += EVENT_MARKER_HEIGHT + EVENT_MARKER_GAP_Y
    }

    // Draw current time line
    const centerLinePosX = this.canvas.width / 2
    ctx.fillStyle = TIMELINE_CURRENT_TIME_LINE_COLOR
    ctx.fillRect(centerLinePosX, 0, 1, this.canvas.height)
  }

  time2pix(timeMs) {
    const leftEndTimeMs = this.currentTimeMs - (this.canvas.width / 2) * this.timeMsPerPix
    return (timeMs - leftEndTimeMs) / this.timeMsPerPix
  }

  pix2time(pix) {
    const leftEndTimeMs = this.currentTimeMs - (this.canvas.width / 2) * this.timeMsPerPix
    return pix * this.timeMsPerPix + leftEndTimeMs
  }

  time2str(timeMs) {
    const HOUR_MS = 60 * 60 * 1000
    const MIN_MS = 60 * 1000
    const SEC_MS = 1000
    const hour = Math.floor(timeMs / HOUR_MS)
    const min = Math.floor((timeMs - hour * HOUR_MS) / MIN_MS)
    const sec = Math.floor((timeMs - hour * HOUR_MS - min * MIN_MS) / SEC_MS)
    return hour + ':' + min.toString().padStart(2, '0') + ':' + sec.toString().padStart(2, '0')
  }

  adjustScale(timeMsPerPix) {
    const map = [
      { timePerPix: 10, scaleInterval: 100, textInterval: 1000 },
      { timePerPix: 50, scaleInterval: 1000, textInterval: 5 * 1000 },
      { timePerPix: 120, scaleInterval: 1000, textInterval: 10 * 1000 },
      { timePerPix: 240, scaleInterval: 1000 * 5, textInterval: 30 * 1000 },
      { timePerPix: 700, scaleInterval: 1000 * 10, textInterval: 60 * 1000 },
      { timePerPix: 2500, scaleInterval: 1000 * 30, textInterval: 5 * 60 * 1000 },
      { timePerPix: 8000, scaleInterval: 1000 * 60, textInterval: 10 * 60 * 1000 },
      { timePerPix: 24000, scaleInterval: 1000 * 60 * 5, textInterval: 30 * 60 * 1000 },
      { timePerPix: 80000, scaleInterval: 1000 * 60 * 10, textInterval: 60 * 60 * 1000 },
      { timePerPix: 120000, scaleInterval: 1000 * 60 * 60, textInterval: 3 * 60 * 60 * 1000 },
      { timePerPix: 400000, scaleInterval: 1000 * 60 * 60, textInterval: 6 * 60 * 60 * 1000 },
    ]

    for (const m of map) {
      if (m.timePerPix > timeMsPerPix) {
        return {
          scaleInterval: m.scaleInterval,
          textInterval: m.textInterval,
        }
      }
    }

    return {
      scaleInterval: 1000 * 60 * 60,
      textInterval: 6 * 60 * 60 * 1000,
    }
  }
}

class Rect {
  constructor(
    x,
    y,
    width,
    height,
  ) {
    this.x = x
    this.y = y
    this.width = width
    this.height = height
  }

  isInside(x, y) {
    return x >= this.x && x <= this.x + this.width && y >= this.y && y <= this.y + this.height
  }
}