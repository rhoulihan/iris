-- Workload 1: E-Commerce User Profiles Schema
-- Relational schema that should be recommended for document storage

-- Drop existing objects (errors handled by Python)
DROP TABLE customer_order_history CASCADE CONSTRAINTS;
DROP TABLE customer_preferences CASCADE CONSTRAINTS;
DROP TABLE customer_addresses CASCADE CONSTRAINTS;
DROP TABLE customers CASCADE CONSTRAINTS;
DROP SEQUENCE seq_customer_id;
DROP SEQUENCE seq_address_id;
DROP SEQUENCE seq_pref_id;
DROP SEQUENCE seq_order_id;

-- Create parent table
CREATE TABLE customers (
    customer_id NUMBER PRIMARY KEY,
    email VARCHAR2(100) NOT NULL UNIQUE,
    name VARCHAR2(100) NOT NULL,
    created_date DATE DEFAULT SYSDATE,
    loyalty_tier VARCHAR2(20) DEFAULT 'BRONZE'
);

-- Create child tables (1-N relationships)
CREATE TABLE customer_addresses (
    address_id NUMBER PRIMARY KEY,
    customer_id NUMBER NOT NULL,
    address_type VARCHAR2(20) NOT NULL,
    street VARCHAR2(200) NOT NULL,
    city VARCHAR2(100) NOT NULL,
    state VARCHAR2(2) NOT NULL,
    zip VARCHAR2(10) NOT NULL,
    CONSTRAINT fk_addr_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE customer_preferences (
    pref_id NUMBER PRIMARY KEY,
    customer_id NUMBER NOT NULL,
    category VARCHAR2(50) NOT NULL,
    preference_value VARCHAR2(200) NOT NULL,
    CONSTRAINT fk_pref_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE customer_order_history (
    order_id NUMBER PRIMARY KEY,
    customer_id NUMBER NOT NULL,
    order_date DATE DEFAULT SYSDATE,
    total_amount NUMBER(10,2) NOT NULL,
    status VARCHAR2(20) DEFAULT 'COMPLETED',
    CONSTRAINT fk_order_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Create indexes for better query performance
CREATE INDEX idx_addr_customer ON customer_addresses(customer_id);
CREATE INDEX idx_pref_customer ON customer_preferences(customer_id);
CREATE INDEX idx_order_customer ON customer_order_history(customer_id);
CREATE INDEX idx_customer_email ON customers(email);

-- Create sequences
CREATE SEQUENCE seq_customer_id START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE seq_address_id START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE seq_pref_id START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE seq_order_id START WITH 1 INCREMENT BY 1;
