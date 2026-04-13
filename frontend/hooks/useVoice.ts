"use client";

export function useVoice() {
  return {
    supported: false,
    listening: false,
    speaking: false,
    startListening: () => undefined,
    stopListening: () => undefined,
    speak: (_text: string) => undefined,
    stopSpeaking: () => undefined
  };
}
