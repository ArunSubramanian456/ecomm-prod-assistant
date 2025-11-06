# ShopBuddy Architecture Diagram

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              SHOPBUDDY E-COMMERCE ASSISTANT                      │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   USER LAYER    │    │  INTERFACE      │    │  API GATEWAY    │
│                 │    │     LAYER       │    │                 │
│  Web Browser    │◄──►│  FastAPI Web    │◄──►│  REST Endpoints │
│  Mobile App     │    │  Chat Interface │    │  WebSocket      │
│  API Clients    │    │  Static Assets  │    │  CORS Handling  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           INTELLIGENCE LAYER                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    AGENTIC RAG WORKFLOW (LangGraph)                     │   │
│  │                                                                         │   │
│  │  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐ │   │
│  │  │  ASSISTANT  │──►│    TOOLS    │──►│   GRADER    │──►│  GENERATE   │ │   │
│  │  │    NODE     │   │    NODE     │   │    NODE     │   │    NODE     │ │   │
│  │  │             │   │             │   │             │   │             │ │   │
│  │  │ • Route     │   │ • MCP Tools │   │ • Evaluate  │   │ • Final     │ │   │
│  │  │ • Decide    │   │ • Search    │   │ • Relevance │   │ • Response  │ │   │
│  │  │ • Plan      │   │ • Retrieve  │   │ • Quality   │   │ • Format    │ │   │
│  │  └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘ │   │
│  │           │                                   │                         │   │
│  │           └───────────────┐       ┌───────────┘                         │   │
│  │                           ▼       ▼                                     │   │
│  │                    ┌─────────────┐                                      │   │
│  │                    │   REWRITE   │                                      │   │
│  │                    │    NODE     │                                      │   │
│  │                    │             │                                      │   │
│  │                    │ • Improve   │                                      │   │
│  │                    │ • Refine    │                                      │   │
│  │                    │ • Optimize  │                                      │   │
│  │                    └─────────────┘                                      │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            TOOL INTEGRATION LAYER                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                   MODEL CONTEXT PROTOCOL (MCP)                          │   │
│  │                                                                         │   │
│  │  ┌─────────────────┐              ┌─────────────────┐                  │   │
│  │  │ PRODUCT SEARCH  │              │   WEB SEARCH    │                  │   │
│  │  │     SERVER      │              │     TOOL        │                  │   │
│  │  │                 │              │                 │                  │   │
│  │  │ • Local Retriev │              │ • DuckDuckGo    │                  │   │
│  │  │ • Vector Search │              │ • Real-time     │                  │   │
│  │  │ • Metadata      │              │ • Fallback      │                  │   │
│  │  └─────────────────┘              └─────────────────┘                  │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              AI/ML LAYER                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐              │
│  │   EMBEDDING     │   │      LLM        │   │   EVALUATION    │              │
│  │    MODELS       │   │    MODELS       │   │    MODELS       │              │
│  │                 │   │                 │   │                 │              │
│  │ • Google        │   │ • Groq LLaMA    │   │ • RAGAS         │              │
│  │   Embeddings    │   │ • Google Gemini │   │ • Context       │              │
│  │ • text-embed    │   │ • OpenAI GPT-4  │   │ • Relevancy     │              │
│  │   -004          │   │ • Multi-provider│   │ • Precision     │              │
│  └─────────────────┘   └─────────────────┘   └─────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                             DATA LAYER                                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐              │
│  │   VECTOR DB     │   │   RAW DATA      │   │   WEB SCRAPING  │              │
│  │                 │   │                 │   │                 │              │
│  │ • AstraDB       │   │ • CSV Files     │   │ • Flipkart      │              │
│  │ • Similarity    │   │ • Product Info  │   │ • Selenium      │              │
│  │ • Metadata      │   │ • Reviews       │   │ • BeautifulSoup │              │
│  │ • Indexing      │   │ • Ratings       │   │ • Anti-bot      │              │
│  └─────────────────┘   └─────────────────┘   └─────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         INFRASTRUCTURE LAYER                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐              │
│  │   CONTAINER     │   │   ORCHESTRATION │   │   CLOUD         │              │
│  │                 │   │                 │   │                 │              │
│  │ • Docker        │   │ • Kubernetes    │   │ • AWS EKS       │              │
│  │ • Multi-stage   │   │ • Auto-scaling  │   │ • ECR Registry  │              │
│  │ • Health Check  │   │ • Load Balance  │   │ • CI/CD         │              │
│  │ • Optimization  │   │ • Service Mesh  │   │ • Monitoring    │              │
│  └─────────────────┘   └─────────────────┘   └─────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
USER QUERY
    │
    ▼
┌─────────────────┐
│   FastAPI       │
│   Endpoint      │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│   Agentic RAG   │
│   Workflow      │
└─────────────────┘
    │
    ▼
┌─────────────────┐    ┌─────────────────┐
│   Assistant     │───►│   Tool Node     │
│   Node          │    │   (MCP)         │
└─────────────────┘    └─────────────────┘
                           │
                           ▼
                    ┌─────────────────┐
                    │   Product       │
                    │   Search        │
                    └─────────────────┘
                           │
                           ▼
                    ┌─────────────────┐
                    │   Vector        │
                    │   Retrieval     │
                    └─────────────────┘
                           │
                           ▼
                    ┌─────────────────┐
                    │   AstraDB       │
                    │   Query         │
                    └─────────────────┘
                           │
                           ▼
                    ┌─────────────────┐
                    │   Similarity    │
                    │   Search        │
                    └─────────────────┘
                           │
                           ▼
                    ┌─────────────────┐
                    │   Retrieved     │
                    │   Documents     │
                    └─────────────────┘
                           │
                           ▼
┌─────────────────┐    ┌─────────────────┐
│   Grader Node   │◄───│   Context       │
│                 │    │   Evaluation    │
└─────────────────┘    └─────────────────┘
    │
    ▼
┌─────────────────┐    ┌─────────────────┐
│   Generate      │    │   Rewrite       │
│   Response      │◄───│   Query         │
└─────────────────┘    └─────────────────┘
    │
    ▼
┌─────────────────┐
│   Final         │
│   Response      │
└─────────────────┘
    │
    ▼
USER INTERFACE
```

## Component Interaction Matrix

| Component | Interacts With | Purpose |
|-----------|----------------|---------|
| FastAPI Router | Agentic RAG Workflow | HTTP request handling |
| Assistant Node | MCP Tools, LLM Models | Query routing and planning |
| Tool Node | Product Search Server | Tool execution |
| Grader Node | LLM Models | Quality assessment |
| Generate Node | LLM Models, Prompt Library | Response generation |
| Rewrite Node | LLM Models | Query improvement |
| MCP Server | Vector Retriever, Web Search | Tool orchestration |
| Vector Retriever | AstraDB, Embedding Models | Semantic search |
| Data Scraper | Flipkart, CSV Storage | Data collection |
| Model Loader | Multiple LLM Providers | Model management |

## Technology Stack Layers

### Frontend Layer
- **HTML5/CSS3/JavaScript**: Core web technologies
- **Bootstrap 4**: Responsive UI framework
- **jQuery**: DOM manipulation and AJAX
- **Font Awesome**: Icon library

### Backend Layer
- **FastAPI**: Async web framework
- **Uvicorn**: ASGI server
- **Jinja2**: Template engine
- **Python-multipart**: Form handling

### AI/ML Layer
- **LangChain**: LLM framework
- **LangGraph**: Workflow orchestration
- **LangChain-MCP**: Tool integration
- **RAGAS**: Evaluation framework

### Data Layer
- **AstraDB**: Vector database
- **Selenium**: Web automation
- **BeautifulSoup**: HTML parsing
- **Pandas**: Data manipulation

### Infrastructure Layer
- **Docker**: Containerization
- **Kubernetes**: Orchestration
- **AWS EKS**: Managed Kubernetes
- **GitHub Actions**: CI/CD

## Security & Monitoring

```
┌─────────────────────────────────────────────────────────────────┐
│                    SECURITY & MONITORING                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   LOGGING   │  │ MONITORING  │  │  SECURITY   │            │
│  │             │  │             │  │             │            │
│  │ • Structured│  │ • Health    │  │ • API Keys  │            │
│  │ • Rotation  │  │ • Metrics   │  │ • CORS      │            │
│  │ • Levels    │  │ • Alerts    │  │ • Rate Limit│            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

This architecture provides:
- **Scalability**: Horizontal scaling with Kubernetes
- **Reliability**: Multi-model LLM support and fallbacks
- **Performance**: Async processing and caching
- **Maintainability**: Modular design and clear separation
- **Extensibility**: Plugin-based tool system via MCP