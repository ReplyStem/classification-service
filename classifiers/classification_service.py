"""
Classification Orchestrator Service.

Combines Intent and Sentiment classifiers to produce a unified ClassifiedEvent.
"""

import time
from typing import Optional
import logging

from classifiers.intent_classifier import IntentClassifier
from classifiers.sentiment_classifier import SentimentClassifier
from models.events import IncomingEvent, ClassifiedEvent, IntentResult, SentimentResult


class ClassificationOrchestrator:
    """
    Orchestrates multiple classifiers to produce a unified classification result.
    
    This is the main entry point for classification - it loads models once at startup
    and provides a single `classify()` method that runs all classifiers.
    """
    
    _instance: Optional["ClassificationOrchestrator"] = None
    
    def __init__(self):
        """Initialize the orchestrator with classifiers."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self._intent_classifier = IntentClassifier()
        self._sentiment_classifier = SentimentClassifier()
        self._is_ready = False
    
    @classmethod
    def get_instance(cls) -> "ClassificationOrchestrator":
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def load_models(self) -> None:
        """
        Load all models into memory.
        
        This should be called once at application startup.
        """
        self.logger.info("Loading all classification models...")
        
        self._intent_classifier.load()
        self._sentiment_classifier.load()
        
        self._is_ready = True
        self.logger.info("All models loaded. Orchestrator is ready.")
    
    @property
    def is_ready(self) -> bool:
        """Check if all models are loaded and ready."""
        return self._is_ready
    
    def classify(self, event: IncomingEvent) -> ClassifiedEvent:
        """
        Classify an incoming event.
        
        Args:
            event: The incoming event to classify
            
        Returns:
            ClassifiedEvent with intent and sentiment results
            
        Raises:
            RuntimeError: If models are not loaded
        """
        if not self._is_ready:
            raise RuntimeError("Models not loaded. Call load_models() first.")
        
        start_time = time.perf_counter()
        
        text = event.text
        
        # Run intent classification
        self.logger.debug(f"Classifying intent for event {event.event_id}")
        intent_result = self._intent_classifier.classify(text)
        
        # Run sentiment analysis
        self.logger.debug(f"Classifying sentiment for event {event.event_id}")
        sentiment_result = self._sentiment_classifier.classify(text)
        
        # Calculate processing time
        processing_time_ms = (time.perf_counter() - start_time) * 1000
        
        # Build result objects
        intent = IntentResult(
            intent=intent_result["intent"],
            sub_intent=intent_result.get("sub_intent"),
            confidence=intent_result["confidence"],
            alternatives=intent_result.get("alternatives", [])
        )
        
        sentiment = SentimentResult(
            label=sentiment_result["label"],
            score=sentiment_result["score"],
            confidence=sentiment_result["confidence"],
            all_scores=sentiment_result["all_scores"]
        )
        
        # Create classified event
        classified_event = ClassifiedEvent(
            event_id=event.event_id,
            tenant_id=event.tenant_id,
            text=event.text,
            channel=event.channel,
            timestamp=event.timestamp,
            intent=intent,
            sentiment=sentiment,
            processing_time_ms=round(processing_time_ms, 2)
        )
        
        self.logger.info(
            f"Classified event {event.event_id}: "
            f"intent={intent.intent}, sentiment={sentiment.label}, "
            f"time={processing_time_ms:.2f}ms"
        )
        
        return classified_event
