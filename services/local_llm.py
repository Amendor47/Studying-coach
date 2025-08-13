# services/local_llm.py
# -*- coding: utf-8 -*-
"""
Unified Local LLM Adapter

Provides a unified interface for various local LLM providers:
- Ollama (default, via HTTP API)
- GPT4All (via Python library)  
- llama.cpp (via Python bindings)

Supports streaming, embeddings, and graceful fallbacks.
"""

from __future__ import annotations

import os
import time
import json
import logging
from typing import List, Dict, Any, Generator, Optional, Tuple
from dataclasses import dataclass
from functools import lru_cache
import threading

# Setup logging
logger = logging.getLogger(__name__)

# Optional dependencies
try:
    import ollama
except ImportError:
    ollama = None
    
try:
    import gpt4all
except ImportError:
    gpt4all = None

try:
    import llama_cpp
except ImportError:
    llama_cpp = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None


@dataclass
class LLMConfig:
    """Configuration for local LLM providers"""
    provider: str = "ollama"
    model: str = "llama3.1:8b"
    host: str = "http://127.0.0.1:11434"
    temperature: float = 0.2
    max_tokens: Optional[int] = 2048
    cache_ttl: int = 3600
    embedding_model: Optional[str] = "sentence-transformers/all-MiniLM-L6-v2"
    timeout: int = 30

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Load configuration from environment variables"""
        return cls(
            provider=os.getenv("LLM_PROVIDER", "ollama").lower(),
            model=os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
            host=os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.2")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2048")) if os.getenv("LLM_MAX_TOKENS") else None,
            cache_ttl=int(os.getenv("LLM_CACHE_TTL", "3600")),
            embedding_model=os.getenv("EMBEDDINGS_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
            timeout=int(os.getenv("LLM_TIMEOUT", "30"))
        )


class LRUCache:
    """Simple thread-safe LRU cache with TTL"""
    
    def __init__(self, max_size: int = 100, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self._cache:
                value, timestamp = self._cache[key]
                if time.time() - timestamp < self.ttl:
                    # Move to end (LRU)
                    del self._cache[key]
                    self._cache[key] = (value, timestamp)
                    return value
                else:
                    # Expired
                    del self._cache[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        with self._lock:
            # Remove oldest if at capacity
            if len(self._cache) >= self.max_size and key not in self._cache:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
            
            self._cache[key] = (value, time.time())


class LocalLLM:
    """Unified interface for local LLM providers"""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig.from_env()
        self.cache = LRUCache(max_size=100, ttl=self.config.cache_ttl)
        self._embedding_model = None
        self._llm_instance = None
        
    def _get_cache_key(self, prompt: str, system: Optional[str] = None, **kwargs) -> str:
        """Generate cache key for prompt"""
        cache_data = {
            "prompt": prompt,
            "system": system,
            "provider": self.config.provider,
            "model": self.config.model,
            "temperature": kwargs.get("temperature", self.config.temperature)
        }
        return str(hash(json.dumps(cache_data, sort_keys=True)))
    
    def health_check(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Check if LLM provider is available and healthy"""
        try:
            if self.config.provider == "ollama":
                return self._check_ollama_health()
            elif self.config.provider == "gpt4all":
                return self._check_gpt4all_health()  
            elif self.config.provider == "llama_cpp":
                return self._check_llama_cpp_health()
            else:
                return False, f"Unsupported provider: {self.config.provider}", {}
        except Exception as e:
            return False, str(e), {}
    
    def _check_ollama_health(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Check Ollama health"""
        if not ollama:
            return False, "ollama package not installed", {}
            
        try:
            # Set the host for ollama client
            ollama._client.Client(host=self.config.host)
            
            # Try to list models to verify connection
            client = ollama._client.Client(host=self.config.host)
            models = client.list()
            
            # Check if our model is available
            available_models = [model['name'] for model in models.get('models', [])]
            model_available = any(self.config.model in model for model in available_models)
            
            return True, "Ollama service healthy", {
                "host": self.config.host,
                "model": self.config.model,
                "model_available": model_available,
                "available_models": available_models[:5]  # Limit list size
            }
        except Exception as e:
            return False, f"Ollama connection failed: {e}", {}
    
    def _check_gpt4all_health(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Check GPT4All health"""
        if not gpt4all:
            return False, "gpt4all package not installed", {}
            
        try:
            # Try to initialize model (this will download if not available)
            model_name = self.config.model or "mistral-7b-instruct-v0.1.Q4_0.gguf"
            return True, "GPT4All available", {
                "model": model_name,
                "note": "Model will be downloaded on first use"
            }
        except Exception as e:
            return False, f"GPT4All initialization failed: {e}", {}
    
    def _check_llama_cpp_health(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Check llama.cpp health"""
        if not llama_cpp:
            return False, "llama-cpp-python package not installed", {}
            
        model_path = os.getenv("LLAMA_CPP_MODEL_PATH")
        if not model_path or not os.path.exists(model_path):
            return False, "LLAMA_CPP_MODEL_PATH not set or model file not found", {}
            
        return True, "llama.cpp available", {
            "model_path": model_path
        }
    
    def generate(self, 
                 prompt: str, 
                 system: Optional[str] = None,
                 temperature: Optional[float] = None,
                 max_tokens: Optional[int] = None,
                 stream: bool = False) -> Any:
        """Generate text from prompt"""
        
        # Use caching for non-streaming requests
        if not stream:
            cache_key = self._get_cache_key(prompt, system, temperature=temperature)
            cached_result = self.cache.get(cache_key)
            if cached_result:
                return cached_result
        
        # Generate response based on provider
        try:
            if self.config.provider == "ollama":
                result = self._generate_ollama(prompt, system, temperature, max_tokens, stream)
            elif self.config.provider == "gpt4all":
                result = self._generate_gpt4all(prompt, system, temperature, max_tokens, stream)
            elif self.config.provider == "llama_cpp":
                result = self._generate_llama_cpp(prompt, system, temperature, max_tokens, stream)
            else:
                raise ValueError(f"Unsupported provider: {self.config.provider}")
            
            # Cache non-streaming results
            if not stream and result:
                self.cache.set(cache_key, result)
                
            return result
            
        except Exception as e:
            logger.error(f"Generation failed with {self.config.provider}: {e}")
            # Return graceful fallback
            return {"error": str(e), "text": f"[LLM Error: {e}]"}
    
    def _generate_ollama(self, prompt: str, system: Optional[str], temperature: Optional[float], 
                        max_tokens: Optional[int], stream: bool) -> Any:
        """Generate using Ollama"""
        if not ollama:
            raise RuntimeError("ollama package not available")
            
        client = ollama.Client(host=self.config.host)
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        options = {
            "temperature": temperature or self.config.temperature
        }
        if max_tokens:
            options["num_predict"] = max_tokens
            
        if stream:
            return client.chat(
                model=self.config.model,
                messages=messages,
                stream=True,
                options=options
            )
        else:
            response = client.chat(
                model=self.config.model,
                messages=messages,
                stream=False,
                options=options
            )
            return {"text": response["message"]["content"]}
    
    def _generate_gpt4all(self, prompt: str, system: Optional[str], temperature: Optional[float],
                         max_tokens: Optional[int], stream: bool) -> Any:
        """Generate using GPT4All"""
        if not gpt4all:
            raise RuntimeError("gpt4all package not available")
            
        # Initialize model on first use
        if not self._llm_instance:
            model_name = self.config.model or "mistral-7b-instruct-v0.1.Q4_0.gguf"
            self._llm_instance = gpt4all.GPT4All(model_name)
        
        # Build prompt with system message
        full_prompt = prompt
        if system:
            full_prompt = f"System: {system}\n\nUser: {prompt}\n\nAssistant:"
        
        if stream:
            # GPT4All doesn't support streaming in the same way, simulate it
            def stream_generator():
                response = self._llm_instance.generate(
                    full_prompt, 
                    temp=temperature or self.config.temperature,
                    max_tokens=max_tokens or self.config.max_tokens
                )
                yield {"message": {"content": response}}
            return stream_generator()
        else:
            response = self._llm_instance.generate(
                full_prompt,
                temp=temperature or self.config.temperature, 
                max_tokens=max_tokens or self.config.max_tokens
            )
            return {"text": response}
    
    def _generate_llama_cpp(self, prompt: str, system: Optional[str], temperature: Optional[float],
                           max_tokens: Optional[int], stream: bool) -> Any:
        """Generate using llama.cpp"""
        if not llama_cpp:
            raise RuntimeError("llama-cpp-python package not available")
            
        model_path = os.getenv("LLAMA_CPP_MODEL_PATH")
        if not model_path:
            raise RuntimeError("LLAMA_CPP_MODEL_PATH environment variable not set")
            
        # Initialize model on first use
        if not self._llm_instance:
            self._llm_instance = llama_cpp.Llama(model_path=model_path)
        
        # Build prompt with system message
        full_prompt = prompt
        if system:
            full_prompt = f"System: {system}\n\nUser: {prompt}\n\nAssistant:"
            
        if stream:
            return self._llm_instance(
                full_prompt,
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens,
                stream=True
            )
        else:
            response = self._llm_instance(
                full_prompt,
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens,
                stream=False
            )
            return {"text": response["choices"][0]["text"]}
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts"""
        try:
            if self.config.provider == "ollama" and ollama:
                return self._embed_ollama(texts)
            else:
                return self._embed_sentence_transformers(texts)
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            # Return zero vectors as fallback
            return [[0.0] * 384 for _ in texts]
    
    def _embed_ollama(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Ollama"""
        client = ollama.Client(host=self.config.host)
        embeddings = []
        
        for text in texts:
            try:
                response = client.embeddings(
                    model=self.config.embedding_model or "nomic-embed-text",
                    prompt=text
                )
                embeddings.append(response["embedding"])
            except Exception as e:
                logger.warning(f"Ollama embedding failed for text, using fallback: {e}")
                embeddings.append([0.0] * 384)  # Fallback zero vector
                
        return embeddings
    
    def _embed_sentence_transformers(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using sentence-transformers"""
        if not SentenceTransformer:
            raise RuntimeError("sentence-transformers package not available")
            
        # Initialize embedding model on first use
        if not self._embedding_model:
            model_name = self.config.embedding_model or "all-MiniLM-L6-v2"
            self._embedding_model = SentenceTransformer(model_name)
        
        embeddings = self._embedding_model.encode(texts)
        return embeddings.tolist()


# Global instance for easy access
_local_llm_instance = None

def get_local_llm() -> LocalLLM:
    """Get or create the global LocalLLM instance"""
    global _local_llm_instance
    if _local_llm_instance is None:
        _local_llm_instance = LocalLLM()
    return _local_llm_instance