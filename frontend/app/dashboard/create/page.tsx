"use client";

import { useCloneStore } from "@/lib/store";
import { StepUploadPhoto } from "@/components/clone-wizard/step-upload-photo";
import { StepUploadVoice } from "@/components/clone-wizard/step-upload-voice";
import { StepWriteScript } from "@/components/clone-wizard/step-write-script";
import { StepSettingsExtra } from "@/components/clone-wizard/step-settings-extra";
import { StepGenerating } from "@/components/clone-wizard/step-generating";
import { WizardProgress } from "@/components/clone-wizard/wizard-progress";
import Link from "next/link";
import { ArrowLeft, Sparkles } from "lucide-react";

export default function CreatePage() {
  const currentStep = useCloneStore((s) => s.currentStep);

  return (
    <div className="min-h-screen bg-background grid-bg">
      {/* Header */}
      <header className="border-b border-border bg-background/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition">
            <ArrowLeft className="w-4 h-4" />
            Back
          </Link>
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-primary" />
            <span className="text-sm font-semibold">
              Clone<span className="text-primary">AI</span> Pro
            </span>
          </div>
          <div className="w-16" /> {/* Spacer for centering */}
        </div>
      </header>

      {/* Progress */}
      <WizardProgress currentStep={currentStep} />

      {/* Content */}
      <main className="max-w-2xl mx-auto px-4 py-8">
        {currentStep === "photo" && <StepUploadPhoto />}
        {currentStep === "voice" && <StepUploadVoice />}
        {currentStep === "script" && <StepWriteScript />}
        {currentStep === "settings" && <StepSettingsExtra />}
        {currentStep === "generating" && <StepGenerating />}
      </main>
    </div>
  );
}
