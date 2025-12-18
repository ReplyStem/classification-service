"""
Mock Queue for Development and Testing.

Simulates a message queue (like Kafka or SQS) for development.
In production, replace with actual queue consumer.
"""

from typing import List, Optional
from datetime import datetime
import logging
import jwt

from models.events import IncomingEvent, EventHeaders


class MockQueue:
    """
    Mock message queue for testing.
    
    Pre-populated with sample events that simulate real-world scenarios.
    """
    
    def __init__(self, jwt_secret: str = "your-super-secret-key-here"):
        """
        Initialize the mock queue.
        
        Args:
            jwt_secret: Secret for generating test JWTs
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self._jwt_secret = jwt_secret
        self._events: List[IncomingEvent] = []
        self._index = 0
        
        # Pre-populate with sample events
        self._populate_sample_events()
    
    def _generate_token(self, tenant_id: str) -> str:
        """Generate a valid JWT for testing."""
        payload = {
            "sub": tenant_id,
            "tenant_id": tenant_id,
            "iat": datetime.utcnow().timestamp(),
            "exp": datetime.utcnow().timestamp() + 86400  # 24 hours
        }
        return jwt.encode(payload, self._jwt_secret, algorithm="HS256")
    
    def _populate_sample_events(self) -> None:
        """Add sample events to the queue."""
        sample_texts = [
            # User Questions
            ("How do I reset my password?", "tenant_001", "instagram"),
            ("What are your business hours?", "tenant_001", "whatsapp"),
            
            # Feature Requests
            ("It would be great if you added dark mode!", "tenant_002", "twitter"),
            ("Can you add Apple Pay support?", "tenant_001", "instagram"),
            
            # Feedback - Positive
            ("I love your new app update! So much cleaner.", "tenant_001", "facebook"),
            ("Great customer service, thank you!", "tenant_002", "whatsapp"),
            
            # Feedback - Complaint
            ("The app is so slow and laggy, I hate it.", "tenant_001", "instagram"),
            ("Been waiting 2 weeks for my order. Terrible service.", "tenant_002", "twitter"),
            
            # Bug Reports - High Priority
            ("URGENT: Payment system is completely down!", "tenant_001", "whatsapp"),
            ("The checkout keeps crashing. Can't complete any orders!", "tenant_002", "instagram"),
            
            # Bug Reports - Low Priority
            ("There's a typo on the about page.", "tenant_001", "twitter"),
            ("The logo looks slightly blurry on mobile.", "tenant_002", "facebook"),
            
            # Mixed/Ambiguous
            ("Found a glitch but overall loving the new version.", "tenant_001", "instagram"),
            ("When will you fix the login issues? Also, love the new design.", "tenant_002", "twitter"),
        ]
        
        for idx, (text, tenant_id, channel) in enumerate(sample_texts):
            token = self._generate_token(tenant_id)
            event = IncomingEvent(
                event_id=f"evt_{idx:04d}",
                tenant_id=tenant_id,
                text=text,
                channel=channel,
                timestamp=datetime.utcnow(),
                headers=EventHeaders(authorization=f"Bearer {token}"),
                metadata={"source": "mock_queue", "sequence": idx}
            )
            self._events.append(event)
        
        self.logger.info(f"Mock queue populated with {len(self._events)} events")
    
    def poll(self) -> Optional[IncomingEvent]:
        """
        Poll for the next event.
        
        Returns:
            Next event or None if queue is empty
        """
        if self._index >= len(self._events):
            return None
        
        event = self._events[self._index]
        self._index += 1
        self.logger.debug(f"Polled event {event.event_id} from queue")
        return event
    
    def remaining(self) -> int:
        """Get number of remaining events in queue."""
        return len(self._events) - self._index
    
    def reset(self) -> None:
        """Reset queue to start from beginning."""
        self._index = 0
        self.logger.info("Queue reset to beginning")
