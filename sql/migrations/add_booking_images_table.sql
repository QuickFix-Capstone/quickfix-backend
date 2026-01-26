-- Migration: Add booking_images table for 1-to-many image support
-- Date: 2026-01-26
-- Description: Allows customers to upload 3-5 images per booking

USE quickfix;

CREATE TABLE IF NOT EXISTS booking_images (
    image_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    booking_id BIGINT NOT NULL,
    image_key VARCHAR(512) NOT NULL COMMENT 'S3 key (e.g., booking-images/123/photo.jpg)',
    image_order TINYINT NOT NULL DEFAULT 1 COMMENT 'Display order (1-5)',
    content_type VARCHAR(50) NOT NULL COMMENT 'MIME type (e.g., image/jpeg)',
    file_size INT NULL COMMENT 'File size in bytes',
    description VARCHAR(255) NULL COMMENT 'Optional image description',
    uploaded_by_id BIGINT NOT NULL COMMENT 'Customer ID who uploaded',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_booking_image_booking
        FOREIGN KEY (booking_id) REFERENCES bookings(booking_id) ON DELETE CASCADE,
    CONSTRAINT fk_booking_image_customer
        FOREIGN KEY (uploaded_by_id) REFERENCES customers(customer_id) ON DELETE CASCADE,

    INDEX idx_booking_id (booking_id),
    INDEX idx_uploaded_by_id (uploaded_by_id),
    INDEX idx_image_order (booking_id, image_order),

    CONSTRAINT chk_image_order CHECK (image_order BETWEEN 1 AND 5),
    UNIQUE KEY unique_booking_order (booking_id, image_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
