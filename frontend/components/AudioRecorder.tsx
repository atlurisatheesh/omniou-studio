"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Mic, Square, Play, Pause, Trash2, Upload, Timer } from "lucide-react";

interface AudioRecorderProps {
  onRecordingComplete: (blob: Blob, url: string) => void;
  maxDuration?: number; // seconds
  className?: string;
}

export function AudioRecorder({
  onRecordingComplete,
  maxDuration = 120,
  className = "",
}: AudioRecorderProps) {
  const [recording, setRecording] = useState(false);
  const [paused, setPaused] = useState(false);
  const [duration, setDuration] = useState(0);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [playing, setPlaying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [levels, setLevels] = useState<number[]>(new Array(20).fill(0));

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animFrameRef = useRef<number | null>(null);

  const cleanup = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
  }, []);

  useEffect(() => {
    return cleanup;
  }, [cleanup]);

  const startRecording = async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100,
        },
      });

      // Audio visualizer
      const audioCtx = new AudioContext();
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 64;
      source.connect(analyser);
      analyserRef.current = analyser;

      const updateLevels = () => {
        const data = new Uint8Array(analyser.frequencyBinCount);
        analyser.getByteFrequencyData(data);
        const normalized = Array.from(data.slice(0, 20)).map((v) => v / 255);
        setLevels(normalized);
        animFrameRef.current = requestAnimationFrame(updateLevels);
      };
      updateLevels();

      const recorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
          ? "audio/webm;codecs=opus"
          : "audio/webm",
      });

      chunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType });
        const url = URL.createObjectURL(blob);
        setAudioUrl(url);
        setAudioBlob(blob);
        onRecordingComplete(blob, url);
        stream.getTracks().forEach((t) => t.stop());
        cleanup();
      };

      recorder.start(100);
      mediaRecorderRef.current = recorder;
      setRecording(true);
      setDuration(0);

      timerRef.current = setInterval(() => {
        setDuration((d) => {
          if (d + 1 >= maxDuration) {
            stopRecording();
            return d;
          }
          return d + 1;
        });
      }, 1000);
    } catch (err: any) {
      setError(err.message || "Microphone access denied");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
    setRecording(false);
    setPaused(false);
    cleanup();
  };

  const togglePause = () => {
    if (!mediaRecorderRef.current) return;
    if (paused) {
      mediaRecorderRef.current.resume();
      setPaused(false);
    } else {
      mediaRecorderRef.current.pause();
      setPaused(true);
    }
  };

  const deleteRecording = () => {
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    setAudioUrl(null);
    setAudioBlob(null);
    setDuration(0);
    setPlaying(false);
  };

  const togglePlayback = () => {
    if (!audioRef.current || !audioUrl) return;
    if (playing) {
      audioRef.current.pause();
      setPlaying(false);
    } else {
      audioRef.current.play();
      setPlaying(true);
    }
  };

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m}:${sec.toString().padStart(2, "0")}`;
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Visualizer */}
      {recording && (
        <div className="flex items-end justify-center gap-1 h-16 bg-card border border-border rounded-xl p-3">
          {levels.map((level, i) => (
            <div
              key={i}
              className="w-1.5 bg-primary rounded-full transition-all duration-75"
              style={{ height: `${Math.max(4, level * 48)}px` }}
            />
          ))}
        </div>
      )}

      {/* Timer */}
      <div className="text-center">
        <span className="text-3xl font-mono font-bold tabular-nums">
          {formatTime(duration)}
        </span>
        <span className="text-xs text-muted-foreground ml-2">/ {formatTime(maxDuration)}</span>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-center gap-4">
        {!recording && !audioUrl && (
          <button
            onClick={startRecording}
            title="Start recording"
            className="w-16 h-16 rounded-full bg-red-500 hover:bg-red-600 transition flex items-center justify-center shadow-lg shadow-red-500/30"
          >
            <Mic className="w-6 h-6 text-white" />
          </button>
        )}

        {recording && (
          <>
            <button
              onClick={togglePause}
              title={paused ? "Resume" : "Pause"}
              className="w-12 h-12 rounded-full bg-card border border-border flex items-center justify-center hover:bg-accent transition"
            >
              {paused ? <Play className="w-5 h-5" /> : <Pause className="w-5 h-5" />}
            </button>
            <button
              onClick={stopRecording}
              title="Stop recording"
              className="w-16 h-16 rounded-full bg-red-500 hover:bg-red-600 transition flex items-center justify-center shadow-lg shadow-red-500/30"
            >
              <Square className="w-5 h-5 text-white" />
            </button>
          </>
        )}

        {audioUrl && !recording && (
          <>
            <button
              onClick={togglePlayback}
              title={playing ? "Pause playback" : "Play recording"}
              className="w-12 h-12 rounded-full bg-primary/10 border border-primary/30 flex items-center justify-center hover:bg-primary/20 transition"
            >
              {playing ? <Pause className="w-5 h-5 text-primary" /> : <Play className="w-5 h-5 text-primary ml-0.5" />}
            </button>
            <button
              onClick={deleteRecording}
              title="Delete recording"
              className="w-12 h-12 rounded-full bg-red-500/10 border border-red-500/30 flex items-center justify-center hover:bg-red-500/20 transition"
            >
              <Trash2 className="w-5 h-5 text-red-400" />
            </button>
          </>
        )}
      </div>

      {/* Hidden audio element for playback */}
      {audioUrl && (
        <audio
          ref={audioRef}
          src={audioUrl}
          onEnded={() => setPlaying(false)}
          className="hidden"
        />
      )}

      {/* Status text */}
      <p className="text-xs text-center text-muted-foreground">
        {recording
          ? paused
            ? "Recording paused"
            : "Recording... Speak naturally"
          : audioUrl
            ? "Recording saved. You can replay or delete it."
            : "Click the mic button to start recording your voice sample."}
      </p>
    </div>
  );
}
