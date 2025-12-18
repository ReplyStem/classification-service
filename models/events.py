"""
Event Models for Classification Microservice.

Defines the structure of incoming events from the queue
and the classified output events.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class EventHeaders(BaseModel):
    """Headers attached to each event, including auth token."""
    
    authorization: str = Field(..., description="JWT Bearer token")
    content_type: str = Field(default="application/json")
    
    def get_token(self) -> str:
        """Extract token from Authorization header."""
        if self.authorization.startswith("Bearer "):
            return self.authorization[7:]
        return self.authorization


class IncomingEvent(BaseModel):
    """
    Incoming event from the message queue.
    
    This represents a normalized message from any social platform
    (Instagram, Twitter, WhatsApp, etc.) that needs classification.
    """
    
    event_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique event ID")
    tenant_id: str = Field(..., description="Tenant identifier for multi-tenancy")
    text: str = Field(..., min_length=1, description="Message text to classify")
    channel: str = Field(..., description="Source channel (instagram, twitter, whatsapp, etc.)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    headers: EventHeaders = Field(..., description="Event headers including JWT")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "tenant_id": "tenant_123",
                "text": "The app keeps crashing when I try to checkout!",
                "channel": "instagram",
                "timestamp": "2024-12-18T10:30:00Z",
                "headers": {
                    "authorization": "Bearer eyJhbGciOiJIUzI1NiIs..."
                },
                "metadata": {
                    "customer_id": "cust_456",
                    "platform_message_id": "ig_msg_789"
                }
            }
        }


class IntentResult(BaseModel):
    """Result of intent classification."""
    
    intent: str = Field(..., description="Primary classified intent")
    sub_intent: Optional[str] = Field(None, description="Sub-intent if applicable")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    alternatives: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Alternative intents with scores"
    )


class SentimentResult(BaseModel):
    """Result of sentiment analysis."""
    
    label: str = Field(..., description="Sentiment label (positive/negative/neutral)")
    score: float = Field(..., description="Sentiment score (-1 to 1 or 0 to 1)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    all_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Scores for all sentiment labels"
    )


class ClassifiedEvent(BaseModel):
    """
    Classified event output.
    
    Contains the original event data plus classification results.
    """
    
    # Original event data
    event_id: str
    tenant_id: str
    text: str
    channel: str
    timestamp: datetime
    
    # Classification results
    intent: IntentResult
    sentiment: SentimentResult
    
    # Processing metadata
    classified_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: float = Field(..., description="Time taken to classify in milliseconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "tenant_id": "tenant_123",
                "text": "The app keeps crashing when I try to checkout!",
                "channel": "instagram",
                "timestamp": "2024-12-18T10:30:00Z",
                "intent": {
                    "intent": "Bug Report",
                    "sub_intent": "High Priority (P0)",
                    "confidence": 0.87,
                    "alternatives": [
                        {"intent": "Feedback", "confidence": 0.10},
                        {"intent": "User question", "confidence": 0.03}
                    ]
                },
                "sentiment": {
                    "label": "negative",
                    "score": -0.85,
                    "confidence": 0.92,
                    "all_scores": {"negative": 0.92, "neutral": 0.05, "positive": 0.03}
                },
                "classified_at": "2024-12-18T10:30:00.150Z",
                "processing_time_ms": 150.5
            }
        }
