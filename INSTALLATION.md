# 🚀 Installation Guide

This guide will help you set up and run the AI Assistant System on your machine.

## 📋 Prerequisites

- **Python 3.8+** (Python 3.11 recommended)
- **OpenRouter API Key** (for LLM access)
- **Git** (for cloning the repository)
- **4GB+ RAM** (for vector embeddings)
- **2GB+ disk space** (for dependencies and data)

## 🛠️ Installation Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ai-assistant-system
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Install core dependencies
pip install -r requirements.txt

# Optional: Install development dependencies
pip install -e .[dev]
```

### 4. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings
nano .env  # or use your preferred editor
```

**Required Configuration:**
```env
# OpenRouter API Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Optional: Customize other settings
HOST=0.0.0.0
PORT=8000
DEBUG=True
```

### 5. Get OpenRouter API Key

1. Visit [OpenRouter.ai](https://openrouter.ai)
2. Sign up for an account
3. Generate an API key
4. Add the key to your `.env` file

### 6. Test Installation

```bash
# Run system tests
python test_system.py

# Or use the CLI
python cli.py test
```

### 7. Start the System

```bash
# Start the server
python main.py

# Or use the CLI
python cli.py start
```

The system will be available at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Alternative docs**: http://localhost:8000/redoc

## 🔧 Advanced Setup

### Document Processing (Optional)

For full document processing capabilities, install additional dependencies:

```bash
# PDF processing
pip install PyPDF2

# Microsoft Office documents
pip install python-docx python-pptx openpyxl

# File type detection
pip install python-magic

# On Ubuntu/Debian:
sudo apt-get install libmagic1

# On macOS:
brew install libmagic
```

### Performance Optimization

For better performance with large document processing:

```bash
# Install optimized FAISS
pip uninstall faiss-cpu
pip install faiss-gpu  # If you have CUDA GPU

# Or use conda for better optimization
conda install -c conda-forge faiss-cpu
```

### Database Setup (Advanced)

By default, the system uses SQLite. For production, consider PostgreSQL:

```bash
# Install PostgreSQL adapter
pip install psycopg2-binary

# Update .env file
DATABASE_URL=postgresql://user:password@localhost:5432/ai_assistant
```

## 🐳 Docker Installation

### Using Docker Compose

```bash
# Clone repository
git clone <repository-url>
cd ai-assistant-system

# Create .env file
cp .env.example .env
# Edit .env with your OpenRouter API key

# Build and start
docker-compose up -d

# View logs
docker-compose logs -f
```

### Using Docker

```bash
# Build image
docker build -t ai-assistant-system .

# Run container
docker run -d \
  --name ai-assistant \
  -p 8000:8000 \
  -e OPENROUTER_API_KEY=your_key_here \
  -v $(pwd)/data:/app/data \
  ai-assistant-system
```

## 📱 CLI Usage

The system includes a comprehensive CLI tool:

```bash
# Show all available commands
python cli.py --help

# Start the server
python cli.py start

# Interactive chat
python cli.py chat

# Send single message
python cli.py chat "Hello, how can you help me?"

# Check system status
python cli.py status

# Manage memory
python cli.py memory search "python programming"
python cli.py memory add "Important note about the project"

# Process documents
python cli.py docs upload document.pdf
python cli.py docs search --query "key findings"

# Work with agents
python cli.py agents list
python cli.py agents status --agent code
python cli.py agents task --agent code --task "Generate a Python function"

# Configuration management
python cli.py config show
```

## 🔍 Verification

### Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "dependencies": {
    "openrouter": "connected",
    "vector_memory": "active",
    "document_processor": "ready"
  }
}
```

### System Status

```bash
curl http://localhost:8000/status
```

### Test Chat

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, can you help me?"}'
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Ensure you're in the virtual environment
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

#### 2. OpenRouter API Errors
```bash
# Check your API key
python -c "from app.config import settings; print(settings.openrouter_api_key)"

# Test API connection
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://openrouter.ai/api/v1/models
```

#### 3. Memory/FAISS Issues
```bash
# Clear vector database
rm -rf vector_store/

# Reinstall FAISS
pip uninstall faiss-cpu
pip install faiss-cpu
```

#### 4. Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000  # Linux/macOS
netstat -ano | findstr :8000  # Windows

# Use different port
python cli.py start --port 8080
```

#### 5. Permission Errors
```bash
# Ensure directories are writable
chmod -R 755 vector_store/ logs/ uploads/

# Or run with appropriate permissions
sudo python main.py  # Not recommended for production
```

### Debug Mode

Enable debug mode for detailed logging:

```bash
# In .env file
DEBUG=True
LOG_LEVEL=DEBUG

# Or via CLI
python cli.py start --reload
```

### Log Analysis

```bash
# View logs
tail -f logs/ai_assistant.log

# Search for errors
grep ERROR logs/ai_assistant.log

# Monitor system resources
htop  # or top on macOS
```

## 🔒 Security Considerations

### Production Deployment

1. **Environment Variables**
   ```bash
   # Use strong secrets
   JWT_SECRET=your-very-strong-secret-key
   
   # Disable debug mode
   DEBUG=False
   ```

2. **Network Security**
   ```bash
   # Bind to specific interface
   HOST=127.0.0.1  # localhost only
   
   # Use reverse proxy (nginx/apache)
   # Enable HTTPS/TLS
   ```

3. **File Permissions**
   ```bash
   # Restrict file access
   chmod 600 .env
   chmod -R 750 logs/
   ```

4. **API Rate Limiting**
   - Configure rate limiting in production
   - Monitor API usage and costs
   - Implement authentication if needed

## 📈 Performance Tuning

### Memory Optimization

```env
# Adjust memory settings in .env
MAX_MEMORY_SIZE=50000
EMBEDDING_MODEL=all-MiniLM-L6-v2  # Smaller model
```

### Database Optimization

```bash
# For SQLite
pip install pysqlite3-binary

# For PostgreSQL production setup
pip install psycopg2-binary
```

### Concurrent Processing

```env
# Adjust worker settings
WORKERS=4
MAX_CONCURRENT_TASKS=10
```

## 🆘 Getting Help

### Documentation
- **API Docs**: http://localhost:8000/docs
- **README**: [README.md](README.md)
- **Code Examples**: See `examples/` directory

### Support Channels
- **Issues**: Create GitHub issue
- **Discussions**: GitHub discussions
- **Community**: Join our Discord/Slack

### Useful Commands

```bash
# System information
python cli.py status

# Test specific components
python -c "from app.core.memory import memory; print(memory.get_stats())"

# Check model availability
python -c "from app.core.llm import llm_manager; import asyncio; print(asyncio.run(llm_manager.client.get_available_models()))"

# Validate configuration
python cli.py config validate
```

---

**Need more help?** Check our [FAQ](FAQ.md) or create an issue on GitHub!