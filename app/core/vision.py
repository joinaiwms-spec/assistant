"""Vision support for image analysis using multimodal models."""

from typing import List, Dict, Any, Optional
from loguru import logger

from app.core.llm import ChatMessage, ModelType, llm_manager


class VisionProcessor:
    """Process images and generate descriptions using vision-capable models."""
    
    def __init__(self):
        self.vision_model = ModelType.DEFAULT  # Horizon Beta has excellent vision capabilities
    
    async def analyze_image(
        self, 
        image_url: str, 
        prompt: str = "What is in this image?",
        context: Optional[str] = None
    ) -> str:
        """Analyze a single image with the given prompt."""
        try:
            # Create multimodal message content
            content = [
                {
                    "type": "text",
                    "text": prompt
                }
            ]
            
            # Add context if provided
            if context:
                content[0]["text"] = f"{context}\n\n{prompt}"
            
            # Add image
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": image_url
                }
            })
            
            # Create message with multimodal content
            messages = [ChatMessage(role="user", content=content)]
            
            # Generate response using vision model
            response = await llm_manager.generate_response(
                messages=messages,
                model_type=self.vision_model,
                task_type="image_analysis"
            )
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return f"Error analyzing image: {str(e)}"
    
    async def analyze_multiple_images(
        self, 
        image_urls: List[str], 
        prompt: str = "What do you see in these images?",
        context: Optional[str] = None
    ) -> str:
        """Analyze multiple images with the given prompt."""
        try:
            # Create multimodal message content
            content = [
                {
                    "type": "text",
                    "text": prompt
                }
            ]
            
            # Add context if provided
            if context:
                content[0]["text"] = f"{context}\n\n{prompt}"
            
            # Add all images
            for i, image_url in enumerate(image_urls):
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": image_url
                    }
                })
            
            # Create message with multimodal content
            messages = [ChatMessage(role="user", content=content)]
            
            # Generate response using vision model
            response = await llm_manager.generate_response(
                messages=messages,
                model_type=self.vision_model,
                task_type="image_analysis"
            )
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error analyzing images: {e}")
            return f"Error analyzing images: {str(e)}"
    
    async def compare_images(
        self, 
        image_urls: List[str], 
        comparison_prompt: str = "Compare these images and describe the differences and similarities."
    ) -> str:
        """Compare multiple images and describe differences/similarities."""
        if len(image_urls) < 2:
            return "At least two images are required for comparison."
        
        return await self.analyze_multiple_images(
            image_urls=image_urls,
            prompt=comparison_prompt,
            context="You are comparing multiple images."
        )
    
    async def describe_image_for_context(
        self, 
        image_url: str, 
        task_context: str
    ) -> str:
        """Describe an image in the context of a specific task."""
        prompt = f"""
        Analyze this image in the context of: {task_context}
        
        Please provide:
        1. A general description of what you see
        2. How this image relates to the given context
        3. Any relevant details that might be important for the task
        """
        
        return await self.analyze_image(image_url, prompt)
    
    def create_vision_message(
        self, 
        text_prompt: str, 
        image_urls: List[str]
    ) -> ChatMessage:
        """Create a properly formatted multimodal message."""
        content = [
            {
                "type": "text",
                "text": text_prompt
            }
        ]
        
        # Add all images
        for image_url in image_urls:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": image_url
                }
            })
        
        return ChatMessage(role="user", content=content)
    
    def is_vision_supported(self, model_type: ModelType) -> bool:
        """Check if a model supports vision capabilities."""
        # Both DEFAULT (Horizon Beta) and MISTRAL support vision
        return model_type in [ModelType.DEFAULT, ModelType.MISTRAL]
    
    async def extract_text_from_image(self, image_url: str) -> str:
        """Extract text from an image (OCR functionality)."""
        prompt = """
        Please extract and transcribe any text you can see in this image.
        If there's no text visible, please say "No text found in image".
        Preserve the formatting and structure of the text as much as possible.
        """
        
        return await self.analyze_image(image_url, prompt)
    
    async def analyze_chart_or_graph(self, image_url: str) -> str:
        """Analyze charts, graphs, or data visualizations."""
        prompt = """
        Analyze this chart, graph, or data visualization. Please provide:
        
        1. Type of chart/graph (bar chart, line graph, pie chart, etc.)
        2. What data is being presented
        3. Key trends or patterns you observe
        4. Any notable insights or conclusions
        5. Axis labels, legends, and other important details
        """
        
        return await self.analyze_image(image_url, prompt)
    
    async def analyze_document_image(self, image_url: str) -> str:
        """Analyze document images for content extraction."""
        prompt = """
        This appears to be a document image. Please:
        
        1. Identify the type of document (form, report, letter, etc.)
        2. Extract the main text content
        3. Identify key sections, headings, and structure
        4. Note any important data, numbers, or dates
        5. Describe the overall layout and formatting
        """
        
        return await self.analyze_image(image_url, prompt)


# Global vision processor instance
vision_processor = VisionProcessor()