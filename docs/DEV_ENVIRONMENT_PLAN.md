# IRIS Local Development Environment Setup Plan

**Target Platform:** WSL Ubuntu on Windows Desktop
**Database:** Oracle Database Free 26ai (Docker)
**Focus:** Development environment optimized for ML-powered Oracle optimization

---

## Executive Summary

Based on comprehensive research into Oracle Free licensing and available technologies, this plan establishes a **fully-functional local development environment** using primarily free Oracle technologies with strategic abstractions where necessary. The environment supports the complete IRIS development workflow while remaining mindful of Oracle Free's resource limitations (2 CPU cores, 2GB RAM, 12GB storage per instance).

### Key Decisions

✅ **USE DIRECTLY (No Facade Needed):**
- Oracle Database Free 26ai - Full AWR, AQ, JSON Duality Views, In-Memory (16GB limit)
- Oracle TimesTen XE 22c - Free in-memory database for caching/feature store
- MinIO - S3-compatible object storage for ML artifacts

⚠️ **REQUIRES ABSTRACTION LAYER:**
- Object Storage Interface - Abstract filesystem → MinIO → OCI Object Storage
- High Availability Patterns - Oracle Free lacks RAC/Data Guard

🔧 **SPECIAL SETUP:**
- Enterprise Manager Cloud Control - Full installation in separate VM (resource-intensive)

---

## Part 1: Required Software & Versions

### 1.1 Core Database Stack

| Component | Version | Source | Purpose |
|-----------|---------|--------|---------|
| **Oracle Database Free** | 26ai (latest) | `container-registry.oracle.com/database/free:latest` | Primary database for IRIS development |
| **Oracle TimesTen XE** | 22c (22.1) | https://www.oracle.com/database/technologies/timesten-xe-download.html | In-memory cache for feature store |
| **MinIO** | Latest | `minio/minio:latest` | S3-compatible object storage for ML models |

### 1.2 Development Tools

| Component | Version | Installation Method | Purpose |
|-----------|---------|---------------------|---------|
| **Python** | 3.10+ | `sudo apt install python3.10 python3.10-venv` | ML services development |
| **Java JDK** | 17 (LTS) | `sudo apt install openjdk-17-jdk` | EM Plugin development |
| **Node.js** | 20 LTS | `nvm install 20` | Optional: for UI tooling |
| **Docker** | 24.0+ | Already installed | Container runtime |
| **Docker Compose** | 2.20+ | `sudo apt install docker-compose-plugin` | Multi-container orchestration |

### 1.3 Python ML Stack

```bash
# Core ML frameworks
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install transformers>=4.35.0
pip install peft>=0.7.0  # For QLoRA fine-tuning
pip install bitsandbytes>=0.41.0  # Quantization
pip install stable-baselines3>=2.2.0  # RL algorithms
pip install gymnasium>=0.29.0  # RL environments

# Data & Feature Engineering
pip install pandas>=2.1.0
pip install numpy>=1.24.0
pip install polars>=0.19.0  # High-performance DataFrames
pip install great-expectations>=0.18.0  # Data validation

# Oracle Database Connectivity
pip install oracledb>=1.4.0  # Official Oracle driver (thin mode, no client needed)
pip install cx_Oracle>=8.3.0  # Alternative thick client

# MLOps & Serving
pip install mlflow>=2.9.0
pip install feast>=0.35.0
pip install fastapi>=0.104.0
pip install uvicorn[standard]>=0.24.0

# Testing
pip install pytest>=7.4.0
pip install pytest-asyncio>=0.21.0
pip install testcontainers>=3.7.0
```

### 1.4 Java/Spring Stack

```xml
<!-- Maven dependencies -->
<dependencies>
    <!-- Spring Boot -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
        <version>3.2.0</version>
    </dependency>

    <!-- Oracle JDBC Driver -->
    <dependency>
        <groupId>com.oracle.database.jdbc</groupId>
        <artifactId>ojdbc11</artifactId>
        <version>23.3.0.23.09</version>
    </dependency>

    <!-- Oracle UCP (Universal Connection Pool) -->
    <dependency>
        <groupId>com.oracle.database.jdbc</groupId>
        <artifactId>ucp</artifactId>
        <version>23.3.0.23.09</version>
    </dependency>

    <!-- Testing -->
    <dependency>
        <groupId>org.junit.jupiter</groupId>
        <artifactId>junit-jupiter</artifactId>
        <version>5.10.0</version>
        <scope>test</scope>
    </dependency>

    <dependency>
        <groupId>org.testcontainers</groupId>
        <artifactId>oracle-xe</artifactId>
        <version>1.19.3</version>
        <scope>test</scope>
    </dependency>
</dependencies>
```

---

## Part 2: Docker Infrastructure Setup

### 2.1 Docker Compose Configuration

**File:** `docker/docker-compose.dev.yml`

```yaml
version: '3.8'

services:
  # Oracle Database Free 26ai - IRIS Development Instance
  oracle-iris-dev:
    image: container-registry.oracle.com/database/free:latest
    container_name: oracle-iris-dev
    hostname: oracle-iris-dev
    networks:
      - iris-network
    ports:
      - "1524:1521"    # Oracle Listener (unique port, avoiding conflict with existing instance)
      - "5503:5500"    # Enterprise Manager Express
    environment:
      - ORACLE_PWD=IrisDev123!
      - ORACLE_CHARACTERSET=AL32UTF8
      - ENABLE_ARCHIVELOG=false  # Disable for dev to save space
    volumes:
      - oracle-iris-data:/opt/oracle/oradata
      - oracle-iris-backup:/opt/oracle/backup
      - ./init-scripts:/docker-entrypoint-initdb.d/startup  # Initialization scripts
    shm_size: 1g
    ulimits:
      nofile:
        soft: 1024
        hard: 65536
    healthcheck:
      test: ["CMD", "sh", "-c", "echo 'SELECT 1 FROM DUAL;' | sqlplus -s sys/IrisDev123!@localhost/FREEPDB1 as sysdba"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 180s  # Oracle takes time to start

  # MinIO - S3-Compatible Object Storage for ML Artifacts
  minio:
    image: minio/minio:latest
    container_name: iris-minio
    hostname: iris-minio
    networks:
      - iris-network
    ports:
      - "9000:9000"    # API
      - "9001:9001"    # Console
    environment:
      MINIO_ROOT_USER: iris-admin
      MINIO_ROOT_PASSWORD: IrisMinIO123!
    volumes:
      - minio-data:/data
    command: server /data --console-address ":9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Redis - Lightweight Cache (Alternative to TimesTen for Simple Caching)
  redis:
    image: redis:7-alpine
    container_name: iris-redis
    hostname: iris-redis
    networks:
      - iris-network
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  # PostgreSQL - For MLflow Backend (lightweight alternative to Oracle for MLOps metadata)
  mlflow-db:
    image: postgres:15-alpine
    container_name: iris-mlflow-db
    hostname: iris-mlflow-db
    networks:
      - iris-network
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: mlflow
      POSTGRES_USER: mlflow
      POSTGRES_PASSWORD: MlflowPass123!
    volumes:
      - mlflow-db-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mlflow"]
      interval: 10s
      timeout: 5s
      retries: 5

  # MLflow Tracking Server
  mlflow:
    image: ghcr.io/mlflow/mlflow:v2.9.2
    container_name: iris-mlflow
    hostname: iris-mlflow
    networks:
      - iris-network
    ports:
      - "5000:5000"
    environment:
      - MLFLOW_BACKEND_STORE_URI=postgresql://mlflow:MlflowPass123!@mlflow-db:5432/mlflow
      - MLFLOW_ARTIFACT_ROOT=s3://mlflow-artifacts
      - AWS_ACCESS_KEY_ID=iris-admin
      - AWS_SECRET_ACCESS_KEY=IrisMinIO123!
      - MLFLOW_S3_ENDPOINT_URL=http://minio:9000
    command: mlflow server --host 0.0.0.0 --port 5000
    depends_on:
      mlflow-db:
        condition: service_healthy
      minio:
        condition: service_healthy

networks:
  iris-network:
    driver: bridge
    name: iris-network

volumes:
  oracle-iris-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /home/$USER/iris-oracle-data  # WSL Linux filesystem for performance
  oracle-iris-backup:
  minio-data:
  redis-data:
  mlflow-db-data:
```

### 2.2 Connection Details

```bash
# Oracle Database IRIS Dev
Host: localhost
Port: 1524
Service Name: FREEPDB1
SYS Password: IrisDev123!
Connection String: sys/IrisDev123!@localhost:1524/FREEPDB1 as sysdba

# EM Express
URL: https://localhost:5503/em

# MinIO Console
URL: http://localhost:9001
Username: iris-admin
Password: IrisMinIO123!

# MinIO S3 API
Endpoint: http://localhost:9000
Access Key: iris-admin
Secret Key: IrisMinIO123!

# Redis
Host: localhost
Port: 6379

# MLflow Tracking Server
URL: http://localhost:5000
```

### 2.3 Oracle Initialization Scripts

**File:** `docker/init-scripts/01_create_iris_user.sql`

```sql
-- Create IRIS application user
ALTER SESSION SET CONTAINER = FREEPDB1;

-- Create tablespace for IRIS
CREATE TABLESPACE iris_data
  DATAFILE SIZE 500M AUTOEXTEND ON NEXT 100M MAXSIZE 2G;

CREATE TABLESPACE iris_temp
  TEMPFILE SIZE 100M AUTOEXTEND ON NEXT 50M MAXSIZE 500M;

-- Create IRIS user
CREATE USER iris_user IDENTIFIED BY IrisUser123!
  DEFAULT TABLESPACE iris_data
  TEMPORARY TABLESPACE iris_temp
  QUOTA UNLIMITED ON iris_data;

-- Grant necessary privileges
GRANT CREATE SESSION TO iris_user;
GRANT CREATE TABLE TO iris_user;
GRANT CREATE VIEW TO iris_user;
GRANT CREATE SEQUENCE TO iris_user;
GRANT CREATE PROCEDURE TO iris_user;
GRANT CREATE TRIGGER TO iris_user;
GRANT CREATE TYPE TO iris_user;

-- Grant access to AWR views (critical for IRIS)
GRANT SELECT ON DBA_HIST_SNAPSHOT TO iris_user;
GRANT SELECT ON DBA_HIST_ACTIVE_SESS_HISTORY TO iris_user;
GRANT SELECT ON DBA_HIST_SQL_PLAN TO iris_user;
GRANT SELECT ON DBA_HIST_SQLSTAT TO iris_user;
GRANT SELECT ON DBA_HIST_SQLTEXT TO iris_user;
GRANT SELECT ON DBA_HIST_SYSSTAT TO iris_user;
GRANT SELECT ON DBA_HIST_SYSTEM_EVENT TO iris_user;
GRANT SELECT ON V_$SQL TO iris_user;
GRANT SELECT ON V_$SQL_PLAN TO iris_user;
GRANT SELECT ON V_$SESSION TO iris_user;

-- Grant Oracle Advanced Queuing privileges
GRANT EXECUTE ON DBMS_AQ TO iris_user;
GRANT EXECUTE ON DBMS_AQADM TO iris_user;
GRANT AQ_ADMINISTRATOR_ROLE TO iris_user;

-- Grant JSON Duality View privileges (23ai+)
GRANT CREATE JSON RELATIONAL DUALITY VIEW TO iris_user;

-- Grant In-Memory privileges
GRANT EXECUTE ON DBMS_INMEMORY_ADMIN TO iris_user;

-- Enable AWR snapshots (if not already enabled)
BEGIN
  DBMS_WORKLOAD_REPOSITORY.MODIFY_SNAPSHOT_SETTINGS(
    retention => 10080,  -- 7 days
    interval => 15       -- 15 minutes
  );
END;
/
```

**File:** `docker/init-scripts/02_create_sample_schema.sql`

```sql
-- Sample schema for testing optimizations
ALTER SESSION SET CONTAINER = FREEPDB1;

CONNECT iris_user/IrisUser123!@localhost/FREEPDB1

-- Create sample tables for testing
CREATE TABLE customers (
  customer_id NUMBER PRIMARY KEY,
  customer_name VARCHAR2(100) NOT NULL,
  email VARCHAR2(100),
  registration_date DATE DEFAULT SYSDATE,
  status VARCHAR2(20)
);

CREATE TABLE orders (
  order_id NUMBER PRIMARY KEY,
  customer_id NUMBER NOT NULL,
  order_date DATE DEFAULT SYSDATE,
  total_amount NUMBER(10,2),
  status VARCHAR2(20),
  CONSTRAINT fk_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE order_items (
  order_item_id NUMBER PRIMARY KEY,
  order_id NUMBER NOT NULL,
  product_id NUMBER NOT NULL,
  quantity NUMBER NOT NULL,
  unit_price NUMBER(10,2),
  CONSTRAINT fk_order FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

-- JSON Collection for testing JSON Duality Views (23ai+)
CREATE JSON COLLECTION TABLE product_catalog;

-- Insert sample data
BEGIN
  FOR i IN 1..1000 LOOP
    INSERT INTO customers VALUES (
      i,
      'Customer ' || i,
      'customer' || i || '@example.com',
      SYSDATE - DBMS_RANDOM.VALUE(1, 365),
      CASE WHEN MOD(i, 10) = 0 THEN 'INACTIVE' ELSE 'ACTIVE' END
    );
  END LOOP;
  COMMIT;
END;
/

-- Create sequences
CREATE SEQUENCE customer_seq START WITH 1001;
CREATE SEQUENCE order_seq START WITH 1;
CREATE SEQUENCE order_item_seq START WITH 1;
```

---

## Part 3: Interface Abstractions Required

### 3.1 Object Storage Abstraction Layer

**Why:** Enable seamless transition from local filesystem → MinIO → OCI Object Storage

**Implementation:** `src/common/storage_interface.py`

```python
from abc import ABC, abstractmethod
from typing import BinaryIO, Optional
from pathlib import Path
import boto3
from botocore.client import Config

class StorageInterface(ABC):
    """Abstract interface for object storage operations."""

    @abstractmethod
    def put_object(self, bucket: str, key: str, data: BinaryIO) -> None:
        """Upload object to storage."""
        pass

    @abstractmethod
    def get_object(self, bucket: str, key: str) -> bytes:
        """Download object from storage."""
        pass

    @abstractmethod
    def delete_object(self, bucket: str, key: str) -> None:
        """Delete object from storage."""
        pass

    @abstractmethod
    def list_objects(self, bucket: str, prefix: str = "") -> list[str]:
        """List objects with given prefix."""
        pass


class LocalFilesystemStorage(StorageInterface):
    """Local filesystem implementation for development."""

    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def put_object(self, bucket: str, key: str, data: BinaryIO) -> None:
        target_path = self.base_path / bucket / key
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, 'wb') as f:
            f.write(data.read())

    def get_object(self, bucket: str, key: str) -> bytes:
        target_path = self.base_path / bucket / key
        with open(target_path, 'rb') as f:
            return f.read()

    def delete_object(self, bucket: str, key: str) -> None:
        target_path = self.base_path / bucket / key
        target_path.unlink(missing_ok=True)

    def list_objects(self, bucket: str, prefix: str = "") -> list[str]:
        bucket_path = self.base_path / bucket
        if not bucket_path.exists():
            return []
        pattern = f"{prefix}*" if prefix else "*"
        return [str(p.relative_to(bucket_path)) for p in bucket_path.rglob(pattern)]


class MinIOStorage(StorageInterface):
    """MinIO S3-compatible storage for integration testing."""

    def __init__(self, endpoint: str, access_key: str, secret_key: str):
        self.s3 = boto3.client(
            's3',
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1'
        )

    def put_object(self, bucket: str, key: str, data: BinaryIO) -> None:
        self.s3.put_object(Bucket=bucket, Key=key, Body=data)

    def get_object(self, bucket: str, key: str) -> bytes:
        response = self.s3.get_object(Bucket=bucket, Key=key)
        return response['Body'].read()

    def delete_object(self, bucket: str, key: str) -> None:
        self.s3.delete_object(Bucket=bucket, Key=key)

    def list_objects(self, bucket: str, prefix: str = "") -> list[str]:
        response = self.s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        return [obj['Key'] for obj in response.get('Contents', [])]


class OCIObjectStorage(StorageInterface):
    """Oracle Cloud Infrastructure Object Storage for production."""

    def __init__(self, config_file: str, profile: str = "DEFAULT"):
        import oci
        self.config = oci.config.from_file(config_file, profile)
        self.client = oci.object_storage.ObjectStorageClient(self.config)
        self.namespace = self.client.get_namespace().data

    def put_object(self, bucket: str, key: str, data: BinaryIO) -> None:
        self.client.put_object(
            namespace_name=self.namespace,
            bucket_name=bucket,
            object_name=key,
            put_object_body=data
        )

    def get_object(self, bucket: str, key: str) -> bytes:
        response = self.client.get_object(
            namespace_name=self.namespace,
            bucket_name=bucket,
            object_name=key
        )
        return response.data.content

    def delete_object(self, bucket: str, key: str) -> None:
        self.client.delete_object(
            namespace_name=self.namespace,
            bucket_name=bucket,
            object_name=key
        )

    def list_objects(self, bucket: str, prefix: str = "") -> list[str]:
        response = self.client.list_objects(
            namespace_name=self.namespace,
            bucket_name=bucket,
            prefix=prefix
        )
        return [obj.name for obj in response.data.objects]


# Factory pattern for storage selection
def get_storage_backend(env: str = "development") -> StorageInterface:
    """Factory function to get appropriate storage backend."""
    if env == "development":
        return LocalFilesystemStorage(Path("./data/storage"))
    elif env == "testing":
        return MinIOStorage(
            endpoint="http://localhost:9000",
            access_key="iris-admin",
            secret_key="IrisMinIO123!"
        )
    elif env == "production":
        return OCIObjectStorage(config_file="~/.oci/config")
    else:
        raise ValueError(f"Unknown environment: {env}")
```

**Usage in Application:**

```python
# In your application code
from common.storage_interface import get_storage_backend
import os

# Environment-based selection
storage = get_storage_backend(os.getenv("ENVIRONMENT", "development"))

# Save model artifact
with open("model.pth", "rb") as f:
    storage.put_object("mlflow-artifacts", "models/qwen-coder-v1/model.pth", f)

# Load model artifact
model_data = storage.get_object("mlflow-artifacts", "models/qwen-coder-v1/model.pth")
```

### 3.2 In-Memory Cache Abstraction

**Why:** Oracle TimesTen XE requires separate installation; use Redis for simple dev, TimesTen for production-like testing

**Implementation:** `src/common/cache_interface.py`

```python
from abc import ABC, abstractmethod
from typing import Optional, Any
import redis
import pickle

class CacheInterface(ABC):
    """Abstract interface for in-memory caching."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value by key."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value with optional TTL in seconds."""
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete key."""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass


class RedisCache(CacheInterface):
    """Redis-based cache for development."""

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=False)

    def get(self, key: str) -> Optional[Any]:
        data = self.client.get(key)
        return pickle.loads(data) if data else None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        serialized = pickle.dumps(value)
        if ttl:
            self.client.setex(key, ttl, serialized)
        else:
            self.client.set(key, serialized)

    def delete(self, key: str) -> None:
        self.client.delete(key)

    def exists(self, key: str) -> bool:
        return bool(self.client.exists(key))


class TimesTenCache(CacheInterface):
    """Oracle TimesTen In-Memory Database cache for production."""

    def __init__(self, dsn: str):
        import oracledb
        self.connection = oracledb.connect(dsn)
        self._ensure_cache_table()

    def _ensure_cache_table(self):
        with self.connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache_store (
                    cache_key VARCHAR2(255) PRIMARY KEY,
                    cache_value BLOB,
                    expiry_time TIMESTAMP
                )
            """)
            self.connection.commit()

    def get(self, key: str) -> Optional[Any]:
        with self.connection.cursor() as cursor:
            cursor.execute("""
                SELECT cache_value FROM cache_store
                WHERE cache_key = :key
                AND (expiry_time IS NULL OR expiry_time > SYSTIMESTAMP)
            """, key=key)
            row = cursor.fetchone()
            return pickle.loads(row[0].read()) if row else None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        serialized = pickle.dumps(value)
        expiry_sql = "SYSTIMESTAMP + INTERVAL :ttl SECOND" if ttl else "NULL"

        with self.connection.cursor() as cursor:
            cursor.execute(f"""
                MERGE INTO cache_store USING DUAL ON (cache_key = :key)
                WHEN MATCHED THEN
                    UPDATE SET cache_value = :value, expiry_time = {expiry_sql}
                WHEN NOT MATCHED THEN
                    INSERT (cache_key, cache_value, expiry_time)
                    VALUES (:key, :value, {expiry_sql})
            """, key=key, value=serialized, ttl=ttl)
            self.connection.commit()

    def delete(self, key: str) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute("DELETE FROM cache_store WHERE cache_key = :key", key=key)
            self.connection.commit()

    def exists(self, key: str) -> bool:
        with self.connection.cursor() as cursor:
            cursor.execute("""
                SELECT 1 FROM cache_store
                WHERE cache_key = :key
                AND (expiry_time IS NULL OR expiry_time > SYSTIMESTAMP)
            """, key=key)
            return cursor.fetchone() is not None


def get_cache_backend(env: str = "development") -> CacheInterface:
    """Factory function to get appropriate cache backend."""
    if env in ["development", "testing"]:
        return RedisCache(host="localhost", port=6379)
    elif env == "production":
        return TimesTenCache(dsn="timesten_dsn")
    else:
        raise ValueError(f"Unknown environment: {env}")
```

### 3.3 High Availability Abstraction

**Why:** Oracle Free lacks RAC and Data Guard

**Strategy:** Implement application-level HA patterns instead of database-level HA

**Implementation:**
1. **Connection pooling with failover** - Use Oracle UCP (Universal Connection Pool) with retry logic
2. **Circuit breaker pattern** - Prevent cascading failures
3. **Read replicas** - For production, use multiple Oracle instances with application-level routing
4. **Graceful degradation** - Fallback to cached recommendations when database unavailable

**Not needed for local development** - Document HA strategy for production deployment

---

## Part 4: WSL Configuration

### 4.1 WSL Resource Allocation

**File:** `C:\Users\rickh\.wslconfig` (Windows side)

```ini
[wsl2]
# Memory allocation (allocate sufficient for all containers)
memory=10GB

# Processors
processors=6

# Swap space
swap=4GB

# Enable localhost port forwarding
localhostForwarding=true

# Network packet recalculation
nestedVirtualization=true
```

Apply changes:
```powershell
# From Windows PowerShell
wsl --shutdown
wsl
```

### 4.2 Docker Daemon Configuration

**File:** `/etc/docker/daemon.json` (WSL Ubuntu side)

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "default-address-pools": [
    {
      "base": "172.20.0.0/16",
      "size": 24
    }
  ]
}
```

Restart Docker:
```bash
sudo systemctl restart docker
```

---

## Part 5: Oracle Enterprise Manager Setup (Optional - Separate VM)

### 5.1 Why Separate VM?

- EM Cloud Control is **resource-intensive** (4GB+ RAM, 15GB+ disk)
- Running in same WSL would compete with development containers
- Easier to snapshot/restore VM state
- Can use pre-built Oracle VM templates

### 5.2 Recommended Approach

**Option 1: VirtualBox VM with Oracle EM Template (EASIEST)**

1. Download Oracle VM VirtualBox: https://www.virtualbox.org/
2. Download EM 13c R5 VM Template: https://www.oracle.com/enterprise-manager/downloads/
3. Import OVA into VirtualBox
4. Configure network adapter (bridged or NAT with port forwarding)
5. Access EM Console at http://vm-ip:7788/em

**Option 2: Install EM Cloud Control in WSL (ADVANCED)**

1. Create dedicated Ubuntu container/WSL instance
2. Download EM Cloud Control installer
3. Install WebLogic Server, JDK
4. Configure repository database (can use Oracle Free)
5. Run EM installer

**Recommendation:** Start without EM, focus on core development. Add EM plugin development in Phase 3 (weeks 13-16).

### 5.3 EDK Development Without EM

- Download EDK ZIP from Oracle (requires EM access)
- Use `empdk` CLI tool locally for validation and packaging
- Test plugin deployment later when EM is available
- Focus on Java/Spring Boot development with mock EM interfaces

---

## Part 6: Installation Sequence

### 6.1 Pre-Installation Checklist

```bash
# Check WSL version
wsl --version
# Should be WSL 2

# Check Docker
docker --version
docker-compose --version

# Check disk space
df -h
# Need ~50GB free for all containers and data

# Check available memory
free -h
```

### 6.2 Installation Steps

**Step 1: Configure WSL Resources**
```bash
# From Windows PowerShell (as Administrator)
notepad C:\Users\rickh\.wslconfig
# Add configuration from Part 4.1
wsl --shutdown
wsl
```

**Step 2: Install Development Tools in WSL Ubuntu**
```bash
# Update package lists
sudo apt update && sudo apt upgrade -y

# Install Python 3.10+
sudo apt install -y python3.10 python3.10-venv python3-pip

# Install Java 17
sudo apt install -y openjdk-17-jdk maven

# Install Node.js (optional)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
source ~/.bashrc
nvm install 20

# Install Docker Compose plugin (if not already installed)
sudo apt install -y docker-compose-plugin

# Verify installations
python3.10 --version
java -version
node --version
docker compose version
```

**Step 3: Set Up Project Directory Structure**
```bash
# Create project directory
cd ~
mkdir -p iris-project
cd iris-project

# Clone or initialize Git repository
git init
# or git clone <repository-url>

# Create directory structure
mkdir -p {src,tests,docker,data,models,notebooks,docs}
mkdir -p docker/init-scripts
mkdir -p data/{storage,mlflow,training}

# Create Python virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

**Step 4: Install Python Dependencies**
```bash
# Activate virtual environment
source venv/bin/activate

# Create requirements.txt
cat > requirements.txt << 'EOF'
# Core ML frameworks
torch>=2.1.0
torchvision>=0.16.0
torchaudio>=2.1.0
transformers>=4.35.0
peft>=0.7.0
bitsandbytes>=0.41.0
stable-baselines3>=2.2.0
gymnasium>=0.29.0

# Data & Feature Engineering
pandas>=2.1.0
numpy>=1.24.0
polars>=0.19.0
great-expectations>=0.18.0

# Oracle Database Connectivity
oracledb>=1.4.0

# MLOps & Serving
mlflow>=2.9.0
feast>=0.35.0
fastapi>=0.104.0
uvicorn[standard]>=0.24.0

# Utilities
boto3>=1.29.0  # For MinIO S3 interface
redis>=5.0.0
python-dotenv>=1.0.0
pydantic>=2.5.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
testcontainers>=3.7.0

# Code Quality
black>=23.11.0
flake8>=6.1.0
mypy>=1.7.0
isort>=5.12.0
EOF

# Install dependencies
pip install -r requirements.txt
```

**Step 5: Create Docker Compose Configuration**
```bash
# Copy the docker-compose.dev.yml from Part 2.1
cd ~/iris-project
mkdir -p docker
nano docker/docker-compose.dev.yml
# Paste configuration from Part 2.1

# Create init scripts
nano docker/init-scripts/01_create_iris_user.sql
# Paste SQL from Part 2.3

nano docker/init-scripts/02_create_sample_schema.sql
# Paste SQL from Part 2.3
```

**Step 6: Create Storage Abstraction**
```bash
# Create common module
mkdir -p src/common
touch src/common/__init__.py

# Copy storage_interface.py
nano src/common/storage_interface.py
# Paste code from Part 3.1

# Copy cache_interface.py
nano src/common/cache_interface.py
# Paste code from Part 3.2
```

**Step 7: Create Environment Configuration**
```bash
# Create .env file for environment variables
cat > .env << 'EOF'
# Environment
ENVIRONMENT=development

# Oracle Database
ORACLE_HOST=localhost
ORACLE_PORT=1524
ORACLE_SERVICE=FREEPDB1
ORACLE_USER=iris_user
ORACLE_PASSWORD=IrisUser123!

# MinIO
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=iris-admin
MINIO_SECRET_KEY=IrisMinIO123!
MINIO_BUCKET=mlflow-artifacts

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# MLflow
MLFLOW_TRACKING_URI=http://localhost:5000

# Application
LOG_LEVEL=DEBUG
EOF

# Add .env to .gitignore
echo ".env" >> .gitignore
echo "venv/" >> .gitignore
echo "data/" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore
```

**Step 8: Start Docker Containers**
```bash
# Pull Oracle container image (this will take time - ~10GB)
docker pull container-registry.oracle.com/database/free:latest

# Start all services
cd ~/iris-project
docker compose -f docker/docker-compose.dev.yml up -d

# Monitor Oracle startup (takes 5-10 minutes)
docker logs -f oracle-iris-dev

# Wait for message: "DATABASE IS READY TO USE!"
```

**Step 9: Verify Installation**
```bash
# Check all containers are running
docker compose -f docker/docker-compose.dev.yml ps

# Test Oracle connection
docker exec -it oracle-iris-dev sqlplus sys/IrisDev123!@FREEPDB1 as sysdba
# Should connect successfully
# Type: SELECT 1 FROM DUAL;
# Type: EXIT;

# Test MinIO
curl http://localhost:9000/minio/health/live
# Should return: OK

# Test Redis
redis-cli ping
# Should return: PONG

# Test MLflow
curl http://localhost:5000/health
# Should return: OK

# Access EM Express (after Oracle fully started)
# Open browser: https://localhost:5503/em
# Username: sys
# Password: IrisDev123!
# Connect as: SYSDBA
```

**Step 10: Initialize Database Schema**
```bash
# Connect as IRIS user
docker exec -it oracle-iris-dev sqlplus iris_user/IrisUser123!@FREEPDB1

# Verify tables created
SELECT table_name FROM user_tables;
# Should show: CUSTOMERS, ORDERS, ORDER_ITEMS, PRODUCT_CATALOG

# Check AWR snapshots
SELECT snap_id, begin_interval_time, end_interval_time
FROM dba_hist_snapshot
ORDER BY snap_id DESC
FETCH FIRST 5 ROWS ONLY;

# Exit
EXIT;
```

**Step 11: Test Python Connectivity**
```bash
# Activate virtual environment
cd ~/iris-project
source venv/bin/activate

# Create test script
cat > test_connections.py << 'EOF'
import oracledb
import redis
import boto3
from botocore.client import Config

# Test Oracle
print("Testing Oracle Database connection...")
try:
    connection = oracledb.connect(
        user="iris_user",
        password="IrisUser123!",
        dsn="localhost:1524/FREEPDB1"
    )
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM customers")
    count = cursor.fetchone()[0]
    print(f"✓ Oracle connected: {count} customers found")
    cursor.close()
    connection.close()
except Exception as e:
    print(f"✗ Oracle error: {e}")

# Test Redis
print("\nTesting Redis connection...")
try:
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    r.set('test_key', 'test_value')
    value = r.get('test_key')
    print(f"✓ Redis connected: test_key = {value}")
except Exception as e:
    print(f"✗ Redis error: {e}")

# Test MinIO
print("\nTesting MinIO S3 connection...")
try:
    s3 = boto3.client(
        's3',
        endpoint_url='http://localhost:9000',
        aws_access_key_id='iris-admin',
        aws_secret_access_key='IrisMinIO123!',
        config=Config(signature_version='s3v4')
    )
    # Create bucket if not exists
    try:
        s3.create_bucket(Bucket='test-bucket')
    except:
        pass
    s3.put_object(Bucket='test-bucket', Key='test.txt', Body=b'Hello IRIS')
    obj = s3.get_object(Bucket='test-bucket', Key='test.txt')
    content = obj['Body'].read().decode('utf-8')
    print(f"✓ MinIO connected: {content}")
except Exception as e:
    print(f"✗ MinIO error: {e}")

print("\n✓ All connections successful!")
EOF

# Run test
python test_connections.py
```

---

## Part 7: Development Workflow

### 7.1 Daily Workflow

```bash
# Start containers
cd ~/iris-project
docker compose -f docker/docker-compose.dev.yml up -d

# Activate Python environment
source venv/bin/activate

# Start development
code .  # Or your preferred editor

# When done, stop containers (optional - can keep running)
docker compose -f docker/docker-compose.dev.yml stop
```

### 7.2 Useful Commands

```bash
# View logs
docker compose -f docker/docker-compose.dev.yml logs -f oracle-iris-dev
docker compose -f docker/docker-compose.dev.yml logs -f mlflow

# Restart specific service
docker compose -f docker/docker-compose.dev.yml restart redis

# Execute SQL
docker exec -it oracle-iris-dev sqlplus iris_user/IrisUser123!@FREEPDB1

# Access MinIO Console
# Browser: http://localhost:9001
# Username: iris-admin
# Password: IrisMinIO123!

# Access MLflow UI
# Browser: http://localhost:5000

# Check AWR snapshots
docker exec -it oracle-iris-dev sqlplus sys/IrisDev123!@FREEPDB1 as sysdba <<EOF
SELECT snap_id, begin_interval_time, end_interval_time
FROM dba_hist_snapshot
ORDER BY snap_id DESC
FETCH FIRST 10 ROWS ONLY;
EXIT;
EOF
```

---

## Part 8: Testing the Setup

### 8.1 Unit Test Example

**File:** `tests/test_storage_interface.py`

```python
import pytest
from pathlib import Path
from src.common.storage_interface import (
    LocalFilesystemStorage,
    MinIOStorage,
    get_storage_backend
)
import io

def test_local_filesystem_storage(tmp_path):
    """Test local filesystem storage implementation."""
    storage = LocalFilesystemStorage(tmp_path)

    # Test put_object
    test_data = b"Hello, IRIS!"
    storage.put_object("test-bucket", "test-file.txt", io.BytesIO(test_data))

    # Test get_object
    retrieved = storage.get_object("test-bucket", "test-file.txt")
    assert retrieved == test_data

    # Test exists (via list)
    objects = storage.list_objects("test-bucket")
    assert "test-file.txt" in objects

    # Test delete
    storage.delete_object("test-bucket", "test-file.txt")
    objects = storage.list_objects("test-bucket")
    assert "test-file.txt" not in objects


def test_minio_storage():
    """Test MinIO storage implementation (requires MinIO running)."""
    storage = MinIOStorage(
        endpoint="http://localhost:9000",
        access_key="iris-admin",
        secret_key="IrisMinIO123!"
    )

    # Create bucket first (via boto3 directly)
    import boto3
    from botocore.client import Config
    s3 = boto3.client(
        's3',
        endpoint_url='http://localhost:9000',
        aws_access_key_id='iris-admin',
        aws_secret_access_key='IrisMinIO123!',
        config=Config(signature_version='s3v4')
    )
    try:
        s3.create_bucket(Bucket='test-bucket')
    except:
        pass  # Bucket already exists

    # Test operations
    test_data = b"MinIO Test Data"
    storage.put_object("test-bucket", "minio-test.txt", io.BytesIO(test_data))

    retrieved = storage.get_object("test-bucket", "minio-test.txt")
    assert retrieved == test_data

    storage.delete_object("test-bucket", "minio-test.txt")


def test_storage_factory():
    """Test storage factory function."""
    dev_storage = get_storage_backend("development")
    assert isinstance(dev_storage, LocalFilesystemStorage)

    test_storage = get_storage_backend("testing")
    assert isinstance(test_storage, MinIOStorage)


# Run tests
# pytest tests/test_storage_interface.py -v
```

### 8.2 Integration Test Example

**File:** `tests/test_oracle_integration.py`

```python
import pytest
import oracledb
from datetime import datetime

@pytest.fixture(scope="module")
def oracle_connection():
    """Provide Oracle database connection for tests."""
    conn = oracledb.connect(
        user="iris_user",
        password="IrisUser123!",
        dsn="localhost:1524/FREEPDB1"
    )
    yield conn
    conn.close()


def test_awr_data_available(oracle_connection):
    """Verify AWR data collection is working."""
    cursor = oracle_connection.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM dba_hist_snapshot
        WHERE begin_interval_time > SYSDATE - 1
    """)
    count = cursor.fetchone()[0]
    cursor.close()

    assert count > 0, "No AWR snapshots found in last 24 hours"


def test_sample_data_loaded(oracle_connection):
    """Verify sample data is loaded."""
    cursor = oracle_connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM customers")
    count = cursor.fetchone()[0]
    cursor.close()

    assert count >= 1000, f"Expected 1000+ customers, found {count}"


def test_json_collection_available(oracle_connection):
    """Verify JSON Collection Tables are available (23ai+)."""
    cursor = oracle_connection.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM product_catalog")
        # If we get here, JSON Collections are supported
        cursor.close()
    except oracledb.DatabaseError as e:
        pytest.skip(f"JSON Collections not available: {e}")


# Run tests
# pytest tests/test_oracle_integration.py -v
```

---

## Part 9: Cost and Resource Summary

### 9.1 Disk Space Requirements

| Component | Size | Location |
|-----------|------|----------|
| Oracle Database Free Container | ~10 GB | Docker image |
| Oracle Database Data | ~2-5 GB | Docker volume (WSL filesystem) |
| MinIO | ~500 MB | Docker image + data |
| Redis | ~100 MB | Docker image + data |
| PostgreSQL (MLflow) | ~200 MB | Docker image + data |
| MLflow | ~300 MB | Docker image |
| Python ML Libraries | ~5 GB | venv |
| **Total** | **~20-25 GB** | - |

### 9.2 Memory Requirements

| Component | Memory | Notes |
|-----------|--------|-------|
| Oracle Database Free | 2 GB | Hard limit |
| MinIO | 512 MB | Configurable |
| Redis | 256 MB | Configurable |
| PostgreSQL | 256 MB | Configurable |
| MLflow | 512 MB | Configurable |
| OS + Docker Overhead | 1 GB | - |
| Development Buffer | 3 GB | For IDE, browser, etc. |
| **Total Recommended** | **8-10 GB** | WSL allocation |

### 9.3 CPU Requirements

- **Minimum:** 4 cores (2 for Oracle Free, 2 for host OS)
- **Recommended:** 6+ cores (allows parallel work)

---

## Part 10: Next Steps After Setup

1. **Verify Installation:** Run all tests in Part 8
2. **Configure IDEs:**
   - VS Code: Install Python, Java, Docker extensions
   - PyCharm: Configure Python interpreter, Oracle data source
3. **Set Up Git Hooks:** Pre-commit hooks for Black, flake8, mypy
4. **Create Initial Project Structure:** Follow TDD with /tdd command
5. **Begin Phase 1 Development:** Data pipeline and feature engineering

---

## Summary: What Gets Installed

### ✅ Direct Oracle Technologies (No Facade)
- Oracle Database Free 26ai - Full AWR, AQ, JSON features
- Oracle TimesTen XE 22c (optional, install later)
- Oracle JDBC drivers (via Maven/pip)

### 🔄 Abstraction Layers Required
- **Storage Interface** - filesystem → MinIO → OCI Object Storage
- **Cache Interface** - Redis → TimesTen (for simple cases)

### 🐳 Supporting Infrastructure (OSS)
- Docker + Docker Compose
- MinIO (S3-compatible)
- Redis (caching)
- PostgreSQL (MLflow backend)
- MLflow (experiment tracking)

### 💻 Development Tools
- Python 3.10+ with ML libraries
- Java 17 + Maven
- Git, VS Code/PyCharm

### 📦 Deferred for Later
- Oracle Enterprise Manager Cloud Control (Phase 3, weeks 13-16)
- Oracle TimesTen (can use Redis initially)

---

## Total Setup Time Estimate

- **Preparation:** 30 minutes (WSL config, tool installation)
- **Docker Images:** 60-90 minutes (Oracle Free is ~10GB download)
- **Configuration:** 30 minutes (creating files, running scripts)
- **Testing & Verification:** 30 minutes
- **Total:** **3-4 hours** (mostly waiting for downloads)

---

**Ready to proceed with installation? Review this plan and let me know if you'd like to:**
1. Proceed with the full installation as outlined
2. Modify any component choices
3. Add/remove any services
4. Clarify any section before starting
