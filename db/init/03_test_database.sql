-- ============================================================================
-- Hotel Kong Arthur Operations & Analytics Platform
-- 03_test_database.sql: the separate hotel_test database used by the automated tests (research R16)
-- The test harness builds the schema in it from 01_schema.sql and 02_reference_data.sql.
-- ============================================================================

CREATE DATABASE hotel_test WITH ENCODING 'UTF8';

GRANT ALL PRIVILEGES ON DATABASE hotel_test TO hotel;
