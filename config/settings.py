"""
Classification Microservice Settings.

All configuration is loaded from environment variables.
Uses pydantic-settings for validation and type coercion.
"""

from typing import Dict, List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ─────────────────────────────────────────────────────────────────────────
    # JWT Authentication
    # ─────────────────────────────────────────────────────────────────────────
    JWT_SECRET: str = Field(..., description="Secret key for JWT verification")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")

    # ─────────────────────────────────────────────────────────────────────────
    # Logging
    # ─────────────────────────────────────────────────────────────────────────
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FILE: str = Field(default="logs/classification_service.log", description="Log file path")
    LOG_FORMAT: str = Field(
        default="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
        description="Log format string"
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Classification Thresholds
    # ─────────────────────────────────────────────────────────────────────────
    INTENT_CONFIDENCE_THRESHOLD: float = Field(
        default=0.5,
        description="Minimum confidence for intent classification"
    )
    SENTIMENT_CONFIDENCE_THRESHOLD: float = Field(
        default=0.5,
        description="Minimum confidence for sentiment classification"
    )
    TOP_K_ALTERNATIVES: int = Field(
        default=3,
        description="Number of alternative classifications to return"
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Model Configuration
    # ─────────────────────────────────────────────────────────────────────────
    INTENT_MODEL_NAME: str = Field(
        default="typeform/distilbert-base-uncased-mnli",
        description="HuggingFace model for intent classification"
    )
    SENTIMENT_MODEL_NAME: str = Field(
        default="cardiffnlp/twitter-xlm-roberta-base-sentiment",
        description="HuggingFace model for sentiment analysis"
    )

    # ─────────────────────────────────────────────────────────────────────────
    # API Server
    # ─────────────────────────────────────────────────────────────────────────
    API_HOST: str = Field(default="0.0.0.0", description="API server host")
    API_PORT: int = Field(default=8000, description="API server port")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# ─────────────────────────────────────────────────────────────────────────────
# Intent Labels (fixed hierarchy, later can come from API)
# ─────────────────────────────────────────────────────────────────────────────
INTENT_LABELS = {
    "top_level": {
        # key = model-friendly label, value = display label
        "asking a question": "User question",
        "giving feedback": "Feedback",
        "reporting a bug": "Bug Report",
        "requesting a feature": "Feature Request",
    },
    "sub_intents": {
        "Feedback": {
            "happy": "Positive",
            "unhappy": "Complaint",
            "neutral": "Neutral",
        },
        "Bug Report": {
            "reporting a critical emergency": "High Priority (P0)",
            "reporting a broken feature": "Medium Priority (P1)",
            "reporting a minor issue": "Low Priority (P2)",
        },
    },
}

# Sentiment labels (from XLM-RoBERTa model)
SENTIMENT_LABELS = ["negative", "neutral", "positive"]


def get_settings() -> Settings:
    """Factory function to get settings instance."""
    return Settings()
