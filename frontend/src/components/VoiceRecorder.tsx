import { useEffect, useRef, useState } from 'react'
import { MicIcon, SquareIcon } from 'lucide-react'
import { transcribeAudio } from '../api'
import { Alert, AlertDescription, Button, Spinner } from './primitives'

interface VoiceRecorderProps {
  disabled?: boolean
  onTranscript: (transcript: string) => void
}

export function VoiceRecorder({ disabled, onTranscript }: VoiceRecorderProps) {
  const recorderRef = useRef<MediaRecorder | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const [recording, setRecording] = useState(false)
  const [transcribing, setTranscribing] = useState(false)
  const [error, setError] = useState('')

  async function startRecording() {
    setError('')
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      setError('Voice recording is not supported by this browser.')
      return
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mimeType = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus'].find(type => MediaRecorder.isTypeSupported(type))
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined)
      streamRef.current = stream
      recorderRef.current = recorder
      chunksRef.current = []
      recorder.ondataavailable = event => { if (event.data.size > 0) chunksRef.current.push(event.data) }
      recorder.onstop = async () => {
        stream.getTracks().forEach(track => track.stop())
        streamRef.current = null
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || 'audio/webm' })
        if (!blob.size) { setError('The recording was empty. Please try again.'); return }
        setTranscribing(true)
        try {
          const result = await transcribeAudio(blob)
          if (result.transcript) onTranscript(result.transcript)
          else setError('No speech was detected in that recording.')
        } catch (cause) {
          setError(cause instanceof Error ? cause.message : 'Transcription failed.')
        } finally { setTranscribing(false) }
      }
      recorder.start()
      setRecording(true)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Microphone permission was denied.')
    }
  }

  function stopRecording() {
    if (recorderRef.current?.state === 'recording') {
      recorderRef.current.stop()
      setRecording(false)
    }
  }

  useEffect(() => () => {
    if (recorderRef.current?.state === 'recording') recorderRef.current.stop()
    streamRef.current?.getTracks().forEach(track => track.stop())
  }, [])

  return <div className="voice-recorder"><Button type="button" variant="outline" disabled={disabled || transcribing} onClick={recording ? stopRecording : startRecording}>{transcribing ? <><Spinner /> Transcribing</> : recording ? <><SquareIcon size={15} /> Stop recording</> : <><MicIcon size={15} /> Record answer</>}</Button>{error && <Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert>}</div>
}