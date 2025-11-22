"""LLM interface for abstracting language model providers."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class LLMMessage:
    """Represents a message in LLM conversation."""
    role: str  # "system", "user", "assistant"
    content: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class LLMResponse:
    """Represents a response from LLM."""
    content: str
    tokens_used: int
    model: str
    metadata: Optional[Dict[str, Any]] = None


class ILLMProvider(ABC):
    """Abstract interface for LLM providers."""
    
    @abstractmethod
    def __init__(self, model: str, temperature: float = 0.1, **kwargs):
        """
        Initialize the LLM provider.
        
        Args:
            model: Model name/identifier
            temperature: Temperature for generation
            **kwargs: Additional provider-specific parameters
        """
        pass
    
    @abstractmethod
    def generate(
        self,
        messages: List[LLMMessage],
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response from the LLM.
        
        Args:
            messages: List of conversation messages
            max_tokens: Maximum tokens to generate
            **kwargs: Additional generation parameters
            
        Returns:
            LLMResponse object
        """
        pass
    
    @abstractmethod
    def generate_with_retry(
        self,
        messages: List[LLMMessage],
        max_retries: int = 3,
        **kwargs
    ) -> LLMResponse:
        """
        Generate with automatic retry on failure.
        
        Args:
            messages: List of conversation messages
            max_retries: Maximum number of retries
            **kwargs: Additional generation parameters
            
        Returns:
            LLMResponse object
        """
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the provider is available.
        
        Returns:
            True if available, False otherwise
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.
        
        Returns:
            Dictionary with model information
        """
        pass


class LLMProviderFactory:
    """Factory for creating LLM providers."""
    
    _providers: Dict[str, type] = {}
    
    @classmethod
    def register_provider(cls, name: str, provider_class: type):
        """
        Register an LLM provider.
        
        Args:
            name: Provider name
            provider_class: Provider class implementing ILLMProvider
        """
        cls._providers[name] = provider_class
    
    @classmethod
    def create_provider(
        cls,
        provider_name: str,
        model: str,
        **kwargs
    ) -> ILLMProvider:
        """
        Create an LLM provider instance.
        
        Args:
            provider_name: Name of the provider
            model: Model name
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Instance of ILLMProvider
            
        Raises:
            ValueError: If provider not found
        """
        if provider_name not in cls._providers:
            raise ValueError(f"Provider '{provider_name}' not registered")
        
        provider_class = cls._providers[provider_name]
        return provider_class(model=model, **kwargs)
    
    @classmethod
    def list_providers(cls) -> List[str]:
        """
        List registered providers.
        
        Returns:
            List of provider names
        """
        return list(cls._providers.keys())
