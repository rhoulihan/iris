-- Sample schema for testing optimizations
-- This script should run as iris_user

-- Note: This script will be executed by the container initialization
-- We need to connect as iris_user within the script

ALTER SESSION SET CONTAINER = FREEPDB1;

-- Connect as iris_user
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
-- Note: This may fail on older versions, which is fine
BEGIN
  EXECUTE IMMEDIATE 'CREATE JSON COLLECTION TABLE product_catalog';
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('JSON Collections not supported in this version - skipping');
END;
/

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

-- Display summary
SELECT 'Sample schema created successfully' AS status FROM DUAL;
SELECT COUNT(*) || ' customers created' AS result FROM customers;

EXIT;
