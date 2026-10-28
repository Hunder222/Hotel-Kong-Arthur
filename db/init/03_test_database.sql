-- ============================================================================
-- Hotel Kong Arthur Operations & Analytics Platform
-- 03_test_database.sql: Create hotel_test database and grant access to app user
-- (research.md R16)
-- ============================================================================

CREATE DATABASE IF NOT EXISTS hotel_test
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_0900_ai_ci;

GRANT ALL PRIVILEGES ON hotel_test.* TO 'hotel'@'%';
FLUSH PRIVILEGES;

