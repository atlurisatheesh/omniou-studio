"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { useCloneStore } from "@/lib/store";
import { uploadVoice } from "@/lib/api";
import { Mic, Upload, X, ArrowRight, ArrowLeft, Loader2, CheckCircle } from "lucide-react";

export function StepUploadVoice() {
  const { voiceFile, voicePath, setVoice, setStep } = useCloneStore();
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (!file) return;

      setError(null);
      setUploading(true);

      try {
        const result = await uploadVoice(file);
        setVoice(file, result.path);
      } catch (err) {
        // Allow local file for demo
        setVoice(file, `uploads/voices/${file.name}`);
        console.warn("Upload API unavailable, using local reference:", err);
      } finally {
        setUploading(false);
      }
    },
    [setVoice]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "audio/wav": [".wav"],
      "audio/mpeg": [".mp3"],
      "audio/mp4": [".m4a"],
      "audio/flac": [".flac"],
      "audio/ogg": [".ogg"],
    },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024,
  });

  const clearVoice = () => {
    useCloneStore.setState({ voiceFile: null, voicePath: null });
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="text-center">
        <h1 className="text-2xl font-bold mb-2">Upload Your Voice Sample</h1>
        <p className="text-muted-foreground text-sm">
          Record or upload at least 30 seconds of your voice. Our AI will learn your unique vocal signature.
        </p>
      </div>

      {/* Tips */}
      <div className="bg-card border border-border rounded-xl p-4 text-sm text-muted-foreground">
        <p className="font-semibold text-foreground mb-2">Tips for best voice clone:</p>
        <ul className="space-y-1 list-disc list-inside">
          <li>Record in a quiet room with minimal background noise</li>
          <li>Speak naturally — don&apos;t whisper or shout</li>
          <li>Minimum 30 seconds of clear speech</li>
          <li>Longer samples (1-2 min) produce better results</li>
          <li>Read anything — a paragraph from a book works great</li>
        </ul>
      </div>

      {/* Sample text to read */}
      <div className="bg-primary/5 border border-primary/20 rounded-xl p-4 text-sm">
        <p className="font-semibold text-primary mb-2">Suggested script to read aloud (30s):</p>
        <p className="text-muted-foreground italic leading-relaxed">
          &quot;The quick brown fox jumps over the lazy dog. I love creating content that
          inspires and educates people around the world. Technology is advancing at an incredible
          pace, and I believe that AI tools should be accessible to everyone, not just
          large corporations. Today I&apos;m recording this sample so that my AI voice clone
          can sound just like me in any language.&quot;
        </p>
      </div>

      {/* Dropzone */}
      {!voiceFile ? (
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all ${
            isDragActive
              ? "border-primary bg-primary/5"
              : "border-border hover:border-primary/50 hover:bg-primary/[0.02]"
          }`}
        >
          <input {...getInputProps()} />
          {uploading ? (
            <div className="flex flex-col items-center gap-3">
              <Loader2 className="w-10 h-10 text-primary animate-spin" />
              <p className="text-sm text-muted-foreground">Uploading...</p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-3">
              <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center">
                <Mic className="w-8 h-8 text-primary" />
              </div>
              <div>
                <p className="text-foreground font-medium">
                  {isDragActive ? "Drop your audio here" : "Click to upload or drag & drop"}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  WAV, MP3, M4A, FLAC • Min 30 seconds • Max 50MB
                </p>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="bg-card border border-green-500/30 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <CheckCircle className="w-5 h-5 text-green-500" />
              <div>
                <p className="text-sm font-medium">{voiceFile.name}</p>
                <p className="text-xs text-muted-foreground">
                  {(voiceFile.size / (1024 * 1024)).toFixed(1)} MB
                </p>
              </div>
            </div>
            <button
              onClick={clearVoice}
              title="Remove voice"
              className="w-8 h-8 rounded-full bg-red-500/10 flex items-center justify-center hover:bg-red-500/20 transition"
            >
              <X className="w-4 h-4 text-red-400" />
            </button>
          </div>

          {/* Audio preview */}
          <audio controls className="w-full mt-4" src={URL.createObjectURL(voiceFile)}>
            Your browser does not support audio.
          </audio>
        </div>
      )}

      {error && <p className="text-sm text-red-400 text-center">{error}</p>}

      {/* Navigation */}
      <div className="flex gap-3">
        <button
          onClick={() => setStep("photo")}
          className="flex items-center gap-2 px-6 py-3 border border-border rounded-xl text-sm text-muted-foreground hover:text-foreground hover:bg-secondary transition"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>
        <button
          onClick={() => setStep("script")}
          disabled={!voiceFile}
          className="flex-1 flex items-center justify-center gap-2 py-3 bg-primary text-primary-foreground font-semibold rounded-xl disabled:opacity-30 disabled:cursor-not-allowed hover:bg-primary/90 transition"
        >
          Next: Write Script
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
