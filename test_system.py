"""Simple test script to verify the AI Assistant System works correctly."""

import asyncio
import json
import time
from pathlib import Path

# Test imports
try:
    from app.config import settings
    from app.agents.assistant import AssistantAgent
    from app.agents.code_agent import CodeAgent
    from app.agents.docs_agent import DocsAgent
    from app.agents.planner_agent import PlannerAgent
    from app.agents.tool_agent import ToolAgent
    from app.core.memory import memory
    from app.core.llm import llm_manager
    from app.core.document_processor import document_processor
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)


async def test_basic_functionality():
    """Test basic system functionality."""
    print("\n🧪 Testing Basic Functionality")
    print("=" * 50)
    
    # Test memory system
    print("📝 Testing memory system...")
    try:
        memory_id = memory.add_memory("Test memory entry", {"test": True})
        results = memory.search_memories("test", k=1)
        if results:
            print("✅ Memory system working")
        else:
            print("❌ Memory system not working")
    except Exception as e:
        print(f"❌ Memory system error: {e}")
    
    # Test agents
    print("🤖 Testing agents...")
    try:
        assistant = AssistantAgent()
        code_agent = CodeAgent()
        docs_agent = DocsAgent()
        planner_agent = PlannerAgent()
        tool_agent = ToolAgent()
        
        # Register agents
        assistant.register_agent(code_agent)
        assistant.register_agent(docs_agent)
        assistant.register_agent(planner_agent)
        assistant.register_agent(tool_agent)
        
        print("✅ All agents initialized successfully")
        
        # Test basic chat (if API key is available)
        if hasattr(settings, 'openrouter_api_key') and settings.openrouter_api_key != "your_openrouter_api_key_here":
            print("💬 Testing basic chat...")
            try:
                response = await assistant.chat("Hello, can you help me?")
                if response:
                    print("✅ Chat functionality working")
                    print(f"   Response: {response[:100]}...")
                else:
                    print("❌ Chat returned empty response")
            except Exception as e:
                print(f"❌ Chat error: {e}")
        else:
            print("⚠️  Skipping chat test - no API key configured")
        
    except Exception as e:
        print(f"❌ Agent initialization error: {e}")
    
    # Test document processor
    print("📄 Testing document processor...")
    try:
        supported_formats = document_processor.get_supported_formats()
        print(f"✅ Document processor supports {len(supported_formats)} formats")
        print(f"   Formats: {', '.join(supported_formats[:10])}...")
    except Exception as e:
        print(f"❌ Document processor error: {e}")


def test_configuration():
    """Test configuration system."""
    print("\n⚙️  Testing Configuration")
    print("=" * 50)
    
    try:
        print(f"📍 Host: {settings.host}")
        print(f"🔌 Port: {settings.port}")
        print(f"🐛 Debug: {settings.debug}")
        print(f"📊 Log Level: {settings.log_level}")
        print(f"🗄️  Database URL: {settings.database_url}")
        print(f"🧠 Vector DB Path: {settings.vector_db_path}")
        print(f"📈 Max Memory Size: {settings.max_memory_size}")
        print("✅ Configuration loaded successfully")
    except Exception as e:
        print(f"❌ Configuration error: {e}")


def test_directory_structure():
    """Test that all necessary directories exist or can be created."""
    print("\n📁 Testing Directory Structure")
    print("=" * 50)
    
    directories = [
        settings.vector_db_path,
        settings.upload_dir,
        Path(settings.log_file).parent
    ]
    
    for directory in directories:
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
            print(f"✅ Directory OK: {directory}")
        except Exception as e:
            print(f"❌ Directory error {directory}: {e}")


def test_dependencies():
    """Test that all dependencies are available."""
    print("\n📦 Testing Dependencies")
    print("=" * 50)
    
    dependencies = {
        "fastapi": "FastAPI web framework",
        "uvicorn": "ASGI server",
        "pydantic": "Data validation",
        "loguru": "Logging",
        "httpx": "HTTP client",
        "sentence_transformers": "Embeddings",
        "faiss": "Vector search",
        "numpy": "Numerical computing",
        "sqlalchemy": "Database ORM"
    }
    
    for package, description in dependencies.items():
        try:
            __import__(package)
            print(f"✅ {package}: {description}")
        except ImportError:
            print(f"❌ {package}: {description} - NOT INSTALLED")


async def main():
    """Run all tests."""
    print("🤖 AI ASSISTANT SYSTEM - SYSTEM TEST")
    print("=" * 60)
    
    test_configuration()
    test_directory_structure()
    test_dependencies()
    await test_basic_functionality()
    
    print("\n" + "=" * 60)
    print("🎉 System test completed!")
    print("=" * 60)
    
    print("\n🚀 To start the system:")
    print("   python main.py")
    print("\n📊 API Documentation:")
    print(f"   http://{settings.host}:{settings.port}/docs")
    print("\n⚠️  Remember to:")
    print("   1. Set your OpenRouter API key in .env")
    print("   2. Configure other settings as needed")
    print("   3. Install optional dependencies for document processing")


if __name__ == "__main__":
    asyncio.run(main())