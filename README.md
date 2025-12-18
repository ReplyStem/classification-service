# Classification Microservice

A modular, OOP-based Python microservice for **Intent Classification** and **Sentiment Analysis**.

## Features

- **Intent Classification**: Hierarchical classification using DistilBERT (zero-shot)
  - Top-level: User Question, Feedback, Bug Report, Feature Request
  - Sub-intents: P0/P1/P2 for bugs, Positive/Negative/Neutral for feedback
  
- **Sentiment Analysis**: Multi-language support using XLM-RoBERTa (Twitter-trained)

- **JWT Authentication**: Token validation on every event

- **Structured Logging**: File + console output with file-level tracking

- **Health Endpoints**: `/health` and `/ready` for Kubernetes probes

## Quick Start

### 1. Setup Environment

```bash
cd classification_service

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env and set JWT_SECRET
```

### 2. Generate a Test JWT Token

```python
import jwt
from datetime import datetime, timedelta

secret = "your-super-secret-key-here"  # Same as JWT_SECRET in .env
payload = {
    "sub": "tenant_123",
    "tenant_id": "tenant_123",
    "iat": datetime.utcnow(),
    "exp": datetime.utcnow() + timedelta(hours=24)
}
token = jwt.encode(payload, secret, algorithm="HS256")
print(f"Bearer {token}")
```

### 3. Run the Service

```bash
python main.py
```

### 4. Check Health

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

## Project Structure

```
classification_service/
├── api/                    # FastAPI endpoints
│   └── health.py           # Health/readiness probes
├── auth/                   # Authentication
│   └── jwt_handler.py      # JWT verification
├── classifiers/            # ML classifiers
│   ├── base.py             # Abstract base class
│   ├── intent_classifier.py
│   ├── sentiment_classifier.py
│   └── classification_service.py  # Orchestrator
├── config/                 # Configuration
│   └── settings.py         # Pydantic settings
├── models/                 # Pydantic models
│   └── events.py           # Event schemas
├── queue/                  # Message queue
│   └── mock_queue.py       # Mock for testing
├── utils/                  # Utilities
│   └── logger.py           # Structured logging
├── workers/                # Background workers
│   └── classification_worker.py
├── main.py                 # Entry point
├── requirements.txt
└── .env.example
```

## Configuration

All settings are loaded from environment variables (see `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `JWT_SECRET` | Secret for JWT verification | *required* |
| `LOG_LEVEL` | Logging level | `INFO` |
| `LOG_FILE` | Log file path | `logs/classification_service.log` |
| `INTENT_CONFIDENCE_THRESHOLD` | Min confidence for intent | `0.5` |
| `SENTIMENT_CONFIDENCE_THRESHOLD` | Min confidence for sentiment | `0.5` |
| `API_PORT` | Health API port | `8000` |

## Output Format

The service logs classified events in this format:

```
CLASSIFIED | event_id=evt_0001 | tenant=tenant_001 | channel=instagram 
           | intent=Bug Report | sub_intent=High Priority (P0) 
           | intent_conf=0.8725 | sentiment=negative | sentiment_score=-0.8456 
           | time_ms=145.32
```

## Extending

### Adding a New Classifier

1. Create a new file in `classifiers/`
2. Extend `BaseClassifier`
3. Implement `_load_model()` and `classify()`
4. Add to `ClassificationOrchestrator`

### Replacing the Mock Queue

Replace `MockQueue` with your actual queue consumer (Kafka, SQS, etc.) by implementing the same interface:
- `poll() -> Optional[IncomingEvent]`
- `remaining() -> int`
