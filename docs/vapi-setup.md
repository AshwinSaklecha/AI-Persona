# Vapi Setup

This project now treats Vapi as the voice transport layer and keeps `FastAPI + Gemini + FAISS + Cal.com` as the grounded backend.

## What Is Already Wired In Code

- Web chat continues to use `POST /api/chat`
- Vapi custom tools should call `POST /api/vapi/tools`
- The Vapi tool endpoint reuses the same RAG + booking flow as chat
- `POST /api/vapi/sync` can create/update the Vapi tool and patch the assistant/phone number once you have a public backend URL
- Browser voice now uses `@vapi-ai/web` with:
  - `NEXT_PUBLIC_VAPI_PUBLIC_KEY`
  - `NEXT_PUBLIC_VAPI_ASSISTANT_ID`

## Required Environment Variables

Backend:

```env
PUBLIC_BACKEND_URL=https://your-render-service.onrender.com
VAPI_PRIVATE_API_KEY=
VAPI_ASSISTANT_ID=
VAPI_PHONE_NUMBER_ID=
VAPI_SHARED_SECRET=
```

Frontend:

```env
NEXT_PUBLIC_VAPI_PUBLIC_KEY=
NEXT_PUBLIC_VAPI_ASSISTANT_ID=
NEXT_PUBLIC_API_BASE_URL=https://your-render-service.onrender.com
```

## Custom Tool To Create In Vapi

Create a `Function` tool in the Vapi dashboard with:

- Function name: `ask_persona`
- Description:
  `Call this on every user turn to get Ashwin's grounded response from the external RAG backend. Use it for resume questions, project questions, scheduling, booking follow-ups, and general conversation.`
- Server URL:
  `https://your-render-service.onrender.com/api/vapi/tools`

Parameters schema:

```json
{
  "type": "object",
  "properties": {
    "message": {
      "type": "string",
      "description": "The user's latest message, verbatim."
    }
  },
  "required": ["message"]
}
```

Add a header in the tool configuration:

- `X-Vapi-Secret: <VAPI_SHARED_SECRET>`

Recommended tool messages:

- Request Start: `Let me think through that.`
- Request Complete: `Got it.`
- Request Failed: `I'm having trouble reaching my backend right now.`

## Assistant Prompt

Update the Vapi assistant so it behaves like a thin voice shell over the backend.

Suggested system prompt:

```text
You are Ashwin Saklecha's AI representative.

Speak in first person as Ashwin.
Tone: honest, slightly informal, clear reasoning, no exaggeration.

Important rules:
- For every user turn, call the ask_persona tool with the user's latest message.
- Do not answer from memory when the tool can answer.
- If the tool says it does not know, stay honest and say that clearly.
- Use the tool for scheduling and booking too.
- Keep spoken responses concise and natural.
```

Suggested first message:

```text
Hi, this is Ashwin's AI representative. I can talk about Ashwin's background, projects, and help book a time to chat. What would you like to know?
```

## Voice Provider

Right now your verified assistant is using:

- Assistant: `Riley`
- Voice provider: `vapi`
- Voice ID: `Elliot`

If you want ElevenLabs instead:

1. Add the ElevenLabs provider key in the Vapi dashboard integrations.
2. Change the assistant voice provider to `11labs`.
3. Set the voice ID to:
   `a1TnjruAs5jTzdrjL8Vd`

## Phone Number

Your current Vapi phone number ID is:

`a851389e-f728-42a7-a625-cc5f95bf4e78`

In Vapi, assign that number to the assistant:

- Assistant ID: `024b43ad-979d-433d-8391-5d99c42be2e1`

## Local Testing

For local testing, the web voice UI can start Vapi calls immediately because it only needs the public key and assistant ID.

For phone calls or custom tool execution, Vapi must reach your backend over a public URL, so use one of:

- Render deployment
- `ngrok`
- `cloudflared`

## Smoke Test

After deployment and Vapi setup:

1. Start a web voice call from the Next.js UI.
2. Ask: `Tell me about your DeepChem contributions.`
3. Ask: `Book a meeting with me next week.`
4. Provide an exact window.
5. Choose a slot and give contact details.
6. Call the Vapi phone number and repeat the same flow.

## Optional One-Shot Sync

After your backend is deployed and `PUBLIC_BACKEND_URL` is set, you can let this app patch Vapi for you:

```bash
curl -X POST https://your-render-service.onrender.com/api/vapi/sync \
  -H "Content-Type: application/json" \
  -d "{}"
```

This will:

- create or update the `ask_persona` tool
- patch the assistant prompt and first message to the Ashwin persona
- ensure the phone number stays attached to the configured assistant
