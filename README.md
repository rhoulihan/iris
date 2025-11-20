# IRIS - Intelligent Recommendation and Inference System

Oracle Enterprise Manager plugin with AI-powered schema optimization for Oracle 26ai databases.

[![Test Coverage](https://img.shields.io/badge/coverage-0%25-red)]()
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)]()
[![Oracle](https://img.shields.io/badge/oracle-26ai-red.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()

---

## 🎯 Project Vision

IRIS combines **local LLM analysis** (Qwen 2.5 Coder - 82% SQL accuracy) with **reinforcement learning** (DS-DDPG) to deliver intelligent schema optimization recommendations for Oracle 26ai databases, achieving **60%+ performance improvements** while maintaining ACID guarantees.

**Key Innovation**: Unlike traditional rule-based advisors, IRIS understands the semantic meaning of queries through LLM analysis, learns optimal configurations through RL feedback loops, and adapts recommendations to Oracle 26ai's unique hybrid relational-document architecture.

---

## 🚀 Quick Start

### Prerequisites
- WSL Ubuntu (or Linux)
- Docker & Docker Compose
- Python 3.10+
- 10GB RAM, 50GB disk space

### Start Development Environment

```bash
# Start all services (Oracle 26ai, MinIO, Redis, MLflow)
./scripts/start-dev.sh

# Activate Python environment
source venv/bin/activate

# Run tests
pytest tests/ -v

# Stop environment
./scripts/stop-dev.sh
```

### Service Access

| Service | URL | Credentials |
|---------|-----|-------------|
| **Oracle Database** | `localhost:1524/FREEPDB1` | `iris_user / IrisUser123!` |
| **EM Express** | https://localhost:5503/em | `sys / IrisDev123!` (as SYSDBA) |
| **MinIO Console** | http://localhost:9001 | `iris-admin / IrisMinIO123!` |
| **MLflow UI** | http://localhost:5000 | - |
| **Redis** | `localhost:6379` | - |

---

## 📚 Documentation

### Core Documentation
- **[IRIS.md](docs/IRIS.md)** - Complete project specification and architecture
- **[CLAUDE.md](docs/CLAUDE.md)** - Development persona and TDD standards
- **[Phase 1 Plan](docs/PHASE_1_PLAN.md)** - Current implementation plan (Weeks 1-4)
- **[Dev Environment Setup](docs/DEV_ENVIRONMENT_PLAN.md)** - Detailed setup guide

### Quick Links
- [Test-Driven Development Workflow](#tdd-workflow)
- [Contributing Guidelines](#contributing)
- [Architecture Overview](#architecture)
- [Technology Stack](#technology-stack)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Oracle EM Plugin (Java)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ UI Components│  │ AWR Collector│  │  Orchestrator │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                               │
                    REST/gRPC  │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ML Services (Python)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ LLM Inference│  │ RL Optimizer │  │Feature Engine│          │
│  │ (Qwen 2.5)   │  │  (DS-DDPG)   │  │   (Q2V)      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data Layer                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │Oracle 26ai DB│  │ Feature Store│  │Object Storage│          │
│  │(AWR, Duality)│  │(Redis/TT/FS) │  │  (MinIO/OCI) │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

**Hybrid Microservices**: Java EM plugin handles UI and orchestration; Python services handle ML inference. Independent scaling reduces infrastructure costs 40-60%.

---

## 🧪 TDD Workflow

IRIS follows strict **Test-Driven Development** with 80%+ coverage target.

### Red-Green-Refactor Cycle

```bash
# 1. RED: Write failing test
cat > tests/unit/test_feature.py << 'EOF'
def test_new_feature():
    result = new_feature()
    assert result == expected_value
EOF

# 2. Run test (should fail)
pytest tests/unit/test_feature.py -v

# 3. GREEN: Implement minimal code to pass
# Edit src/module/feature.py

# 4. Run test again (should pass)
pytest tests/unit/test_feature.py -v

# 5. REFACTOR: Improve code quality
# Refactor while keeping tests green

# 6. Verify coverage
pytest tests/ --cov=src --cov-report=html
```

### Test Coverage Requirements
- **Unit Tests**: 80%+ coverage
- **Integration Tests**: All critical paths
- **Data Tests**: Great Expectations for all inputs
- **ML Tests**: Model performance, invariance, pipeline

---

## 🛠️ Technology Stack

### Databases
- Oracle Database Free 26ai (JSON Duality Views, AWR, AQ)
- Oracle TimesTen In-Memory Database XE 22c (optional)
- Redis 7 (development cache)

### Machine Learning
- **LLM**: Qwen 2.5 Coder (7B/14B) - 82% SQL accuracy
- **RL**: DS-DDPG (Double-State Deep Deterministic Policy Gradient)
- **Frameworks**: PyTorch, Transformers, Stable-Baselines3
- **MLOps**: MLflow, TorchServe, vLLM

### Backend
- **Python**: 3.10+ (FastAPI, pytest, pandas, numpy)
- **Java**: 21+ (Spring Boot, Maven, JUnit 5)

### Infrastructure
- Docker & Docker Compose
- Kubernetes (production)
- MinIO (S3-compatible storage)
- Prometheus & Grafana (monitoring)

---

## 📊 Project Status

**Current Phase**: Phase 1 - Foundation (Weeks 1-4)

**Completed**:
- ✅ Development environment setup
- ✅ Docker infrastructure (Oracle, MinIO, Redis, MLflow)
- ✅ Storage and cache abstraction layers
- ✅ Project structure and Git repository
- ✅ Documentation framework

**In Progress**:
- 🔄 Pre-commit hooks setup
- 🔄 AWR data collector module (TDD)
- 🔄 CI/CD pipeline (GitHub Actions)

**Next Up**:
- ⏳ Query parser and template extraction
- ⏳ Workload compression (ISUM algorithm)
- ⏳ Feature engineering pipeline
- ⏳ Feature store implementation

**Timeline**: 20 weeks to production (target: April 2026)

---

## 🤝 Contributing

### Development Setup

```bash
# 1. Clone repository
git clone <repository-url>
cd iris

# 2. Start Docker services
./scripts/start-dev.sh

# 3. Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Install pre-commit hooks
pre-commit install

# 5. Run tests
pytest tests/ -v --cov=src
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

### Pull Request Process

1. Create feature branch: `git checkout -b feature/your-feature`
2. Write tests first (TDD)
3. Implement feature to pass tests
4. Ensure 80%+ test coverage
5. Run pre-commit hooks: `pre-commit run --all-files`
6. Submit PR with:
   - Clear description
   - Test coverage report
   - Documentation updates

---

## 📈 Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| **Recommendation Latency** | < 100ms (p95) | - |
| **Model Accuracy** | > 85% | - |
| **Test Coverage** | > 80% | 0% |
| **Uptime** | > 99.9% | - |
| **Performance Improvement** | > 60% | - |

---

## 🎓 Learning Resources

### Oracle 26ai
- [JSON Duality Views Documentation](https://docs.oracle.com/en/database/oracle/oracle-database/23/jsnvu/)
- [AWR Best Practices](https://docs.oracle.com/en/database/oracle/oracle-database/23/tgdba/automatic-performance-diagnostics.html)
- [EM Plugin Development Guide](https://docs.oracle.com/en/enterprise-manager/)

### Machine Learning
- [Qwen 2.5 Coder](https://github.com/QwenLM/Qwen2.5-Coder)
- [DS-DDPG Paper](https://arxiv.org/abs/2103.16186)
- [MLOps Best Practices](https://ml-ops.org/)

### Test-Driven Development
- [Python TDD with pytest](https://testdriven.io/blog/modern-tdd/)
- [Testing ML Systems](https://madewithml.com/courses/mlops/testing/)

---

## 📄 License

[Your License Here]

---

## 📧 Contact

- **Project Lead**: [Your Name]
- **Team**: IRIS Development Team
- **Repository**: [GitHub URL]
- **Issues**: [GitHub Issues URL]

---

**Built with ❤️ using Test-Driven Development and Claude Code**

Last Updated: 2025-11-20
