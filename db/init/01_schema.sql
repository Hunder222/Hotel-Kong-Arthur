-- ============================================================================
-- Hotel Kong Arthur Operations & Analytics Platform
-- 01_schema.sql: Database tables, constraints, and indexes (data-model.md §2–§3)
-- ============================================================================

SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS room_types (
    id TINYINT UNSIGNED NOT NULL,
    name VARCHAR(40) NOT NULL,
    name_da VARCHAR(60) NOT NULL,
    room_count SMALLINT UNSIGNED NOT NULL,
    max_guests TINYINT UNSIGNED NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uk_room_types_name (name),
    CONSTRAINT chk_room_types_room_count CHECK (room_count > 0),
    CONSTRAINT chk_room_types_max_guests CHECK (max_guests BETWEEN 1 AND 4)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS room_type_rates (
    room_type_id TINYINT UNSIGNED NOT NULL,
    season ENUM('low', 'mid', 'high') NOT NULL,
    min_nightly_dkk DECIMAL(10, 2) NOT NULL,
    max_nightly_dkk DECIMAL(10, 2) NOT NULL,
    standard_nightly_dkk DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY (room_type_id, season),
    CONSTRAINT fk_room_type_rates_room_type
        FOREIGN KEY (room_type_id) REFERENCES room_types (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_rates_min_positive CHECK (min_nightly_dkk > 0),
    CONSTRAINT chk_rates_max_ge_min CHECK (max_nightly_dkk >= min_nightly_dkk),
    CONSTRAINT chk_rates_standard_between CHECK (
        standard_nightly_dkk >= min_nightly_dkk AND standard_nightly_dkk <= max_nightly_dkk
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS bookings (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    first_name VARCHAR(100) NOT NULL,
    family_name VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    room_type_id TINYINT UNSIGNED NOT NULL,
    check_in_date DATE NOT NULL,
    days_rented SMALLINT UNSIGNED NOT NULL,
    price_dkk DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_bookings_check_in_date (check_in_date),
    KEY ix_bookings_room_type_id (room_type_id),
    CONSTRAINT fk_bookings_room_type
        FOREIGN KEY (room_type_id) REFERENCES room_types (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_bookings_days_rented CHECK (days_rented BETWEEN 1 AND 365),
    CONSTRAINT chk_bookings_price_dkk CHECK (price_dkk > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS reviews (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    booking_id INT UNSIGNED NULL,
    room_type_id TINYINT UNSIGNED NOT NULL,
    stay_date DATE NOT NULL,
    rating TINYINT UNSIGNED NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_reviews_stay_date (stay_date),
    KEY ix_reviews_room_type_id (room_type_id),
    KEY ix_reviews_booking_id (booking_id),
    CONSTRAINT fk_reviews_booking
        FOREIGN KEY (booking_id) REFERENCES bookings (id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_reviews_room_type
        FOREIGN KEY (room_type_id) REFERENCES room_types (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_reviews_rating CHECK (rating BETWEEN 1 AND 5)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS bar_drink_sales (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    sales_year SMALLINT UNSIGNED NOT NULL,
    drink_name VARCHAR(100) NOT NULL,
    category ENUM('Cocktail', 'Coffee') NOT NULL,
    unit_price_dkk DECIMAL(10, 2) NOT NULL,
    units_sold INT UNSIGNED NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uk_bar_drink_sales_year_drink (sales_year, drink_name),
    CONSTRAINT chk_bar_drink_sales_unit_price CHECK (unit_price_dkk > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

