#!/usr/bin/env python3
"""
Test Event Publisher.

Use this script to publish test events to the classification service.
The service must be running for this to work.

Usage:
    python test_publish.py                    # Publish default test events
    python test_publish.py "Your custom text" # Publish custom text
"""

import sys
import os
import json
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import jwt


def generate_token(tenant_id: str, secret: str = "your-super-secret-key-here") -> str:
    """Generate a valid JWT token for testing."""
    payload = {
        "sub": tenant_id,
        "tenant_id": tenant_id,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def create_test_event(text: str, tenant_id: str = "test_tenant", channel: str = "test") -> dict:
    """Create a test event payload."""
    token = generate_token(tenant_id)
    
    return {
        "event_id": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "tenant_id": tenant_id,
        "text": text,
        "channel": channel,
        "timestamp": datetime.utcnow().isoformat(),
        "headers": {
            "authorization": f"Bearer {token}"
        },
        "metadata": {
            "source": "test_publisher"
        }
    }


# Sample test cases covering different intents and sentiments
DEFAULT_TEST_CASES = [
    # User Questions
    ("How do I change my password?", "User question expected"),
    ("What are your refund policies?", "User question expected"),
    
    # Feature Requests
    ("Please add dark mode to the app", "Feature Request expected"),
    ("It would be great if you supported Apple Pay", "Feature Request expected"),
    
    # Feedback - Positive
    ("Amazing product! I love everything about it!", "Positive feedback expected"),
    ("Your customer support team is fantastic", "Positive feedback expected"),
    
    # Feedback - Negative/Complaint
    ("This is the worst service I've ever used", "Negative feedback/Complaint expected"),
    ("I've been waiting 3 weeks for my order, this is unacceptable", "Complaint expected"),
    
    # Bug Reports - High Priority
    ("CRITICAL: The entire checkout system is down!", "High priority bug expected"),
    ("Payment processing is completely broken, losing money!", "High priority bug expected"),
    
    # Bug Reports - Low Priority
    ("There's a small typo on the settings page", "Low priority bug expected"),
    ("The logo looks a bit blurry on retina displays", "Low priority bug expected"),
    
    # Mixed/Complex
    ("Found a bug but overall loving the new update!", "Mixed sentiment"),
    ("When will you fix login? Also great new design", "Question + positive feedback"),
]


def main():
    """Main entry point."""
    print("=" * 60)
    print("Classification Service - Test Event Publisher")
    print("=" * 60)
    
    # Check if custom text provided
    if len(sys.argv) > 1:
        custom_text = " ".join(sys.argv[1:])
        events = [(custom_text, "Custom input")]
    else:
        events = DEFAULT_TEST_CASES
    
    print(f"\n📤 Generating {len(events)} test event(s)...\n")
    
    for text, description in events:
        event = create_test_event(text)
        print(f"─" * 60)
        print(f"📝 Text: {text[:60]}{'...' if len(text) > 60 else ''}")
        print(f"💡 Expected: {description}")
        print(f"🔑 Event ID: {event['event_id']}")
        print()
    
    print("=" * 60)
    print("\n✅ Events generated successfully!")
    print("\n📋 To use these events, you can:")
    print("   1. Add them to the MockQueue in message_queue/mock_queue.py")
    print("   2. Or implement a real queue (Kafka/SQS) and publish there")
    print("\n💡 TIP: The MockQueue is pre-populated with similar test cases.")
    print("        Just restart the service to process them again:")
    print("        docker compose restart")
    print()
    
    # Print sample JSON for one event
    sample = create_test_event("Sample text for API")
    print("📄 Sample Event JSON (for API integration):")
    print(json.dumps(sample, indent=2, default=str))


if __name__ == "__main__":
    main()
