-- ============================================================================
-- Hotel Kong Arthur Operations & Analytics Platform
-- 02_reference_data.sql: 8 room types (214 rooms) and 24 seasonal rate bands
-- (data-model.md §2.1–§2.2)
-- ============================================================================

SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

INSERT INTO room_types (id, name, name_da, room_count, max_guests) VALUES
    (1, 'Standard Single', 'Standard enkeltværelse', 27, 1),
    (2, 'Grand Lit', 'Grand lit værelse', 27, 2),
    (3, 'Standard Double', 'Standard dobbeltværelse', 27, 2),
    (4, 'Superior Double', 'Superior dobbeltværelse', 27, 2),
    (5, 'Junior Suite', 'Junior suite', 27, 2),
    (6, 'Spa Executive', 'Spa executive', 27, 2),
    (7, 'Suite', 'Suite', 26, 2),
    (8, 'LOFT Suite', 'LOFT suite', 26, 3);

INSERT INTO room_type_rates (room_type_id, season, min_nightly_dkk, max_nightly_dkk, standard_nightly_dkk) VALUES
    -- 1. Standard Single
    (1, 'low',  900.00, 1200.00, 1050.00),
    (1, 'mid', 1000.00, 1300.00, 1150.00),
    (1, 'high', 1200.00, 1500.00, 1350.00),
    -- 2. Grand Lit
    (2, 'low', 1100.00, 1400.00, 1250.00),
    (2, 'mid', 1200.00, 1600.00, 1400.00),
    (2, 'high', 1400.00, 1800.00, 1600.00),
    -- 3. Standard Double
    (3, 'low', 1200.00, 1600.00, 1400.00),
    (3, 'mid', 1300.00, 1700.00, 1500.00),
    (3, 'high', 1600.00, 2000.00, 1800.00),
    -- 4. Superior Double
    (4, 'low', 1400.00, 1800.00, 1600.00),
    (4, 'mid', 1500.00, 2000.00, 1750.00),
    (4, 'high', 1800.00, 2200.00, 2000.00),
    -- 5. Junior Suite
    (5, 'low', 1800.00, 2200.00, 2000.00),
    (5, 'mid', 2000.00, 2400.00, 2200.00),
    (5, 'high', 2200.00, 2500.00, 2350.00),
    -- 6. Spa Executive
    (6, 'low', 2000.00, 2500.00, 2250.00),
    (6, 'mid', 2200.00, 2600.00, 2400.00),
    (6, 'high', 2500.00, 2800.00, 2650.00),
    -- 7. Suite
    (7, 'low', 2500.00, 3000.00, 2750.00),
    (7, 'mid', 2700.00, 3300.00, 3000.00),
    (7, 'high', 3000.00, 3500.00, 3250.00),
    -- 8. LOFT Suite
    (8, 'low', 3000.00, 3500.00, 3250.00),
    (8, 'mid', 3200.00, 3800.00, 3500.00),
    (8, 'high', 3500.00, 4000.00, 3750.00);

