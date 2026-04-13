"use client";

export function useVapiVoice() {
  return {
    supported: false,
    ready: false,
    connecting: false,
    active: false,
    speaking: false,
    error: null as string | null,
    startCall: async () => undefined,
    stopCall: async () => undefined
  };
}
