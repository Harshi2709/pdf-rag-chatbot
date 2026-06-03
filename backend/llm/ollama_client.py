"""
Ollama LLM Client
Handles local LLM inference using Ollama
"""
import ollama
from typing import Optional, Dict


class OllamaClient:
    """
    Ollama Client for local LLM inference
    Supports configurable models and future streaming
    """
    
    def __init__(self, model_name: str = "llama3"):
        """
        Initialize Ollama client
        
        Args:
            model_name: Name of the Ollama model to use
        """
        self.model_name = model_name
        self.client = ollama
    
    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate response from LLM
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        
        Returns:
            Generated text response
        """
        try:
            options = {
                "temperature": temperature,
            }
            
            if max_tokens:
                options["num_predict"] = max_tokens
            
            response = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                options=options
            )
            
            return response["response"]
        
        except Exception as e:
            raise Exception(f"Ollama generation failed: {str(e)}")
    
    def chat(
        self,
        messages: list,
        temperature: float = 0.7
    ) -> str:
        """
        Chat completion using Ollama
        
        Args:
            messages: List of message dictionaries
            temperature: Sampling temperature
        
        Returns:
            Generated response
        """
        try:
            response = self.client.chat(
                model=self.model_name,
                messages=messages,
                options={"temperature": temperature}
            )
            
            return response["message"]["content"]
        
        except Exception as e:
            raise Exception(f"Ollama chat failed: {str(e)}")
    
    def check_availability(self) -> bool:
        """
        Check if Ollama is available and model is accessible
        
        Returns:
            True if available, False otherwise
        """
        try:
            # Try to list models
            models = self.client.list()
            return True
        except:
            return False
