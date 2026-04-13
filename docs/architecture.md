# AI Persona Architecture

A FastAPI-powered conversational AI system with RAG-based knowledge retrieval, multi-surface interaction (web chat and voice calls), and integrated scheduling. The backend serves as the unified control plane for consistent behavior across all client interfaces.

## System Overview

```mermaid
flowchart TB
    subgraph "Client Layer"
        WEB[Next.js Web Chat]
        PHONE[Vapi Voice Calls]
    end
    
    subgraph "FastAPI Backend"
        ROUTES[API Routes]
        SERVICES[Core Services]
    end
    
    subgraph "Knowledge Base"
        SOURCES[Resume + GitHub Repos]
        FAISS[Vector Index]
    end
    
    subgraph "External APIs"
        GROQ[Groq LLM]
        GEMINI[Gemini Embeddings]
        CAL[Cal.com Booking]
        GITHUB[GitHub API]
    end
    
    WEB --> ROUTES
    PHONE --> ROUTES
    ROUTES --> SERVICES
    SERVICES --> FAISS
    SERVICES --> GROQ
    SERVICES --> GEMINI
    SERVICES --> CAL
    SERVICES --> GITHUB
    SOURCES --> FAISS
```

## Backend Architecture

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

## Web Chat Request Flow

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

## Voice & Booking Flow

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

## Architecture Strengths

**Unified Backend Logic**: Both web chat and voice calls flow through the same PersonaChatService, ensuring consistent behavior and responses across all interaction surfaces.

**Grounded Knowledge**: RAG pipeline uses only curated sources (resume, selected repos, PR summaries) stored locally, eliminating hallucination and maintaining answer quality through controlled indexing.

**Clean Separation**: Ingestion, retrieval, generation, and external integrations are isolated into dedicated services, allowing independent evolution and easier testing of each component.

**Stateless Design**: Request-response model with conversation context managed at the application layer enables horizontal scaling and simplified deployment.