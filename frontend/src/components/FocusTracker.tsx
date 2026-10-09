import { useEffect, useRef, useState } from 'react'
import { CameraIcon, EyeIcon } from 'lucide-react'
import { sendFocusFrame } from '../api'
import { Alert, AlertDescription, Badge, Card, Progress, Spinner } from './primitives'

interface FocusTrackerProps {
  sessionId: string
  active: boolean
}

export function FocusTracker({ sessionId, active }: FocusTrackerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const requestInFlight = useRef(false)
  const [score, setScore] = useState<number | null>(null)
  const [facePresent, setFacePresent] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let timer: number | undefined
    let cancelled = false

    async function start() {
      if (!active) return
      if (!navigator.mediaDevices?.getUserMedia) { setError('Camera tracking is not supported by this browser.'); return }
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user', width: 640, height: 480 }, audio: false })
        if (cancelled) { stream.getTracks().forEach(track => track.stop()); return }
        streamRef.current = stream
        if (videoRef.current) { videoRef.current.srcObject = stream; await videoRef.current.play() }
        timer = window.setInterval(captureFrame, 1000)
      } catch (cause) { setError(cause instanceof Error ? cause.message : 'Camera permission was denied.') }
    }

    async function captureFrame() {
      if (requestInFlight.current || !videoRef.current || !canvasRef.current || videoRef.current.readyState < 2) return
      const video = videoRef.current
      const canvas = canvasRef.current
      canvas.width = 320; canvas.height = Math.round(320 * video.videoHeight / video.videoWidth)
      canvas.getContext('2d')?.drawImage(video, 0, 0, canvas.width, canvas.height)
      requestInFlight.current = true
      try {
        const frame = await new Promise<Blob | null>(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.7))
        if (!frame) return
        const result = await sendFocusFrame(sessionId, frame)
        if (!cancelled) { setScore(result.focus_score); setFacePresent(result.face_present) }
      } catch (cause) { if (!cancelled) setError(cause instanceof Error ? cause.message : 'Focus tracking is unavailable.') }
      finally { requestInFlight.current = false }
    }

    start()
    return () => { cancelled = true; if (timer) window.clearInterval(timer); streamRef.current?.getTracks().forEach(track => track.stop()); streamRef.current = null }
  }, [active, sessionId])

  return <Card className="focus-panel"><div className="focus-panel__head"><span><CameraIcon size={16} /> Focus tracking</span>{score === null ? <Badge variant="outline"><Spinner /> Starting</Badge> : <Badge><EyeIcon size={14} /> {Math.round(score)}% focused</Badge>}</div><video ref={videoRef} className="focus-panel__video" muted playsInline /><canvas ref={canvasRef} hidden />{score !== null && <Progress value={score} /> }<p className="focus-panel__status">{facePresent ? 'Face detected' : 'Look toward the screen'}</p>{error && <Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert>}</Card>
}