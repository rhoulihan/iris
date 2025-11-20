# IRIS - Intelligent Recommendation and Inference System

Oracle Enterprise Manager plugin with AI-powered schema optimization for Oracle 26ai databases.

## Quick Start

### Start Development Environment

```bash
./scripts/start-dev.sh
```

This starts:
- Oracle Database Free 26ai (port 1524)
- MinIO S3-compatible storage (ports 9000, 9001)
- Redis cache (port 6379)
- MLflow tracking server (port 5000)

### Stop Development Environment

```bash
./scripts/stop-dev.sh

# To remove all data volumes:
./scripts/stop-dev.sh --volumes
```

## Service Access

### Oracle Database
- **Host:** localhost
- **Port:** 1524
- **Service:** FREEPDB1
- **SYS Password:** IrisDev123!
- **App User:** iris_user / IrisUser123!
- **EM Express:** https://localhost:5503/em

**Connect via SQL*Plus:**
```bash
sqlplus iris_user/IrisUser123!@localhost:1524/FREEPDB1
```

### MinIO Console
- **URL:** http://localhost:9001
- **Username:** iris-admin
- **Password:** IrisMinIO123!

### MinIO S3 API
- **Endpoint:** http://localhost:9000
- **Access Key:** iris-admin
- **Secret Key:** IrisMinIO123!

### Redis
- **Host:** localhost
- **Port:** 6379

### MLflow
- **URL:** http://localhost:5000

## Development

### Activate Python Environment

```bash
source venv/bin/activate
```

### Run Tests

```bash
pytest tests/ -v
```

### Code Quality

```bash
# Format code
black src/ tests/

# Check linting
flake8 src/ tests/

# Type checking
mypy src/

# Sort imports
isort src/ tests/
```

## Project Structure

```
iris/
├── src/                    # Source code
│   └── common/            # Shared utilities
│       ├── storage_interface.py  # Object storage abstraction
│       └── cache_interface.py    # Cache abstraction
├── tests/                 # Test files
├── docker/                # Docker configuration
│   ├── docker-compose.dev.yml
│   └── init-scripts/      # Oracle initialization SQL
├── scripts/               # Management scripts
│   ├── start-dev.sh
│   └── stop-dev.sh
├── data/                  # Local data (gitignored)
├── models/                # ML models
├── notebooks/             # Jupyter notebooks
└── docs/                  # Documentation
```

## Documentation

- **[IRIS.md](IRIS.md)** - Complete project specification and architecture
- **[CLAUDE.md](CLAUDE.md)** - Development persona and standards for AI-assisted development
- **[DEV_ENVIRONMENT_PLAN.md](DEV_ENVIRONMENT_PLAN.md)** - Detailed setup plan

## Technology Stack

### Databases
- Oracle Database Free 26ai
- Oracle TimesTen In-Memory Database (optional)
- Redis (development cache)

### ML/AI
- Qwen 2.5 Coder (7B, 14B)
- PyTorch, Transformers
- Stable-Baselines3 (RL)
- MLflow

### Backend
- Python 3.12+ (FastAPI)
- Java 21+ (Spring Boot)

### Infrastructure
- Docker & Docker Compose
- Kubernetes (production)
- MinIO (S3-compatible storage)

## License

[Your License Here]

## Contact

[Your Contact Information]
