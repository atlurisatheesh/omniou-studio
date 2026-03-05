"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { useCloneStore } from "@/lib/store";
import { uploadPhoto } from "@/lib/api";
import { Camera, Upload, X, ArrowRight, Loader2 } from "lucide-react";
import Image from "next/image";

export function StepUploadPhoto() {
  const { photoPreview, setPhoto, setStep } = useCloneStore();
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (!file) return;

      setError(null);
      setUploading(true);

      // Create local preview
      const preview = URL.createObjectURL(file);

      try {
        const result = await uploadPhoto(file);
        setPhoto(file, result.path, preview);
      } catch (err) {
        // If backend is down, still allow local preview for demo
        setPhoto(file, `uploads/photos/${file.name}`, preview);
        console.warn("Upload API unavailable, using local preview:", err);
      } finally {
        setUploading(false);
      }
    },
    [setPhoto]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "image/jpeg": [".jpg", ".jpeg"],
      "image/png": [".png"],
      "image/webp": [".webp"],
    },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024,
  });

  const clearPhoto = () => {
    useCloneStore.setState({ photoFile: null, photoPath: null, photoPreview: null });
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="text-center">
        <h1 className="text-2xl font-bold mb-2">Upload Your Face Photo</h1>
        <p className="text-muted-foreground text-sm">
          Upload a clear, front-facing photo. This will be your AI avatar.
        </p>
      </div>

      {/* Tips */}
      <div className="bg-card border border-border rounded-xl p-4 text-sm text-muted-foreground">
        <p className="font-semibold text-foreground mb-2">Tips for best results:</p>
        <ul className="space-y-1 list-disc list-inside">
          <li>Use a clear, front-facing photo with good lighting</li>
          <li>Your face should take up most of the frame</li>
          <li>Avoid sunglasses, masks, or heavy shadows</li>
          <li>Minimum resolution: 256x256 pixels</li>
        </ul>
      </div>

      {/* Dropzone */}
      {!photoPreview ? (
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
                <Camera className="w-8 h-8 text-primary" />
              </div>
              <div>
                <p className="text-foreground font-medium">
                  {isDragActive ? "Drop your photo here" : "Click to upload or drag & drop"}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  JPG, PNG, or WebP • Max 50MB
                </p>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="relative">
          <div className="relative w-full aspect-square max-w-sm mx-auto rounded-xl overflow-hidden border border-border">
            <img
              src={photoPreview}
              alt="Uploaded face"
              className="w-full h-full object-cover"
            />
          </div>
          <button
            onClick={clearPhoto}
            className="absolute top-2 right-2 w-8 h-8 bg-red-500/80 rounded-full flex items-center justify-center hover:bg-red-500 transition"
          >
            <X className="w-4 h-4 text-white" />
          </button>
        </div>
      )}

      {error && (
        <p className="text-sm text-red-400 text-center">{error}</p>
      )}

      {/* Next button */}
      <button
        onClick={() => setStep("voice")}
        disabled={!photoPreview}
        className="w-full flex items-center justify-center gap-2 py-3 bg-primary text-primary-foreground font-semibold rounded-xl disabled:opacity-30 disabled:cursor-not-allowed hover:bg-primary/90 transition"
      >
        Next: Record Voice
        <ArrowRight className="w-4 h-4" />
      </button>
    </div>
  );
}
