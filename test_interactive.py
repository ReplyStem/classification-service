#!/usr/bin/env python3
"""
Interactive Classification Test.

Run this to interactively test classification without the full service.
Loads models once and lets you test multiple texts.

Usage:
    python test_interactive.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variable for settings
os.environ.setdefault("JWT_SECRET", "test-secret")

from datetime import datetime
from models.events import IncomingEvent, EventHeaders
from classifiers.classification_service import ClassificationOrchestrator
from utils.logger import setup_logger


def main():
    """Interactive classification test."""
    # Setup
    logger = setup_logger("interactive_test")
    
    print("=" * 60)
    print("🧪 Interactive Classification Test")
    print("=" * 60)
    print("\nLoading models (this may take a minute on first run)...")
    
    # Load models
    orchestrator = ClassificationOrchestrator.get_instance()
    orchestrator.load_models()
    
    print("\n✅ Models loaded! Enter text to classify (or 'quit' to exit)\n")
    
    while True:
        try:
            text = input("📝 Enter text: ").strip()
            
            if text.lower() in ('quit', 'exit', 'q'):
                print("\n👋 Goodbye!")
                break
            
            if not text:
                print("⚠️  Please enter some text\n")
                continue
            
            # Create a mock event
            event = IncomingEvent(
                event_id=f"test_{datetime.now().strftime('%H%M%S')}",
                tenant_id="interactive_test",
                text=text,
                channel="cli",
                headers=EventHeaders(authorization="Bearer test")
            )
            
            # Classify
            start = datetime.now()
            result = orchestrator.classify(event)
            
            # Display results
            print("\n" + "─" * 60)
            print(f"🎯 INTENT: {result.intent.intent} ({result.intent.confidence:.1%})")
            if result.intent.sub_intent:
                print(f"   └─ SUB: {result.intent.sub_intent}")
            if result.intent.alternatives:
                print(f"   📊 Alternatives: {', '.join(a['intent'] for a in result.intent.alternatives[:2])}")
            
            print(f"💭 SENTIMENT: {result.sentiment.label.upper()} (score: {result.sentiment.score:+.2f})")
            print(f"   📊 Scores: {result.sentiment.all_scores}")
            
            print(f"⏱️  Time: {result.processing_time_ms:.0f}ms")
            print("─" * 60 + "\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()
