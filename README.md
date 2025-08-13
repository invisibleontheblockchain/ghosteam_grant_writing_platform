# GhostTeam Grant Writing Platform

A comprehensive AI-powered grant writing platform based on real-world research and the successful SAFE grant writing system.

## Project Overview

This platform implements the vision from the comprehensive research plan, creating a unified system that seamlessly integrates AI-powered content generation with robust grant management workflow.

### Key Features
- **RAG-Powered AI Engine**: Uses organizational knowledge base for contextual content generation
- **Complete Grant Lifecycle Management**: From prospecting to post-award reporting
- **SAFE Knowledge Base Integration**: Pre-loaded with proven organizational models
- **Intelligent Content Reuse**: Adapts successful past content for new applications
- **Compliance Checking**: Automated verification of grant requirements
- **Modular Architecture**: Clean separation of concerns for maintainability

### Market Opportunity
- **$3-5B Market**: Grant management software market with 10%+ CAGR
- **User Archetypes**: Non-profits, Academic/Research Institutions, Small Businesses
- **Competitive Gap**: First platform combining AI content generation with full workflow management

## Architecture

```
ghosteam_grant_writing_platform/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── config/                           # Configuration files
│   ├── __init__.py
│   ├── settings.py                   # Application settings
│   └── database.py                   # Database configuration
├── core/                             # Core business logic
│   ├── __init__.py
│   ├── models.py                     # Data models
│   ├── rag_engine.py                 # RAG AI engine
│   ├── grant_manager.py              # Grant lifecycle management
│   └── document_processor.py         # Document parsing and processing
├── api/                              # REST API endpoints
│   ├── __init__.py
│   ├── app.py                        # Flask application
│   ├── auth.py                       # Authentication routes
│   ├── grants.py                     # Grant management routes
│   ├── content.py                    # Content library routes
│   └── ai.py                         # AI generation routes
├── frontend/                         # Web interface
│   ├── static/                       # CSS, JS, images
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── templates/                    # HTML templates
│       ├── base.html
│       ├── dashboard.html
│       ├── login.html
│       ├── grant_form.html
│       ├── content_library.html
│       └── ai_assistant.html
├── data/                             # Data and knowledge base
│   ├── safe_knowledge_base/          # SAFE organizational content
│   ├── templates/                    # Grant templates
│   └── research/                     # Supporting research
├── utils/                            # Utility functions
│   ├── __init__.py
│   ├── file_utils.py                 # File operations
│   ├── text_processing.py           # Text processing utilities
│   └── validation.py                # Input validation
├── tests/                            # Test suite
│   ├── __init__.py
│   ├── test_core/
│   ├── test_api/
│   └── test_integration/
├── scripts/                          # Deployment and utility scripts
│   ├── setup_database.py            # Database initialization
│   ├── load_safe_data.py             # Load SAFE knowledge base
│   └── run_dev_server.py             # Development server
└── docker/                          # Containerization
    ├── Dockerfile
    ├── docker-compose.yml
    └── docker-compose.dev.yml
```

## Quick Start

1. **Setup Environment**
   ```bash
   cd ghosteam_grant_writing_platform
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   export SECRET_KEY="your-secret-key"
   export DATABASE_URL="sqlite:///ghosteam_grants.db"
   ```

3. **Initialize Database**
   ```bash
   python scripts/setup_database.py
   python scripts/load_safe_data.py
   ```

4. **Run Development Server**
   ```bash
   python scripts/run_dev_server.py
   ```

5. **Access Platform**
   - Open http://localhost:5000
   - Create account or use demo credentials
   - Start creating grant applications!

## Module Descriptions

### Core Modules

- **RAG Engine** (`core/rag_engine.py`): Retrieval-Augmented Generation for AI content creation
- **Grant Manager** (`core/grant_manager.py`): Complete grant lifecycle management
- **Document Processor** (`core/document_processor.py`): PDF, DOCX, and text extraction

### API Modules

- **Authentication** (`api/auth.py`): User registration, login, session management
- **Grant Management** (`api/grants.py`): CRUD operations for grant applications
- **Content Library** (`api/content.py`): Knowledge base management and search
- **AI Assistant** (`api/ai.py`): Content generation and writing assistance

### Frontend Modules

- **Dashboard**: Main interface showing active grants and quick actions
- **Grant Builder**: Step-by-step grant application creation
- **AI Assistant**: Interactive writing helper with contextual suggestions
- **Content Library**: Searchable organizational knowledge base

## Development Guidelines

### Code Style
- Follow PEP 8 for Python code
- Use type hints for function parameters and return values
- Include docstrings for all classes and functions
- Write unit tests for all core functionality

### Database Design
- Use SQLAlchemy ORM for database operations
- Implement proper foreign key relationships
- Include created/updated timestamps on all models
- Use database migrations for schema changes

### Security
- Hash all passwords using werkzeug.security
- Implement CSRF protection for forms
- Validate all user inputs
- Use prepared statements to prevent SQL injection

### AI Integration
- Use semantic embeddings for content similarity
- Implement rate limiting for AI API calls
- Cache AI responses when appropriate
- Provide fallback content when AI is unavailable

## Deployment

### Development
```bash
python scripts/run_dev_server.py
```

### Production (Docker)
```bash
docker-compose up -d
```

### Cloud Deployment
- AWS/Azure/GCP compatible
- Use environment variables for configuration
- Implement proper logging and monitoring
- Set up automated backups for database

## Contributing

1. Create feature branch from main
2. Implement changes with tests
3. Update documentation as needed
4. Submit pull request with description

## License

MIT License - See LICENSE file for details

## Support

For questions or issues:
- Create GitHub issue
- Email: support@ghosteam.dev
- Documentation: https://docs.ghosteam.dev
