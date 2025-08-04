"""Docs Agent - Specialized agent for document processing and analysis."""

import hashlib
from typing import Dict, List, Any, Optional
from pathlib import Path

from loguru import logger

from app.agents.base import BaseAgent, AgentTask
from app.core.llm import ChatMessage, ModelType


class DocsAgent(BaseAgent):
    """Agent specialized in document processing, analysis, and information extraction."""
    
    def __init__(self):
        super().__init__(
            name="DocsAgent",
            description="Specialized agent for document processing, analysis, and information extraction",
            model_type=ModelType.DEFAULT
        )
    
    def _get_system_prompt(self) -> str:
        return """You are DocsAgent, a specialized AI agent focused on document processing and analysis. Your expertise includes:

1. Document content extraction and parsing
2. Information retrieval and summarization
3. Document structure analysis
4. Content classification and categorization
5. Key information identification
6. Document comparison and analysis
7. Question answering from document content
8. Document metadata extraction

When handling document-related tasks:
- Accurately extract and interpret document content
- Provide structured summaries and analyses
- Identify key information and insights
- Maintain context and relationships between information
- Handle multiple document formats appropriately
- Preserve important formatting and structure when relevant
- Provide clear, organized responses

Always ensure accuracy and completeness in document analysis while being concise and relevant."""
    
    async def _execute_task(self, task: AgentTask) -> str:
        """Execute a document-related task."""
        try:
            task_type = self._classify_task(task.description)
            
            if task_type == "summarization":
                return await self._summarize_document(task)
            elif task_type == "extraction":
                return await self._extract_information(task)
            elif task_type == "analysis":
                return await self._analyze_document(task)
            elif task_type == "question_answering":
                return await self._answer_from_document(task)
            elif task_type == "comparison":
                return await self._compare_documents(task)
            else:
                return await self._handle_general_doc_task(task)
                
        except Exception as e:
            logger.error(f"Error in DocsAgent task execution: {e}")
            raise
    
    def _classify_task(self, description: str) -> str:
        """Classify the type of document task."""
        description_lower = description.lower()
        
        if any(keyword in description_lower for keyword in ["summarize", "summary", "overview"]):
            return "summarization"
        elif any(keyword in description_lower for keyword in ["extract", "find", "identify", "get"]):
            return "extraction"
        elif any(keyword in description_lower for keyword in ["analyze", "analysis", "examine"]):
            return "analysis"
        elif any(keyword in description_lower for keyword in ["question", "answer", "what", "how", "why"]):
            return "question_answering"
        elif any(keyword in description_lower for keyword in ["compare", "comparison", "difference"]):
            return "comparison"
        else:
            return "general"
    
    async def _summarize_document(self, task: AgentTask) -> str:
        """Summarize document content."""
        content = task.context.get("content", "")
        document_name = task.context.get("document_name", "document")
        
        # Get relevant memories for context
        memories = await self.get_relevant_memories(f"summary {document_name}")
        memory_context = ""
        if memories:
            memory_context = "\n\nPrevious document summaries:\n"
            for mem in memories[:2]:
                memory_context += f"- {mem['text'][:200]}...\n"
        
        summary_prompt = f"""
        Summarize the following document:
        
        Document: {document_name}
        Task: {task.description}
        {memory_context}
        
        Content:
        {content[:4000]}  # Limit content to avoid token limits
        
        Please provide:
        1. Executive summary (2-3 sentences)
        2. Key points and main topics
        3. Important details and findings
        4. Conclusions or recommendations (if applicable)
        
        Keep the summary concise but comprehensive.
        """
        
        messages = [ChatMessage(role="user", content=summary_prompt)]
        response = await self.generate_response(messages)
        
        return response.content
    
    async def _extract_information(self, task: AgentTask) -> str:
        """Extract specific information from documents."""
        content = task.context.get("content", "")
        extraction_criteria = task.context.get("criteria", task.description)
        
        extraction_prompt = f"""
        Extract specific information from the following document:
        
        Extraction criteria: {extraction_criteria}
        
        Document content:
        {content[:4000]}
        
        Please provide:
        1. Extracted information that matches the criteria
        2. Source context for each piece of information
        3. Confidence level for each extraction
        4. Any related or relevant information
        
        Format the response clearly and organize by relevance.
        """
        
        messages = [ChatMessage(role="user", content=extraction_prompt)]
        response = await self.generate_response(messages)
        
        return response.content
    
    async def _analyze_document(self, task: AgentTask) -> str:
        """Analyze document structure, content, and patterns."""
        content = task.context.get("content", "")
        analysis_focus = task.context.get("focus", "general analysis")
        
        analysis_prompt = f"""
        Analyze the following document with focus on: {analysis_focus}
        
        Task: {task.description}
        
        Document content:
        {content[:4000]}
        
        Please provide:
        1. Document structure and organization
        2. Content themes and patterns
        3. Key insights and observations
        4. Quality and completeness assessment
        5. Recommendations or suggestions
        
        Provide a thorough analytical perspective.
        """
        
        messages = [ChatMessage(role="user", content=analysis_prompt)]
        response = await self.generate_response(messages)
        
        return response.content
    
    async def _answer_from_document(self, task: AgentTask) -> str:
        """Answer questions based on document content."""
        content = task.context.get("content", "")
        question = task.context.get("question", task.description)
        
        # Search for relevant memories about similar questions
        memories = await self.get_relevant_memories(question)
        memory_context = ""
        if memories:
            memory_context = "\n\nRelevant context from previous Q&A:\n"
            for mem in memories[:2]:
                memory_context += f"- {mem['text'][:200]}...\n"
        
        qa_prompt = f"""
        Answer the following question based on the document content:
        
        Question: {question}
        {memory_context}
        
        Document content:
        {content[:4000]}
        
        Please provide:
        1. Direct answer to the question
        2. Supporting evidence from the document
        3. Page/section references (if available)
        4. Confidence level in the answer
        5. Related information that might be helpful
        
        Be accurate and cite specific parts of the document.
        """
        
        messages = [ChatMessage(role="user", content=qa_prompt)]
        response = await self.generate_response(messages)
        
        return response.content
    
    async def _compare_documents(self, task: AgentTask) -> str:
        """Compare multiple documents."""
        documents = task.context.get("documents", [])
        comparison_criteria = task.context.get("criteria", "general comparison")
        
        if len(documents) < 2:
            return "At least two documents are required for comparison."
        
        comparison_prompt = f"""
        Compare the following documents based on: {comparison_criteria}
        
        Task: {task.description}
        
        Documents to compare:
        """
        
        for i, doc in enumerate(documents[:3]):  # Limit to 3 documents
            comparison_prompt += f"\n\nDocument {i+1}: {doc.get('name', f'Document {i+1}')}\n"
            comparison_prompt += f"Content: {doc.get('content', '')[:1500]}...\n"
        
        comparison_prompt += """
        
        Please provide:
        1. Key similarities between documents
        2. Major differences and unique aspects
        3. Comparative analysis of quality and completeness
        4. Recommendations based on the comparison
        5. Summary of findings
        
        Structure the comparison clearly and systematically.
        """
        
        messages = [ChatMessage(role="user", content=comparison_prompt)]
        response = await self.generate_response(messages)
        
        return response.content
    
    async def _handle_general_doc_task(self, task: AgentTask) -> str:
        """Handle general document-related tasks."""
        content = task.context.get("content", "")
        
        memories = await self.get_relevant_memories(task.description)
        memory_context = ""
        if memories:
            memory_context = "\n\nRelevant context:\n"
            for mem in memories[:3]:
                memory_context += f"- {mem['text'][:200]}...\n"
        
        general_prompt = f"""
        Handle this document-related task:
        
        Task: {task.description}
        Context: {task.context}
        {memory_context}
        
        Document content (if provided):
        {content[:4000] if content else "No content provided"}
        
        Provide a comprehensive response that addresses the task requirements.
        Include relevant analysis, insights, and recommendations.
        """
        
        messages = [ChatMessage(role="user", content=general_prompt)]
        response = await self.generate_response(messages)
        
        return response.content
    
    def process_document_metadata(self, file_path: str, content: str) -> Dict[str, Any]:
        """Extract metadata from document."""
        try:
            file_path_obj = Path(file_path)
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            metadata = {
                "filename": file_path_obj.name,
                "extension": file_path_obj.suffix,
                "size": len(content),
                "content_hash": content_hash,
                "word_count": len(content.split()),
                "line_count": len(content.splitlines()),
                "character_count": len(content)
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error processing document metadata: {e}")
            return {}
    
    def chunk_document(self, content: str, chunk_size: int = 1000, overlap: int = 100) -> List[Dict[str, Any]]:
        """Split document into chunks for processing."""
        chunks = []
        
        try:
            words = content.split()
            
            for i in range(0, len(words), chunk_size - overlap):
                chunk_words = words[i:i + chunk_size]
                chunk_text = " ".join(chunk_words)
                
                chunks.append({
                    "index": len(chunks),
                    "content": chunk_text,
                    "word_count": len(chunk_words),
                    "start_word": i,
                    "end_word": min(i + chunk_size, len(words))
                })
            
            logger.info(f"Split document into {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Error chunking document: {e}")
            return [{"index": 0, "content": content, "word_count": len(content.split())}]