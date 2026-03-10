"use client";

import { useEffect, useRef, useState } from "react";

interface LivePreviewProps {
  jobId: string;
  className?: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function LivePreview({ jobId, className = "" }: LivePreviewProps) {
  const [frameSrc, setFrameSrc] = useState<string | null>(null);
  const [frameCount, setFrameCount] = useState(0);
  const [status, setStatus] = useState<"connecting" | "streaming" | "complete" | "error">("connecting");
  const evtSourceRef = useRef<EventSource | null>(null);
  const sinceRef = useRef(0);

  useEffect(() => {
    let retries = 0;
    const maxRetries = 5;

    function connect() {
      const url = `${API_BASE}/api/v1/stream/${jobId}/frames?since_frame=${sinceRef.current}`;
      const es = new EventSource(url);
      evtSourceRef.current = es;

      es.addEventListener("frame", (e) => {
        retries = 0;
        setStatus("streaming");
        try {
          const data = JSON.parse(e.data);
          setFrameSrc(`data:image/jpeg;base64,${data.data}`);
          setFrameCount(data.frame);
          sinceRef.current = data.frame;
        } catch {
          // skip malformed
        }
      });

      es.addEventListener("complete", () => {
        setStatus("complete");
        es.close();
      });

      es.addEventListener("heartbeat", () => {
        // keep-alive, no action
      });

      es.onerror = () => {
        es.close();
        if (retries < maxRetries) {
          retries++;
          const delay = Math.min(1000 * 2 ** retries, 16000);
          setTimeout(connect, delay);
        } else {
          setStatus("error");
        }
      };

      es.onopen = () => {
        setStatus("streaming");
      };
    }

    connect();

    return () => {
      evtSourceRef.current?.close();
    };
  }, [jobId]);

  if (status === "error") {
    return (
      <div className={`flex items-center justify-center bg-card border border-border rounded-xl p-8 ${className}`}>
        <p className="text-sm text-muted-foreground">Preview unavailable</p>
      </div>
    );
  }

  return (
    <div className={`relative overflow-hidden bg-black rounded-xl ${className}`}>
      {frameSrc ? (
        <img
          src={frameSrc}
          alt={`Preview frame ${frameCount}`}
          className="w-full h-auto object-contain"
        />
      ) : (
        <div className="flex items-center justify-center h-48 text-muted-foreground text-sm">
          Waiting for preview frames…
        </div>
      )}

      {/* Overlay badge */}
      <div className="absolute top-2 right-2 flex items-center gap-1.5 px-2 py-1 bg-black/60 rounded-full text-xs text-white">
        <span
          className={`w-2 h-2 rounded-full ${
            status === "streaming"
              ? "bg-green-400 animate-pulse"
              : status === "complete"
              ? "bg-blue-400"
              : "bg-yellow-400 animate-pulse"
          }`}
        />
        {status === "streaming"
          ? `Live — Frame ${frameCount}`
          : status === "complete"
          ? "Preview complete"
          : "Connecting…"}
      </div>
    </div>
  );
}
