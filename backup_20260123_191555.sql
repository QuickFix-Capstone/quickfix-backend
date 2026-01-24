-- MySQL dump 10.13  Distrib 5.7.24, for osx11.1 (x86_64)
--
-- Host: quickfix-mysql.cno624c2aarh.us-east-2.rds.amazonaws.com    Database: quickfix
-- ------------------------------------------------------
-- Server version	8.0.43

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
SET @MYSQLDUMP_TEMP_LOG_BIN = @@SESSION.SQL_LOG_BIN;
SET @@SESSION.SQL_LOG_BIN= 0;

--
-- GTID state at the beginning of the backup 
--

SET @@GLOBAL.GTID_PURGED='';

--
-- Table structure for table `admins`
--

DROP TABLE IF EXISTS `admins`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `admins` (
  `admin_id` varchar(40) NOT NULL,
  `cognito_sub` varchar(64) NOT NULL,
  `name` varchar(100) NOT NULL,
  `email` varchar(150) NOT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  `created_at` datetime NOT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`admin_id`),
  UNIQUE KEY `cognito_sub` (`cognito_sub`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `admins`
--

LOCK TABLES `admins` WRITE;
/*!40000 ALTER TABLE `admins` DISABLE KEYS */;
INSERT INTO `admins` VALUES ('7b6ece2d-af9a-4cb6-928b-e1636382b2f0','f16b05e0-d0a1-7089-518f-78f5f153ad51','Target Admin','target@example.com',1,'2026-01-14 05:40:04','2026-01-14 05:40:04');
/*!40000 ALTER TABLE `admins` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bookings`
--

DROP TABLE IF EXISTS `bookings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `bookings` (
  `booking_id` bigint NOT NULL AUTO_INCREMENT,
  `customer_id` bigint NOT NULL,
  `provider_id` varchar(40) NOT NULL,
  `service_category` varchar(100) NOT NULL,
  `service_description` text NOT NULL,
  `scheduled_date` date NOT NULL,
  `scheduled_time` time NOT NULL,
  `status` enum('pending','confirmed','in_progress','completed','cancelled') NOT NULL DEFAULT 'pending',
  `service_address` varchar(255) NOT NULL,
  `service_city` varchar(100) NOT NULL,
  `service_state` varchar(100) NOT NULL,
  `service_postal_code` varchar(20) NOT NULL,
  `estimated_price` decimal(10,2) DEFAULT NULL,
  `final_price` decimal(10,2) DEFAULT NULL,
  `notes` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `completed_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`booking_id`),
  KEY `idx_customer_id` (`customer_id`),
  KEY `idx_provider_id` (`provider_id`),
  KEY `idx_status` (`status`),
  KEY `idx_scheduled_date` (`scheduled_date`),
  CONSTRAINT `fk_booking_customer` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_booking_provider` FOREIGN KEY (`provider_id`) REFERENCES `service_providers` (`provider_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=35 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bookings`
--

LOCK TABLES `bookings` WRITE;
/*!40000 ALTER TABLE `bookings` DISABLE KEYS */;
INSERT INTO `bookings` VALUES (1,2,'SP-001','plumber','Fix leaking kitchen sink','2026-01-15','14:00:00','pending','123 Main St','Toronto','ON','M5H 1J9',150.00,NULL,'Please call before arriving','2026-01-02 02:22:27','2026-01-02 02:22:27',NULL),(2,2,'SP-002','plumber','Fix leaking kitchen sink','2026-01-15','14:00:00','pending','123 Main St','Toronto','ON','M5H 1J9',150.00,NULL,'Please call before arriving','2026-01-02 02:47:12','2026-01-02 02:47:12',NULL),(3,2,'SP-002','plumber','Fix leaking kitchen sink','2026-01-15','14:00:00','pending','123 Main St','Toronto','ON','M5H 1J9',150.00,NULL,'Please call before arriving','2026-01-02 03:03:07','2026-01-02 03:03:07',NULL),(5,2,'SP-001','PLUMBING','Emergency Plumbing Repair','2026-01-08','15:15:00','pending','4954 Rosebush Rd','Mississauga','ON','L5M 5M8',NULL,NULL,'','2026-01-04 06:14:07','2026-01-04 06:14:07',NULL),(6,2,'SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c','MOVING_SERVICES','NEW TEST','2026-01-15','12:12:00','pending','4954 Rosebush Rd','Mississauga','ON','L5M 5M8',NULL,NULL,'','2026-01-06 03:10:38','2026-01-06 03:10:38',NULL),(7,3,'SP-2f2664c0-7488-429c-9ad2-5d2c10787ead','PLUMBING','landscaping','2026-01-27','15:33:00','pending','332 Bankside Drive','Kitchener','ON','N2N 3K2',NULL,NULL,'','2026-01-06 17:33:29','2026-01-06 17:33:29',NULL),(8,5,'SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c','PLUMBING','testing','2026-01-20','14:00:00','pending','1430 Trafalgar Rd','Oakville','ON','L6H2L1',NULL,NULL,'1 hour','2026-01-15 04:31:17','2026-01-15 04:31:17',NULL),(9,5,'SP-2f2664c0-7488-429c-9ad2-5d2c10787ead','PLUMBING','admin test','2026-01-23','14:00:00','pending','1430 Trafalgar Rd','Oakville','ON','L6H 2L1',NULL,NULL,'1 hour','2026-01-21 04:08:41','2026-01-21 04:08:41',NULL),(10,5,'SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c','PLUMBING','testing','2026-12-11','12:11:00','pending','1430 Trafalgar Rd','Oakville','ON','L6H2L1',NULL,NULL,'','2026-01-21 19:45:02','2026-01-21 19:45:02',NULL),(11,5,'SP-2f2664c0-7488-429c-9ad2-5d2c10787ead','PLUMBING','admin test','2026-12-11','23:12:00','pending','1430 Trafalgar Rd','Oakville','ON','L6H2L1',NULL,NULL,'1 hour','2026-01-21 19:46:00','2026-01-21 19:46:00',NULL),(12,5,'SP-2f2664c0-7488-429c-9ad2-5d2c10787ead','PLUMBING','admin test','2026-11-12','23:00:00','pending','1430 Trafalgar Rd','Oakville','ON','L6H2L1',NULL,NULL,'1 hour','2026-01-21 19:51:00','2026-01-21 19:51:00',NULL),(13,5,'SP-2f2664c0-7488-429c-9ad2-5d2c10787ead','PLUMBING','admin test','2026-12-11','23:00:00','pending','1430 Trafalgar Rd','Oakville','ON','L6H2L1',NULL,NULL,'1 hour','2026-01-21 19:53:54','2026-01-21 19:53:54',NULL),(14,5,'SP-2f2664c0-7488-429c-9ad2-5d2c10787ead','PLUMBING','admin test','2026-12-11','23:11:00','pending','1430 Trafalgar Rd','Oakville','ON','L6H2L1',NULL,NULL,'1 hour','2026-01-21 19:56:28','2026-01-21 19:56:28',NULL),(15,5,'SP-2f2664c0-7488-429c-9ad2-5d2c10787ead','PLUMBING','landscaping','2026-12-11','23:12:00','pending','1430 Trafalgar Rd','Oakville','ON','L6H2L1',NULL,NULL,'1 hour','2026-01-21 20:05:46','2026-01-21 20:05:46',NULL),(16,5,'SP-e136768b-492e-4150-948a-9efa53f759c0','SNOW_REMOVAL','DEMO SERVICE','2026-12-11','00:22:00','pending','1430 Trafalgar Rd','Oakville','ON','L6H2L1',NULL,NULL,'1 hour','2026-01-21 20:12:40','2026-01-21 20:12:40',NULL),(17,5,'SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c','PLUMBING','3123','2026-12-11','11:11:00','pending','1430 Trafalgar Rd','Oakville','ON','L6H2L1',NULL,NULL,'1 Hour','2026-01-21 20:16:15','2026-01-21 20:16:15',NULL),(18,5,'SP-2f2664c0-7488-429c-9ad2-5d2c10787ead','PLUMBING','admin test','2026-12-11','11:11:00','pending','1430 Trafalgar Rd','Oakville','ON','L6H2L1',NULL,NULL,'1 hour','2026-01-21 20:33:45','2026-01-21 20:33:45',NULL),(19,5,'SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c','PLUMBING','testing','2026-12-11','11:11:00','pending','1430 Trafalgar Rd','Oakville','ON','L6H2L1',NULL,NULL,'1 hour','2026-01-21 21:01:58','2026-01-21 21:01:58',NULL),(20,5,'SP-e136768b-492e-4150-948a-9efa53f759c0','SNOW_REMOVAL','DEMO SERVICE','2026-12-11','11:11:00','pending','1430 Trafalgar Rd','Oakville','ON','L6H2L1',NULL,NULL,'1 hour','2026-01-21 21:30:55','2026-01-21 21:30:55',NULL),(21,5,'SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c','ROOFING','Roofing Inspection','2026-12-11','11:11:00','pending','1430 Trafalgar Rd','Oakville','ON','L6H2L1',NULL,NULL,'1 hour','2026-01-21 21:45:33','2026-01-21 21:45:33',NULL),(22,5,'SP-2f2664c0-7488-429c-9ad2-5d2c10787ead','PLUMBING','landscaping','2026-11-11','11:11:00','pending','1430 Trafalgar Rd','Oakville','ON','L6H2L1',NULL,NULL,'1 hour','2026-01-22 02:05:56','2026-01-22 02:05:56',NULL),(23,3,'SP-2f2664c0-7488-429c-9ad2-5d2c10787ead','PLUMBING','admin test','2026-01-31','00:54:00','pending','332 Bankside Drive','Kitchener','ON','N2N 3K2',NULL,NULL,'2312','2026-01-22 02:52:37','2026-01-22 02:52:37',NULL),(24,5,'SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c','PLUMBING','3123','2026-11-11','11:11:00','pending','1430 Trafalgar Rd','Oakville','ON','L6H2L1',NULL,NULL,'1 hour','2026-01-22 03:03:04','2026-01-22 03:03:04',NULL),(25,2,'SP-2f2664c0-7488-429c-9ad2-5d2c10787ead','PLUMBING','admin test','2026-01-30','14:19:00','pending','4954 Rosebush Rd','Mississauga','ON','L5M 5M8',NULL,NULL,'This is new booking test','2026-01-22 04:16:27','2026-01-22 04:16:27',NULL),(26,5,'SP-e136768b-492e-4150-948a-9efa53f759c0','SNOW_REMOVAL','DEMO SERVICE','2026-11-11','11:11:00','pending','1430 Trafalgar Rd','Oakville','ON','L6H2L1',NULL,NULL,'1 hour','2026-01-22 04:18:56','2026-01-22 04:18:56',NULL),(27,6,'SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c','ROOFING','Roofing Inspection','2026-01-28','00:11:00','pending','1430 Trafalgar Rd','Oakville','ON','L6H2L1',NULL,NULL,'1 hour','2026-01-22 04:26:49','2026-01-22 04:26:49',NULL),(28,6,'SP-2f2664c0-7488-429c-9ad2-5d2c10787ead','PLUMBING','landscaping','2026-11-11','11:11:00','pending','1430 Trafalgar Rd','Oakville','ON','L6H2L1',NULL,NULL,'1 hour','2026-01-22 04:28:24','2026-01-22 04:28:24',NULL),(29,6,'SP-2f2664c0-7488-429c-9ad2-5d2c10787ead','PLUMBING','admin test','2026-11-11','11:11:00','pending','1430 Trafalgar Rd','Oakville','ON','L6H2L1',NULL,NULL,'1 hour','2026-01-22 15:26:52','2026-01-22 15:26:52',NULL),(30,3,'SP-2f2664c0-7488-429c-9ad2-5d2c10787ead','PLUMBING','admin test','2026-01-29','21:25:00','pending','332 Bankside Drive','Kitchener','ON','N2N 3K2',NULL,NULL,'iio','2026-01-23 00:24:03','2026-01-23 00:24:03',NULL),(31,5,'SP-2f2664c0-7488-429c-9ad2-5d2c10787ead','PLUMBING','landscaping','2026-11-11','11:11:00','pending','1430 Trafalgar Rd','Oakville','ON','L6H2L1',NULL,NULL,'1 hour','2026-01-23 16:08:38','2026-01-23 16:08:38',NULL),(32,5,'SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c','ROOFING','Roofing Inspection','2026-11-11','11:11:00','pending','1430 Trafalgar Rd','Oakville','ON','L6H2L1',NULL,NULL,'1 hour','2026-01-23 16:53:09','2026-01-23 16:53:09',NULL),(33,5,'SP-2f2664c0-7488-429c-9ad2-5d2c10787ead','PLUMBING','admin test','2026-11-11','11:11:00','pending','1430 Trafalgar Rd','Oakville','ON','L6H2L1',NULL,NULL,'1 hour','2026-01-23 17:29:56','2026-01-23 17:29:56',NULL),(34,5,'SP-2f2664c0-7488-429c-9ad2-5d2c10787ead','PLUMBING','admin test','2026-11-11','11:11:00','pending','1430 Trafalgar Rd','Oakville','ON','L6H2L1',NULL,NULL,'1 hour','2026-01-23 17:38:33','2026-01-23 17:38:33',NULL);
/*!40000 ALTER TABLE `bookings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `customer_provider_reviews`
--

DROP TABLE IF EXISTS `customer_provider_reviews`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `customer_provider_reviews` (
  `review_id` bigint NOT NULL AUTO_INCREMENT,
  `job_id` bigint NOT NULL,
  `booking_id` bigint DEFAULT NULL,
  `customer_id` bigint NOT NULL,
  `provider_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `rating` int NOT NULL,
  `comment` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`review_id`),
  UNIQUE KEY `unique_reviewer_job` (`job_id`,`customer_id`),
  KEY `idx_job_id` (`job_id`),
  KEY `idx_reviewer` (`customer_id`),
  KEY `idx_reviewee_created` (`provider_id`,`created_at` DESC),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_cp_booking_id` (`booking_id`),
  CONSTRAINT `fk_cp_review_booking` FOREIGN KEY (`booking_id`) REFERENCES `bookings` (`booking_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_review_job` FOREIGN KEY (`job_id`) REFERENCES `jobs` (`job_id`) ON DELETE CASCADE,
  CONSTRAINT `chk_comment_length` CHECK (((char_length(`comment`) >= 10) and (char_length(`comment`) <= 1000))),
  CONSTRAINT `chk_rating_range` CHECK (((`rating` >= 1) and (`rating` <= 5)))
) ENGINE=InnoDB AUTO_INCREMENT=38 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `customer_provider_reviews`
--

LOCK TABLES `customer_provider_reviews` WRITE;
/*!40000 ALTER TABLE `customer_provider_reviews` DISABLE KEYS */;
INSERT INTO `customer_provider_reviews` VALUES (27,1,NULL,1,'1',5,'Test review for DELETE API - Excellent service!','2026-01-21 00:09:44','2026-01-21 00:09:44'),(34,2,NULL,2,'SP-002',4,'Good work on the electrical installation. Professional and clean.','2026-01-21 04:48:33','2026-01-21 04:48:33'),(35,3,NULL,2,'SP-003',5,'Outstanding HVAC service! Very knowledgeable and thorough.','2026-01-21 04:48:33','2026-01-21 04:48:33'),(36,1,NULL,3,'SP-001',5,'Fantastic plumbing repair! Highly recommend.','2026-01-21 04:48:33','2026-01-21 04:48:33'),(37,2,NULL,3,'SP-002',3,'Decent work but took longer than expected.','2026-01-21 04:48:33','2026-01-21 04:48:33');
/*!40000 ALTER TABLE `customer_provider_reviews` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `customers`
--

DROP TABLE IF EXISTS `customers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `customers` (
  `customer_id` bigint NOT NULL AUTO_INCREMENT,
  `first_name` varchar(100) NOT NULL,
  `last_name` varchar(100) NOT NULL,
  `email` varchar(255) NOT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `address` varchar(255) DEFAULT NULL,
  `city` varchar(100) DEFAULT NULL,
  `state` varchar(100) DEFAULT NULL,
  `postal_code` varchar(20) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `cognito_sub` varchar(255) DEFAULT NULL,
  `avatar_url` varchar(512) DEFAULT NULL COMMENT 'S3 URL for customer profile avatar',
  `total_rating_points` int NOT NULL DEFAULT '0' COMMENT 'Sum of all ratings received from providers',
  `total_review_count` int NOT NULL DEFAULT '0' COMMENT 'Total number of reviews received from providers',
  `average_rating` decimal(3,2) NOT NULL DEFAULT '0.00' COMMENT 'Calculated average rating (total_rating_points / total_review_count)',
  PRIMARY KEY (`customer_id`),
  UNIQUE KEY `uq_customers_cognito_sub` (`cognito_sub`),
  KEY `idx_customer_rating` (`average_rating` DESC)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `customers`
--

LOCK TABLES `customers` WRITE;
/*!40000 ALTER TABLE `customers` DISABLE KEYS */;
INSERT INTO `customers` VALUES (1,'Test','User','test.user@example.com','123-456-7890','123 Test St','Test City','TS','T3S 7T1','2025-12-31 01:37:56',NULL,NULL,9,2,4.50),(2,'KunPeng','Yang','ykphrfly@gmail.com','6470000001','UPDATED VIA TEST','Mississauga','ON','L5M 5M8','2026-01-01 03:41:11','415b3510-a0a1-708e-6a02-dc457aec9ecc','https://quickfix-app-files.s3.amazonaws.com/customers-avatar/415b3510-a0a1-708e-6a02-dc457aec9ecc/20260102-005121-Screenshot 2026-01-01 at 3.16.42 PM.png',14,3,4.67),(3,'Customer','1','ajaypersaudyt@gmail.com','6479841050','69696969 James Charles Drive, 12213','Kitchener','ON','N2N 3K2','2026-01-06 17:32:36','819bd5f0-e011-7081-2819-5188d5a2bb2f',NULL,7,2,3.50),(4,'Testing','Testing','persaudskip173@gmail.com','6479841111','332 Bankside Drive','Kitchener','ON','N2N 3K2','2026-01-06 19:30:47','817b75d0-a041-708d-988e-8b71cf3df92c',NULL,0,0,0.00),(5,'Jaskaran','Jot','sing5424@sheridancollege.ca','4379983716','1430 Trafalgar Rd','Oakville','ON','L6H2L1','2026-01-15 04:29:38','214b3530-7051-7066-00d7-307f8d9e468f',NULL,0,0,0.00),(6,'JOT','Jask','ps11121997@gmail.com','8979864539','7899 McLaughlin Rd','Brampton','ON',' L6Y5H9','2026-01-22 04:26:01','114b95b0-50b1-70ba-21cd-e67cce52fffe',NULL,0,0,0.00);
/*!40000 ALTER TABLE `customers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `job_applications`
--

DROP TABLE IF EXISTS `job_applications`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `job_applications` (
  `application_id` bigint NOT NULL AUTO_INCREMENT,
  `job_id` bigint NOT NULL,
  `provider_id` varchar(40) COLLATE utf8mb4_unicode_ci NOT NULL,
  `proposed_price` decimal(10,2) DEFAULT NULL,
  `message` text COLLATE utf8mb4_unicode_ci,
  `status` enum('pending','accepted','rejected') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'pending',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`application_id`),
  UNIQUE KEY `unique_application` (`job_id`,`provider_id`),
  KEY `idx_job_id` (`job_id`),
  KEY `idx_provider_id` (`provider_id`),
  KEY `idx_status` (`status`),
  CONSTRAINT `fk_application_job` FOREIGN KEY (`job_id`) REFERENCES `jobs` (`job_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `job_applications`
--

LOCK TABLES `job_applications` WRITE;
/*!40000 ALTER TABLE `job_applications` DISABLE KEYS */;
INSERT INTO `job_applications` VALUES (1,1,'SP-001',125.00,'I have 15 years of plumbing experience and can fix this today. Available immediately!','accepted','2026-01-04 00:50:25'),(2,1,'SP-005',95.00,'Experienced handyman, can handle all plumbing issues. Best price guaranteed!','rejected','2026-01-04 00:50:25'),(3,3,'SP-002',200.00,'Licensed electrician with 10+ years experience. Can start this week.','accepted','2026-01-04 00:50:25'),(4,3,'SP-005',150.00,'Handyman service - we handle all types of repairs. Quick turnaround!','rejected','2026-01-04 00:50:25'),(5,4,'SP-002',180.00,'Electrical specialist. Will diagnose and fix the power issue safely.','accepted','2026-01-04 00:50:25'),(6,4,'SP-aed80f54-56bd-46a0-83ce-2dd4334ff75a',120.00,'I can fix this today','rejected','2026-01-04 04:13:16'),(7,1001,'SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c',1211110.00,'I cant start today.','accepted','2026-01-04 04:49:10'),(8,4,'SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c',123.00,'i am','pending','2026-01-04 05:10:54'),(9,1003,'SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c',200.00,'i can do this all','pending','2026-01-04 05:51:05'),(10,1002,'SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c',200.00,'this is testing','rejected','2026-01-04 05:54:09'),(11,1007,'SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c',129.00,'i can do this\n','pending','2026-01-05 02:55:32'),(12,1007,'SP-2f2664c0-7488-429c-9ad2-5d2c10787ead',111.00,'this is sheridan campus test','pending','2026-01-06 17:29:08'),(13,1008,'SP-2f2664c0-7488-429c-9ad2-5d2c10787ead',150000.00,'150000','accepted','2026-01-06 17:35:44'),(14,1009,'SP-2f2664c0-7488-429c-9ad2-5d2c10787ead',258.00,'Message ','pending','2026-01-06 21:14:27'),(15,1001,'SP-e136768b-492e-4150-948a-9efa53f759c0',140.00,'descirption ','pending','2026-01-07 02:45:29'),(16,1009,'SP-e136768b-492e-4150-948a-9efa53f759c0',111.00,'testing','pending','2026-01-07 02:46:03'),(17,1001,'SP-2f2664c0-7488-429c-9ad2-5d2c10787ead',500.00,'test','pending','2026-01-23 20:16:29');
/*!40000 ALTER TABLE `job_applications` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `jobs`
--

DROP TABLE IF EXISTS `jobs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `jobs` (
  `job_id` bigint NOT NULL AUTO_INCREMENT,
  `customer_id` bigint NOT NULL,
  `title` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `category` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `location_address` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL,
  `location_city` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `location_state` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `location_zip` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `preferred_date` date DEFAULT NULL,
  `preferred_time` time DEFAULT NULL,
  `budget_min` decimal(10,2) DEFAULT NULL,
  `budget_max` decimal(10,2) DEFAULT NULL,
  `status` enum('open','assigned','in_progress','completed','cancelled') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'open',
  `assigned_provider_id` varchar(40) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`job_id`),
  KEY `idx_customer_id` (`customer_id`),
  KEY `idx_status` (`status`),
  KEY `idx_category` (`category`),
  KEY `idx_created_at` (`created_at`),
  CONSTRAINT `fk_job_customer` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1010 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `jobs`
--

LOCK TABLES `jobs` WRITE;
/*!40000 ALTER TABLE `jobs` DISABLE KEYS */;
INSERT INTO `jobs` VALUES (1,2,'Fix leaking kitchen sink - UPDATED','Sink has been leaking for 2 days, need urgent repair','plumber','123 Main St','Toronto','ON','M5H 1J9','2026-01-15','14:00:00',100.00,200.00,'completed',NULL,'2026-01-03 03:20:09','2026-01-08 02:41:54'),(2,2,'New Test Event','Sink has been leaking for 2 days, need urgent repair','plumber','123 Main St','Toronto','ON','M5H 1J9','2026-01-15','14:00:00',100.00,150.00,'cancelled',NULL,'2026-01-03 04:26:44','2026-01-03 18:15:04'),(3,2,'Test From Postman','Kitchen sink has been leaking for 2 days. Water is dripping from the pipe under the sink. Need urgent repair.','plumber','123 Main St','Toronto','ON','M5H 1J9','2026-01-15','14:00:00',100.00,150.00,'open',NULL,'2026-01-03 04:45:59','2026-01-04 05:12:29'),(4,2,'Fixed Kithchen power','This is job for us','electrician','123 yonge st','Mississauga','Ontario','L5M 5M8','2026-01-15','09:10:00',100.00,150.00,'open',NULL,'2026-01-03 21:05:42','2026-01-04 05:09:29'),(1001,2,'Fix Kitchen Sink Leak','Water leaking under the kitchen sink. Needs inspection and repair.','PLUMBING','123 Maple Street','Mississauga','ON','L5B 3Y4','2026-01-10','09:00:00',80.00,150.00,'open',NULL,'2026-01-04 04:40:43','2026-01-04 06:07:31'),(1002,2,'Install Ceiling Light Fixture','Need a licensed electrician to install a new ceiling light in living room.','ELECTRICAL','45 King Street West','Toronto','ON','M5H 1J8','2026-01-12','14:00:00',120.00,250.00,'open',NULL,'2026-01-04 04:40:43','2026-01-04 18:32:46'),(1003,2,'Furnace Not Heating Properly','Furnace turns on but does not heat the house evenly.','HVAC','88 Oak Avenue','Brampton','ON','L6P 2R9','2026-01-05','10:30:00',150.00,300.00,'open',NULL,'2026-01-03 08:15:00','2026-01-05 16:45:00'),(1004,2,'Deep Clean 2-Bedroom Apartment','Looking for a full deep cleaning including kitchen and bathrooms.','CLEANING','210 Lakeshore Road','Oakville','ON','L6K 1E3','2026-01-15','11:00:00',100.00,180.00,'open',NULL,'2026-01-04 04:40:43','2026-01-04 04:40:43'),(1005,2,'Assemble IKEA Furniture','Bed frame and desk need assembly.','HANDYMAN','17 Pine Crescent','Milton','ON','L9T 6K2','2026-01-08','13:00:00',70.00,120.00,'open',NULL,'2026-01-04 04:40:43','2026-01-04 04:40:43'),(1006,2,'Emergency Toilet Overflow','Toilet overflowing and water not stopping. Immediate help required.','PLUMBING','301 Dundas Street East','Toronto','ON','M5A 2A6','2026-01-04','22:00:00',200.00,400.00,'open',NULL,'2026-01-04 04:40:43','2026-01-04 04:40:43'),(1007,2,'new test','New test for post job','carpenter','123 Main St','Mississauga','ON','L5M 5M8','2026-01-13','13:55:00',100.00,150.00,'open',NULL,'2026-01-04 16:54:14','2026-01-04 16:54:14'),(1008,3,'teting my ajay','teting my ajay','other','1213 teting my ajay','Mississauga','ON','L5A 2H9','2026-01-09','03:35:00',10000.00,2000000.00,'assigned','SP-2f2664c0-7488-429c-9ad2-5d2c10787ead','2026-01-06 17:35:32','2026-01-06 17:36:04'),(1009,4,'i need a water man','i need a water man','plumber','1213 teting my ajay','Mississauga','ON','L5A 2H9','2026-01-08','19:49:00',13.00,11111.00,'open',NULL,'2026-01-06 19:44:01','2026-01-06 19:44:01');
/*!40000 ALTER TABLE `jobs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `payment`
--

DROP TABLE IF EXISTS `payment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `payment` (
  `id` int NOT NULL AUTO_INCREMENT,
  `customer_id` bigint NOT NULL,
  `provider_id` varchar(64) NOT NULL,
  `service_offering_id` varchar(64) NOT NULL,
  `amount_cents` int NOT NULL,
  `currency` varchar(10) DEFAULT 'cad',
  `status` varchar(50) DEFAULT 'pending',
  `stripe_payment_intent_id` varchar(255) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=93 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `payment`
--

LOCK TABLES `payment` WRITE;
/*!40000 ALTER TABLE `payment` DISABLE KEYS */;
INSERT INTO `payment` VALUES (78,5,'SP-e136768b-492e-4150-948a-9efa53f759c0','SO-ca7517d9-ae08-4e61-8ff2-cbbeae1b8b58',12000,'cad','pending','pi_3SsFMGRzTbQue2gf0k8DnzTF','2026-01-22 04:18:57'),(79,5,'SP-e136768b-492e-4150-948a-9efa53f759c0','SO-ca7517d9-ae08-4e61-8ff2-cbbeae1b8b58',12000,'cad','paid','pi_3SsFMFRzTbQue2gf1jJzbaYl','2026-01-22 04:18:57'),(80,6,'SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c','SO-2fd51330-35e3-4b11-8e1a-b0ba3bd1b738',12000,'cad','paid','pi_3SsFTpRzTbQue2gf0l3MEjMz','2026-01-22 04:26:49'),(81,6,'SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c','SO-2fd51330-35e3-4b11-8e1a-b0ba3bd1b738',12000,'cad','pending','pi_3SsFTsRzTbQue2gf0AjgpmBq','2026-01-22 04:26:50'),(82,6,'SP-2f2664c0-7488-429c-9ad2-5d2c10787ead','SO-f4e10380-6ec7-4cd7-9ce5-4e0e769549ab',11100,'cad','paid','pi_3SsFVMRzTbQue2gf1fMxPky0','2026-01-22 04:28:24'),(83,6,'SP-2f2664c0-7488-429c-9ad2-5d2c10787ead','SO-f4e10380-6ec7-4cd7-9ce5-4e0e769549ab',11100,'cad','pending','pi_3SsFVNRzTbQue2gf0xW0b85J','2026-01-22 04:28:24'),(84,6,'SP-2f2664c0-7488-429c-9ad2-5d2c10787ead','SO-10f177a7-2cb9-4c57-9235-d38e5971e551',1200,'cad','pending','pi_3SsPmdRzTbQue2gf1Jm9LttP','2026-01-22 15:26:53'),(85,6,'SP-2f2664c0-7488-429c-9ad2-5d2c10787ead','SO-10f177a7-2cb9-4c57-9235-d38e5971e551',1200,'cad','pending','pi_3SsPmdRzTbQue2gf1pwPKMHr','2026-01-22 15:26:53'),(86,6,'SP-2f2664c0-7488-429c-9ad2-5d2c10787ead','SO-10f177a7-2cb9-4c57-9235-d38e5971e551',1200,'cad','pending','pi_3SsQhyRzTbQue2gf0dHYAk9G','2026-01-22 16:26:08'),(87,6,'SP-2f2664c0-7488-429c-9ad2-5d2c10787ead','SO-10f177a7-2cb9-4c57-9235-d38e5971e551',1200,'cad','pending','pi_3SsUhkRzTbQue2gf1JRXBm28','2026-01-22 20:42:10'),(88,5,'SP-2f2664c0-7488-429c-9ad2-5d2c10787ead','SO-f4e10380-6ec7-4cd7-9ce5-4e0e769549ab',11100,'cad','paid','pi_3SsmubRzTbQue2gf0sZ5RW2Z','2026-01-23 16:08:39'),(89,5,'SP-2f2664c0-7488-429c-9ad2-5d2c10787ead','SO-f4e10380-6ec7-4cd7-9ce5-4e0e769549ab',11100,'cad','pending','pi_3SsmubRzTbQue2gf17LyjRt0','2026-01-23 16:08:39'),(90,5,'SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c','SO-2fd51330-35e3-4b11-8e1a-b0ba3bd1b738',12000,'cad','paid','pi_3SsnbhRzTbQue2gf0qSSliJN','2026-01-23 16:53:10'),(91,5,'SP-2f2664c0-7488-429c-9ad2-5d2c10787ead','SO-10f177a7-2cb9-4c57-9235-d38e5971e551',2756,'cad','paid','pi_3SsoBWRzTbQue2gf0TSQlHaq','2026-01-23 17:30:12'),(92,5,'SP-2f2664c0-7488-429c-9ad2-5d2c10787ead','SO-10f177a7-2cb9-4c57-9235-d38e5971e551',2756,'cad','paid','pi_3SsoJdRzTbQue2gf0y32EuMc','2026-01-23 17:38:35');
/*!40000 ALTER TABLE `payment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `provider_certifications`
--

DROP TABLE IF EXISTS `provider_certifications`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `provider_certifications` (
  `certification_id` varchar(50) NOT NULL,
  `provider_id` varchar(40) NOT NULL,
  `certification_s3_key` varchar(512) NOT NULL,
  `certification_type` varchar(100) DEFAULT NULL,
  `verification_status` varchar(20) NOT NULL DEFAULT 'PENDING',
  `uploaded_at` datetime NOT NULL,
  PRIMARY KEY (`certification_id`),
  KEY `fk_provider_certifications_provider` (`provider_id`),
  CONSTRAINT `fk_provider_certifications_provider` FOREIGN KEY (`provider_id`) REFERENCES `service_providers` (`provider_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `provider_certifications`
--

LOCK TABLES `provider_certifications` WRITE;
/*!40000 ALTER TABLE `provider_certifications` DISABLE KEYS */;
INSERT INTO `provider_certifications` VALUES ('045006e3-f681-4422-a854-c7f5521a47dd','SP-29d228a8-020a-4d94-abeb-f5ee6dac3df4','certifications/c10b15c0-b071-7001-e818-aab3968064be/d51dc18c-a3a5-4f54-a1e9-fdb2f4e7aa5d-Lab 4 - Creating Monitoring Dashboard Using Glances.pdf','GENERAL','PENDING','2026-01-22 03:23:05'),('33e384cc-7fd0-47fc-9b5f-8503c208c92a','SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c','certifications/510ba500-c021-70c2-f03e-590fd18ca5ad/ccd44d81-cce5-4bb4-a81c-ca4fc6c856d3-P1.pdf','General','PENDING','2026-01-03 01:58:33'),('49d451f3-b6c2-4406-8241-5b4ab387a01b','SP-e136768b-492e-4150-948a-9efa53f759c0','certifications/81fbb540-f0e1-70b4-15e7-8c0c04dbcc07/e8cd4eab-3bc1-4e70-b544-8a28d8bc11f4-cert.pdf','General','PENDING','2026-01-07 02:40:45'),('55ec388b-4822-4b1d-b549-6f7f3ef5914c','SP-2f2664c0-7488-429c-9ad2-5d2c10787ead','certifications/515b5500-f0c1-7031-70ee-1ef9e9413a79/3969727f-cc35-4857-823a-56b776f3c84a-cert.pdf','General','PENDING','2026-01-06 03:32:56'),('76bfa345-d475-4e93-ba9f-13fb69e9e486','SP-4282638f-9c8a-4af5-84fa-c60f9239f6c1','certifications/a10b1510-b001-705b-fa22-f91abc9f23a1/4189f3e2-fb18-4a0e-8a7d-4b0a09b27d55-Lab6.pdf','General','PENDING','2026-01-04 21:21:48'),('ed20084c-0986-4139-94c8-175bd390522e','SP-2bcd1c71-2ead-4163-a01d-1075b7448b78','certifications/81abb5e0-4031-70cb-f545-0097b65649b0/bd985e67-741e-4a94-91b4-4a8d205ddec9-Reply Document – QuickFix Capstone Project.pdf','GENERAL','PENDING','2026-01-10 21:25:35'),('fb9371f6-685a-402a-a108-f68d7eb7e749','SP-9905ad93-2e72-4227-9b73-5f0a4474b969','certifications/313b5500-20f1-7050-c56b-7e4acb990529/b591754a-6c95-4b19-b970-f790de8f7b1e-IMM5739_1-12KWOVNY.pdf','General','PENDING','2026-01-04 23:43:47');
/*!40000 ALTER TABLE `provider_certifications` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `provider_customer_reviews`
--

DROP TABLE IF EXISTS `provider_customer_reviews`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `provider_customer_reviews` (
  `review_id` bigint NOT NULL AUTO_INCREMENT,
  `job_id` bigint NOT NULL,
  `booking_id` bigint DEFAULT NULL,
  `provider_id` varchar(50) NOT NULL,
  `customer_id` bigint NOT NULL,
  `rating` int NOT NULL,
  `comment` text NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`review_id`),
  UNIQUE KEY `unique_provider_job` (`provider_id`,`job_id`),
  KEY `idx_provider` (`provider_id`),
  KEY `idx_customer` (`customer_id`),
  KEY `idx_job` (`job_id`),
  KEY `idx_pc_booking_id` (`booking_id`),
  CONSTRAINT `fk_pc_review_booking` FOREIGN KEY (`booking_id`) REFERENCES `bookings` (`booking_id`) ON DELETE CASCADE,
  CONSTRAINT `provider_customer_reviews_ibfk_1` FOREIGN KEY (`job_id`) REFERENCES `jobs` (`job_id`) ON DELETE CASCADE,
  CONSTRAINT `provider_customer_reviews_ibfk_2` FOREIGN KEY (`provider_id`) REFERENCES `service_providers` (`provider_id`) ON DELETE CASCADE,
  CONSTRAINT `provider_customer_reviews_ibfk_3` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE CASCADE,
  CONSTRAINT `provider_customer_reviews_chk_1` CHECK ((`rating` between 1 and 5))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `provider_customer_reviews`
--

LOCK TABLES `provider_customer_reviews` WRITE;
/*!40000 ALTER TABLE `provider_customer_reviews` DISABLE KEYS */;
/*!40000 ALTER TABLE `provider_customer_reviews` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `service_offerings`
--

DROP TABLE IF EXISTS `service_offerings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `service_offerings` (
  `service_offering_id` varchar(40) NOT NULL,
  `provider_id` varchar(40) NOT NULL,
  `title` varchar(150) NOT NULL,
  `description` text NOT NULL,
  `category` varchar(50) NOT NULL,
  `price` decimal(10,2) NOT NULL,
  `pricing_type` varchar(30) NOT NULL,
  `rating` decimal(3,2) DEFAULT '0.00',
  `main_image_url` varchar(512) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`service_offering_id`),
  KEY `fk_service_offering_provider` (`provider_id`),
  CONSTRAINT `fk_service_offering_provider` FOREIGN KEY (`provider_id`) REFERENCES `service_providers` (`provider_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `service_offerings`
--

LOCK TABLES `service_offerings` WRITE;
/*!40000 ALTER TABLE `service_offerings` DISABLE KEYS */;
INSERT INTO `service_offerings` VALUES ('SO-10f177a7-2cb9-4c57-9235-d38e5971e551','SP-2f2664c0-7488-429c-9ad2-5d2c10787ead','admin test','admin test','PLUMBING',12.00,'HOURLY',0.00,'service-offerings/SP-2f2664c0-7488-429c-9ad2-5d2c10787ead/SP-2f2664c0-7488-429c-9ad2-5d2c10787ead_admin-test_f579729d.jpg',1,'2026-01-13 19:31:15'),('SO-25fa6cac-6e90-42c5-b87f-7c3b4dec7b4d','SP-9905ad93-2e72-4227-9b73-5f0a4474b969','bedroom cleaning','bedroom cleaning','CLEANING',120.00,'HOURLY',0.00,NULL,1,'2026-01-05 01:03:04'),('SO-2fd51330-35e3-4b11-8e1a-b0ba3bd1b738','SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c','Roofing Inspection','Roofing Inspection','ROOFING',120.00,'FIXED',0.00,'service-offerings/SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c/SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c_roofing-inspection_80cd75f6.jpg',1,'2026-01-05 03:08:34'),('SO-34089e2e-5be3-47f0-b26a-1cc160eda076','SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c','3123','213123','PLUMBING',213.00,'HOURLY',0.00,'service-offerings/SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c/SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c_3123_a76fae85.png',1,'2026-01-12 21:03:08'),('SO-57de4abd-e2c6-4d6e-8a50-c94af086d5b2','SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c','NEW TEST','NEW TEST','MOVING_SERVICES',1208.00,'HOURLY',0.00,'service-offerings/SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c/SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c_new-test_292270ec.jpg',1,'2026-01-05 16:47:27'),('SO-5a95b50c-0d16-4fea-b40a-35c280842871','SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c','pipe cleaning','pipe cleaning','PLUMBING',110.00,'HOURLY',0.00,NULL,1,'2026-01-04 22:08:51'),('SO-5dd2103e-ceb3-481b-a79d-b15ee4ec4627','SP-9905ad93-2e72-4227-9b73-5f0a4474b969','water','water','JUNK_REMOVAL',11111.00,'HOURLY',0.00,'service-offerings/SP-9905ad93-2e72-4227-9b73-5f0a4474b969/SP-9905ad93-2e72-4227-9b73-5f0a4474b969_water_6bdc3298.jpg',1,'2026-01-05 01:38:30'),('SO-5efc876c-ad59-492f-ba99-a1b81f9502fd','SP-9905ad93-2e72-4227-9b73-5f0a4474b969','Ajay Tets','Ajay Tets','PLUMBING',1212.00,'HOURLY',0.00,NULL,1,'2026-01-05 01:14:12'),('SO-6caec370-4df5-45fe-8860-c3e910cc1cef','SP-9905ad93-2e72-4227-9b73-5f0a4474b969','test image','test image','PLUMBING',121.00,'HOURLY',0.00,NULL,1,'2026-01-05 01:22:35'),('SO-8699f6d1-0ffb-4583-b383-a1acc7e10f82','SP-2f2664c0-7488-429c-9ad2-5d2c10787ead','Test AMplify','Test AMplify','ROOFING',696969.00,'HOURLY',0.00,'service-offerings/SP-2f2664c0-7488-429c-9ad2-5d2c10787ead/SP-2f2664c0-7488-429c-9ad2-5d2c10787ead_test-amplify_48388261.png',1,'2026-01-06 19:36:52'),('SO-8a7d866e-4432-4382-89c8-a2803f2aa902','SP-9905ad93-2e72-4227-9b73-5f0a4474b969','Water tank Cleaning','Water tank Cleaning','PLUMBING',250.00,'FIXED',0.00,'https://quickfix-app-files.s3.us-east-2.amazonaws.com/service-offerings/SP-9905ad93-2e72-4227-9b73-5f0a4474b969/SP-9905ad93-2e72-4227-9b73-5f0a4474b969_water-tank-cleaning_24b727f4.jpg',1,'2026-01-05 00:53:57'),('SO-b422c316-916e-407c-a58f-7912d316fe12','SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c','wawter lear','wawter lear','PLUMBING',122.00,'HOURLY',0.00,'',1,'2026-01-03 02:07:15'),('SO-ca7517d9-ae08-4e61-8ff2-cbbeae1b8b58','SP-e136768b-492e-4150-948a-9efa53f759c0','DEMO SERVICE','DEMO SERVICE','SNOW_REMOVAL',120.00,'HOURLY',0.00,'service-offerings/SP-e136768b-492e-4150-948a-9efa53f759c0/SP-e136768b-492e-4150-948a-9efa53f759c0_demo-service_e0ed3f95.jpg',1,'2026-01-07 02:43:46'),('SO-ca93bf88-bdf4-406e-a4c1-5813a621cf6d','SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c','testing','testing','PLUMBING',11.00,'HOURLY',0.00,'service-offerings/SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c/SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c_testing_99267486.png',1,'2026-01-13 16:39:51'),('SO-eb3c413c-8025-497c-9703-897ec78fc5bd','SP-9905ad93-2e72-4227-9b73-5f0a4474b969','testing new image','testing new image','PLUMBING',1111111.00,'HOURLY',0.00,'service-offerings/SP-9905ad93-2e72-4227-9b73-5f0a4474b969/SP-9905ad93-2e72-4227-9b73-5f0a4474b969_testing-new-image_d69ec9a8.jpg',1,'2026-01-05 01:34:43'),('SO-f4e10380-6ec7-4cd7-9ce5-4e0e769549ab','SP-2f2664c0-7488-429c-9ad2-5d2c10787ead','landscaping','landscaping','PLUMBING',111.00,'HOURLY',0.00,'service-offerings/SP-2f2664c0-7488-429c-9ad2-5d2c10787ead/SP-2f2664c0-7488-429c-9ad2-5d2c10787ead_landscaping_5e72644f.jpg',1,'2026-01-06 17:26:58'),('SO-SP001-1','SP-001','Emergency Plumbing Repair','24/7 plumbing repairs for leaks and bursts.','PLUMBING',150.00,'FIXED',4.80,'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRAjk2AT-VSnr_lGW-AiP9dFV86KPBXG0DPgQ&s',1,'2026-01-01 18:24:56'),('SO-SP001-2','SP-001','Drain Cleaning','Professional drain and pipe cleaning.','PLUMBING',90.00,'FIXED',4.70,'https://media.istockphoto.com/id/157376761/photo/close-up-of-drain-pipe-leaking-water.jpg?s=1024x1024&w=is&k=20&c=FZOllkZ2bD8HUjyFeTJW_ulUjg6AcT-W3aw23oyx7jE=',1,'2026-01-01 18:24:56'),('SO-SP002-1','SP-002','Electrical Panel Upgrade','Upgrade and replace electrical panels.','ELECTRICAL',200.00,'FIXED',4.60,'https://electriciansserviceteam.com/wp-content/uploads/2024/01/before-and-after-electrical-panel-upgrade.jpeg',1,'2026-01-01 18:24:56'),('SO-SP002-2','SP-002','Outlet & Switch Repair','Repair faulty outlets and switches.','ELECTRICAL',75.00,'FIXED',4.50,'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQxm19NHZLWFxy6UmGvczjzHhrtM5IGhR_c9Q&s',1,'2026-01-01 18:24:56'),('SO-SP003-1','SP-003','AC Repair','Fast and reliable air conditioning repair.','HVAC',120.00,'HOURLY',4.70,'https://shiptons.ca/wp-content/uploads/2023/05/Air-Conditioning-Maintenance-Service.webp',1,'2026-01-01 18:24:56'),('SO-SP003-2','SP-003','Furnace Maintenance','Seasonal furnace inspection and maintenance.','HVAC',100.00,'FIXED',4.60,'https://www.serviceexperts.ca/wp-content/uploads/2022/12/heating-FurnaceMaintenance-SupportingGD-1-1100x825-2.webp',1,'2026-01-01 18:24:56'),('SO-SP004-1','SP-004','Home Deep Cleaning','Eco-friendly full home deep cleaning.','CLEANING',140.00,'FIXED',4.90,'https://scrubnbubbles.com/wp-content/uploads/2022/05/cleaning-service.jpeg',1,'2026-01-01 18:24:56'),('SO-SP004-2','SP-004','Office Cleaning','Professional office cleaning services.','CLEANING',60.00,'HOURLY',4.80,'https://contentgrid.homedepot-static.com/hdus/en_US/DTCCOMNEW/Articles/Office-Cleaning-Hero.jpg',1,'2026-01-01 18:24:56'),('SO-SP005-1','SP-005','General Handyman Services','Repairs, installations, and small renovations.','HANDYMAN',85.00,'HOURLY',4.50,'https://gillespiehandyman.com/wp-content/uploads/2020/04/c82b0e2a-fe76-11e9-93f4-0242ac110002-jpg-thumbnail_image.jpeg',1,'2026-01-01 18:24:56'),('SO-SP005-2','SP-005','Furniture Assembly','Assemble furniture quickly and safely.','HANDYMAN',70.00,'FIXED',4.40,'https://images.ctfassets.net/vwt5n1ljn95x/3e1hJzjKMgT039qOZua4Le/55e9a93ced05255acccd3641a46526dc/SLP_Furniture_Assembly_390x182.jpg?w=3840&q=75&fm=webp',1,'2026-01-01 18:24:56'),('SO-SP006-1','SP-006','Pest Inspection','Full home pest inspection service.','PEST_CONTROL',95.00,'FIXED',4.70,'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQHNKTIKlpSHz6PAr6_BXv7yNAEX6vHRrQ9FQ&s',1,'2026-01-01 18:24:56'),('SO-SP006-2','SP-006','Rodent Removal','Safe and effective rodent removal.','PEST_CONTROL',130.00,'FIXED',4.80,'https://www.ontariowildliferemoval.ca/wp-content/uploads/2025/06/mice-removal-kitchener.jpg',1,'2026-01-01 18:24:56');
/*!40000 ALTER TABLE `service_offerings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `service_providers`
--

DROP TABLE IF EXISTS `service_providers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `service_providers` (
  `provider_id` varchar(40) NOT NULL,
  `cognito_sub` varchar(64) NOT NULL,
  `name` varchar(100) NOT NULL,
  `email` varchar(150) NOT NULL,
  `phone_number` varchar(20) DEFAULT NULL,
  `address_line` varchar(150) DEFAULT NULL,
  `city` varchar(100) DEFAULT NULL,
  `province` varchar(50) DEFAULT NULL,
  `postal_code` varchar(20) DEFAULT NULL,
  `bio` text,
  `certification_url` varchar(512) DEFAULT NULL,
  `verification_status` varchar(20) NOT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  `created_at` datetime NOT NULL,
  `business_name` varchar(255) NOT NULL,
  `updated_at` datetime NOT NULL,
  `total_rating_points` int NOT NULL DEFAULT '0' COMMENT 'Sum of all ratings received',
  `total_review_count` int NOT NULL DEFAULT '0' COMMENT 'Total number of reviews received',
  `average_rating` decimal(3,2) DEFAULT '0.00',
  `verified_by` varchar(255) DEFAULT NULL,
  `verified_at` datetime DEFAULT NULL,
  `rejection_reason` text,
  PRIMARY KEY (`provider_id`),
  UNIQUE KEY `uq_service_provider_email` (`email`),
  UNIQUE KEY `cognito_sub` (`cognito_sub`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `service_providers`
--

LOCK TABLES `service_providers` WRITE;
/*!40000 ALTER TABLE `service_providers` DISABLE KEYS */;
INSERT INTO `service_providers` VALUES ('SP-001','cognito-sp-001','John Carter','john.carter@quickfix.dev',NULL,'123 Main St','Toronto','ON','M5V1A1','Licensed plumber with 10+ years of experience.','https://example.com/cert/plumbing.pdf','VERIFIED',1,'2026-01-01 18:06:36','Carter Plumbing','0000-00-00 00:00:00',13,3,5.00,NULL,NULL,NULL),('SP-002','cognito-sp-002','Emily Rogers','emily.rogers@quickfix.dev',NULL,'456 King St','Mississauga','ON','L5B3Y4','Certified electrician specializing in residential upgrades.','https://example.com/cert/electrical.pdf','VERIFIED',1,'2026-01-01 18:06:36','Rogers Electrical','0000-00-00 00:00:00',7,2,4.00,NULL,NULL,NULL),('SP-003','cognito-sp-003','Michael Chen','michael.chen@quickfix.dev',NULL,'789 Queen St','Markham','ON','L3R5G2','HVAC technician providing fast and reliable service.','https://example.com/cert/hvac.pdf','VERIFIED',1,'2026-01-01 18:06:36','Chen HVAC Services','0000-00-00 00:00:00',13,3,5.00,NULL,NULL,NULL),('SP-004','cognito-sp-004','Sarah Patel','sarah.patel@quickfix.dev',NULL,'321 Bay St','Brampton','ON','L6T2K4','Eco-friendly residential and office cleaning specialist.','https://example.com/cert/cleaning.pdf','VERIFIED',1,'2026-01-01 18:06:36','SparkleClean Co.','0000-00-00 00:00:00',-1,0,4.00,NULL,NULL,NULL),('SP-005','cognito-sp-005','David Wilson','david.wilson@quickfix.dev',NULL,'654 Dundas St','Oakville','ON','L6H2L1','Reliable handyman for repairs and renovations.','https://example.com/cert/handyman.pdf','VERIFIED',1,'2026-01-01 18:06:36','Wilson Handyman Services','0000-00-00 00:00:00',-1,0,4.00,NULL,NULL,NULL),('SP-006','cognito-sp-006','Ayesha Khan','ayesha.khan@quickfix.dev',NULL,'987 Lakeshore Rd','Kitchener','ON','N2G1A3','Professional pest control specialist.','https://example.com/cert/pest.pdf','VERIFIED',1,'2026-01-01 18:06:36','SafeHome Pest Control','0000-00-00 00:00:00',-1,0,4.00,NULL,NULL,NULL),('SP-1047','cognito-sub-1047','Daniel Roberts','daniel.roberts@testmail.com','4165551122','210 Queen St W','Toronto','ON','M5V1Z4','Electrician offering residential wiring and lighting services.','s3://quickfix-certifications/daniel_roberts.pdf','PENDING',1,'2026-01-21 00:07:17','Roberts Electrical','2026-01-21 00:07:17',0,0,0.00,NULL,NULL,NULL),('SP-2093','cognito-sub-2093','Emily Chen','emily.chen@testmail.com','6475553344','75 Bay St','Toronto','ON','M5J2R8','Interior painter focused on condos and small offices.','s3://quickfix-certifications/emily_chen.pdf','PENDING',1,'2026-01-21 00:07:17','EC Paint Studio','2026-01-21 00:07:17',0,0,0.00,NULL,NULL,NULL),('SP-29d228a8-020a-4d94-abeb-f5ee6dac3df4','c10b15c0-b071-7001-e818-aab3968064be','JaskaranJOT','jaskaranjot11@gmail.com',NULL,'1430 Trafalgar Rd','Oakville','ON','L6H 2L1','10 years in service',NULL,'PENDING',1,'2026-01-22 03:23:05','JotPlumbers','0000-00-00 00:00:00',0,0,0.00,NULL,NULL,NULL),('SP-2bcd1c71-2ead-4163-a01d-1075b7448b78','81abb5e0-4031-70cb-f545-0097b65649b0','Ajay Persaud 21323123','gqasuhmkgdcvbokfzn@xfavaj.com',NULL,'332 Bankside Drive','Kitchener','ON','N2N 3K2','12312312321',NULL,'VERIFIED',1,'2026-01-10 21:25:35','Other213231','2026-01-20 20:40:38',-1,0,4.00,'b12ba550-c081-70c0-9852-303bd8a7b85a','2026-01-20 20:40:38',NULL),('SP-2f2664c0-7488-429c-9ad2-5d2c10787ead','515b5500-f0c1-7031-70ee-1ef9e9413a79','Ajay Persaud','ajaypersaud04@gmail.com','6479841050','332 Bankside Drive','Kitchener','ON','N2N 3K2','We provide reliable, high-quality landscaping services designed to keep your outdoor spaces clean, healthy, and visually appealing. From routine lawn care to seasonal cleanups, we focus on precision, consistency, and customer satisfaction.',NULL,'VERIFIED',1,'2026-01-06 03:32:56','VerdantLine Landscaping Updtaed','2026-01-06 18:52:52',-1,0,4.00,NULL,NULL,NULL),('SP-3321','cognito-sub-3321','Mohammed Ali','mohammed.ali@testmail.com','9055557788','19 Lakeshore Rd','Oakville','ON','L6K1C2','HVAC technician specializing in AC and furnace maintenance.','s3://quickfix-certifications/mohammed_ali.pdf','PENDING',1,'2026-01-21 00:07:17','Ali HVAC Services','2026-01-21 00:07:17',0,0,0.00,NULL,NULL,NULL),('SP-380f2870-2ee7-4183-8a91-11ab24b93792','1111-2132-2131-ef31-bbf1cea82651','Ajay Persaud','ajasdasdasdasdy.p@example.com',NULL,'21321312 Bankside Drive','Kitchener','ON','N2N 3K2','Certified professional',NULL,'VERIFIED',1,'2026-01-02 19:40:09','Other','0000-00-00 00:00:00',-1,0,4.00,NULL,NULL,NULL),('SP-4282638f-9c8a-4af5-84fa-c60f9239f6c1','a10b1510-b001-705b-fa22-f91abc9f23a1','Ajay King','ajaypersaud4@gmail.com','519-555-7788','332 Bankside Drive','Kitchener','ON','N2N 3K2','Professional plumbing and pipe cleaning services',NULL,'VERIFIED',1,'2026-01-04 21:21:48','Golden Shower Plumbing','2026-01-04 21:47:36',-1,0,4.00,NULL,NULL,NULL),('SP-4589','cognito-sub-4589','Jessica Brown','jessica.brown@testmail.com','2895559911','402 King St E','Hamilton','ON','L8N1C3','Professional organizer helping declutter homes and offices.','s3://quickfix-certifications/jessica_brown.pdf','PENDING',1,'2026-01-21 00:07:17','ClearSpace Organizing','2026-01-21 00:07:17',0,0,0.00,NULL,NULL,NULL),('SP-5724','cognito-sub-5724','Ryan Patel','ryan.patel@testmail.com','4165556633','150 Bloor St W','Toronto','ON','M5S1M4','IT technician providing home network setup and troubleshooting.','s3://quickfix-certifications/ryan_patel.pdf','PENDING',1,'2026-01-21 00:07:17','Patel Tech Solutions','2026-01-21 00:07:17',0,0,0.00,NULL,NULL,NULL),('SP-5a5ea285-8d2f-4343-b72d-73ddc2cc14d9','a17b1510-2132-2131-ef31-bbf1cea82651','Ajay Persaud','ajay.p@example.com',NULL,'21321312 Bankside Drive','Kitchener','ON','N2N 3K2','Certified professional',NULL,'VERIFIED',1,'2026-01-02 19:36:04','Other','0000-00-00 00:00:00',-1,0,4.00,NULL,NULL,NULL),('SP-69696','cognito-sub-12345','John Doe','john.doe@example.com','6471234567','123 Main Street','Mississauga','ON','L5B 1M7','Experienced handyman offering home repair services.','s3://quickfix-certifications/SP-001/cert.pdf','APPROVED',1,'2026-01-20 19:44:51','JD Home Services','2026-01-20 19:59:46',0,0,0.00,NULL,NULL,NULL),('SP-9905ad93-2e72-4227-9b73-5f0a4474b969','313b5500-20f1-7050-c56b-7e4acb990529','KSI','ajaypersaudyt@gmail.com','6479841050','332 Bankside Drive','Kitchener','ON','N2N 3K2','ANTMAN',NULL,'VERIFIED',1,'2026-01-04 23:43:47','WATERMAN','2026-01-05 00:20:38',-1,0,4.00,NULL,NULL,NULL),('SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c','510ba500-c021-70c2-f03e-590fd18ca5ad','Ajay','legandary362@gmail.com','6479841050','688 332 sdasd','Kitchener','ON','N2N 3K2','i deal with the water',NULL,'VERIFIED',1,'2026-01-03 01:58:33','Water Man','2026-01-05 03:03:26',-1,0,4.00,NULL,NULL,NULL),('SP-aed80f54-56bd-46a0-83ce-2dd4334ff75a','0911-2132-2131-ef31-bbf1cea82651','Ajay Persaud','sdasdajasdasdasdasdy.p@example.com','+1-647-984-1050','21321312 Bankside Drive','Kitchener','ON','N2N 3K2','Certified professional',NULL,'VERIFIED',1,'2026-01-02 19:41:37','Other','0000-00-00 00:00:00',-1,0,4.00,NULL,NULL,NULL),('SP-e136768b-492e-4150-948a-9efa53f759c0','81fbb540-f0e1-70b4-15e7-8c0c04dbcc07','Demo UPDATE','persaudskip173@gmail.com','6479841050','332 Bankside Drive','Kitchener','ON','N2N 3K2','Demo Demo UPDATE',NULL,'VERIFIED',1,'2026-01-07 02:40:45','Demo Company Demo UPDATE','2026-01-07 02:41:18',-1,0,4.00,NULL,NULL,NULL);
/*!40000 ALTER TABLE `service_providers` ENABLE KEYS */;
UNLOCK TABLES;
SET @@SESSION.SQL_LOG_BIN = @MYSQLDUMP_TEMP_LOG_BIN;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-01-23 19:16:02
