"""
Base Classifier Abstract Class.

Defines the interface that all classifiers must implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging


class BaseClassifier(ABC):
    """
    Abstract base class for all classifiers.
    
    Provides a consistent interface for loading models and classifying text.
    Subclasses must implement `_load_model()` and `classify()`.
    """
    
    def __init__(self, model_name: str):
        """
        Initialize the classifier.
        
        Args:
            model_name: HuggingFace model name or path
        """
        self.model_name = model_name
        self.model = None
        self.is_loaded = False
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def load(self) -> None:
        """
        Load the model into memory.
        
        This should be called once at startup.
        """
        if self.is_loaded:
            self.logger.warning(f"Model {self.model_name} already loaded, skipping.")
            return
        
        self.logger.info(f"Loading model: {self.model_name}...")
        self._load_model()
        self.is_loaded = True
        self.logger.info(f"Model {self.model_name} loaded successfully.")
    
    @abstractmethod
    def _load_model(self) -> None:
        """
        Implementation-specific model loading.
        
        Must be implemented by subclasses.
        """
        pass
    
    @abstractmethod
    def classify(self, text: str) -> Dict[str, Any]:
        """
        Classify the given text.
        
        Args:
            text: Input text to classify
            
        Returns:
            Classification result as a dictionary
        """
        pass
    
    def ensure_loaded(self) -> None:
        """Ensure the model is loaded before classification."""
        if not self.is_loaded:
            self.load()
