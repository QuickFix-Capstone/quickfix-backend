-- Migration: Add job_images table for 1-to-many image support
-- Date: 2026-01-30
-- Description: Allows customers to upload 3-5 images per job posting
USE quickfix;
CREATE TABLE IF NOT EXISTS job_images (
    image_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    job_id BIGINT NOT NULL,
    image_key VARCHAR(512) NOT NULL COMMENT 'S3 key (e.g., job-images/123/photo.jpg)',
    image_order TINYINT NOT NULL DEFAULT 1 COMMENT 'Display order (1-5)',
    content_type VARCHAR(50) NOT NULL COMMENT 'MIME type (e.g., image/jpeg)',
    file_size INT NULL COMMENT 'File size in bytes',
    description VARCHAR(255) NULL COMMENT 'Optional image description',
    uploaded_by_id BIGINT NOT NULL COMMENT 'Customer ID who uploaded',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_job_image_job FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE,
    CONSTRAINT fk_job_image_customer FOREIGN KEY (uploaded_by_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    INDEX idx_job_id (job_id),
    INDEX idx_uploaded_by_id (uploaded_by_id),
    INDEX idx_image_order (job_id, image_order),
    CONSTRAINT chk_job_image_order CHECK (
        image_order BETWEEN 1 AND 5
    ),
    UNIQUE KEY unique_job_order (job_id, image_order)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;