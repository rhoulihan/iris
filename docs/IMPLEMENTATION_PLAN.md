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

### Phase 3: Schema Policy Engine 📋 PLANNED

**Module: Pattern Detector** (src/analysis/pattern_detector.py)

Purpose: Identify schema anti-patterns and optimization opportunities

**Detection Capabilities:**
1. **LOB Cliff Detector**
   - Input: Table statistics, update patterns, column sizes
   - Logic: Identify tables with frequent small updates to large LOB columns
   - Output: LOB cliff risk score, affected tables/columns

2. **Join Dimension Analyzer**
   - Input: Query patterns, join frequencies, table relationships
   - Logic: Detect expensive join patterns by analyzing execution frequency and cost
   - Output: Denormalization candidates with join cost metrics

3. **Document vs Relational Classifier**
   - Input: Access patterns, query types, schema structure
   - Logic: Identify objects accessed as units vs individual columns
   - Output: Document storage candidates with confidence scores

4. **Duality View Opportunity Finder**
   - Input: OLTP vs Analytics query mix, access patterns
   - Logic: Find tables accessed both as documents (OLTP) and relational (Analytics)
   - Output: Duality View candidates with dual access frequency

**Module: Cost Calculator** (src/analysis/cost_calculator.py)

Purpose: Quantify impact of schema changes

**Calculation Methods:**
1. **Performance Impact**
   - Query execution time changes (before/after estimation)
   - Affected query frequency weighting
   - Cascading effects on dependent queries

2. **Storage Cost**
   - Additional storage for denormalization
   - Duality View storage overhead
   - Index storage requirements

3. **Compute Cost**
   - Materialization overhead for Duality Views
   - Update propagation cost
   - Query rewrite overhead

4. **Maintenance Burden**
   - Schema complexity increase
   - Application code changes required
   - Operational monitoring needs

**Module: Tradeoff Analyzer** (src/analysis/tradeoff_analyzer.py)

Purpose: Evaluate competing optimizations and their interactions

**Analysis Framework:**
1. **Query Frequency Distribution**
   - Identify high-frequency queries (optimize these)
   - Identify low-frequency queries (acceptable cost increase)
   - Calculate frequency-weighted performance impact

2. **Conflict Resolution**
   - Detect when optimizations conflict
   - Prioritize based on frequency and impact
   - Suggest Duality Views when both relational and document access needed

3. **Threshold Calculation**
   - Determine when storage/compute overhead justified
   - Calculate break-even points for Duality Views
   - Identify diminishing returns

**Module: Policy Recommendation Engine** (src/llm/recommendation_engine.py)

Purpose: Generate actionable schema recommendations using LLM reasoning

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

### Phase 4: Integration & Testing 📋 PLANNED

**Integration Tests:**
- End-to-end workload analysis pipeline
- Schema recommendation generation
- Cost/benefit validation
- Oracle 23ai integration tests

**Components:**
- Integration test suite (tests/integration/)
- Performance benchmarking
- Real workload validation
- Recommendation accuracy testing

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
│ 3. PATTERN DETECTION (Planned - Next)                            │
├─────────────────────────────────────────────────────────────────┤
│ Pattern Detector                                                  │
│   ├─> LOB Cliff Detector                                         │
│   ├─> Join Dimension Analyzer                                    │
│   ├─> Document vs Relational Classifier                          │
│   └─> Duality View Opportunity Finder                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. COST/BENEFIT ANALYSIS (Planned)                               │
├─────────────────────────────────────────────────────────────────┤
│ Cost Calculator                                                   │
│   ├─> Performance Impact (query time changes)                    │
│   ├─> Storage Cost (overhead calculation)                        │
│   ├─> Compute Cost (CPU/memory impact)                          │
│   └─> Maintenance Burden (complexity score)                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. TRADEOFF ANALYSIS (Planned)                                   │
├─────────────────────────────────────────────────────────────────┤
│ Tradeoff Analyzer                                                 │
│   ├─> Query Frequency Weighting                                  │
│   ├─> Conflict Resolution                                        │
│   └─> Threshold Calculation                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. LLM-POWERED RECOMMENDATION (In Progress)                      │
├─────────────────────────────────────────────────────────────────┤
│ LLM Client (Infrastructure Layer)                                │
│   ├─> Claude API Integration                                     │
│   ├─> Prompt Engineering                                         │
│   └─> Response Parsing                                           │
│                                                                   │
│ Recommendation Engine (Analysis Layer)                           │
│   ├─> Generate comprehensive prompts                             │
│   ├─> Synthesize LLM reasoning with metrics                      │
│   ├─> Rank recommendations by net benefit                        │
│   └─> Generate implementation plans                              │
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

### Immediate (Current Sprint)
1. ✅ Update requirements.txt with anthropic SDK
2. 🔄 Implement LLM Client infrastructure
   - Claude API integration
   - Retry logic and error handling
   - Token management
   - Prompt templating

### Short-term (Next Sprint)
3. Pattern Detector implementation
   - LOB Cliff Detector
   - Join Dimension Analyzer
   - Document vs Relational Classifier
   - Duality View Opportunity Finder

4. Cost Calculator implementation
   - Performance impact estimation
   - Storage/compute cost calculation
   - Maintenance burden scoring

### Medium-term
5. Tradeoff Analyzer implementation
6. Recommendation Engine with LLM integration
7. Integration testing
8. Real workload validation

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
