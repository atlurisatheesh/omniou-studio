/**
 * CLONEAI PRO — Global State Store (Zustand) — Phase 12
 */

import { create } from "zustand";

export type WizardStep = "photo" | "voice" | "script" | "settings" | "generating";

interface CloneState {
  // Wizard state
  currentStep: WizardStep;
  setStep: (step: WizardStep) => void;

  // Photo
  photoFile: File | null;
  photoPath: string | null;
  photoPreview: string | null;
  setPhoto: (file: File, path: string, preview: string) => void;

  // Voice
  voiceFile: File | null;
  voicePath: string | null;
  setVoice: (file: File, path: string) => void;

  // Script
  scriptText: string;
  targetLanguage: string;
  setScript: (text: string) => void;
  setLanguage: (lang: string) => void;

  // Settings (ULTRA)
  emotion: string;
  background: string;
  setEmotion: (emotion: string) => void;
  setBackground: (bg: string) => void;

  // Job
  jobId: string | null;
  jobStatus: string;
  jobProgress: number;
  jobStep: string;
  jobError: string | null;
  resultUrl: string | null;
  setJob: (id: string) => void;
  setJobProgress: (progress: number) => void;
  setJobStep: (step: string) => void;
  setJobError: (error: string | null) => void;
  setResultUrl: (url: string | null) => void;
  updateJobProgress: (status: string, progress: number, step: string, error?: string | null, resultUrl?: string | null) => void;

  // Template (Phase 12)
  applyTemplate: (template: {
    script_text: string;
    language: string;
    emotion: string;
    background: string;
  }) => void;

  // Reset
  reset: () => void;
}

export const useCloneStore = create<CloneState>((set) => ({
  // Wizard
  currentStep: "photo",
  setStep: (step) => set({ currentStep: step }),

  // Photo
  photoFile: null,
  photoPath: null,
  photoPreview: null,
  setPhoto: (file, path, preview) => set({ photoFile: file, photoPath: path, photoPreview: preview }),

  // Voice
  voiceFile: null,
  voicePath: null,
  setVoice: (file, path) => set({ voiceFile: file, voicePath: path }),

  // Script
  scriptText: "",
  targetLanguage: "en",
  setScript: (text) => set({ scriptText: text }),
  setLanguage: (lang) => set({ targetLanguage: lang }),

  // Settings (ULTRA)
  emotion: "neutral",
  background: "original",
  setEmotion: (emotion) => set({ emotion }),
  setBackground: (bg) => set({ background: bg }),

  // Job
  jobId: null,
  jobStatus: "idle",
  jobProgress: 0,
  jobStep: "",
  jobError: null,
  resultUrl: null,
  setJob: (id) => set({ jobId: id, jobStatus: "queued", jobProgress: 0, jobStep: "queued" }),
  setJobProgress: (progress) => set({ jobProgress: progress }),
  setJobStep: (step) => set({ jobStep: step }),
  setJobError: (error) => set({ jobError: error }),
  setResultUrl: (url) => set({ resultUrl: url }),
  updateJobProgress: (status, progress, step, error = null, resultUrl = null) =>
    set({ jobStatus: status, jobProgress: progress, jobStep: step, jobError: error, resultUrl }),

  // Template (Phase 12)
  applyTemplate: (template) =>
    set({
      scriptText: template.script_text,
      targetLanguage: template.language,
      emotion: template.emotion,
      background: template.background,
      currentStep: "script",
    }),

  // Reset
  reset: () =>
    set({
      currentStep: "photo",
      photoFile: null,
      photoPath: null,
      photoPreview: null,
      voiceFile: null,
      voicePath: null,
      scriptText: "",
      targetLanguage: "en",
      emotion: "neutral",
      background: "original",
      jobId: null,
      jobStatus: "idle",
      jobProgress: 0,
      jobStep: "",
      jobError: null,
      resultUrl: null,
    }),
}));


// ── Project Store (Long-Form Video) ──

interface SceneConsistency {
  sceneIndex: number;
  identityScore: number | null;
  colorScore: number | null;
  crossSceneScore: number | null;
  status: string;
}

interface ProjectState {
  // Project data
  projectId: string | null;
  projectName: string;
  projectStatus: string;
  scenes: any[];
  activeSceneIndex: number;

  // Identity
  identityAnchorCreated: boolean;
  overallIdentityScore: number | null;
  overallColorScore: number | null;

  // Per-scene consistency
  sceneConsistency: SceneConsistency[];

  // Generation
  isGenerating: boolean;
  generationProgress: number;
  completedScenes: number;
  totalScenes: number;
  currentGeneratingScene: number | null;

  // Output
  finalVideoPath: string | null;
  processingTime: number | null;

  // Actions
  setProject: (id: string, name: string, scenes: any[]) => void;
  setProjectStatus: (status: string) => void;
  setActiveScene: (index: number) => void;
  setSceneConsistency: (consistency: SceneConsistency[]) => void;
  updateSceneStatus: (index: number, status: string, scores?: Partial<SceneConsistency>) => void;
  setGenerationProgress: (progress: number, completed: number, current: number | null) => void;
  setIdentityScores: (identity: number | null, color: number | null) => void;
  setFinalVideo: (path: string | null, time: number | null) => void;
  resetProject: () => void;
}

export const useProjectStore = create<ProjectState>((set) => ({
  projectId: null,
  projectName: "",
  projectStatus: "idle",
  scenes: [],
  activeSceneIndex: 0,
  identityAnchorCreated: false,
  overallIdentityScore: null,
  overallColorScore: null,
  sceneConsistency: [],
  isGenerating: false,
  generationProgress: 0,
  completedScenes: 0,
  totalScenes: 0,
  currentGeneratingScene: null,
  finalVideoPath: null,
  processingTime: null,

  setProject: (id, name, scenes) =>
    set({
      projectId: id,
      projectName: name,
      scenes,
      totalScenes: scenes.length,
      identityAnchorCreated: true,
      projectStatus: "draft",
      sceneConsistency: scenes.map((_: any, i: number) => ({
        sceneIndex: i,
        identityScore: null,
        colorScore: null,
        crossSceneScore: null,
        status: "pending",
      })),
    }),

  setProjectStatus: (status) => set({ projectStatus: status, isGenerating: status === "generating" }),

  setActiveScene: (index) => set({ activeSceneIndex: index }),

  setSceneConsistency: (consistency) => set({ sceneConsistency: consistency }),

  updateSceneStatus: (index, status, scores) =>
    set((state) => ({
      sceneConsistency: state.sceneConsistency.map((sc) =>
        sc.sceneIndex === index
          ? { ...sc, status, ...scores }
          : sc,
      ),
    })),

  setGenerationProgress: (progress, completed, current) =>
    set({
      generationProgress: progress,
      completedScenes: completed,
      currentGeneratingScene: current,
    }),

  setIdentityScores: (identity, color) =>
    set({
      overallIdentityScore: identity,
      overallColorScore: color,
    }),

  setFinalVideo: (path, time) =>
    set({
      finalVideoPath: path,
      processingTime: time,
      isGenerating: false,
    }),

  resetProject: () =>
    set({
      projectId: null,
      projectName: "",
      projectStatus: "idle",
      scenes: [],
      activeSceneIndex: 0,
      identityAnchorCreated: false,
      overallIdentityScore: null,
      overallColorScore: null,
      sceneConsistency: [],
      isGenerating: false,
      generationProgress: 0,
      completedScenes: 0,
      totalScenes: 0,
      currentGeneratingScene: null,
      finalVideoPath: null,
      processingTime: null,
    }),
}));

