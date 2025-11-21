-- Workload 2: Real-Time Inventory Management Schema
-- JSON document schema that should be recommended for relational normalization

-- Drop existing objects (errors handled by Python)
DROP TABLE inventory_items CASCADE CONSTRAINTS;
DROP SEQUENCE seq_item_id;

-- Current: JSON document approach
CREATE TABLE inventory_items (
    item_id VARCHAR2(20) PRIMARY KEY,
    inventory_doc JSON,
    last_updated TIMESTAMP DEFAULT SYSTIMESTAMP,
    CONSTRAINT check_json CHECK (inventory_doc IS JSON)
);

-- Create index for JSON queries
CREATE INDEX idx_inv_warehouse ON inventory_items i (
    JSON_VALUE(i.inventory_doc, '$.warehouses[0].warehouseId')
);

-- Create sequence
CREATE SEQUENCE seq_item_id START WITH 1 INCREMENT BY 1;

-- Sample JSON structure for reference:
/*
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
        {"type": "receipt", "quantity": 100, "timestamp": "2025-01-15T10:30:00Z"},
        {"type": "shipment", "quantity": 30, "timestamp": "2025-01-15T14:20:00Z"}
    ],
    "pricing": {
        "cost": 10.50,
        "retail": 19.99,
        "discounts": []
    }
}
*/
