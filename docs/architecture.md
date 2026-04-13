# AI Persona Architecture

A conversational AI that people can chat with on the web or call on the phone, and can also book meetings. Built with FastAPI backend, Next.js frontend, Vapi voice integration, and RAG-based knowledge retrieval.

## System Overview

Two ways to interact: web chat interface built with Next.js, or voice calls through Vapi. Both go into the same FastAPI backend - that's the key. Whether someone types a message or speaks on the phone, it all flows through the same logic for consistent responses.

The backend talks to external services: Groq for generating responses, Gemini for understanding text meaning, Cal.com for booking meetings, and GitHub to pull in work information.

```mermaid
flowchart TB
    subgraph "Client Interfaces"
        WEB[Next.js Web Chat]
        PHONE[Vapi Voice Calls]
    end
    
    subgraph "FastAPI Backend"
        ROUTES[API Routes]
        SERVICES[Core Services]
    end
    
    subgraph "External Services"
        GROQ[Groq - Response Generation]
        GEMINI[Gemini - Text Embeddings]
        CAL[Cal.com - Meeting Booking]
        GITHUB[GitHub - Work Data]
    end
    
    subgraph "Knowledge Base"
        SOURCES[Resume + GitHub Repos + PR Summaries]
        FAISS[FAISS Vector Database]
    end
    
    WEB --> ROUTES
    PHONE --> ROUTES
    ROUTES --> SERVICES
    SERVICES --> GROQ
    SERVICES --> GEMINI
    SERVICES --> CAL
    SERVICES --> GITHUB
    SERVICES --> FAISS
    SOURCES --> FAISS
```

## Backend Architecture

Everything starts with main.py, which sets up API routes for chat, booking, data ingestion, and Vapi integration. The real magic happens in the service container - like a toolbox where each tool has a specific job. 

The persona chat service is the brain that decides how to respond. The retrieval service finds relevant information. The LLM service talks to Groq to generate natural responses. Data services handle embeddings and the vector store (turning text into numbers for fast search). Integration services handle booking meetings through Cal.com.

```mermaid
flowchart TB
    subgraph "FastAPI Application"
        MAIN[main.py]
        
        subgraph "API Routes"
            CHAT["/api/chat"]
            AVAILABILITY["/api/availability"]
            BOOK["/api/book"]
            INGEST_GH["/api/ingest/github"]
            INGEST_RB["/api/ingest/rebuild"]
            VAPI_TOOLS["/api/vapi/tools"]
            VAPI_SYNC["/api/vapi/sync"]
            HEALTH["/api/health"]
        end
        
        subgraph "Service Container"
            CONTAINER[container.py]
            
            subgraph "Core Services"
                PERSONA[persona_chat.py]
                RETRIEVAL[retrieval.py]
                PROMPTING[prompting.py]
                LLM[llm.py]
            end
            
            subgraph "Data Services"
                EMBEDDINGS[embeddings.py]
                VECTOR_STORE[vector_store.py]
                GITHUB_SOURCE[github_source.py]
            end
            
            subgraph "Integration Services"
                BOOKING_FLOW[booking_flow.py]
                CALCOM[calcom.py]
            end
        end
    end
    
    MAIN --> CHAT
    MAIN --> AVAILABILITY
    MAIN --> BOOK
    MAIN --> INGEST_GH
    MAIN --> INGEST_RB
    MAIN --> VAPI_TOOLS
    MAIN --> VAPI_SYNC
    MAIN --> HEALTH
    
    CHAT --> CONTAINER
    AVAILABILITY --> CONTAINER
    BOOK --> CONTAINER
    INGEST_GH --> CONTAINER
    INGEST_RB --> CONTAINER
    VAPI_TOOLS --> CONTAINER
    VAPI_SYNC --> CONTAINER
    
    CONTAINER --> PERSONA
    CONTAINER --> RETRIEVAL
    CONTAINER --> PROMPTING
    CONTAINER --> LLM
    CONTAINER --> EMBEDDINGS
    CONTAINER --> VECTOR_STORE
    CONTAINER --> GITHUB_SOURCE
    CONTAINER --> BOOKING_FLOW
    CONTAINER --> CALCOM
```

## RAG Pipeline

This keeps the AI grounded in real information instead of making things up. It pulls from three sources: resume, selected GitHub repositories, and contribution summaries.

All content gets chunked up, turned into embeddings through Gemini, and stored in a FAISS vector database. When someone asks a question, we embed their question the same way, search for similar content, and use that as context for generating the response.

```mermaid
flowchart LR
    subgraph "Source Ingestion"
        RESUME[Resume]
        REPOS[Selected GitHub Repos]
        PRS[PR Summaries]
        
        GITHUB_API[GitHub API]
        SOURCE_LOADER[github_source.py]
        CHUNKING[Text Chunking]
    end
    
    subgraph "Vector Processing"
        GEMINI_EMB[Gemini Embeddings API]
        EMBEDDINGS_SVC[embeddings.py]
        FAISS_STORE[FAISS Vector Store]
    end
    
    subgraph "Query Processing"
        QUERY[User Query]
        QUERY_EMB[Query Embedding]
        SIMILARITY[Similarity Search]
        RERANK[Reranking & Filtering]
        CONTEXT[Retrieved Context]
    end
    
    REPOS --> GITHUB_API
    GITHUB_API --> SOURCE_LOADER
    SOURCE_LOADER --> CHUNKING
    RESUME --> CHUNKING
    PRS --> CHUNKING
    
    CHUNKING --> EMBEDDINGS_SVC
    EMBEDDINGS_SVC --> GEMINI_EMB
    GEMINI_EMB --> FAISS_STORE
    
    QUERY --> QUERY_EMB
    QUERY_EMB --> EMBEDDINGS_SVC
    EMBEDDINGS_SVC --> SIMILARITY
    SIMILARITY --> FAISS_STORE
    FAISS_STORE --> RERANK
    RERANK --> CONTEXT
```

## Request Flow - Web Chat

When someone uses the web chat, they send a message that goes to the persona service, which decides if they're trying to book a meeting or asking a question.

For regular questions: retrieve relevant context from the vector store, build a prompt with that context, send it to Groq, and return a grounded response.

```mermaid
sequenceDiagram
    participant Client as Next.js Client
    participant API as /api/chat
    participant Persona as PersonaChatService
    participant Retrieval as RetrievalService
    participant VectorStore as FAISS Store
    participant LLM as Groq API
    
    Client->>API: POST chat message
    API->>Persona: process_message()
    
    alt Booking Intent Detected
        Persona->>Persona: handle_booking_flow()
        Persona-->>API: booking response
    else Regular Query
        Persona->>Retrieval: retrieve_context()
        Retrieval->>VectorStore: similarity_search()
        VectorStore-->>Retrieval: relevant chunks
        Retrieval-->>Persona: ranked context
        
        Persona->>LLM: generate_response()
        LLM-->>Persona: completion
        Persona-->>API: formatted response
    end
    
    API-->>Client: JSON response
```

## Request Flow - Voice & Booking

For voice calls, it's similar but goes through Vapi first. The cool thing is that booking works the same way whether you're typing or talking - it all uses the same booking flow service that connects to Cal.com.

```mermaid
sequenceDiagram
    participant Caller
    participant Vapi as Vapi Platform
    participant API as /api/vapi/tools
    participant Persona as PersonaChatService
    participant Booking as BookingFlowService
    participant CalCom as Cal.com API
    
    Caller->>Vapi: Voice interaction
    Vapi->>API: Tool call request
    API->>Persona: process_vapi_message()
    
    alt Scheduling Request
        Persona->>Booking: handle_booking()
        Booking->>CalCom: get_availability()
        CalCom-->>Booking: available slots
        Booking->>CalCom: create_booking()
        CalCom-->>Booking: confirmation
        Booking-->>Persona: booking details
    else Information Query
        Persona->>Persona: standard_rag_flow()
        Note over Persona: Uses same retrieval as web chat
    end
    
    Persona-->>API: response
    API-->>Vapi: tool result
    Vapi-->>Caller: Spoken response
```

## Why This Architecture Works

**Unified**: Web and voice use the same backend logic, so responses stay consistent no matter how people interact with it.

**Grounded**: Answers come from real sources (resume, GitHub repos, PR summaries), not hallucinations.

**Clean**: Each service has one job, so you can update parts without breaking everything else.

The system is straightforward: take input from multiple channels, find relevant information, generate a response, and handle booking if needed. The key is keeping everything flowing through the same backend for consistent experience.