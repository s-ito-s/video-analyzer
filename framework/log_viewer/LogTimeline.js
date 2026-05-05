// type InternalTimelineData = {
//   readonly label: string
//   readonly labelColor: string
//   readonly backgroundColor: string
//   readonly data: readonly {
//     readonly start: number
//     readonly end: number
//     readonly color: string
//     readonly memo: string
//   }[]
// }

const SCALE_HEIGHT = 80
const MARGIN_Y = 40
const TIMELINE_HEIGHT = 40

const TIME_MS_PER_PIX = 1000 * 50
const MIN_TIME_MS_PER_PIX = 0.005
const MAX_TIME_MS_PER_PIX = 1500000

// デフォルトカラー
const DEFAULT_CHART_COLOR = '#fff'
const DEFAULT_SCALE_COLOR = '#e9e9e9'
const DEFAULT_SCALE_LINE_COLOR = '#9e9e9e'
const DEFAULT_SCALE_TEXT_COLOR = '#000'
const DEFAULT_TIMELINE_LABEL_COLOR = '#000'
const DEFAULT_TIMELINE_DATA_COLOR = '#156ce6'
const DEFAULT_TIMELINE_BACKGROUND_COLOR = '#e9e9e9'

class LogTimeline {
  parentDom = null
  canvas = null
  ctx = null

  timelines = [] // タイムラインのデータ
  startTimeMs = 0// 表示する開始時間
  fromTimeMs = 0// 表示範囲の開始時間
  toTimeMs = 0// 表示範囲の終了時間
  timeMsPerPix = TIME_MS_PER_PIX // 1 ピクセル当たりミリ秒
  timelineDrawData = []

  minTimeMsPerPix = MIN_TIME_MS_PER_PIX // 最小のピクセル当たりミリ秒
  maxTimeMsPerPix = MAX_TIME_MS_PER_PIX // 最大のピクセル当たりミリ秒

  chartColor = DEFAULT_CHART_COLOR
  scaleColor = DEFAULT_SCALE_COLOR
  scaleLineColor = DEFAULT_SCALE_LINE_COLOR
  scaleTextColor = DEFAULT_SCALE_TEXT_COLOR
  timelineLabelColor = DEFAULT_TIMELINE_LABEL_COLOR

  isMouseDown = false
  mousePosX = 0 

  constructor() {
    this.parentDom = null
    this.canvas = document.createElement('canvas')
    this.ctx = this.canvas.getContext('2d')

    this.timelines = []
    this.startTimeMs = new Date().getTime()
    this.fromTimeMs = new Date().getTime() - 1000 * 60 * 60 * 24
    this.toTimeMs = new Date().getTime() + 1000 * 60 * 60 * 24
    this.timelineDrawData = []
    this.mouseHoveredTimelineDataIdx = null
    this.mouseHoveredTimelineData = null

    this.timeMsPerPix = TIME_MS_PER_PIX // 1 ピクセル当たりミリ秒
    this.minTimeMsPerPix = MIN_TIME_MS_PER_PIX // 最小のピクセル当たりミリ秒
    this.maxTimeMsPerPix = MAX_TIME_MS_PER_PIX // 最大のピクセル当たりミリ秒

    // カラー
    this.chartColor = DEFAULT_CHART_COLOR
    this.scaleColor = DEFAULT_SCALE_COLOR
    this.scaleLineColor = DEFAULT_SCALE_LINE_COLOR
    this.scaleTextColor = DEFAULT_SCALE_TEXT_COLOR
    this.timelineLabelColor = DEFAULT_TIMELINE_LABEL_COLOR

    // マウス操作
    this.isMouseDown = false
    this.mousePosX = 0

    this.resize = this.resize.bind(this)
    this.mouseUp = this.mouseUp.bind(this)
    this.mouseDown = this.mouseDown.bind(this)
    this.mouseMove = this.mouseMove.bind(this)
    this.wheel = this.wheel.bind(this)

    this.init()
  }

  init() {
    this.canvas.addEventListener('mousedown', this.mouseDown)
    document.addEventListener('mouseup', this.mouseUp)
    document.addEventListener('mousemove', this.mouseMove)
    this.canvas.addEventListener('wheel', this.wheel, { passive: false })
    window.addEventListener('resize', this.resize)
  }  

  destroy() {
    window.removeEventListener('resize', this.resize)
    document.removeEventListener('mouseup', this.mouseUp)
    document.removeEventListener('mousemove', this.mouseMove)
    this.canvas.removeEventListener('mousedown', this.mouseDown)
    this.canvas.removeEventListener('wheel', this.wheel)
    if (this.canvas.parentElement) {
      this.canvas.parentElement.removeChild(this.canvas)
    }
    this.parentDom = null
  }

  setParent(target) {
    if (this.parentDom && this.canvas.parentNode === this.parentDom) {
      this.parentDom.removeChild(this.canvas)
    }
    this.parentDom = target
    target.appendChild(this.canvas)
    this.canvas.style.cursor = 'grab'
    this.resize()
  }

  setTimelines(timelines) {
    this.timelines = timelines.map((timeline) => ({
      label: timeline.label,
      labelColor: timeline.labelColor,
      backgroundColor: timeline.backgroundColor ?? DEFAULT_TIMELINE_BACKGROUND_COLOR,
      data: timeline.data.map((data) => ({
        start: dateTimeToMs(data.start),
        end: dateTimeToMs(data.end),
        color: data.color,
        comment: data.comment,
      })),
    }))
    this.resize()
  }

  setTimeRange(from, to) {
    this.fromTimeMs = dateTimeToMs(from)
    this.toTimeMs = dateTimeToMs(to)
    this.startTimeMs = this.fromTimeMs
    this.clampStartTime()
    this.draw()
  }

  setStartTime(start) {
    this.startTimeMs = dateTimeToMs(start)
    this.clampStartTime()
    this.draw()
  }

  setTimeScale(scale) {
    switch (scale) {
      case 'day':
        this.timeMsPerPix = 1000 * 600
        break
      case 'hour':
        this.timeMsPerPix = 1000 * 18
        break
      case 'min':
        this.timeMsPerPix = 240
        break
      case 'sec':
        this.timeMsPerPix = 6
        break
      case 'msec':
        this.timeMsPerPix = 0.01
        break
    }
    this.clampStartTime()
    this.draw()
  }

  setColor(colors) {
    this.chartColor = colors.chartColor ?? this.chartColor
    this.scaleColor = colors.scaleColor ?? this.scaleColor
    this.scaleLineColor = colors.scaleLineColor ?? this.scaleLineColor
    this.scaleTextColor = colors.scaleTextColor ?? this.scaleTextColor
    this.timelineLabelColor = colors.timelineLabelColor ?? this.timelineLabelColor
    this.draw()
  }

  mouseDown(e) {
    this.isMouseDown = true
    this.mousePosX = e.clientX
    this.canvas.style.cursor = 'grabbing'
  }

  mouseMove(e) {
    this.mouseHoveredTimelineDataIdx = null
    const diffX = e.clientX - this.mousePosX
    if (this.isMouseDown) {
      this.startTimeMs -= diffX * this.timeMsPerPix
      this.clampStartTime()
    } else {
      for (let i = this.timelineDrawData.length - 1; i >= 0; i--) {
        const timelineData = this.timelineDrawData[i]
        const rect = timelineData.rect
        if (
          e.offsetX >= rect.x &&
          e.offsetX <= rect.x + rect.width &&
          e.offsetY >= rect.y &&
          e.offsetY <= rect.y + rect.height
        ) {
          this.mouseHoveredTimelineDataIdx = i
          break
        }
      }
      if (this.mouseHoveredTimelineDataIdx !== null) {
        this.canvas.style.cursor = 'pointer'
      } else {
        this.canvas.style.cursor = this.isMouseDown ? 'grabbing' : 'grab'
      }
    }
    this.mousePosX = e.clientX
    this.draw()
  }

  mouseUp() {
    this.isMouseDown = false
    this.canvas.style.cursor = 'grab'
  }  

  wheel(e) {
    e.preventDefault()
    this.mouseHoveredTimelineDataIdx = null

    const prevTimePerPix = this.timeMsPerPix
    const diff = e.deltaY
    let nextTimePerPix = 0
    if (diff > 0) {
      nextTimePerPix = this.timeMsPerPix * 1.1
    } else {
      nextTimePerPix = this.timeMsPerPix * 0.9
    }
    this.timeMsPerPix = Math.max(
      this.minTimeMsPerPix,
      Math.min(this.maxTimeMsPerPix, nextTimePerPix),
    )
    this.startTimeMs += (prevTimePerPix - this.timeMsPerPix) * e.offsetX
    this.clampStartTime()
    this.draw()
  }

  resize() {
    this.canvas.width = this.canvas.parentElement?.clientWidth ?? 0
    this.canvas.height =
      SCALE_HEIGHT + (MARGIN_Y + TIMELINE_HEIGHT) * this.timelines.length + MARGIN_Y
    this.canvas.style.width = this.canvas.width + 'px'
    this.canvas.style.height = this.canvas.height + 'px'
    this.clampStartTime()
    this.draw()
  }

  draw() {
    this.drawFrame()
    this.drawTimelines()
    this.drawScale()
    this.drawHoveredTimelineData()
  }

  drawFrame() {
    const width = this.canvas.width
    const height = this.canvas.height
    this.drawRect(this.ctx, 0, 0, width, height, this.chartColor)
    this.drawRect(this.ctx, 0, 0, width, SCALE_HEIGHT, this.scaleColor)
    this.drawLine(this.ctx, 0, height - 1, width, height - 1, this.scaleLineColor)
  }

  drawScale() {
    const scaleIntervalMs = this.getScaleIntervalMs()
    const scaleTextType = this.getScaleTextType()
    const endTimeMs = this.startTimeMs + this.canvas.width * this.timeMsPerPix
    const scaleStartTimeMs = this.startTimeMs - (this.startTimeMs % scaleIntervalMs)
    let shouldAppendDayScale = true
    let scaleDayText = ''

    for (
      let scaleTimeMs = scaleStartTimeMs;
      scaleTimeMs <= endTimeMs;
      scaleTimeMs += scaleIntervalMs
    ) {
      // 範囲外の目盛りはスキップ
      if (scaleTimeMs < this.fromTimeMs || scaleTimeMs > this.toTimeMs) {
        continue
      }

      // 目盛りを描画する
      const posX = this.time2Pos(scaleTimeMs)
      this.drawLine(
        this.ctx,
        posX,
        SCALE_HEIGHT * 0.7,
        posX,
        this.canvas.height,
        this.scaleLineColor,
      )

      // 目盛りに描画するテキストを調整
      const date = new Date(scaleTimeMs)
      const month = String(date.getUTCMonth() + 1)
      const day = String(date.getUTCDate())
      const hour = String(date.getUTCHours())
      const min = String(date.getUTCMinutes()).padStart(2, '0')
      const sec = String(date.getUTCSeconds()).padStart(2, '0')
      if (scaleTimeMs === scaleStartTimeMs || (scaleTimeMs >= this.fromTimeMs && !scaleDayText)) {
        scaleDayText = month + '/' + day
      }
      let text = ''
      if (scaleTextType === 'day') {
        text = month + '/' + day
        shouldAppendDayScale = false
      } else if (scaleTextType === 'min') {
        text = hour + ':' + min
      } else if (scaleTextType === 'sec' || scaleTextType === 'msec') {
        text = hour + ':' + min + ':' + sec
        if (scaleTextType === 'msec') {
          shouldAppendDayScale = false
        }
      }

      // 日時を描画する
      const textWidth = this.ctx?.measureText(text).width || 0
      if (scaleTextType === 'msec') {
        this.drawText(
          this.ctx,
          posX - textWidth / 2,
          SCALE_HEIGHT * 0.3,
          text,
          this.scaleTextColor,
          16,
        )
        const msec = '.' + String(date.getUTCMilliseconds()).padStart(3, '0')
        const msecTextWidth = this.ctx?.measureText(msec).width || 0
        this.drawText(
          this.ctx,
          posX - msecTextWidth / 2,
          SCALE_HEIGHT * 0.6,
          msec,
          this.scaleTextColor,
          16,
        )
      } else {
        this.drawText(
          this.ctx,
          posX - textWidth / 2,
          SCALE_HEIGHT * 0.6,
          text,
          this.scaleTextColor,
          16,
        )
      }

      // 0:00:00 の場合は日付も描画する
      if (
        (scaleTextType === 'min' && hour === '0' && min === '00') ||
        (scaleTextType === 'sec' && hour === '0' && min === '00' && sec === '00')
      ) {
        shouldAppendDayScale = false
        const dateText = month + '/' + day
        const dateTextWidth = this.ctx?.measureText(dateText).width || 0
        this.drawText(
          this.ctx,
          posX - dateTextWidth / 2,
          SCALE_HEIGHT * 0.3,
          dateText,
          this.scaleTextColor,
          16,
        )
      }
    }
    if (shouldAppendDayScale) {
      // 日付を描画する
      this.drawText(this.ctx, 10, SCALE_HEIGHT * 0.3, scaleDayText, this.scaleTextColor, 16)
    }
  }

  drawTimelines() {
    this.timelineDrawData = []

    const endTimeMs = this.startTimeMs + this.canvas.width * this.timeMsPerPix
    for (let i = 0; i < this.timelines.length; i++) {
      const timelinePosY = SCALE_HEIGHT + MARGIN_Y * (i + 1) + TIMELINE_HEIGHT * i

      // タイムラインにラベルを付与
      const label = this.timelines[i].label ?? ''
      if (label) {
        const labelColor = this.timelines[i].labelColor || this.timelineLabelColor
        this.drawText(this.ctx, 10, timelinePosY - 5, label, labelColor, 16)
      }

      // fromTimeMs と toTimeMs の範囲内の背景色を描画する
      const timelineBackgroundColor = this.timelines[i].backgroundColor
      this.drawRect(
        this.ctx,
        this.time2Pos(this.fromTimeMs),
        timelinePosY,
        this.time2Pos(this.toTimeMs) - this.time2Pos(this.fromTimeMs),
        TIMELINE_HEIGHT,
        timelineBackgroundColor,
      )

      for (let j = 0; j < this.timelines[i].data.length; ++j) {
        const timelineStartTimeMs = this.timelines[i].data[j].start
        const timelineEndTimeMs = this.timelines[i].data[j].end

        // タイムラインが現在表示している範囲外の場合は描画しない
        if (timelineEndTimeMs < this.startTimeMs || endTimeMs < timelineStartTimeMs) {
          continue
        }

        // タイムラインを描画範囲を計算
        let x = this.time2Pos(timelineStartTimeMs)
        let width = this.time2Pos(timelineEndTimeMs) - this.time2Pos(timelineStartTimeMs)

        // タイムラインの開始位置が表示範囲より前の場合の描画位置補正
        if (timelineStartTimeMs < this.startTimeMs && timelineEndTimeMs < endTimeMs) {
          x = 0
          width = this.time2Pos(timelineEndTimeMs) - this.time2Pos(this.startTimeMs)
        }

        // タイムラインの終了位置が表示範囲より後の場合の描画位置補正
        if (this.startTimeMs < timelineStartTimeMs && endTimeMs < timelineEndTimeMs) {
          x = this.time2Pos(timelineStartTimeMs)
          width = this.canvas.width - x
        }

        // 消えてしまわないように最低限の幅を確保
        width = Math.max(1, width)

        const timelineDataColor = this.timelines[i].data[j].color ?? DEFAULT_TIMELINE_DATA_COLOR
        const comment = this.timelines[i].data[j].comment ?? ''
        this.drawRect(this.ctx, x, timelinePosY, width, TIMELINE_HEIGHT, timelineDataColor)
        this.timelineDrawData.push({
          rect: { x, y: timelinePosY, width, height: TIMELINE_HEIGHT },
          comment: comment
        })

        // 隙間が消えてしまわないように最低限の幅を確保
        if (j === 0) {
          continue
        }
        const previousTimelineEndTimeMs = this.timelines[i].data[j - 1].end
        const gapWidth =
          this.time2Pos(timelineStartTimeMs) - this.time2Pos(previousTimelineEndTimeMs)
        if (gapWidth < 1) {
          this.drawRect(
            this.ctx,
            this.time2Pos(previousTimelineEndTimeMs),
            timelinePosY,
            1,
            TIMELINE_HEIGHT,
            timelineBackgroundColor,
          )
        }
      }
    }
  }

  drawHoveredTimelineData() {
    if (this.mouseHoveredTimelineDataIdx === null) {
      return
    }
    const data = this.timelineDrawData[this.mouseHoveredTimelineDataIdx]
    if (!data) {
      return
    }
    const rect = data.rect
    const text = data.comment

    // タイムラインのデータを描画する
    const textWidth = this.ctx?.measureText(text).width || 0
    const posX = Math.min(
      Math.max(0, this.mousePosX - textWidth / 2),
      this.canvas.width - textWidth,
    )
    const posY = rect.y - 10
    this.drawText(this.ctx, posX, posY, text, this.scaleTextColor, 14)

    // タイムラインのデータの枠を描画する
    this.ctx.strokeStyle = '#ff0000'
    this.ctx.strokeRect(rect.x+1, rect.y+1, rect.width-2, rect.height-2)
  }

  drawLine(ctx, x1, y1, x2, y2, color) {
    if (!ctx) return
    ctx.strokeStyle = color
    ctx.beginPath()
    ctx.moveTo(x1, y1)
    ctx.lineTo(x2, y2)
    ctx.stroke()
  }

  drawRect(ctx, x, y, w, h, color) {
    if (!ctx) return
    ctx.fillStyle = color
    ctx.fillRect(x, y, w, h)
  }

  drawText(ctx, x, y, text, color, size) {
    if (!ctx) return
    ctx.font = size + 'px sans-serif'
    ctx.fillStyle = color
    ctx.fillText(text, x, y)
  }

  getScaleIntervalMs() {
    if (this.timeMsPerPix < 0.014) {
      return 1 // 1 ミリ秒
    }
    if (this.timeMsPerPix < 0.04) {
      return 5 // 5 ミリ秒
    }
    if (this.timeMsPerPix < 0.12) {
      return 10 // 10 ミリ秒
    }
    if (this.timeMsPerPix < 0.36) {
      return 50 // 50 ミリ秒
    }
    if (this.timeMsPerPix < 1.2) {
      return 100 // 100 ミリ秒
    }
    if (this.timeMsPerPix < 6) {
      return 500 // 500 ミリ秒
    }
    if (this.timeMsPerPix < 12) {
      return 1000 // 1 秒
    }
    if (this.timeMsPerPix < 50) {
      return 1000 * 5 // 5 秒
    }
    if (this.timeMsPerPix < 120) {
      return 1000 * 10 // 10 秒
    }
    if (this.timeMsPerPix < 240) {
      return 1000 * 30 // 30 秒
    }
    if (this.timeMsPerPix < 1000) {
      return 1000 * 60 // 1 分
    }
    if (this.timeMsPerPix < 1000 * 4) {
      return 1000 * 60 * 5 // 5 分
    }
    if (this.timeMsPerPix < 1000 * 8) {
      return 1000 * 60 * 10 // 10 分
    }
    if (this.timeMsPerPix < 1000 * 18) {
      return 1000 * 60 * 30 // 30 分
    }
    if (this.timeMsPerPix < 1000 * 60) {
      return 1000 * 60 * 60 // 1 時間
    }
    if (this.timeMsPerPix < 1000 * 150) {
      return 1000 * 60 * 60 * 3 // 3 時間
    }
    if (this.timeMsPerPix < 1000 * 300) {
      return 1000 * 60 * 60 * 6 // 6 時間
    }
    if (this.timeMsPerPix < 1000 * 600) {
      return 1000 * 60 * 60 * 12 // 12 時間
    }
    return 1000 * 60 * 60 * 24 // 24 時間
  }

  getScaleTextType() {
    if (this.timeMsPerPix < 6) {
      return 'msec'
    }
    if (this.timeMsPerPix < 240) {
      return 'sec'
    }
    if (this.timeMsPerPix < 1000 * 600) {
      return 'min'
    }
    return 'day'
  }

  time2Pos(time) {
    return (time - this.startTimeMs) / this.timeMsPerPix
  }

  clampStartTime() {
    const viewWidthMs = this.canvas.width * this.timeMsPerPix
    const rangeWidthMs = this.toTimeMs - this.fromTimeMs

    // 表示範囲が期間全体より大きい場合は、期間全体が見えるようズームを調整
    if (viewWidthMs > rangeWidthMs) {
      this.timeMsPerPix = rangeWidthMs / this.canvas.width
    }

    const minStart = this.fromTimeMs
    const maxStart = this.toTimeMs - this.canvas.width * this.timeMsPerPix
    this.startTimeMs = Math.max(minStart, Math.min(maxStart, this.startTimeMs))
  }  
}

const dateTimeToMs = (dt) => {
  return Date.UTC(
    dt.year ?? 0,
    (dt.month ?? 1) - 1,
    dt.day ?? 1,
    dt.hour ?? 0,
    dt.minute ?? 0,
    dt.second ?? 0,
    dt.millisecond ?? 0,
  )
}
