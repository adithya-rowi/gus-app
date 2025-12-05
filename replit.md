# Overview

Gus App is an AI-powered Islamic Q&A chatbot that mimics the warm, storytelling teaching style of Gus Baha, a beloved Javanese Islamic scholar. The application provides conversational responses to questions about Islam, life, and spirituality in both Indonesian and English. It uses RAG (Retrieval-Augmented Generation) to ground answers in actual teachings from YouTube videos and books, ensuring authenticity while maintaining Gus Baha's signature humble, non-judgmental tone.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture

**Technology**: Vanilla JavaScript + TailwindCSS + HTML
- **Design Pattern**: Mobile-first, single-page application
- **Rationale**: Chose vanilla JS over frameworks for simplicity and fast load times on mobile devices. TailwindCSS provides utility-first styling optimized for responsive design.
- **Key Features**: Real-time chat interface with source citations, YouTube and book reference rendering
- **State Management**: Simple client-side state tracking (loading states, message history)

## Backend Architecture

**Technology**: Python Flask (lightweight REST API)
- **Design Pattern**: Modular microservice-style components
- **Rationale**: Flask chosen for its simplicity and Python's strong AI/ML ecosystem integration
- **Key Modules**:
  - `generator.py`: Response generation orchestrator
  - `critic.py`: Quality control layer that validates tone and structure
  - `persona.py`: System prompt and few-shot examples (guardrails embedded)
  - `ragie_client.py`: RAG retrieval interface
  - `main.py`: HTTP endpoints and request handling

**Two-Stage Generation Pipeline**:
1. **Generator**: Creates initial response using DeepSeek API + RAG context
2. **Critic**: Validates tone, structure, and adherence to Gus Baha's style; rewrites if needed
- **Rationale**: Ensures consistent character voice and prevents judgmental or harsh responses

## RAG (Retrieval-Augmented Generation)

**Technology**: Ragie.ai for vector search and retrieval
- **Knowledge Sources**: 
  - YouTube video transcripts (Gus Baha lectures)
  - Book excerpts ("Islam Santuy Ala Gus Baha")
  - Curated summaries and distillations
- **Rationale**: RAG grounds AI responses in authentic source material, reducing hallucinations and providing citation trails
- **Citation System**: Returns source metadata (title, URL, page numbers) for transparency

## Language Detection

**Implementation**: Keyword-based heuristic
- **Supported Languages**: Indonesian (primary), English (secondary)
- **Rationale**: Simple marker-based detection avoids external API calls; sufficient for bilingual use case

## Persona Engineering

**Approach**: Embedded guardrails in system prompt
- **Character Traits**: Humble, storytelling, warm, non-judgmental
- **Structural Constraints**: 5-8 sentence responses, specific format (validation → story → insight → closure)
- **Special Rules**: Distinguishes between Haqqullah (sins against God) and Haqqul Adami (rights of humans) - maintains mercy for former, firmness for latter (e.g., debt repayment)
- **Out-of-Scope Handling**: Redirects non-religious questions (cooking, tech, sports) gracefully

## Response Validation

**Critic Module Checks**:
1. Tone: Warm, hopeful, not harsh or judgmental
2. Structure: Proper length (5-8 sentences), includes story/analogy
3. Cultural Language: Uses informal Indonesian markers ("wong", "gak", "kok")
- **Rationale**: Automated quality control prevents brand inconsistency without manual review

# External Dependencies

## AI/LLM Services

**DeepSeek API** (via OpenAI-compatible client)
- **Purpose**: Core language model for response generation
- **Usage**: Both generator and critic stages
- **Authentication**: API key via environment variable `DEEPSEEK_API_KEY`

**Ragie.ai**
- **Purpose**: Vector database and semantic search for RAG
- **Usage**: Retrieves relevant context from knowledge base (transcripts, books)
- **Authentication**: API key via environment variable `RAGIE_API_KEY`
- **Endpoint**: `https://api.ragie.ai`

## Frontend Libraries

**TailwindCSS** (via CDN)
- **Purpose**: Utility-first CSS framework
- **Delivery**: CDN (`cdn.tailwindcss.com`)

**Google Fonts**
- **Fonts**: Inter (UI), Plus Jakarta Sans (display)
- **Purpose**: Typography matching modern, accessible design

## Python Dependencies

**Flask**
- **Purpose**: Web framework for HTTP server
- **Usage**: Serves HTML template, handles `/chat` POST endpoint

**OpenAI Python Client**
- **Purpose**: Interface to DeepSeek API (OpenAI-compatible)
- **Usage**: LLM communication

**Requests**
- **Purpose**: HTTP client for Ragie API calls
- **Usage**: RAG context retrieval

## Environment Configuration

**Required Environment Variables**:
- `DEEPSEEK_API_KEY`: Authentication for LLM service
- `RAGIE_API_KEY`: Authentication for RAG service

## Content Sources

**Knowledge Base** (ingested into Ragie):
- YouTube transcript: "Ngaji Penuh Humor Ilmiah Gus Baha' bersama Prof Quraish Shihab"
- Book excerpts: "Islam Santuy Ala Gus Baha" by Muhammad Khoirul Huda and Habib Maulana Maslahul Adi
- Custom summaries and distillations

**Source Metadata**: Hardcoded in `ragie_client.py` for citation rendering (titles, URLs, page numbers, authors)