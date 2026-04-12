"use client";

import { useEffect, useRef, useState } from "react";

import { logClientEvent } from "@/lib/api";

type VoiceHookOptions = {
  onTranscript: (transcript: string) => void;
};

type VoiceRecognitionResultEvent = {
  results: ArrayLike<ArrayLike<{ transcript?: string }>>;
};

type RecognitionInstance = {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  start: () => void;
  stop: () => void;
  abort?: () => void;
  onstart: null | (() => void);
  onend: null | (() => void);
  onerror: null | ((event: { error?: string }) => void);
  onresult: null | ((event: VoiceRecognitionResultEvent) => void);
};

type SpeechWindow = Window & {
  SpeechRecognition?: new () => RecognitionInstance;
  webkitSpeechRecognition?: new () => RecognitionInstance;
};

export function useVoice({ onTranscript }: VoiceHookOptions) {
  const [supported, setSupported] = useState(false);
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const recognitionRef = useRef<RecognitionInstance | null>(null);
  const transcriptHandlerRef = useRef(onTranscript);

  useEffect(() => {
    transcriptHandlerRef.current = onTranscript;
  }, [onTranscript]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const speechWindow = window as SpeechWindow;
    const SpeechRecognitionCtor =
      speechWindow.SpeechRecognition ?? speechWindow.webkitSpeechRecognition;

    if (!SpeechRecognitionCtor) {
      setSupported(false);
      void logClientEvent("voice_unsupported", {
        userAgent: window.navigator.userAgent
      });
      return;
    }

    setSupported(true);
    const recognition = new SpeechRecognitionCtor();
    recognition.lang = "en-IN";
    recognition.interimResults = false;
    recognition.continuous = false;
    recognition.onstart = () => setListening(true);
    recognition.onend = () => setListening(false);
    recognition.onerror = (event) => {
      setListening(false);
      void logClientEvent("voice_error", {
        error: event.error ?? "unknown"
      });
    };
    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map((result) => result[0]?.transcript ?? "")
        .join(" ")
        .trim();

      if (transcript) {
        transcriptHandlerRef.current(transcript);
      }
    };

    recognitionRef.current = recognition;

    return () => {
      recognition.onstart = null;
      recognition.onend = null;
      recognition.onerror = null;
      recognition.onresult = null;
      recognition.abort?.();
      recognitionRef.current = null;
      window.speechSynthesis.cancel();
    };
  }, []);

  function startListening() {
    if (!supported) {
      return;
    }
    stopSpeaking("new_recording");
    recognitionRef.current?.start();
  }

  function stopListening() {
    recognitionRef.current?.stop();
    setListening(false);
  }

  function speak(text: string) {
    if (typeof window === "undefined" || !text.trim()) {
      return;
    }

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-IN";
    utterance.rate = 1;
    utterance.pitch = 1;
    utterance.onstart = () => setSpeaking(true);
    utterance.onend = () => setSpeaking(false);
    utterance.onerror = () => setSpeaking(false);

    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  }

  function stopSpeaking(reason: string = "manual_stop") {
    if (typeof window === "undefined") {
      return;
    }
    if (window.speechSynthesis.speaking) {
      window.speechSynthesis.cancel();
      setSpeaking(false);
      void logClientEvent("voice_interrupted", { reason });
    }
  }

  return {
    supported,
    listening,
    speaking,
    startListening,
    stopListening,
    speak,
    stopSpeaking
  };
}
