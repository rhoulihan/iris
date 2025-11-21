-- Workload 3: Sales Order System with Analytics Schema
-- Relational OLTP schema that should be recommended for Duality Views

-- Drop existing objects (errors handled by Python)
DROP TABLE order_payments CASCADE CONSTRAINTS;
DROP TABLE order_items CASCADE CONSTRAINTS;
DROP TABLE orders CASCADE CONSTRAINTS;
DROP SEQUENCE seq_order_id;
DROP SEQUENCE seq_item_id;
DROP SEQUENCE seq_payment_id;

-- Main tables
CREATE TABLE orders (
    order_id NUMBER PRIMARY KEY,
    customer_id NUMBER NOT NULL,
    order_date DATE DEFAULT SYSDATE,
    status VARCHAR2(20) DEFAULT 'PENDING',
    total_amount NUMBER(10,2) NOT NULL,
    shipping_address VARCHAR2(500),
    billing_address VARCHAR2(500)
);

CREATE TABLE order_items (
    item_id NUMBER PRIMARY KEY,
    order_id NUMBER NOT NULL,
    product_id NUMBER NOT NULL,
    quantity NUMBER NOT NULL,
    unit_price NUMBER(10,2) NOT NULL,
    discount NUMBER(5,2) DEFAULT 0,
    CONSTRAINT fk_item_order FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

CREATE TABLE order_payments (
    payment_id NUMBER PRIMARY KEY,
    order_id NUMBER NOT NULL,
    payment_method VARCHAR2(20) NOT NULL,
    amount NUMBER(10,2) NOT NULL,
    payment_date DATE DEFAULT SYSDATE,
    CONSTRAINT fk_payment_order FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

-- Indexes for OLTP performance
CREATE INDEX idx_order_customer ON orders(customer_id);
CREATE INDEX idx_order_date ON orders(order_date);
CREATE INDEX idx_order_status ON orders(status);
CREATE INDEX idx_item_order ON order_items(order_id);
CREATE INDEX idx_item_product ON order_items(product_id);
CREATE INDEX idx_payment_order ON order_payments(order_id);

-- Sequences
CREATE SEQUENCE seq_order_id START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE seq_item_id START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE seq_payment_id START WITH 1 INCREMENT BY 1;
