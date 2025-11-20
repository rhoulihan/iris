-- Create MLflow user for experiment tracking backend
ALTER SESSION SET CONTAINER = FREEPDB1;

-- Create tablespace for MLflow
CREATE TABLESPACE mlflow_data
  DATAFILE '/opt/oracle/oradata/FREE/FREEPDB1/mlflow_data01.dbf'
  SIZE 200M AUTOEXTEND ON NEXT 50M MAXSIZE 1G;

-- Create MLflow user
CREATE USER mlflow_user IDENTIFIED BY "MlflowPass123!"
  DEFAULT TABLESPACE mlflow_data
  TEMPORARY TABLESPACE iris_temp
  QUOTA UNLIMITED ON mlflow_data;

-- Grant necessary privileges for MLflow
GRANT CREATE SESSION TO mlflow_user;
GRANT CREATE TABLE TO mlflow_user;
GRANT CREATE VIEW TO mlflow_user;
GRANT CREATE SEQUENCE TO mlflow_user;
GRANT CREATE PROCEDURE TO mlflow_user;
GRANT CREATE TRIGGER TO mlflow_user;

-- MLflow needs to be able to create and manage its own schema
GRANT RESOURCE TO mlflow_user;
GRANT CONNECT TO mlflow_user;

EXIT;
