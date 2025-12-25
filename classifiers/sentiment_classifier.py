"""
Sentiment Classifier using XLM-RoBERTa.

Multi-language sentiment analysis using the Twitter-trained model.
"""

from typing import Any, Dict, Optional
import numpy as np
import torch
from scipy.special import softmax
from transformers import AutoModelForSequenceClassification, AutoTokenizer, AutoConfig

from classifiers.base import BaseClassifier
from config.settings import SENTIMENT_LABELS, get_settings


class SentimentClassifier(BaseClassifier):
    """
    Sentiment classifier using XLM-RoBERTa trained on Twitter data.
    
    Supports multiple languages and returns sentiment scores.
    """
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the sentiment classifier.
        
        Args:
            model_name: HuggingFace model name (defaults to settings)
        """
        settings = get_settings()
        super().__init__(model_name or settings.SENTIMENT_MODEL_NAME)
        self._settings = settings
        self._tokenizer = None
        self._config = None
    
    def _load_model(self) -> None:
        """Load the sentiment analysis model."""
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self._config = AutoConfig.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name, 
                                                                        dtype=torch.float16, 
                                                                        low_cpu_mem_usage=True)
        
        # Move to appropriate device
        device = "mps" if torch.backends.mps.is_available() else (
            "cuda" if torch.cuda.is_available() else "cpu"
        )
        self.model.to(device)
        
        # # Clone parameters to fix potential mmap issues on macOS
        # for param in self.model.parameters():
        #     param.data = param.data.clone()
        
        self.model.eval()
    
    @staticmethod
    def _preprocess(text: str) -> str:
        """Preprocess text for Twitter-trained model."""
        tokens = []
        for token in text.split(" "):
            if token.startswith('@') and len(token) > 1:
                token = '@user'
            elif token.startswith('http'):
                token = 'http'
            tokens.append(token)
        return " ".join(tokens)
    
    def classify(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of the given text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary with label, score, confidence, and all_scores
        """
        self.ensure_loaded()
        
        # Preprocess
        processed_text = self._preprocess(text)
        
        # Tokenize
        encoded = self._tokenizer(
            processed_text,
            return_tensors='pt',
            padding=True,
            truncation=True,
            max_length=512
        )
        
        # Move to same device as model
        device = next(self.model.parameters()).device
        encoded = {k: v.to(device) for k, v in encoded.items()}
        
        # Inference
        with torch.no_grad():
            output = self.model(**encoded)
        
        # Get scores
        logits = output.logits[0].cpu().numpy()
        scores = softmax(logits)
        
        # Build result
        ranking = np.argsort(scores)[::-1]
        top_idx = ranking[0]
        top_label = self._config.id2label[top_idx]
        top_score = float(scores[top_idx])
        
        # Convert label to lowercase for consistency
        label = top_label.lower()
        
        # Build all_scores dictionary
        all_scores = {}
        for idx, score in enumerate(scores):
            lbl = self._config.id2label[idx].lower()
            all_scores[lbl] = round(float(score), 4)
        
        # Calculate normalized score (-1 to 1) based on sentiment polarity
        # negative = -1, neutral = 0, positive = 1
        polarity_map = {"negative": -1.0, "neutral": 0.0, "positive": 1.0}
        weighted_score = sum(
            all_scores.get(lbl, 0) * polarity_map.get(lbl, 0)
            for lbl in polarity_map
        )
        
        return {
            "label": label,
            "score": round(weighted_score, 4),
            "confidence": round(top_score, 4),
            "all_scores": all_scores
        }
