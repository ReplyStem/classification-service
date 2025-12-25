"""
Intent Classifier using DistilBERT Zero-Shot Classification.

Uses hierarchical classification: first top-level intent, then sub-intent if applicable.
"""

from typing import Any, Dict, List, Optional
import torch
from transformers import pipeline

from classifiers.base import BaseClassifier
from config.settings import INTENT_LABELS, get_settings


class IntentClassifier(BaseClassifier):
    """
    Intent classifier using DistilBERT fine-tuned on MNLI.
    
    Supports hierarchical classification with top-level intents
    and sub-intents for specific categories.
    """
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the intent classifier.
        
        Args:
            model_name: HuggingFace model name (defaults to settings)
        """
        settings = get_settings()
        super().__init__(model_name or settings.INTENT_MODEL_NAME)
        self._settings = settings
        self._pipeline = None
        
        # Load labels from settings
        self._top_level_mapping = INTENT_LABELS["top_level"]
        self._sub_intent_mapping = INTENT_LABELS["sub_intents"]
    
    def _load_model(self) -> None:
        """Load the zero-shot classification pipeline."""
        self._pipeline = pipeline(
            "zero-shot-classification",
            model=self.model_name,
            device="mps" if torch.backends.mps.is_available() else (
                "cuda" if torch.cuda.is_available() else "cpu"
            ),
            model_kwargs={"low_cpu_mem_usage": True}
        )
        
        # Clone parameters to fix potential mmap issues on macOS
        # if hasattr(self._pipeline.model, 'parameters'):
        #     for param in self._pipeline.model.parameters():
        #         param.data = param.data.clone()
        
        self.model = self._pipeline
    
    def classify(self, text: str) -> Dict[str, Any]:
        """
        Classify text into intent hierarchy.
        
        Args:
            text: Input text to classify
            
        Returns:
            Dictionary with intent, sub_intent, confidence, and alternatives
        """
        self.ensure_loaded()
        
        # Step 1: Top-level classification
        top_labels = list(self._top_level_mapping.keys())
        top_result = self._pipeline(
            text,
            top_labels,
            hypothesis_template="The user is {}."
        )
        
        # Map model labels to display labels
        top_intent_model = top_result['labels'][0]
        top_intent = self._top_level_mapping[top_intent_model]
        top_confidence = top_result['scores'][0]
        
        # Build alternatives
        alternatives = []
        for i, (label, score) in enumerate(zip(top_result['labels'][1:], top_result['scores'][1:])):
            if i >= self._settings.TOP_K_ALTERNATIVES - 1:
                break
            alternatives.append({
                "intent": self._top_level_mapping[label],
                "confidence": round(score, 4)
            })
        
        result = {
            "intent": top_intent,
            "sub_intent": None,
            "confidence": round(top_confidence, 4),
            "alternatives": alternatives
        }
        
        # Step 2: Sub-intent classification if applicable
        if top_intent in self._sub_intent_mapping:
            sub_mapping = self._sub_intent_mapping[top_intent]
            sub_labels = list(sub_mapping.keys())
            
            sub_result = self._pipeline(
                text,
                sub_labels,
                hypothesis_template="The user is {}."
            )
            
            sub_intent_model = sub_result['labels'][0]
            sub_intent = sub_mapping[sub_intent_model]
            sub_confidence = sub_result['scores'][0]
            
            result["sub_intent"] = sub_intent
            result["sub_confidence"] = round(sub_confidence, 4)
            
            # Add sub-intent alternatives
            sub_alternatives = []
            for label, score in zip(sub_result['labels'][1:], sub_result['scores'][1:]):
                sub_alternatives.append({
                    "sub_intent": sub_mapping[label],
                    "confidence": round(score, 4)
                })
            result["sub_alternatives"] = sub_alternatives
        
        return result
