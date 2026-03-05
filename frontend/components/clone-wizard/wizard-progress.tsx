"use client";

import type { WizardStep } from "@/lib/store";
import { Camera, Mic, FileText, Settings, Play } from "lucide-react";

const steps: { key: WizardStep; label: string; icon: typeof Camera }[] = [
  { key: "photo", label: "Photo", icon: Camera },
  { key: "voice", label: "Voice", icon: Mic },
  { key: "script", label: "Script", icon: FileText },
  { key: "settings", label: "Settings", icon: Settings },
  { key: "generating", label: "Generate", icon: Play },
];

const stepOrder: WizardStep[] = ["photo", "voice", "script", "settings", "generating"];

export function WizardProgress({ currentStep }: { currentStep: WizardStep }) {
  const currentIdx = stepOrder.indexOf(currentStep);

  return (
    <div className="max-w-2xl mx-auto px-4 pt-8">
      <div className="flex items-center justify-between">
        {steps.map((step, i) => {
          const isActive = i === currentIdx;
          const isCompleted = i < currentIdx;

          return (
            <div key={step.key} className="flex items-center flex-1">
              <div className="flex flex-col items-center gap-2">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all ${
                    isActive
                      ? "border-primary bg-primary/10 text-primary"
                      : isCompleted
                      ? "border-green-500 bg-green-500/10 text-green-500"
                      : "border-border bg-card text-muted-foreground"
                  }`}
                >
                  <step.icon className="w-4 h-4" />
                </div>
                <span
                  className={`text-xs font-medium ${
                    isActive ? "text-primary" : isCompleted ? "text-green-500" : "text-muted-foreground"
                  }`}
                >
                  {step.label}
                </span>
              </div>

              {/* Connector */}
              {i < steps.length - 1 && (
                <div
                  className={`flex-1 h-px mx-4 ${
                    isCompleted ? "bg-green-500" : "bg-border"
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
