"""
Classification Worker.

Polls the queue and processes events through the classification pipeline.
"""

import logging
from typing import Optional

from auth.jwt_handler import JWTHandler, JWTError
from classifiers.classification_service import ClassificationOrchestrator
from models.events import IncomingEvent, ClassifiedEvent
from message_queue.mock_queue import MockQueue


class ClassificationWorker:
    """
    Worker that processes events from the queue.
    
    Responsibilities:
    1. Poll events from the queue
    2. Validate JWT tokens
    3. Run classification
    4. Log results (in production, would publish to output queue)
    """
    
    def __init__(
        self,
        queue: MockQueue,
        orchestrator: ClassificationOrchestrator,
        jwt_handler: JWTHandler
    ):
        """
        Initialize the worker.
        
        Args:
            queue: Message queue to poll from
            orchestrator: Classification orchestrator
            jwt_handler: JWT verification handler
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self._queue = queue
        self._orchestrator = orchestrator
        self._jwt_handler = jwt_handler
        
        self._processed_count = 0
        self._error_count = 0
    
    def process_event(self, event: IncomingEvent) -> Optional[ClassifiedEvent]:
        """
        Process a single event.
        
        Args:
            event: The event to process
            
        Returns:
            ClassifiedEvent if successful, None if failed
        """
        try:
            # Step 1: Validate JWT
            token = event.headers.get_token()
            try:
                payload = self._jwt_handler.verify_token(token)
                self.logger.debug(f"JWT valid for tenant: {payload.get('tenant_id')}")
            except JWTError as e:
                self.logger.warning(f"JWT validation failed for event {event.event_id}: {e}")
                self._error_count += 1
                return None
            
            # Step 2: Classify
            classified_event = self._orchestrator.classify(event)
            
            # Step 3: Log result (in production, would publish to output queue)
            self._log_classified_event(classified_event)
            
            self._processed_count += 1
            return classified_event
            
        except Exception as e:
            self.logger.error(f"Error processing event {event.event_id}: {e}", exc_info=True)
            self._error_count += 1
            return None
    
    def _log_classified_event(self, event: ClassifiedEvent) -> None:
        """Log the classified event in structured format."""
        # Log a separator for visibility
        self.logger.info("─" * 80)
        self.logger.info(f"📝 TEXT: {event.text[:100]}{'...' if len(event.text) > 100 else ''}")
        self.logger.info(
            f"🎯 INTENT: {event.intent.intent} "
            f"(confidence: {event.intent.confidence:.2%})"
        )
        if event.intent.sub_intent:
            self.logger.info(f"   └─ SUB-INTENT: {event.intent.sub_intent}")
        self.logger.info(
            f"💭 SENTIMENT: {event.sentiment.label.upper()} "
            f"(score: {event.sentiment.score:+.2f}, confidence: {event.sentiment.confidence:.2%})"
        )
        self.logger.info(
            f"📊 META: event_id={event.event_id} | tenant={event.tenant_id} | "
            f"channel={event.channel} | time={event.processing_time_ms:.0f}ms"
        )
    
    def run(self) -> None:
        """
        Run the worker loop.
        
        Polls events until the queue is empty.
        """
        self.logger.info("Classification worker started")
        
        while True:
            event = self._queue.poll()
            if event is None:
                self.logger.info(
                    f"Queue empty. Worker finished. "
                    f"Processed: {self._processed_count}, Errors: {self._error_count}"
                )
                break
            
            self.process_event(event)
        
        self.logger.info("Classification worker stopped")
    
    @property
    def stats(self) -> dict:
        """Get worker statistics."""
        return {
            "processed": self._processed_count,
            "errors": self._error_count,
            "remaining": self._queue.remaining()
        }
