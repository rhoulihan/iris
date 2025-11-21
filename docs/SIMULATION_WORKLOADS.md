# IRIS Pipeline Simulation Workloads

This document defines three comprehensive workloads for end-to-end pipeline testing and validation.

---

## Workload 1: E-Commerce User Profiles (Relational → Document)

### Business Scenario
Customer profile management system with user preferences, addresses, and order history. Read-heavy access pattern for personalization and recommendations.

### Schema Structure
```sql
-- Parent table
CREATE TABLE customers (
    customer_id NUMBER PRIMARY KEY,
    email VARCHAR2(100),
    name VARCHAR2(100),
    created_date DATE,
    loyalty_tier VARCHAR2(20)
);

-- Child tables (1-N relationships)
CREATE TABLE customer_addresses (
    address_id NUMBER PRIMARY KEY,
    customer_id NUMBER REFERENCES customers,
    address_type VARCHAR2(20), -- 'billing', 'shipping'
    street VARCHAR2(200),
    city VARCHAR2(100),
    state VARCHAR2(2),
    zip VARCHAR2(10)
);

CREATE TABLE customer_preferences (
    pref_id NUMBER PRIMARY KEY,
    customer_id NUMBER REFERENCES customers,
    category VARCHAR2(50),
    preference_value VARCHAR2(200)
);

CREATE TABLE customer_order_history (
    order_id NUMBER PRIMARY KEY,
    customer_id NUMBER REFERENCES customers,
    order_date DATE,
    total_amount NUMBER(10,2),
    status VARCHAR2(20)
);
```

### Query Patterns & Frequencies

**Read Queries (95% of workload, ~10,000 executions/hour)**
```sql
-- Profile retrieval with all nested data (70% of reads)
SELECT c.*, a.*, p.*, o.*
FROM customers c
LEFT JOIN customer_addresses a ON c.customer_id = a.customer_id
LEFT JOIN customer_preferences p ON c.customer_id = p.customer_id
LEFT JOIN customer_order_history o ON c.customer_id = o.customer_id
WHERE c.customer_id = :1;
-- Execution: 7,000/hour, Avg time: 15ms

-- Profile lookup by email (20% of reads)
SELECT c.*, a.*
FROM customers c
LEFT JOIN customer_addresses a ON c.customer_id = a.customer_id
WHERE c.email = :1;
-- Execution: 2,000/hour, Avg time: 12ms

-- Preference lookup (5% of reads)
SELECT p.*
FROM customer_preferences p
WHERE p.customer_id = :1;
-- Execution: 500/hour, Avg time: 5ms
```

**Write Queries (5% of workload, ~500 executions/hour)**
```sql
-- New customer registration (40% of writes)
INSERT INTO customers (customer_id, email, name, created_date, loyalty_tier)
VALUES (:1, :2, :3, SYSDATE, 'BRONZE');
-- Execution: 200/hour, Avg time: 3ms

-- Add address (30% of writes)
INSERT INTO customer_addresses (address_id, customer_id, address_type, street, city, state, zip)
VALUES (:1, :2, :3, :4, :5, :6, :7);
-- Execution: 150/hour, Avg time: 2ms

-- Update preference (20% of writes)
UPDATE customer_preferences
SET preference_value = :1
WHERE customer_id = :2 AND category = :3;
-- Execution: 100/hour, Avg time: 2ms

-- Update loyalty tier (10% of writes)
UPDATE customers
SET loyalty_tier = :1
WHERE customer_id = :2;
-- Execution: 50/hour, Avg time: 2ms
```

### Table Statistics
- **customers**: 1,000,000 rows, avg_row_len: 150 bytes
- **customer_addresses**: 2,500,000 rows (avg 2.5 addresses/customer), avg_row_len: 200 bytes
- **customer_preferences**: 5,000,000 rows (avg 5 prefs/customer), avg_row_len: 100 bytes
- **customer_order_history**: 10,000,000 rows (avg 10 orders/customer), avg_row_len: 80 bytes

### Expected Pattern Detection
- **JoinDimensionAnalyzer**: Detects expensive 3-4 table joins with high execution frequency
- **DocumentRelationalClassifier**: Should detect:
  - Read/Write Ratio: 95:5 (highly read-heavy)
  - Join Complexity: 3-4 tables per query
  - Data Access Pattern: Always fetching parent + children together
  - Update Velocity: Low (5% writes, mostly inserts)

### Expected Recommendation
**Pattern Type**: DOCUMENT_RELATIONAL
**Recommendation**: Convert to JSON document collection
**Confidence**: HIGH (>0.8)
**Priority**: HIGH

**Recommended Schema**:
```sql
CREATE TABLE customer_profiles (
    customer_id NUMBER PRIMARY KEY,
    profile_doc JSON,
    CONSTRAINT check_json CHECK (profile_doc IS JSON)
);

-- JSON structure:
{
    "customerId": 12345,
    "email": "user@example.com",
    "name": "John Doe",
    "loyaltyTier": "GOLD",
    "addresses": [
        {"type": "billing", "street": "123 Main St", ...},
        {"type": "shipping", "street": "456 Oak Ave", ...}
    ],
    "preferences": [
        {"category": "communication", "value": "email"},
        {"category": "newsletter", "value": "weekly"}
    ],
    "orderHistory": [...]
}
```

**Expected Benefits**:
- Reduced I/O: Single table scan vs 4-table join
- Lower latency: ~15ms → ~3ms (80% improvement)
- Simplified queries: Single SELECT vs JOIN

---

## Workload 2: Real-Time Inventory Management (Document → Relational)

### Business Scenario
High-velocity inventory tracking system with frequent stock updates, reservations, and complex transactional workflows. Currently using JSON documents but suffering from consistency issues.

### Current Schema Structure
```sql
-- Current: JSON document approach
CREATE TABLE inventory_items (
    item_id NUMBER PRIMARY KEY,
    inventory_doc JSON,
    last_updated TIMESTAMP,
    CONSTRAINT check_json CHECK (inventory_doc IS JSON)
);

-- JSON structure being used:
{
    "itemId": "SKU-12345",
    "description": "Product Name",
    "warehouses": [
        {
            "warehouseId": "WH-001",
            "location": "Building A",
            "stockLevels": [
                {"bin": "A1-001", "quantity": 50, "reserved": 10},
                {"bin": "A1-002", "quantity": 25, "reserved": 5}
            ]
        }
    ],
    "transactions": [
        {"type": "receipt", "quantity": 100, "timestamp": "..."},
        {"type": "shipment", "quantity": 30, "timestamp": "..."}
    ],
    "pricing": {
        "cost": 10.50,
        "retail": 19.99,
        "discounts": [...]
    }
}
```

### Query Patterns & Frequencies

**Read Queries (30% of workload, ~3,000 executions/hour)**
```sql
-- Stock level check (60% of reads)
SELECT JSON_VALUE(inventory_doc, '$.warehouses[*].stockLevels[*].quantity')
FROM inventory_items
WHERE item_id = :1;
-- Execution: 1,800/hour, Avg time: 8ms

-- Available quantity (unreserved) (30% of reads)
SELECT JSON_VALUE(inventory_doc, '$.warehouses[0].stockLevels[0].quantity') -
       JSON_VALUE(inventory_doc, '$.warehouses[0].stockLevels[0].reserved')
FROM inventory_items
WHERE item_id = :1;
-- Execution: 900/hour, Avg time: 10ms

-- Warehouse-specific lookup (10% of reads)
SELECT inventory_doc
FROM inventory_items
WHERE JSON_EXISTS(inventory_doc, '$.warehouses[?(@.warehouseId == "WH-001")]');
-- Execution: 300/hour, Avg time: 25ms (table scan!)
```

**Write Queries (70% of workload, ~7,000 executions/hour)**
```sql
-- Update stock quantity (40% of writes)
UPDATE inventory_items
SET inventory_doc = JSON_TRANSFORM(
    inventory_doc,
    SET '$.warehouses[0].stockLevels[0].quantity' = :new_qty
),
last_updated = SYSTIMESTAMP
WHERE item_id = :1;
-- Execution: 2,800/hour, Avg time: 15ms

-- Reserve stock (30% of writes)
UPDATE inventory_items
SET inventory_doc = JSON_TRANSFORM(
    inventory_doc,
    SET '$.warehouses[0].stockLevels[0].reserved' =
        JSON_VALUE(inventory_doc, '$.warehouses[0].stockLevels[0].reserved') + :reserve_qty
),
last_updated = SYSTIMESTAMP
WHERE item_id = :1;
-- Execution: 2,100/hour, Avg time: 18ms

-- Add transaction record (20% of writes)
UPDATE inventory_items
SET inventory_doc = JSON_TRANSFORM(
    inventory_doc,
    APPEND '$.transactions' = JSON_OBJECT(
        'type' VALUE :txn_type,
        'quantity' VALUE :qty,
        'timestamp' VALUE SYSTIMESTAMP
    )
),
last_updated = SYSTIMESTAMP
WHERE item_id = :1;
-- Execution: 1,400/hour, Avg time: 20ms

-- Insert new item (10% of writes)
INSERT INTO inventory_items (item_id, inventory_doc, last_updated)
VALUES (:1, :2, SYSTIMESTAMP);
-- Execution: 700/hour, Avg time: 5ms
```

### Table Statistics
- **inventory_items**: 500,000 rows, avg_row_len: 4,000 bytes (large JSON docs)
- Document size growing over time (transactions array)
- High update contention on popular items

### Expected Pattern Detection
- **DocumentRelationalClassifier**: Should detect:
  - Read/Write Ratio: 30:70 (write-heavy)
  - Update Frequency: Very high (7,000/hour)
  - Document Complexity: Nested arrays, frequent partial updates
  - Access Pattern: Mostly accessing specific fields, not entire document
  - Growth Pattern: Documents growing unbounded (transactions array)

### Expected Recommendation
**Pattern Type**: DOCUMENT_RELATIONAL
**Recommendation**: Normalize to relational schema
**Confidence**: HIGH (>0.8)
**Priority**: HIGH

**Recommended Schema**:
```sql
-- Normalized relational schema
CREATE TABLE items (
    item_id VARCHAR2(20) PRIMARY KEY,
    description VARCHAR2(200),
    cost NUMBER(10,2),
    retail_price NUMBER(10,2)
);

CREATE TABLE warehouses (
    warehouse_id VARCHAR2(20) PRIMARY KEY,
    location VARCHAR2(100)
);

CREATE TABLE inventory_stock (
    stock_id NUMBER PRIMARY KEY,
    item_id VARCHAR2(20) REFERENCES items,
    warehouse_id VARCHAR2(20) REFERENCES warehouses,
    bin_location VARCHAR2(20),
    quantity NUMBER,
    reserved NUMBER,
    CONSTRAINT ck_qty CHECK (quantity >= reserved)
);

CREATE INDEX idx_stock_item_wh ON inventory_stock(item_id, warehouse_id);

CREATE TABLE inventory_transactions (
    txn_id NUMBER PRIMARY KEY,
    item_id VARCHAR2(20) REFERENCES items,
    warehouse_id VARCHAR2(20) REFERENCES warehouses,
    txn_type VARCHAR2(20),
    quantity NUMBER,
    txn_timestamp TIMESTAMP
);

CREATE INDEX idx_txn_item ON inventory_transactions(item_id, txn_timestamp);
```

**Expected Benefits**:
- Atomic updates to individual stock levels (no JSON_TRANSFORM overhead)
- Efficient queries on specific warehouses/bins (indexed access)
- ACID guarantees for reservations
- Bounded row size (no growing transaction arrays)
- Better concurrency (row-level locks vs document-level)
- Query optimization: ~20ms → ~2ms for updates

---

## Workload 3: Sales Order System with Analytics (Hybrid → Duality Views)

### Business Scenario
OLTP order processing system that also needs to support heavy analytical workloads for dashboards, reporting, and business intelligence. Currently serving two user populations with different access patterns.

### Schema Structure
```sql
CREATE TABLE orders (
    order_id NUMBER PRIMARY KEY,
    customer_id NUMBER,
    order_date DATE,
    status VARCHAR2(20),
    total_amount NUMBER(10,2),
    shipping_address VARCHAR2(500),
    billing_address VARCHAR2(500)
);

CREATE TABLE order_items (
    item_id NUMBER PRIMARY KEY,
    order_id NUMBER REFERENCES orders,
    product_id NUMBER,
    quantity NUMBER,
    unit_price NUMBER(10,2),
    discount NUMBER(5,2)
);

CREATE TABLE order_payments (
    payment_id NUMBER PRIMARY KEY,
    order_id NUMBER REFERENCES orders,
    payment_method VARCHAR2(20),
    amount NUMBER(10,2),
    payment_date DATE
);
```

### Query Patterns & Frequencies

**OLTP Workload (60% of total, ~6,000 executions/hour)**

```sql
-- Order lookup (50% of OLTP)
SELECT o.*, oi.*, op.*
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
LEFT JOIN order_payments op ON o.order_id = op.order_id
WHERE o.order_id = :1;
-- Execution: 3,000/hour, Avg time: 8ms

-- Create order (20% of OLTP)
INSERT INTO orders (order_id, customer_id, order_date, status, total_amount, ...)
VALUES (:1, :2, SYSDATE, 'PENDING', :3, ...);
-- Execution: 1,200/hour, Avg time: 3ms

-- Add order items (20% of OLTP)
INSERT INTO order_items (item_id, order_id, product_id, quantity, unit_price, discount)
VALUES (:1, :2, :3, :4, :5, :6);
-- Execution: 1,200/hour (multiple per order), Avg time: 2ms

-- Update order status (10% of OLTP)
UPDATE orders
SET status = :1
WHERE order_id = :2;
-- Execution: 600/hour, Avg time: 2ms
```

**Analytics Workload (40% of total, ~4,000 executions/hour)**

```sql
-- Daily sales summary (25% of analytics)
SELECT
    TRUNC(order_date) as day,
    COUNT(*) as order_count,
    SUM(total_amount) as revenue,
    AVG(total_amount) as avg_order_value
FROM orders
WHERE order_date >= TRUNC(SYSDATE) - 30
GROUP BY TRUNC(order_date);
-- Execution: 1,000/hour, Avg time: 150ms

-- Top products analysis (25% of analytics)
SELECT
    oi.product_id,
    COUNT(DISTINCT oi.order_id) as orders,
    SUM(oi.quantity) as units_sold,
    SUM(oi.quantity * oi.unit_price) as revenue
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_date >= TRUNC(SYSDATE) - 7
GROUP BY oi.product_id
ORDER BY revenue DESC
FETCH FIRST 20 ROWS ONLY;
-- Execution: 1,000/hour, Avg time: 200ms

-- Customer order history with items (25% of analytics)
SELECT
    o.order_id,
    o.order_date,
    o.status,
    JSON_ARRAYAGG(
        JSON_OBJECT(
            'product_id' VALUE oi.product_id,
            'quantity' VALUE oi.quantity,
            'price' VALUE oi.unit_price
        )
    ) as items
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.customer_id = :1
GROUP BY o.order_id, o.order_date, o.status;
-- Execution: 1,000/hour, Avg time: 120ms

-- Real-time dashboard queries (25% of analytics)
SELECT
    COUNT(*) as total_orders,
    COUNT(CASE WHEN status = 'COMPLETED' THEN 1 END) as completed,
    COUNT(CASE WHEN status = 'PENDING' THEN 1 END) as pending,
    SUM(total_amount) as total_revenue
FROM orders
WHERE order_date >= TRUNC(SYSDATE);
-- Execution: 1,000/hour, Avg time: 80ms
```

### Table Statistics
- **orders**: 5,000,000 rows, avg_row_len: 250 bytes
- **order_items**: 20,000,000 rows (avg 4 items/order), avg_row_len: 100 bytes
- **order_payments**: 5,500,000 rows (some split payments), avg_row_len: 80 bytes

### Expected Pattern Detection
- **JoinDimensionAnalyzer**: Detects frequent 2-3 table joins
- **DualityViewOpportunityFinder**: Should detect:
  - Dual Access Patterns: OLTP (transactional) + Analytics (aggregate/JSON)
  - OLTP Queries: 60% using traditional SQL with joins
  - Analytics Queries: 40% needing flexible JSON output or aggregations
  - Steady concurrent workload from both populations
  - Some queries already using JSON_OBJECT/JSON_ARRAYAGG

### Expected Recommendation
**Pattern Type**: DUALITY_VIEW_OPPORTUNITY
**Recommendation**: Create Oracle 23ai JSON Duality Views
**Confidence**: HIGH (>0.8)
**Priority**: MEDIUM-HIGH

**Recommended Implementation**:
```sql
-- Keep existing relational tables for OLTP (ACID guarantees)
-- Add Duality Views for flexible JSON access

CREATE JSON RELATIONAL DUALITY VIEW order_dv AS
SELECT JSON {
    'orderId': o.order_id,
    'customerId': o.customer_id,
    'orderDate': o.order_date,
    'status': o.status,
    'totalAmount': o.total_amount,
    'shippingAddress': o.shipping_address,
    'items': [
        SELECT JSON {
            'itemId': oi.item_id,
            'productId': oi.product_id,
            'quantity': oi.quantity,
            'unitPrice': oi.unit_price,
            'discount': oi.discount
        }
        FROM order_items oi
        WHERE oi.order_id = o.order_id
    ],
    'payments': [
        SELECT JSON {
            'paymentId': op.payment_id,
            'method': op.payment_method,
            'amount': op.amount,
            'date': op.payment_date
        }
        FROM order_payments op
        WHERE op.order_id = o.order_id
    ]
}
FROM orders o;
```

**Expected Benefits**:
- OLTP queries continue using relational tables (optimized performance)
- Analytics can use Duality View for flexible JSON access
- Single source of truth (no data duplication/sync issues)
- ACID guarantees maintained (Duality Views are updatable)
- Simplified analytics queries: No manual JSON_ARRAYAGG needed
- Better developer experience: Apps can use JSON or SQL as needed

**Tradeoff Analysis**:
- Pro: Supports both access patterns without duplication
- Pro: Maintains ACID guarantees
- Pro: No application migration needed (backwards compatible)
- Con: Small overhead for view maintenance
- Con: Requires Oracle 23ai or later

---

## Simulation Execution Plan

### Phase 1: Data Generation
1. Generate synthetic data for all three schemas
2. Load into Oracle 26ai test database
3. Collect baseline statistics (DBA_TABLES, DBA_INDEXES)

### Phase 2: Workload Simulation
1. Execute query patterns at specified frequencies
2. Capture AWR snapshots (begin/end)
3. Collect SQL statistics

### Phase 3: Pipeline Execution
1. Run PipelineOrchestrator with AWR snapshots
2. Verify pattern detection for each workload
3. Validate recommendations against expected outcomes

### Phase 4: Validation
1. Compare actual vs expected recommendations
2. Verify confidence scores and priorities
3. Test tradeoff analysis (if conflicting patterns detected)

---

## Success Criteria

### Workload 1 Success
- ✅ JoinDimensionAnalyzer detects expensive joins
- ✅ DocumentRelationalClassifier recommends DOCUMENT storage
- ✅ Confidence ≥ 0.7
- ✅ Priority = HIGH
- ✅ Generated SQL includes JSON document schema

### Workload 2 Success
- ✅ DocumentRelationalClassifier recommends RELATIONAL schema
- ✅ Confidence ≥ 0.7
- ✅ Priority = HIGH
- ✅ Generated SQL includes normalized relational tables

### Workload 3 Success
- ✅ DualityViewOpportunityFinder detects hybrid pattern
- ✅ Recommendation includes Duality View creation
- ✅ Confidence ≥ 0.7
- ✅ Priority = MEDIUM or HIGH
- ✅ Generated SQL includes CREATE JSON RELATIONAL DUALITY VIEW

---

## Next Steps

1. Review workload specifications
2. Create data generation scripts (Python + Faker)
3. Create workload execution scripts (simulate queries)
4. Build integration test harness
5. Execute simulations and validate results
