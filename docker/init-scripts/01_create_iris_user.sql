-- Create IRIS application user
ALTER SESSION SET CONTAINER = FREEPDB1;

-- Create tablespace for IRIS
CREATE TABLESPACE iris_data
  DATAFILE '/opt/oracle/oradata/FREE/FREEPDB1/iris_data01.dbf'
  SIZE 500M AUTOEXTEND ON NEXT 100M MAXSIZE 2G;

CREATE TEMPORARY TABLESPACE iris_temp
  TEMPFILE '/opt/oracle/oradata/FREE/FREEPDB1/iris_temp01.dbf'
  SIZE 100M AUTOEXTEND ON NEXT 50M MAXSIZE 500M;

-- Create IRIS user
CREATE USER iris_user IDENTIFIED BY "IrisUser123!"
  DEFAULT TABLESPACE iris_data
  TEMPORARY TABLESPACE iris_temp
  QUOTA UNLIMITED ON iris_data;

-- Grant necessary privileges
GRANT CREATE SESSION TO iris_user;
GRANT CREATE TABLE TO iris_user;
GRANT CREATE VIEW TO iris_user;
GRANT CREATE SEQUENCE TO iris_user;
GRANT CREATE PROCEDURE TO iris_user;
GRANT CREATE TRIGGER TO iris_user;
GRANT CREATE TYPE TO iris_user;

-- Grant access to AWR views (critical for IRIS)
GRANT SELECT ON DBA_HIST_SNAPSHOT TO iris_user;
GRANT SELECT ON DBA_HIST_ACTIVE_SESS_HISTORY TO iris_user;
GRANT SELECT ON DBA_HIST_SQL_PLAN TO iris_user;
GRANT SELECT ON DBA_HIST_SQLSTAT TO iris_user;
GRANT SELECT ON DBA_HIST_SQLTEXT TO iris_user;
GRANT SELECT ON DBA_HIST_SYSSTAT TO iris_user;
GRANT SELECT ON DBA_HIST_SYSTEM_EVENT TO iris_user;
GRANT SELECT ON V_$SQL TO iris_user;
GRANT SELECT ON V_$SQL_PLAN TO iris_user;
GRANT SELECT ON V_$SESSION TO iris_user;

-- Grant Oracle Advanced Queuing privileges
GRANT EXECUTE ON DBMS_AQ TO iris_user;
GRANT EXECUTE ON DBMS_AQADM TO iris_user;
GRANT AQ_ADMINISTRATOR_ROLE TO iris_user;

-- Note: JSON Duality View privileges granted via CREATE VIEW privilege

-- Grant In-Memory privileges
GRANT EXECUTE ON DBMS_INMEMORY_ADMIN TO iris_user;

-- Enable AWR snapshots (if not already enabled)
BEGIN
  DBMS_WORKLOAD_REPOSITORY.MODIFY_SNAPSHOT_SETTINGS(
    retention => 10080,  -- 7 days
    interval => 15       -- 15 minutes
  );
END;
/

EXIT;
