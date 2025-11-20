# IRIS Recommendation Engine Design Document

## Overview

The **Recommendation Engine** is the final integration layer of IRIS that combines pattern detection, cost analysis, and LLM reasoning to generate actionable, production-ready database optimization recommendations.

**Purpose**: Transform detected anti-patterns and cost estimates into comprehensive recommendations with implementation SQL, rollback plans, and testing strategies.

**Key Innovation**: Unlike traditional advisory tools that simply suggest "create index on column X", IRIS provides:
- **Context-aware recommendations** that understand query workload patterns
- **Tradeoff analysis** showing what you gain and what you sacrifice
- **LLM-generated implementation SQL** specific to Oracle 23ai/26ai
- **Conflict resolution** when multiple optimizations compete
- **ROI-ranked priorities** so you implement high-value changes first

---

## Architecture

### Phase 3 consists of 3 modules:

```
┌─────────────────────────────────────────────────────────────────┐
│ Phase 1: Pattern Detector ✅                                     │
│   ├─> LOB Cliff Detector                                        │
│   ├─> Join Dimension Analyzer                                   │
│   ├─> Document vs Relational Classifier                         │
│   └─> Duality View Opportunity Finder                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Phase 2: Cost Calculator ✅                                      │
│   ├─> Pattern-Specific Cost Calculators                         │
│   ├─> ROI Calculator                                            │
│   └─> Priority Scorer                                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Phase 3.1: Tradeoff Analyzer 🔄                                 │
│   ├─> Query Frequency Analyzer                                  │
│   ├─> Conflict Detector                                         │
│   └─> Break-Even Calculator                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Phase 3.2: Recommendation Engine Core 🔄                        │
│   ├─> Recommendation Builder                                    │
│   ├─> Implementation Planner                                    │
│   └─> Rollback Strategy Generator                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Phase 3.3: LLM Enhancement 🔄                                   │
│   ├─> Claude SQL Generator                                      │
│   ├─> Rationale Generator                                       │
│   └─> Testing Strategy Generator                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    Final Recommendations
```

---

## Success Criteria

### Functional
- ✅ Detects and resolves conflicts between optimizations
- ✅ Generates frequency-weighted impact analysis
- ✅ Produces complete recommendations with SQL, rollback, and testing
- ✅ LLM-enhanced SQL is syntactically valid Oracle DDL
- ✅ Handles all 4 pattern types (LOB, Join, Document, Duality View)

### Quality
- ✅ 80%+ test coverage across all modules
- ✅ All tests passing
- ✅ No critical security vulnerabilities (SQL injection, etc.)
- ✅ Clean code quality (Black, flake8, mypy passing)

---

See full design document content for detailed algorithms, data models, and implementation plan.
