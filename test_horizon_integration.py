#!/usr/bin/env python3
"""
Test script for OpenRouter Horizon Beta integration with vision capabilities.
This script verifies that the AI Assistant System properly uses the new model configuration.
"""

import asyncio
import os
import sys
import json
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from app.config import settings
    from app.core.llm import llm_manager, ModelType, ChatMessage
    from app.core.vision import vision_processor
    from app.agents.assistant import AssistantAgent
    from app.agents.code_agent import CodeAgent
    from app.agents.docs_agent import DocsAgent
    from app.agents.planner_agent import PlannerAgent
    from app.agents.tool_agent import ToolAgent
    from loguru import logger
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)


class HorizonBetaTestSuite:
    """Test suite for OpenRouter Horizon Beta integration."""
    
    def __init__(self):
        self.results = {
            "passed": 0,
            "failed": 0,
            "tests": []
        }
    
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        
        self.results["tests"].append({
            "name": test_name,
            "passed": passed,
            "details": details
        })
        
        if passed:
            self.results["passed"] += 1
        else:
            self.results["failed"] += 1
    
    def test_configuration(self):
        """Test that configuration is properly set to use Horizon Beta."""
        print("\n🔧 Testing Configuration...")
        
        # Test default model
        expected_default = "openrouter/horizon-beta"
        actual_default = settings.default_model
        self.log_test(
            "Default model configuration",
            actual_default == expected_default,
            f"Expected: {expected_default}, Got: {actual_default}"
        )
        
        # Test other models
        expected_mistral = "mistralai/mistral-small-3.2-24b-instruct:free"
        actual_mistral = settings.mistral_model
        self.log_test(
            "Mistral model configuration",
            actual_mistral == expected_mistral,
            f"Expected: {expected_mistral}, Got: {actual_mistral}"
        )
        
        expected_qwen = "qwen/qwen3-coder:free"
        actual_qwen = settings.qwen_model
        self.log_test(
            "Qwen model configuration",
            actual_qwen == expected_qwen,
            f"Expected: {expected_qwen}, Got: {actual_qwen}"
        )
        
        # Test OpenRouter API key
        has_api_key = bool(settings.openrouter_api_key and settings.openrouter_api_key != "your-openrouter-api-key-here")
        self.log_test(
            "OpenRouter API key configured",
            has_api_key,
            "API key is required for testing actual model calls"
        )
    
    def test_model_selection(self):
        """Test that model selection logic works correctly."""
        print("\n🧠 Testing Model Selection Logic...")
        
        # Test coding task selection
        coding_model = llm_manager.select_best_model("code generation", "write a python function")
        self.log_test(
            "Coding task model selection",
            coding_model == ModelType.QWEN,
            f"Expected: QWEN, Got: {coding_model}"
        )
        
        # Test vision task selection
        vision_model = llm_manager.select_best_model("image analysis", "analyze this image")
        self.log_test(
            "Vision task model selection",
            vision_model == ModelType.DEFAULT,
            f"Expected: DEFAULT (Horizon Beta), Got: {vision_model}"
        )
        
        # Test general task selection
        general_model = llm_manager.select_best_model("general chat", "hello world")
        self.log_test(
            "General task model selection",
            general_model == ModelType.DEFAULT,
            f"Expected: DEFAULT (Horizon Beta), Got: {general_model}"
        )
    
    def test_vision_capabilities(self):
        """Test vision processor capabilities."""
        print("\n👁️ Testing Vision Capabilities...")
        
        # Test vision model assignment
        vision_model = vision_processor.vision_model
        self.log_test(
            "Vision processor model assignment",
            vision_model == ModelType.DEFAULT,
            f"Expected: DEFAULT (Horizon Beta), Got: {vision_model}"
        )
        
        # Test vision support detection
        horizon_support = vision_processor.is_vision_supported(ModelType.DEFAULT)
        mistral_support = vision_processor.is_vision_supported(ModelType.MISTRAL)
        qwen_support = vision_processor.is_vision_supported(ModelType.QWEN)
        
        self.log_test(
            "Horizon Beta vision support",
            horizon_support,
            "Horizon Beta should support vision"
        )
        
        self.log_test(
            "Mistral vision support",
            mistral_support,
            "Mistral Small should support vision"
        )
        
        self.log_test(
            "Qwen vision support (should be False)",
            not qwen_support,
            "Qwen3 Coder should not support vision"
        )
    
    def test_multimodal_message_creation(self):
        """Test multimodal message creation."""
        print("\n📝 Testing Multimodal Message Creation...")
        
        # Test vision message creation
        test_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
        test_prompt = "What is in this image?"
        
        message = vision_processor.create_vision_message(test_prompt, [test_url])
        
        # Verify message structure
        is_valid_structure = (
            isinstance(message.content, list) and
            len(message.content) == 2 and
            message.content[0]["type"] == "text" and
            message.content[1]["type"] == "image_url"
        )
        
        self.log_test(
            "Multimodal message structure",
            is_valid_structure,
            "Message should have text and image_url components"
        )
        
        # Verify image URL format
        image_url_format = (
            "image_url" in message.content[1] and
            "url" in message.content[1]["image_url"] and
            message.content[1]["image_url"]["url"] == test_url
        )
        
        self.log_test(
            "Image URL format",
            image_url_format,
            "Image URL should match OpenRouter's expected format"
        )
    
    async def test_llm_integration(self):
        """Test actual LLM integration if API key is available."""
        print("\n🚀 Testing LLM Integration...")
        
        if not settings.openrouter_api_key or settings.openrouter_api_key == "your-openrouter-api-key-here":
            self.log_test(
                "LLM integration test",
                False,
                "Skipped - No valid OpenRouter API key configured"
            )
            return
        
        try:
            # Test simple text completion
            messages = [ChatMessage(role="user", content="Hello! Please respond with 'Integration test successful'.")]
            
            response = await llm_manager.generate_response(
                messages=messages,
                model_type=ModelType.DEFAULT,
                task_type="general"
            )
            
            success = response.content and "Integration test successful" in response.content
            self.log_test(
                "Horizon Beta text completion",
                success,
                f"Response: {response.content[:100]}..." if response.content else "No response"
            )
            
        except Exception as e:
            self.log_test(
                "Horizon Beta text completion",
                False,
                f"Error: {str(e)}"
            )
    
    def test_agent_initialization(self):
        """Test that all agents initialize correctly with new configuration."""
        print("\n🤖 Testing Agent Initialization...")
        
        try:
            # Test AssistantAgent
            assistant = AssistantAgent()
            self.log_test(
                "AssistantAgent initialization",
                assistant.name == "AssistantAgent",
                "AssistantAgent should initialize successfully"
            )
            
            # Test CodeAgent
            code_agent = CodeAgent()
            self.log_test(
                "CodeAgent initialization",
                code_agent.name == "CodeAgent" and code_agent.model_type == ModelType.QWEN,
                "CodeAgent should use QWEN model"
            )
            
            # Test other agents
            docs_agent = DocsAgent()
            planner_agent = PlannerAgent()
            tool_agent = ToolAgent()
            
            self.log_test(
                "All agents initialization",
                all([
                    docs_agent.name == "DocsAgent",
                    planner_agent.name == "PlannerAgent",
                    tool_agent.name == "ToolAgent"
                ]),
                "All specialized agents should initialize successfully"
            )
            
        except Exception as e:
            self.log_test(
                "Agent initialization",
                False,
                f"Error: {str(e)}"
            )
    
    def test_model_capabilities(self):
        """Test model capabilities mapping."""
        print("\n📊 Testing Model Capabilities...")
        
        capabilities = llm_manager._model_capabilities
        
        # Test DEFAULT model capabilities
        default_caps = capabilities.get(ModelType.DEFAULT, {})
        has_vision = "vision" in default_caps.get("good_for", [])
        has_multimodal = "multimodal" in default_caps.get("good_for", [])
        
        self.log_test(
            "Horizon Beta vision capability",
            has_vision,
            "DEFAULT model should have vision capability"
        )
        
        self.log_test(
            "Horizon Beta multimodal capability",
            has_multimodal,
            "DEFAULT model should have multimodal capability"
        )
        
        # Test QWEN model capabilities
        qwen_caps = capabilities.get(ModelType.QWEN, {})
        has_code = "code" in qwen_caps.get("good_for", [])
        
        self.log_test(
            "Qwen coding capability",
            has_code,
            "QWEN model should have coding capability"
        )
    
    def print_summary(self):
        """Print test summary."""
        total_tests = self.results["passed"] + self.results["failed"]
        success_rate = (self.results["passed"] / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n{'='*60}")
        print(f"🧪 HORIZON BETA INTEGRATION TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {self.results['passed']} ✅")
        print(f"Failed: {self.results['failed']} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.results["failed"] > 0:
            print(f"\n❌ Failed Tests:")
            for test in self.results["tests"]:
                if not test["passed"]:
                    print(f"  - {test['name']}: {test['details']}")
        
        print(f"\n🎯 System Status: {'READY' if success_rate >= 80 else 'NEEDS ATTENTION'}")
        
        return success_rate >= 80


async def main():
    """Run the comprehensive test suite."""
    print("🚀 Starting OpenRouter Horizon Beta Integration Tests...")
    print("=" * 60)
    
    test_suite = HorizonBetaTestSuite()
    
    # Run all tests
    test_suite.test_configuration()
    test_suite.test_model_selection()
    test_suite.test_vision_capabilities()
    test_suite.test_multimodal_message_creation()
    await test_suite.test_llm_integration()
    test_suite.test_agent_initialization()
    test_suite.test_model_capabilities()
    
    # Print summary
    success = test_suite.print_summary()
    
    if success:
        print("\n🎉 All systems are ready for OpenRouter Horizon Beta!")
        print("You can now use the AI Assistant with advanced vision capabilities.")
    else:
        print("\n⚠️  Some tests failed. Please check the configuration and try again.")
    
    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        sys.exit(1)