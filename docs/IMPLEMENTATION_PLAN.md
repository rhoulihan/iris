# IRIS Implementation Plan - Schema Policy Engine

## Project Vision

IRIS is a sophisticated **Schema Policy Recommendation Engine** for Oracle 23ai databases that goes beyond simple index recommendations. It analyzes workload patterns, schema relationships, and Oracle 23ai capabilities to recommend schema transformations that optimize overall database efficiency through intelligent tradeoff analysis.

## Core Capabilities

### 1. Anti-Pattern Detection
- **LOB Cliff Detection**: Identify when small updates to large documents cause LOB storage issues
- **Join Dimension Analysis**: Detect expensive join patterns that could benefit from denormalization
- **Over-Normalization**: Find schemas where normalization hurts more than helps
- **Under-Denormalization**: Identify document-as-relational patterns that should be documents
- **Inefficient Access Patterns**: Detect mismatches between schema design and actual query patterns

### 2. Oracle 23ai Feature Utilization
- **JSON Duality Views**: Recommend when to use dual representation (OLTP document + Analytics relational)
- **Document Storage**: Identify objects that should be stored as JSON documents
- **Relational Optimization**: Recommend when documents should be relational
- **Hybrid Approaches**: Suggest mixed strategies for complex workloads

### 3. Tradeoff Analysis
- **Query Frequency Weighting**: Optimize high-frequency queries while accepting cost on infrequent ones
- **Performance vs Cost**: Balance performance gains against compute/storage costs
- **Cascading Impact**: Analyze how one optimization affects other queries
- **Threshold Analysis**: Determine when Duality Views become cost-effective

### 4. Cost/Benefit Calculation
- **Execution Time Savings**: Quantify expected performance improvements
- **Storage Overhead**: Calculate additional storage requirements
- **Compute Overhead**: Estimate CPU/memory impact
- **Maintenance Cost**: Factor in complexity and operational burden
- **Net Benefit Score**: Overall recommendation ranking

## Architecture Overview

### Phase 1: Data Collection & Feature Engineering ✅ COMPLETE

**Modules Implemented:**
- ✅ AWR Collector (95.56% coverage) - Workload data collection
- ✅ Query Parser (89.08% coverage) - SQL structure analysis
- ✅ Workload Compressor (100% coverage) - Query deduplication
- ✅ Feature Engineer (98.72% coverage) - Workload feature extraction
- ✅ Schema Collector (92.74% coverage) - Database metadata collection

**Capabilities:**
- Collect and compress SQL workload from AWR
- Extract query patterns, complexity metrics, and execution statistics
- Retrieve table/column/index/constraint metadata
- Generate workload summaries for analysis

### Phase 2: LLM Infrastructure 🔄 IN PROGRESS

**Module: LLM Client** (src/llm/claude_client.py)

Purpose: Claude API integration for sophisticated schema analysis

**Key Features:**
- API authentication and connection management
- Retry logic with exponential backoff
- Token usage tracking and rate limiting
- Streaming response support
- Error handling and validation
- Prompt templating system

**Design Considerations:**
- Support for long-form analysis prompts (workload + schema + context)
- Token budget management (handle large schemas)
- Response parsing for structured recommendations
- Conversation context management for iterative analysis

### Phase 3: Schema Policy Engine 🔄 IN PROGRESS

**Module: Pattern Detector** ✅ COMPLETE (src/recommendation/pattern_detector.py)

Purpose: Identify schema anti-patterns and optimization opportunities

**Status**: 100% complete with 90.12% test coverage (63 tests passing)

**Detection Capabilities:**
1. **LOB Cliff Detector** ✅
   - Input: Table statistics, update patterns, column sizes
   - Logic: Risk scoring algorithm (document size, update frequency, selectivity, JSON in CLOB)
   - Output: LOB cliff risk score (≥0.6 threshold), affected tables/columns
   - **Coverage**: 17 tests, all passing

2. **Join Dimension Analyzer** ✅
   - Input: Query patterns, join frequencies, table relationships
   - Logic: Net benefit calculation (join savings - update propagation cost)
   - Output: Denormalization candidates with positive net benefit only
   - **Coverage**: 15 tests, all passing

3. **Document vs Relational Classifier** ✅
   - Input: Access patterns, query types, schema structure
   - Logic: Multi-factor scoring (SELECT *, object access, flexibility, joins, aggregates)
   - Output: Document/Relational recommendations with confidence >0.3
   - **Coverage**: 16 tests, all passing

4. **Duality View Opportunity Finder** ✅
   - Input: OLTP vs Analytics query mix, access patterns
   - Logic: Dual access pattern detection (requires ≥10% OLTP and ≥10% Analytics)
   - Output: Duality View candidates with severity scoring (HIGH ≥30%, MEDIUM ≥15%)
   - **Coverage**: 15 tests, all passing

**Module: Cost Calculator** ✅ COMPLETE (src/recommendation/cost_calculator.py)

Purpose: Quantify impact of schema changes with ROI and priority scoring

**Status**: 100% complete with 80.92% test coverage (60 tests passing)

**Calculation Methods:**
1. **Pattern-Specific Cost Calculators** ✅
   - LOBCliffCostCalculator: I/O costs, write amplification, chaining overhead
   - JoinDenormalizationCostCalculator: Join cost savings vs update propagation
   - DocumentStorageCostCalculator: Relational vs JSON storage optimization
   - DualityViewCostCalculator: Dual system costs vs single system with conversions
   - **Coverage**: 24 unit tests + 11 integration tests

2. **ROI & Priority Scoring** ✅
   - Multi-factor weighted algorithm (ROI 30%, savings 25%, payback 20%, impl cost 15%, severity 10%)
   - Logarithmic normalization for ROI and savings (handles wide ranges)
   - Exponential decay for payback period and implementation cost
   - Priority tiers: HIGH (≥70), MEDIUM (40-69), LOW (<40)
   - **Coverage**: 27 unit tests

3. **Cost Models** ✅
   - Configurable cost parameters (I/O, CPU, storage, network, labor)
   - Automatic ROI calculations (annual savings, net benefit, payback period)
   - Implementation cost estimation with labor hours
   - **Coverage**: 24 unit tests, 96.77% coverage

4. **Integration & Validation** ✅
   - End-to-end tests using Phase 1 synthetic workloads
   - Complete flow: Pattern Detection → Cost Calculation → Priority Ranking
   - Realistic cost estimates validated (60%+ performance improvements)
   - **Coverage**: 11 integration tests (9 passing, 2 skipped due to metadata mismatch)

**Module: Tradeoff Analyzer** ✅ COMPLETE (src/recommendation/tradeoff_analyzer.py)

Purpose: Evaluate competing optimizations and their interactions

**Status**: 100% complete with 100% test coverage (22 tests passing)

**Analysis Framework:**
1. **Query Frequency Distribution** ✅
   - QueryFrequencyProfile data model
   - Daily executions tracking
   - Response time metrics (avg, p95)
   - Workload percentage calculation
   - **Coverage**: Implemented with full test coverage

2. **Conflict Resolution** ✅
   - OptimizationConflict detection between pattern types
   - Incompatibility checking (Document vs Relational, LOB vs Document)
   - Resolution strategies: DUALITY_VIEW, PRIORITIZE_A, PRIORITIZE_B
   - Affected objects tracking
   - **Coverage**: 6 conflict detection tests

3. **Tradeoff Analysis** ✅
   - TradeoffAnalysis data model
   - High-frequency vs low-frequency query separation
   - Weighted improvement/degradation calculation
   - Net benefit scoring
   - Overhead justification determination
   - Break-even threshold calculation
   - Recommendation generation (APPROVE, REJECT, CONDITIONAL)
   - **Coverage**: 22/22 tests passing, 100% coverage

**Test Results**:
- Unit tests: 22/22 passing
- Coverage: 100% on tradeoff_analyzer.py
- Edge cases: Empty lists, missing priority scores, multi-conflict scenarios
- Integration: Tested with Phase 2 cost estimates

**Module: Policy Recommendation Engine** ✅ COMPLETE (src/recommendation/recommendation_engine.py)

Purpose: Generate actionable schema recommendations with implementation plans

**Status**: Core integration complete with 93.43% test coverage (18 tests passing)

**Implementation Details:**
1. **Recommendation Builder** ✅
   - SchemaRecommendation data model with complete recommendation structure
   - Pattern-specific rationale generation (LOB, Join, Document, Duality View)
   - Rationale, Implementation, Tradeoff, and Alternative data models
   - **Coverage**: 6 data model tests passing

2. **Implementation Planner** ✅
   - Placeholder SQL generation for all 4 pattern types
   - Rollback plan generation for safe deployment
   - Testing approach recommendations
   - Ready for Phase 3.3 LLM enhancement
   - **Coverage**: Tested via recommendation generation tests

3. **Rollback Strategy Generator** ✅
   - Pattern-specific rollback plans
   - Testing strategies for each optimization type
   - Risk assessment and mitigation guidance
   - **Coverage**: Included in implementation tests

4. **Priority-Based Ranking** ✅
   - Sort recommendations by priority tier (HIGH > MEDIUM > LOW)
   - Bulk recommendation generation with conflict handling
   - Rejected tradeoff handling (returns None)
   - **Coverage**: 3 bulk generation tests

**Test Coverage Summary**:
- Unit tests: 18/18 passing
- Coverage: 93.43% on recommendation_engine.py
- Edge cases: Empty patterns, missing estimates, rejected tradeoffs, conflict warnings
- Integration: Tested with Pattern Detector, Cost Calculator, and Tradeoff Analyzer

**Recommendation Types:**

1. **Schema Transformation Recommendations**
   - Relational → Document: "Convert ORDERS table to JSON collection"
   - Document → Relational: "Normalize user preferences into relational tables"
   - Denormalization: "Embed order items into order document"
   - Normalization: "Split large document into referenced tables"

2. **Duality View Recommendations**
   - "Create Duality View for CUSTOMERS: Document for OLTP, Relational for Analytics"
   - Specify when overhead justified by dual access patterns

3. **LOB Optimization Recommendations**
   - "Split large PRODUCT.description into separate table to avoid LOB cliffs"
   - "Move frequently-updated metadata out of document"

4. **Hybrid Strategy Recommendations**
   - "Keep core entity relational, use JSON columns for flexible attributes"
   - "Use Duality Views for high-frequency tables, accept overhead for occasional tables"

**Recommendation Structure:**
```python
{
    "recommendation_id": "REC-001",
    "type": "duality_view",
    "priority": "high",
    "target_table": "CUSTOMERS",
    "description": "Create JSON Duality View for dual OLTP/Analytics access",

    "rationale": {
        "pattern_detected": "High-frequency document access (75% of queries) + Analytics queries (20%)",
        "current_cost": "Expensive JSON parsing on analytics queries",
        "expected_benefit": "50% improvement on analytics, no impact on OLTP"
    },

    "impact": {
        "affected_queries": 450,  # Count of queries impacted
        "high_frequency_improvement": "+45%",  # Performance gain on frequent queries
        "low_frequency_impact": "+5%",  # Acceptable cost on infrequent queries
        "net_benefit_score": 8.5  # Overall score (0-10)
    },

    "costs": {
        "storage_overhead_mb": 150,
        "compute_overhead_pct": 2,
        "maintenance_complexity": "low"
    },

    "implementation": {
        "sql": "CREATE JSON RELATIONAL DUALITY VIEW customer_dv AS ...",
        "rollback_plan": "DROP VIEW customer_dv; -- No data loss",
        "testing_approach": "Enable for 10% of traffic, monitor metrics"
    },

    "tradeoffs": [
        {
            "description": "2% compute overhead for view maintenance",
            "justified_by": "45% improvement on 450 daily analytics queries"
        }
    ],

    "alternatives": [
        {
            "approach": "Maintain separate JSON and relational tables",
            "pros": ["No view overhead"],
            "cons": ["Application complexity", "Data consistency challenges"]
        }
    ]
}
```

### Phase 4: Pipeline Orchestrator & Integration 🔄 IN PROGRESS

**Module: Pipeline Orchestrator** ✅ PROTOTYPE COMPLETE (src/pipeline/orchestrator.py)

Purpose: Coordinate end-to-end workflow from AWR collection to recommendations

**Status**: Prototype complete with 22 integration tests (100% pass rate)

**Implementation:**
1. **Pipeline Architecture** ✅
   - 6-stage pipeline: Data Collection → Feature Engineering → Pattern Detection → Cost Analysis → Tradeoff Analysis → Recommendation Generation
   - Configurable pattern detectors and thresholds
   - Comprehensive error handling and metrics tracking
   - **Coverage**: 22/22 integration tests passing

2. **Data Model Converters** 🔄 IN PROGRESS
   - Dict → TableMetadata conversion (from schema_collector results)
   - Dict → QueryPattern conversion (from query_parser results)
   - Type-safe conversion utilities with validation
   - **Coverage**: Unit tests in progress

3. **Pattern Detector Interface Standardization** 📋 PLANNED
   - Common `detect()` API across all detectors
   - Consistent method signatures
   - Unified return types

4. **End-to-End Integration** 📋 PLANNED
   - Wire up all pipeline stages
   - Enable query parsing with converters
   - Enable schema collection with converters
   - Enable pattern detection with standardized interfaces

**Integration Tests:**
- ✅ Pipeline orchestrator initialization and configuration
- ✅ Empty workload handling
- ✅ Error handling and resilience
- ✅ Metrics tracking
- 📋 End-to-end workload analysis pipeline (awaiting converters)
- 📋 Schema recommendation generation (awaiting converters)
- 📋 Cost/benefit validation
- 📋 Oracle 23ai integration tests

**Components:**
- ✅ Integration test suite (tests/integration/)
- 📋 Performance benchmarking
- 📋 Real workload validation
- 📋 Recommendation accuracy testing

### Phase 5: User Interface 📋 PLANNED

**Command-Line Interface:**
- Interactive workload analysis
- Schema recommendation browser
- What-if analysis tool
- Recommendation export

**API Interface:**
- RESTful API for programmatic access
- Recommendation retrieval
- Impact analysis endpoints
- Monitoring integration

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. DATA COLLECTION (Complete)                                    │
├─────────────────────────────────────────────────────────────────┤
│ Oracle 23ai Database                                             │
│   ├─> AWR Collector ──> Workload Data                           │
│   └─> Schema Collector ──> Schema Metadata                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. FEATURE ENGINEERING (Complete)                                │
├─────────────────────────────────────────────────────────────────┤
│ Query Parser ──> SQL Structure Analysis                          │
│ Workload Compressor ──> Deduplicated Patterns                   │
│ Feature Engineer ──> Workload Features                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. PATTERN DETECTION (Complete - 90.12% coverage)                │
├─────────────────────────────────────────────────────────────────┤
│ Pattern Detector                                                  │
│   ├─> LOB Cliff Detector ✅                                      │
│   ├─> Join Dimension Analyzer ✅                                 │
│   ├─> Document vs Relational Classifier ✅                       │
│   └─> Duality View Opportunity Finder ✅                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. COST/BENEFIT ANALYSIS (Complete - 87.54% coverage)            │
├─────────────────────────────────────────────────────────────────┤
│ Cost Calculator                                                   │
│   ├─> Pattern-Specific Calculators (4 types) ✅                 │
│   ├─> ROI & Priority Scoring ✅                                  │
│   ├─> Cost Models & Configuration ✅                             │
│   └─> Integration with Pattern Detector ✅                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. TRADEOFF ANALYSIS (Complete - 100% coverage)                  │
├─────────────────────────────────────────────────────────────────┤
│ Tradeoff Analyzer                                                 │
│   ├─> Query Frequency Weighting ✅                               │
│   ├─> Conflict Detection & Resolution ✅                         │
│   ├─> Break-Even Threshold Calculation ✅                        │
│   └─> Net Benefit Scoring ✅                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. RECOMMENDATION ENGINE (Complete - All phases)                 │
├─────────────────────────────────────────────────────────────────┤
│ LLM Client (Infrastructure Layer) ✅ (98.25% coverage)           │
│   ├─> Claude API Integration ✅                                  │
│   ├─> Prompt Engineering ✅                                      │
│   └─> Response Parsing ✅                                        │
│                                                                   │
│ Recommendation Engine Core (Integration Layer) ✅ (89.66%)       │
│   ├─> Pattern-specific rationale builders ✅                     │
│   ├─> Implementation plan generation ✅                          │
│   ├─> Rollback strategy generation ✅                            │
│   ├─> Priority-based ranking ✅                                  │
│   └─> Conflict resolution integration ✅                         │
│                                                                   │
│ LLM SQL Generator (Phase 3.3) ✅ (77.78% coverage)               │
│   ├─> Claude-powered Oracle 23ai DDL generation ✅               │
│   ├─> Pattern-specific prompt engineering ✅                     │
│   ├─> SQL parsing and validation ✅                              │
│   ├─> Error handling with placeholder fallback ✅                │
│   └─> Integration with Recommendation Engine ✅                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. OUTPUT & DELIVERY (Planned)                                   │
├─────────────────────────────────────────────────────────────────┤
│ Structured Recommendations                                        │
│   ├─> Priority ranking                                           │
│   ├─> Implementation SQL                                         │
│   ├─> Rollback plans                                            │
│   ├─> Cost/benefit summary                                      │
│   └─> Testing approach                                          │
└─────────────────────────────────────────────────────────────────┘
```

## Prompt Engineering Strategy

The LLM will receive rich context for sophisticated analysis:

### Input Context Structure
```
# Workload Analysis Context
- Query frequency distribution
- Join patterns and costs
- Access pattern classification (document vs relational)
- Performance bottlenecks
- Execution statistics

# Schema Context
- Table structures and relationships
- Current indexes and constraints
- Storage metrics (LOB usage, table sizes)
- Column access patterns

# Detected Patterns
- Anti-patterns identified
- Optimization opportunities
- Cost/benefit calculations
- Conflict analysis

# Constraints
- Acceptable storage overhead threshold
- Acceptable compute overhead threshold
- Acceptable performance degradation on low-frequency queries
```

### Expected LLM Reasoning
- Synthesize patterns across workload and schema
- Identify non-obvious optimization opportunities
- Reason about cascading effects
- Suggest creative solutions (e.g., partial denormalization)
- Balance competing concerns
- Explain tradeoffs clearly

## Success Metrics

1. **Recommendation Quality**
   - Accuracy of performance predictions
   - Relevance of detected patterns
   - Feasibility of recommendations

2. **Optimization Impact**
   - Percentage improvement on high-frequency queries
   - Acceptable degradation on low-frequency queries
   - Net workload improvement

3. **Cost Efficiency**
   - Storage overhead within acceptable limits
   - Compute overhead minimized
   - Maintenance burden acceptable

4. **Coverage**
   - Percentage of workload analyzed
   - Percentage of schema covered
   - Completeness of recommendations

## Next Steps

### Completed ✅
1. ✅ Update requirements.txt with anthropic SDK
2. ✅ Implement LLM Client infrastructure
   - Claude API integration (98.25% coverage)
   - Retry logic and error handling
   - Token management
   - Prompt templating
3. ✅ Pattern Detector implementation (90.12% coverage)
   - LOB Cliff Detector (17 tests)
   - Join Dimension Analyzer (15 tests)
   - Document vs Relational Classifier (16 tests)
   - Duality View Opportunity Finder (15 tests)
4. ✅ Cost Calculator implementation (87.54% coverage)
   - Pattern-specific cost calculators (4 types)
   - ROI & priority scoring (27 tests)
   - Cost models and configuration (24 tests)
   - Integration testing (11 tests)

### Short-term (Next Sprint)
5. Tradeoff Analyzer implementation
   - Query frequency weighting
   - Conflict resolution
   - Threshold calculation

6. LLM-Enhanced Recommendation Engine
   - Integrate Pattern Detector and Cost Calculator
   - Claude-powered semantic analysis
   - Generate implementation SQL and rollback plans

### Medium-term
7. Data Collection Pipeline (AWR integration)
8. API & CLI Interface
9. Feature store implementation (Feast + TimesTen)
10. Real workload validation

### Long-term
9. CLI interface
10. API interface
11. MLflow integration for tracking
12. Production deployment

## Notes

- This is a **policy-based recommendation engine**, not a simple index advisor
- Focus on **tradeoff analysis** - every recommendation has costs
- Leverage **Oracle 23ai features** - Duality Views are key differentiator
- Use **LLM for synthesis** - Claude can reason about complex tradeoffs
- **Frequency-weighted optimization** - optimize common paths, accept cost on rare paths
- **Threshold-based decisions** - when is overhead justified?
