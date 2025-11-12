-- MySQL dump 10.13  Distrib 9.4.0, for Win64 (x86_64)
--
-- Host: localhost    Database: gym_db
-- ------------------------------------------------------
-- Server version	9.4.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `attendance`
--

DROP TABLE IF EXISTS `attendance`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `attendance` (
  `attendance_id` int NOT NULL AUTO_INCREMENT,
  `member_id` int NOT NULL,
  `date` date NOT NULL,
  `status` enum('Present','Absent') NOT NULL,
  PRIMARY KEY (`attendance_id`),
  KEY `attendance_ibfk_1` (`member_id`),
  CONSTRAINT `attendance_ibfk_1` FOREIGN KEY (`member_id`) REFERENCES `member` (`member_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=614 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `attendance`
--

LOCK TABLES `attendance` WRITE;
/*!40000 ALTER TABLE `attendance` DISABLE KEYS */;
INSERT INTO `attendance` VALUES (601,401,'2024-10-01','Present'),(602,401,'2024-10-02','Present'),(603,402,'2024-10-01','Absent'),(604,403,'2024-10-01','Present'),(605,404,'2024-10-03','Present'),(606,403,'2024-10-04','Present'),(607,405,'2024-10-06','Present'),(608,405,'2024-10-08','Present'),(609,406,'2024-10-07','Absent'),(610,407,'2024-10-11','Present'),(611,408,'2024-10-12','Present'),(612,409,'2024-10-11','Absent'),(613,410,'2024-10-12','Present');
/*!40000 ALTER TABLE `attendance` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `enrollment`
--

DROP TABLE IF EXISTS `enrollment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `enrollment` (
  `member_id` int NOT NULL,
  `plan_id` int NOT NULL,
  `enrollment_date` date NOT NULL,
  PRIMARY KEY (`member_id`,`plan_id`),
  KEY `plan_id` (`plan_id`),
  CONSTRAINT `enrollment_ibfk_1` FOREIGN KEY (`member_id`) REFERENCES `member` (`member_id`) ON DELETE CASCADE,
  CONSTRAINT `enrollment_ibfk_2` FOREIGN KEY (`plan_id`) REFERENCES `membership_plan` (`plan_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `enrollment`
--

LOCK TABLES `enrollment` WRITE;
/*!40000 ALTER TABLE `enrollment` DISABLE KEYS */;
INSERT INTO `enrollment` VALUES (401,201,'2024-09-01'),(401,202,'2024-09-01'),(402,202,'2024-10-01'),(403,204,'2024-09-15'),(404,201,'2024-09-20'),(405,203,'2024-10-05'),(406,202,'2024-10-05'),(407,202,'2024-10-10'),(408,203,'2024-10-10'),(409,201,'2024-10-10'),(410,202,'2024-10-10'),(410,203,'2024-10-10'),(410,204,'2024-10-12');
/*!40000 ALTER TABLE `enrollment` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = cp850 */ ;
/*!50003 SET character_set_results = cp850 */ ;
/*!50003 SET collation_connection  = cp850_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`Vijayarudha_Meti`@`localhost`*/ /*!50003 TRIGGER `trg_recalculate_member_payment_on_enrollment` AFTER INSERT ON `enrollment` FOR EACH ROW BEGIN
    DECLARE v_total_amount DECIMAL(10, 2);

    -- Calculate total fees for all plans the member is enrolled in
    SELECT SUM(mp.fee) INTO v_total_amount
    FROM enrollment e
    INNER JOIN membership_plan mp ON e.plan_id = mp.plan_id
    WHERE e.member_id = NEW.member_id;

    -- If payment record already exists, update it
    IF EXISTS (SELECT 1 FROM payment WHERE member_id = NEW.member_id) THEN
        UPDATE payment
        SET amount = v_total_amount,
            payment_date = NOW(),
            status = 'Pending'
        WHERE member_id = NEW.member_id;
    ELSE
        -- Otherwise, create new pending payment
        INSERT INTO payment (member_id, amount, payment_date, payment_mode, status)
        VALUES (NEW.member_id, v_total_amount, NOW(), 'Cash', 'Pending');
    END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `equipment`
--

DROP TABLE IF EXISTS `equipment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `equipment` (
  `equipment_id` int NOT NULL AUTO_INCREMENT,
  `equipment_name` varchar(150) NOT NULL,
  `purchase_date` date NOT NULL,
  `condition_of_equipment` enum('Good','Okay','Bad') DEFAULT NULL,
  `trainer_id` int NOT NULL,
  PRIMARY KEY (`equipment_id`),
  KEY `trainer_id` (`trainer_id`),
  CONSTRAINT `equipment_ibfk_1` FOREIGN KEY (`trainer_id`) REFERENCES `trainer` (`trainer_id`)
) ENGINE=InnoDB AUTO_INCREMENT=306 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `equipment`
--

LOCK TABLES `equipment` WRITE;
/*!40000 ALTER TABLE `equipment` DISABLE KEYS */;
INSERT INTO `equipment` VALUES (301,'Treadmill X1','2023-01-15','Good',103),(302,'Dumbbell Set','2022-11-20','Okay',101),(303,'Yoga Mat Rack','2023-05-10','Good',102),(304,'Boxing Punching Bag','2024-02-01','Okay',103),(305,'Bench Press','2022-07-01','Bad',101);
/*!40000 ALTER TABLE `equipment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `member`
--

DROP TABLE IF EXISTS `member`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `member` (
  `member_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `DoB` date NOT NULL,
  `gender` enum('Male','Female','Other') NOT NULL,
  `contact_info` varchar(255) DEFAULT NULL,
  `trainer_id` int DEFAULT NULL,
  PRIMARY KEY (`member_id`),
  UNIQUE KEY `contact_info` (`contact_info`),
  KEY `trainer_id` (`trainer_id`),
  CONSTRAINT `member_ibfk_1` FOREIGN KEY (`trainer_id`) REFERENCES `trainer` (`trainer_id`)
) ENGINE=InnoDB AUTO_INCREMENT=418 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `member`
--

LOCK TABLES `member` WRITE;
/*!40000 ALTER TABLE `member` DISABLE KEYS */;
INSERT INTO `member` VALUES (401,'Raj Patel','1995-03-25','Male','raj.p@mail.com',101),(402,'Priya Sharma','2000-08-10','Female','priya.s@mail.com',102),(403,'Omar Hassan','1988-11-01','Male','omar.h@mail.com',103),(404,'Leah Chen','1999-01-20','Female','leah.c@mail.com',101),(405,'Ethan Hunt','1990-05-15','Male','ethan.h@mail.com',102),(406,'Chloe Green','2003-12-03','Female','chloe.g@mail.com',103),(407,'Ben King','1998-07-22','Male','ben.k@mail.com',101),(408,'Maya Singh','2001-04-05','Female','maya.s@mail.com',102),(409,'David Lee','1985-01-30','Male','david.l@mail.com',101),(410,'Anna Zola','1993-09-18','Female','anna.z@mail.com',102);
/*!40000 ALTER TABLE `member` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `membership_plan`
--

DROP TABLE IF EXISTS `membership_plan`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `membership_plan` (
  `plan_id` int NOT NULL AUTO_INCREMENT,
  `plan_name` varchar(100) NOT NULL,
  `duration` int NOT NULL COMMENT 'Duration in months',
  `fee` decimal(10,2) NOT NULL,
  PRIMARY KEY (`plan_id`)
) ENGINE=InnoDB AUTO_INCREMENT=207 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `membership_plan`
--

LOCK TABLES `membership_plan` WRITE;
/*!40000 ALTER TABLE `membership_plan` DISABLE KEYS */;
INSERT INTO `membership_plan` VALUES (201,'Standard Monthly',1,99.99),(202,'Standard Annual',12,999.99),(203,'Zumba Class Pass',3,149.99),(204,'Boxing Masterclass',6,499.00),(205,'Yoga Class',2,329.00);
/*!40000 ALTER TABLE `membership_plan` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `payment`
--

DROP TABLE IF EXISTS `payment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `payment` (
  `payment_id` int NOT NULL AUTO_INCREMENT,
  `member_id` int NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `payment_date` datetime NOT NULL,
  `payment_mode` enum('Cash','UPI','Card') NOT NULL,
  `status` enum('Pending','Completed','Failed') NOT NULL,
  PRIMARY KEY (`payment_id`),
  UNIQUE KEY `member_id` (`member_id`),
  CONSTRAINT `payment_ibfk_1` FOREIGN KEY (`member_id`) REFERENCES `member` (`member_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=516 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `payment`
--

LOCK TABLES `payment` WRITE;
/*!40000 ALTER TABLE `payment` DISABLE KEYS */;
INSERT INTO `payment` VALUES (501,401,1099.98,'2025-10-10 12:11:00','Card','Completed'),(502,402,999.99,'2025-10-10 12:11:00','UPI','Completed'),(503,403,499.00,'2025-10-10 12:11:00','Cash','Completed'),(504,405,149.99,'2025-10-10 12:11:00','Card','Completed'),(505,406,999.99,'2025-10-10 12:11:00','UPI','Completed'),(506,407,999.99,'2025-10-10 12:11:00','UPI','Completed'),(507,408,149.99,'2025-10-10 12:11:00','Card','Completed'),(508,409,99.99,'2025-10-10 12:11:00','Cash','Completed'),(509,410,1648.98,'2025-10-10 12:16:16','Card','Completed'),(510,404,99.99,'2025-10-10 12:11:00','Card','Completed');
/*!40000 ALTER TABLE `payment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `trainer`
--

DROP TABLE IF EXISTS `trainer`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `trainer` (
  `trainer_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `contact_info` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`trainer_id`),
  UNIQUE KEY `contact_info` (`contact_info`)
) ENGINE=InnoDB AUTO_INCREMENT=104 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `trainer`
--

LOCK TABLES `trainer` WRITE;
/*!40000 ALTER TABLE `trainer` DISABLE KEYS */;
INSERT INTO `trainer` VALUES (101,'Alex Johnson','alex.j@gym.com'),(102,'Sara Khan','sara.k@gym.com'),(103,'Mike Davis','mike.d@gym.com');
/*!40000 ALTER TABLE `trainer` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `trainer_specialization`
--

DROP TABLE IF EXISTS `trainer_specialization`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `trainer_specialization` (
  `trainer_id` int NOT NULL,
  `specialization_name` varchar(50) NOT NULL,
  PRIMARY KEY (`trainer_id`,`specialization_name`),
  CONSTRAINT `trainer_specialization_ibfk_1` FOREIGN KEY (`trainer_id`) REFERENCES `trainer` (`trainer_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `trainer_specialization`
--

LOCK TABLES `trainer_specialization` WRITE;
/*!40000 ALTER TABLE `trainer_specialization` DISABLE KEYS */;
INSERT INTO `trainer_specialization` VALUES (101,'Nutrition'),(101,'Weightlifting'),(102,'Pilates'),(102,'Yoga'),(103,'Boxing'),(103,'Zumba');
/*!40000 ALTER TABLE `trainer_specialization` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-11-12 19:30:50
