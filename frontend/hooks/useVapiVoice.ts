"use client";

import { useEffect, useRef, useState } from "react";

import { VAPI_ASSISTANT_ID, VAPI_PUBLIC_KEY, logClientEvent } from "@/lib/api";

type VapiLike = {
  start: (assistantId: string) => Promise<void> | void;
  stop: () => Promise<void> | void;
  on: (event: string, handler: (...args: unknown[]) => void) => void;
  off?: (event: string, handler: (...args: unknown[]) => void) => void;
};

type RegisteredHandler = {
  event: string;
  handler: (...args: unknown[]) => void;
};

function extractErrorMessage(error: unknown) {
  if (error instanceof Error) {
    return error.message;
  }
  if (typeof error === "string") {
    return error;
  }
  return "Unknown Vapi error";
}

export function useVapiVoice() {
  const [supported, setSupported] = useState(Boolean(VAPI_PUBLIC_KEY && VAPI_ASSISTANT_ID));
  const [ready, setReady] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [active, setActive] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const vapiRef = useRef<VapiLike | null>(null);
  const handlersRef = useRef<RegisteredHandler[]>([]);

  useEffect(() => {
    let cancelled = false;

    if (!VAPI_PUBLIC_KEY || !VAPI_ASSISTANT_ID) {
      setSupported(false);
      setReady(false);
      return;
    }

    setSupported(true);

    void import("@vapi-ai/web")
      .then(({ default: Vapi }) => {
        if (cancelled) {
          return;
        }

        const instance = new Vapi(VAPI_PUBLIC_KEY) as unknown as VapiLike;
        const register = (event: string, handler: (...args: unknown[]) => void) => {
          instance.on(event, handler);
          handlersRef.current.push({ event, handler });
        };

        register("call-start", () => {
          setConnecting(false);
          setActive(true);
          setError(null);
          void logClientEvent("voice_call_started");
        });

        register("call-end", (...args) => {
          setConnecting(false);
          setActive(false);
          setSpeaking(false);
          void logClientEvent("voice_call_ended", { payload: args[0] ?? null });
        });

        register("speech-start", () => setSpeaking(true));
        register("speech-end", () => setSpeaking(false));

        register("error", (...args) => {
          const message = extractErrorMessage(args[0]);
          setConnecting(false);
          setActive(false);
          setSpeaking(false);
          setError(message);
          void logClientEvent("voice_call_error", { error: message });
        });

        vapiRef.current = instance;
        setReady(true);
      })
      .catch((loadError) => {
        const message = extractErrorMessage(loadError);
        setSupported(false);
        setReady(false);
        setError(message);
        void logClientEvent("voice_unsupported", { reason: "vapi_sdk_load_failed", error: message });
      });

    return () => {
      cancelled = true;
      const instance = vapiRef.current;
      const off = instance?.off;
      if (instance && off) {
        for (const { event, handler } of handlersRef.current) {
          off.call(instance, event, handler);
        }
      }
      handlersRef.current = [];
      void instance?.stop?.();
      vapiRef.current = null;
    };
  }, []);

  async function startCall() {
    if (!vapiRef.current || !VAPI_ASSISTANT_ID || active || connecting) {
      return;
    }
    setConnecting(true);
    setError(null);
    try {
      await vapiRef.current.start(VAPI_ASSISTANT_ID);
    } catch (startError) {
      const message = extractErrorMessage(startError);
      setConnecting(false);
      setActive(false);
      setError(message);
      void logClientEvent("voice_call_error", { error: message, stage: "start" });
    }
  }

  async function stopCall() {
    if (!vapiRef.current) {
      return;
    }
    try {
      await vapiRef.current.stop();
    } finally {
      setConnecting(false);
      setActive(false);
      setSpeaking(false);
    }
  }

  return {
    supported,
    ready,
    connecting,
    active,
    speaking,
    error,
    startCall,
    stopCall,
  };
}
