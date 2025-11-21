-- Cleanup script for all simulation workloads
-- Errors handled by Python

-- Workload 1: E-Commerce
DROP TABLE customer_order_history CASCADE CONSTRAINTS;
DROP TABLE customer_preferences CASCADE CONSTRAINTS;
DROP TABLE customer_addresses CASCADE CONSTRAINTS;
DROP TABLE customers CASCADE CONSTRAINTS;
DROP SEQUENCE seq_customer_id;
DROP SEQUENCE seq_address_id;
DROP SEQUENCE seq_pref_id;
DROP SEQUENCE seq_order_id;

-- Workload 2: Inventory
DROP TABLE inventory_items CASCADE CONSTRAINTS;
DROP SEQUENCE seq_item_id;

-- Workload 3: Orders
DROP TABLE order_payments CASCADE CONSTRAINTS;
DROP TABLE order_items CASCADE CONSTRAINTS;
DROP TABLE orders CASCADE CONSTRAINTS;
DROP SEQUENCE seq_order_id;
DROP SEQUENCE seq_item_id;
DROP SEQUENCE seq_payment_id;
