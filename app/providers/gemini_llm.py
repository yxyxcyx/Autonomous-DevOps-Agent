"""Google Gemini LLM provider implementation."""

import structlog
from typing import List, Optional, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from app.interfaces.llm import ILLMProvider, LLMMessage, LLMResponse, LLMProviderFactory
from app.config import settings
from app.utils import retry_on_exception

logger = structlog.get_logger()


class GeminiProvider(ILLMProvider):
    """Google Gemini LLM provider."""
    
    def __init__(
        self,
        model: str,
        temperature: float = 0.1,
        api_key: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Gemini provider.
        
        Args:
            model: Gemini model name
            temperature: Temperature for generation
            api_key: API key (uses settings if not provided)
            **kwargs: Additional parameters
        """
        self.model = model
        self.temperature = temperature
        self.api_key = api_key or settings.GEMINI_API_KEY
        
        if not self.api_key:
            raise ValueError("Gemini API key not provided")
        
        self.client = ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=self.api_key
        )
    
    def generate(
        self,
        messages: List[LLMMessage],
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response from Gemini."""
        try:
            # Convert messages to LangChain format
            langchain_messages = self._convert_messages(messages)
            
            # Generate response
            response = self.client.invoke(langchain_messages)
            
            # Extract token usage
            tokens_used = response.response_metadata.get("token_usage", {}).get("total_tokens", 0)
            
            return LLMResponse(
                content=response.content,
                tokens_used=tokens_used,
                model=self.model,
                metadata=response.response_metadata
            )
            
        except Exception as e:
            logger.error(f"Gemini generation failed: {str(e)}")
            raise
    
    @retry_on_exception(max_retries=3, delay=1.0)
    def generate_with_retry(
        self,
        messages: List[LLMMessage],
        max_retries: int = 3,
        **kwargs
    ) -> LLMResponse:
        """Generate with automatic retry."""
        return self.generate(messages, **kwargs)
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text (approximate for Gemini)."""
        # Approximate token count (Gemini doesn't provide exact tokenizer)
        # Using rough estimate of 4 characters per token
        return len(text) // 4
    
    def is_available(self) -> bool:
        """Check if Gemini is available."""
        try:
            test_messages = [
                LLMMessage(role="user", content="test")
            ]
            response = self.generate(test_messages)
            return response is not None
        except Exception:
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get Gemini model information."""
        return {
            "provider": "gemini",
            "model": self.model,
            "temperature": self.temperature,
            "available": self.is_available()
        }
    
    def _convert_messages(self, messages: List[LLMMessage]) -> List:
        """Convert LLMMessage to LangChain format."""
        langchain_messages = []
        
        for msg in messages:
            if msg.role == "system":
                langchain_messages.append(SystemMessage(content=msg.content))
            elif msg.role == "user":
                langchain_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                langchain_messages.append(AIMessage(content=msg.content))
            else:
                logger.warning(f"Unknown message role: {msg.role}")
        
        return langchain_messages


# Register the provider
LLMProviderFactory.register_provider("gemini", GeminiProvider)

# Backward compatibility alias so older imports continue to work
GeminiLLMProvider = GeminiProvider
