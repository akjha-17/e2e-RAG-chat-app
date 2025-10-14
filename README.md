# eLIMSChat.ai

An AI-powered RAG (Retrieval-Augmented Generation) chat application 

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd elimschat-ai-poc

# Run the deployment test
# Windows:
test-deployment.bat
# Linux/Mac:
./test-deployment.sh
```

### Option 2: Local Development

```bash
# Backend
cd llm-backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.development .env
# Edit .env with your OpenAI API key
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Frontend (new terminal)
cd llm-frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env.local
npm run dev
```

Access the application at:
- **Frontend**: http://localhost:5173 (dev) or http://localhost:3000 (Docker)
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🏗️ Architecture

- **Backend**: Python FastAPI with RAG capabilities
- **Frontend**: React + Vite + Material-UI
- **Vector Store**: FAISS (local) or Pinecone (cloud)
- **LLM**: OpenAI GPT-4o-mini (configurable)
- **Database**: SQLite (development) / PostgreSQL (production)

## ✨ Features

- 🤖 **AI Chat Interface** with context-aware responses
- 📚 **Document Upload & Processing** (PDF, DOCX, PPTX, etc.)
- 🔐 **User Authentication & Management**
- 💬 **Chat Session Management**
- 📊 **Analytics & Feedback System**
- 🔧 **Configurable LLM Backends** (OpenAI, Ollama, HuggingFace)
- 🚀 **Production-Ready Deployment** configurations

## 🌐 Deployment Options

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

### Quick Deploy Options:

| Platform | Difficulty | Deploy Link |
|----------|------------|-------------|
| **Vercel + Railway** | ⭐⭐ | [![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new) |
| **Heroku** | ⭐⭐ | [![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy) |
| **DigitalOcean** | ⭐⭐⭐ | [![Deploy to DO](https://www.deploytodo.com/do-btn-blue.svg)](https://cloud.digitalocean.com/apps/new) |

## 📁 Project Structure

```
elimschat-ai-poc/
├── llm-backend/          # FastAPI backend
│   ├── app.py           # Main application
│   ├── auth.py          # Authentication
│   ├── models.py        # Pydantic models
│   ├── store.py         # Vector store management
│   ├── llm.py           # LLM integration
│   ├── requirements.txt # Python dependencies
│   └── Dockerfile       # Backend container
├── llm-frontend/         # React frontend
│   ├── src/
│   │   ├── pages/       # React pages
│   │   ├── components/  # Reusable components
│   │   └── context/     # React contexts
│   ├── package.json     # Node dependencies
│   └── Dockerfile       # Frontend container
├── docker-compose.yml   # Multi-service setup
├── DEPLOYMENT.md        # Detailed deployment guide
└── README.md           # This file
```

## 🔧 Configuration

### Environment Variables

**Backend (.env)**:
```env
OPENAI_API_KEY=your-openai-api-key
LLM_BACKEND=openai
VECTOR_STORE=faiss
JWT_SECRET=your-secure-jwt-secret
CORS_ORIGINS=https://your-frontend-domain.com
```

**Frontend (.env.local)**:
```env
VITE_API_URL=https://your-backend-url.com
```

### Supported LLM Backends

- **OpenAI**: GPT-4, GPT-3.5-turbo, GPT-4o-mini
- **Ollama**: Local LLM deployment (llama2, codellama, etc.)
- **HuggingFace**: Open-source models (Qwen, Phi-3, etc.)

### Vector Store Options

- **FAISS**: Local vector storage (good for development)
- **Pinecone**: Cloud vector database (recommended for production)



## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request


**🚀 Ready to deploy? Check out the [DEPLOYMENT.md](DEPLOYMENT.md) guide!**
