# Gus App - AI Content Generation Platform

## Overview
Gus App is an AI-powered content generation platform built with Flask. It integrates with DeepSeek for AI content generation and Ragie for knowledge base retrieval (RAG). The app features a persona system, content critique, and refinement capabilities.

## Project Structure
```
gus-app/
├── main.py              # Flask application with routes
├── ragie_client.py      # Ragie API client for document retrieval
├── generator.py         # DeepSeek content generator
├── critic.py            # Content critique and refinement
├── persona.py           # Persona management system
├── templates/
│   └── index.html       # Main application template
└── static/
    ├── style.css        # Application styles
    └── app.js           # Frontend JavaScript
```

## Key Features
- **Content Generation**: AI-powered content generation using DeepSeek API
- **Knowledge Base Integration**: Ragie API for RAG (Retrieval-Augmented Generation)
- **Persona System**: 6 predefined personas + custom persona support
- **Content Critique**: AI-powered feedback on generated content
- **Content Refinement**: Automatic improvement based on critique

## API Endpoints
- `GET /` - Main application interface
- `POST /api/generate` - Generate content with AI
- `POST /api/critique` - Get critique of content
- `POST /api/refine` - Refine content based on critique
- `POST /api/retrieve` - Retrieve context from Ragie knowledge base
- `GET /api/personas` - Get list of available personas
- `GET /api/status` - Check API connection status

## Environment Variables (Secrets)
- `DEEPSEEK_API_KEY` - API key for DeepSeek AI
- `RAGIE_API_KEY` - API key for Ragie knowledge base
- `SESSION_SECRET` - Flask session secret

## Available Personas
1. Professional Writer - Clear, engaging content
2. Technical Expert - Documentation and explanations
3. Creative Storyteller - Narrative and storytelling
4. Business Consultant - Professional communication
5. Educator - Teaching and explanations
6. Marketing Specialist - Persuasive content
7. Custom - User-defined instructions

## Tech Stack
- **Backend**: Python, Flask
- **Frontend**: Vanilla JavaScript, CSS
- **AI**: DeepSeek API (OpenAI-compatible)
- **RAG**: Ragie API
- **Icons**: Feather Icons

## Recent Changes
- 2025-11-28: Initial implementation with all core features
  - Implemented Ragie client for knowledge base retrieval
  - Built DeepSeek content generator
  - Created critic module for evaluation and refinement
  - Added persona management system
  - Built interactive frontend interface
