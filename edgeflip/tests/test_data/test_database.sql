-- MySQL dump 10.13  Distrib 5.5.31, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: edgeflip
-- ------------------------------------------------------
-- Server version	5.5.31-0ubuntu0.12.04.2

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

--
-- Table structure for table `assignments`
--

DROP TABLE IF EXISTS `assignments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `assignments` (
  `session_id` varchar(128) DEFAULT NULL,
  `campaign_id` int(11) DEFAULT NULL,
  `content_id` int(11) DEFAULT NULL,
  `feature_type` varchar(128) DEFAULT NULL,
  `feature_row` int(11) DEFAULT NULL,
  `random_assign` tinyint(1) DEFAULT NULL,
  `assign_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `chosen_from_table` varchar(128) DEFAULT NULL,
  `chosen_from_rows` varchar(128) DEFAULT NULL,
  KEY `session_id` (`session_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `assignments`
--

LOCK TABLES `assignments` WRITE;
/*!40000 ALTER TABLE `assignments` DISABLE KEYS */;
/*!40000 ALTER TABLE `assignments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `button_style_files`
--

DROP TABLE IF EXISTS `button_style_files`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `button_style_files` (
  `button_style_file_id` int(11) NOT NULL AUTO_INCREMENT,
  `button_style_id` int(11) DEFAULT NULL,
  `html_template` varchar(128) DEFAULT NULL,
  `css_file` varchar(128) DEFAULT NULL,
  `start_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `end_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`button_style_file_id`),
  KEY `button_style_id` (`button_style_id`),
  KEY `button_style_id_2` (`button_style_id`,`end_dt`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `button_style_files`
--

LOCK TABLES `button_style_files` WRITE;
/*!40000 ALTER TABLE `button_style_files` DISABLE KEYS */;
/*!40000 ALTER TABLE `button_style_files` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `button_style_meta`
--

DROP TABLE IF EXISTS `button_style_meta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `button_style_meta` (
  `button_style_meta_id` int(11) NOT NULL AUTO_INCREMENT,
  `button_style_id` int(11) DEFAULT NULL,
  `name` varchar(256) DEFAULT NULL,
  `value` varchar(1024) DEFAULT NULL,
  `start_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `end_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`button_style_meta_id`),
  KEY `button_style_id` (`button_style_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `button_style_meta`
--

LOCK TABLES `button_style_meta` WRITE;
/*!40000 ALTER TABLE `button_style_meta` DISABLE KEYS */;
/*!40000 ALTER TABLE `button_style_meta` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `button_styles`
--

DROP TABLE IF EXISTS `button_styles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `button_styles` (
  `button_style_id` int(11) NOT NULL AUTO_INCREMENT,
  `client_id` int(11) DEFAULT NULL,
  `name` varchar(256) DEFAULT NULL,
  `description` varchar(1024) DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT '0',
  `create_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `delete_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`button_style_id`),
  KEY `client_id` (`client_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `button_styles`
--

LOCK TABLES `button_styles` WRITE;
/*!40000 ALTER TABLE `button_styles` DISABLE KEYS */;
/*!40000 ALTER TABLE `button_styles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `campaign_button_styles`
--

DROP TABLE IF EXISTS `campaign_button_styles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `campaign_button_styles` (
  `campaign_button_style_id` int(11) NOT NULL AUTO_INCREMENT,
  `campaign_id` int(11) DEFAULT NULL,
  `button_style_id` int(11) DEFAULT NULL,
  `rand_cdf` decimal(10,9) DEFAULT NULL,
  `start_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `end_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`campaign_button_style_id`),
  KEY `campaign_id` (`campaign_id`),
  KEY `campaign_id_2` (`campaign_id`,`end_dt`),
  KEY `button_style_id` (`button_style_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `campaign_button_styles`
--

LOCK TABLES `campaign_button_styles` WRITE;
/*!40000 ALTER TABLE `campaign_button_styles` DISABLE KEYS */;
/*!40000 ALTER TABLE `campaign_button_styles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `campaign_choice_set_algoritm`
--

DROP TABLE IF EXISTS `campaign_choice_set_algoritm`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `campaign_choice_set_algoritm` (
  `campaign_choice_set_algoritm_id` int(11) NOT NULL AUTO_INCREMENT,
  `campaign_id` int(11) DEFAULT NULL,
  `choice_set_algoritm_id` int(11) DEFAULT NULL,
  `rand_cdf` decimal(10,9) DEFAULT NULL,
  `start_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `end_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`campaign_choice_set_algoritm_id`),
  KEY `campaign_id` (`campaign_id`),
  KEY `campaign_id_2` (`campaign_id`,`end_dt`),
  KEY `choice_set_algoritm_id` (`choice_set_algoritm_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `campaign_choice_set_algoritm`
--

LOCK TABLES `campaign_choice_set_algoritm` WRITE;
/*!40000 ALTER TABLE `campaign_choice_set_algoritm` DISABLE KEYS */;
/*!40000 ALTER TABLE `campaign_choice_set_algoritm` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `campaign_choice_sets`
--

DROP TABLE IF EXISTS `campaign_choice_sets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `campaign_choice_sets` (
  `campaign_choice_set_id` int(11) NOT NULL AUTO_INCREMENT,
  `campaign_id` int(11) DEFAULT NULL,
  `choice_set_id` int(11) DEFAULT NULL,
  `rand_cdf` decimal(10,9) DEFAULT NULL,
  `allow_generic` tinyint(1) DEFAULT NULL,
  `generic_url_slug` varchar(64) DEFAULT NULL,
  `start_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `end_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`campaign_choice_set_id`),
  KEY `campaign_id` (`campaign_id`),
  KEY `campaign_id_2` (`campaign_id`,`end_dt`),
  KEY `choice_set_id` (`choice_set_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `campaign_choice_sets`
--

LOCK TABLES `campaign_choice_sets` WRITE;
/*!40000 ALTER TABLE `campaign_choice_sets` DISABLE KEYS */;
INSERT INTO `campaign_choice_sets` VALUES (1,1,2,1.000000000,1,'all','2013-06-28 17:28:36',NULL),(2,2,1,1.000000000,1,'all','2013-06-28 17:28:36',NULL),(3,3,3,1.000000000,1,'all','2013-06-28 17:28:36',NULL);
/*!40000 ALTER TABLE `campaign_choice_sets` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `campaign_faces_styles`
--

DROP TABLE IF EXISTS `campaign_faces_styles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `campaign_faces_styles` (
  `campaign_faces_style_id` int(11) NOT NULL AUTO_INCREMENT,
  `campaign_id` int(11) DEFAULT NULL,
  `faces_style_id` int(11) DEFAULT NULL,
  `rand_cdf` decimal(10,9) DEFAULT NULL,
  `start_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `end_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`campaign_faces_style_id`),
  KEY `campaign_id` (`campaign_id`),
  KEY `campaign_id_2` (`campaign_id`,`end_dt`),
  KEY `faces_style_id` (`faces_style_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `campaign_faces_styles`
--

LOCK TABLES `campaign_faces_styles` WRITE;
/*!40000 ALTER TABLE `campaign_faces_styles` DISABLE KEYS */;
/*!40000 ALTER TABLE `campaign_faces_styles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `campaign_fb_objects`
--

DROP TABLE IF EXISTS `campaign_fb_objects`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `campaign_fb_objects` (
  `campaign_fb_object_id` int(11) NOT NULL AUTO_INCREMENT,
  `campaign_id` int(11) DEFAULT NULL,
  `filter_id` int(11) DEFAULT NULL,
  `fb_object_id` int(11) DEFAULT NULL,
  `rand_cdf` decimal(10,9) DEFAULT NULL,
  `start_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `end_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`campaign_fb_object_id`),
  KEY `campaign_id` (`campaign_id`,`filter_id`),
  KEY `campaign_id_2` (`campaign_id`,`filter_id`,`end_dt`),
  KEY `fb_object_id` (`fb_object_id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `campaign_fb_objects`
--

LOCK TABLES `campaign_fb_objects` WRITE;
/*!40000 ALTER TABLE `campaign_fb_objects` DISABLE KEYS */;
INSERT INTO `campaign_fb_objects` VALUES (1,1,2,1,1.000000000,'2013-06-28 17:28:36',NULL),(2,2,1,2,1.000000000,'2013-06-28 17:28:36',NULL),(3,3,3,3,1.000000000,'2013-06-28 17:28:36',NULL),(4,3,4,4,1.000000000,'2013-06-28 17:28:36',NULL),(5,3,5,5,1.000000000,'2013-06-28 17:28:36',NULL),(6,3,6,6,1.000000000,'2013-06-28 17:28:36',NULL);
/*!40000 ALTER TABLE `campaign_fb_objects` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `campaign_generic_fb_objects`
--

DROP TABLE IF EXISTS `campaign_generic_fb_objects`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `campaign_generic_fb_objects` (
  `campaign_generic_fb_object_id` int(11) NOT NULL AUTO_INCREMENT,
  `campaign_id` int(11) DEFAULT NULL,
  `fb_object_id` int(11) DEFAULT NULL,
  `rand_cdf` decimal(10,9) DEFAULT NULL,
  `start_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `end_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`campaign_generic_fb_object_id`),
  KEY `campaign_id` (`campaign_id`),
  KEY `campaign_id_2` (`campaign_id`,`end_dt`),
  KEY `fb_object_id` (`fb_object_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `campaign_generic_fb_objects`
--

LOCK TABLES `campaign_generic_fb_objects` WRITE;
/*!40000 ALTER TABLE `campaign_generic_fb_objects` DISABLE KEYS */;
INSERT INTO `campaign_generic_fb_objects` VALUES (1,1,1,1.000000000,'2013-06-28 17:28:36',NULL),(2,2,2,1.000000000,'2013-06-28 17:28:36',NULL),(3,3,7,1.000000000,'2013-06-28 17:28:36',NULL);
/*!40000 ALTER TABLE `campaign_generic_fb_objects` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `campaign_global_filters`
--

DROP TABLE IF EXISTS `campaign_global_filters`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `campaign_global_filters` (
  `campaign_global_filter_id` int(11) NOT NULL AUTO_INCREMENT,
  `campaign_id` int(11) DEFAULT NULL,
  `filter_id` int(11) DEFAULT NULL,
  `rand_cdf` decimal(10,9) DEFAULT NULL,
  `start_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `end_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`campaign_global_filter_id`),
  KEY `campaign_id` (`campaign_id`),
  KEY `campaign_id_2` (`campaign_id`,`end_dt`),
  KEY `filter_id` (`filter_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `campaign_global_filters`
--

LOCK TABLES `campaign_global_filters` WRITE;
/*!40000 ALTER TABLE `campaign_global_filters` DISABLE KEYS */;
INSERT INTO `campaign_global_filters` VALUES (1,1,1,1.000000000,'2013-06-28 17:28:36',NULL),(2,2,1,1.000000000,'2013-06-28 17:28:36',NULL),(3,3,1,1.000000000,'2013-06-28 17:28:36',NULL);
/*!40000 ALTER TABLE `campaign_global_filters` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `campaign_meta`
--

DROP TABLE IF EXISTS `campaign_meta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `campaign_meta` (
  `campaign_meta_id` int(11) NOT NULL AUTO_INCREMENT,
  `campaign_id` int(11) DEFAULT NULL,
  `name` varchar(256) DEFAULT NULL,
  `value` varchar(1024) DEFAULT NULL,
  `start_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `end_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`campaign_meta_id`),
  KEY `campaign_id` (`campaign_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `campaign_meta`
--

LOCK TABLES `campaign_meta` WRITE;
/*!40000 ALTER TABLE `campaign_meta` DISABLE KEYS */;
/*!40000 ALTER TABLE `campaign_meta` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `campaign_mix_models`
--

DROP TABLE IF EXISTS `campaign_mix_models`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `campaign_mix_models` (
  `campaign_mix_model_id` int(11) NOT NULL AUTO_INCREMENT,
  `campaign_id` int(11) DEFAULT NULL,
  `mix_model_id` int(11) DEFAULT NULL,
  `rand_cdf` decimal(10,9) DEFAULT NULL,
  `start_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `end_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`campaign_mix_model_id`),
  KEY `campaign_id` (`campaign_id`),
  KEY `campaign_id_2` (`campaign_id`,`end_dt`),
  KEY `mix_model_id` (`mix_model_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `campaign_mix_models`
--

LOCK TABLES `campaign_mix_models` WRITE;
/*!40000 ALTER TABLE `campaign_mix_models` DISABLE KEYS */;
/*!40000 ALTER TABLE `campaign_mix_models` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `campaign_propensity_models`
--

DROP TABLE IF EXISTS `campaign_propensity_models`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `campaign_propensity_models` (
  `campaign_propensity_model_id` int(11) NOT NULL AUTO_INCREMENT,
  `campaign_id` int(11) DEFAULT NULL,
  `propensity_model_id` int(11) DEFAULT NULL,
  `rand_cdf` decimal(10,9) DEFAULT NULL,
  `start_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `end_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`campaign_propensity_model_id`),
  KEY `campaign_id` (`campaign_id`),
  KEY `campaign_id_2` (`campaign_id`,`end_dt`),
  KEY `propensity_model_id` (`propensity_model_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `campaign_propensity_models`
--

LOCK TABLES `campaign_propensity_models` WRITE;
/*!40000 ALTER TABLE `campaign_propensity_models` DISABLE KEYS */;
/*!40000 ALTER TABLE `campaign_propensity_models` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `campaign_properties`
--

DROP TABLE IF EXISTS `campaign_properties`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `campaign_properties` (
  `campaign_property_id` int(11) NOT NULL AUTO_INCREMENT,
  `campaign_id` int(11) DEFAULT NULL,
  `client_faces_url` varchar(2096) DEFAULT NULL,
  `client_thanks_url` varchar(2096) DEFAULT NULL,
  `client_error_url` varchar(2096) DEFAULT NULL,
  `fallback_campaign_id` int(11) DEFAULT NULL,
  `fallback_content_id` int(11) DEFAULT NULL,
  `start_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `end_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`campaign_property_id`),
  KEY `campaign_id` (`campaign_id`),
  KEY `campaign_id_2` (`campaign_id`,`end_dt`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `campaign_properties`
--

LOCK TABLES `campaign_properties` WRITE;
/*!40000 ALTER TABLE `campaign_properties` DISABLE KEYS */;
INSERT INTO `campaign_properties` VALUES (1,1,'http://mockclient.edgeflip.com:5000/guncontrol_share','https://donate.demandaction.org/act/donate','https://donate.demandaction.org/act/donate',NULL,NULL,'2013-06-28 17:28:36',NULL),(2,2,'http://mockclient.edgeflip.com:5000/immigration_share','https://contribute.barackobama.com/donation/orgforaction/2/index.html','https://contribute.barackobama.com/donation/orgforaction/2/index.html',NULL,NULL,'2013-06-28 17:28:36',NULL),(3,3,'http://mockclient.edgeflip.com:5000/ofa_share','https://contribute.barackobama.com/donation/orgforaction/2/index.html','https://contribute.barackobama.com/donation/orgforaction/2/index.html',NULL,NULL,'2013-06-28 17:28:36',NULL);
/*!40000 ALTER TABLE `campaign_properties` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `campaign_proximity_models`
--

DROP TABLE IF EXISTS `campaign_proximity_models`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `campaign_proximity_models` (
  `campaign_proximity_model_id` int(11) NOT NULL AUTO_INCREMENT,
  `campaign_id` int(11) DEFAULT NULL,
  `proximity_model_id` int(11) DEFAULT NULL,
  `rand_cdf` decimal(10,9) DEFAULT NULL,
  `start_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `end_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`campaign_proximity_model_id`),
  KEY `campaign_id` (`campaign_id`),
  KEY `campaign_id_2` (`campaign_id`,`end_dt`),
  KEY `proximity_model_id` (`proximity_model_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `campaign_proximity_models`
--

LOCK TABLES `campaign_proximity_models` WRITE;
/*!40000 ALTER TABLE `campaign_proximity_models` DISABLE KEYS */;
/*!40000 ALTER TABLE `campaign_proximity_models` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `campaigns`
--

DROP TABLE IF EXISTS `campaigns`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `campaigns` (
  `campaign_id` int(11) NOT NULL AUTO_INCREMENT,
  `client_id` int(11) DEFAULT NULL,
  `name` varchar(256) DEFAULT NULL,
  `description` varchar(1024) DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT '0',
  `create_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `delete_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`campaign_id`),
  KEY `client_id` (`client_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `campaigns`
--

LOCK TABLES `campaigns` WRITE;
/*!40000 ALTER TABLE `campaigns` DISABLE KEYS */;
INSERT INTO `campaigns` VALUES (1,1,'Gun Control',NULL,0,'2013-06-28 17:28:36',NULL),(2,1,'Immigration Reform',NULL,0,'2013-06-28 17:28:36',NULL),(3,1,'OFA Enviro Support',NULL,0,'2013-06-28 17:28:36',NULL);
/*!40000 ALTER TABLE `campaigns` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `choice_set_algoritm_definitions`
--

DROP TABLE IF EXISTS `choice_set_algoritm_definitions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `choice_set_algoritm_definitions` (
  `choice_set_algoritm_definition_id` int(11) NOT NULL AUTO_INCREMENT,
  `choice_set_algoritm_id` int(11) DEFAULT NULL,
  `algorithm_definition` varchar(4096) DEFAULT NULL,
  `start_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `end_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`choice_set_algoritm_definition_id`),
  KEY `choice_set_algoritm_id` (`choice_set_algoritm_id`),
  KEY `choice_set_algoritm_id_2` (`choice_set_algoritm_id`,`end_dt`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `choice_set_algoritm_definitions`
--

LOCK TABLES `choice_set_algoritm_definitions` WRITE;
/*!40000 ALTER TABLE `choice_set_algoritm_definitions` DISABLE KEYS */;
/*!40000 ALTER TABLE `choice_set_algoritm_definitions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `choice_set_algoritm_meta`
--

DROP TABLE IF EXISTS `choice_set_algoritm_meta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `choice_set_algoritm_meta` (
  `choice_set_algoritm_meta_id` int(11) NOT NULL AUTO_INCREMENT,
  `choice_set_algoritm_id` int(11) DEFAULT NULL,
  `name` varchar(256) DEFAULT NULL,
  `value` varchar(1024) DEFAULT NULL,
  `start_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `end_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`choice_set_algoritm_meta_id`),
  KEY `choice_set_algoritm_id` (`choice_set_algoritm_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `choice_set_algoritm_meta`
--

LOCK TABLES `choice_set_algoritm_meta` WRITE;
/*!40000 ALTER TABLE `choice_set_algoritm_meta` DISABLE KEYS */;
/*!40000 ALTER TABLE `choice_set_algoritm_meta` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `choice_set_algoritms`
--

DROP TABLE IF EXISTS `choice_set_algoritms`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `choice_set_algoritms` (
  `choice_set_algorithm_id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(256) DEFAULT NULL,
  `description` varchar(1024) DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT '0',
  `create_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `delete_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`choice_set_algorithm_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `choice_set_algoritms`
--

LOCK TABLES `choice_set_algoritms` WRITE;
/*!40000 ALTER TABLE `choice_set_algoritms` DISABLE KEYS */;
/*!40000 ALTER TABLE `choice_set_algoritms` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `choice_set_filters`
--

DROP TABLE IF EXISTS `choice_set_filters`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `choice_set_filters` (
  `choice_set_filter_id` int(11) NOT NULL AUTO_INCREMENT,
  `choice_set_id` int(11) DEFAULT NULL,
  `filter_id` int(11) DEFAULT NULL,
  `url_slug` varchar(64) DEFAULT NULL,
  `propensity_model_type` varchar(32) DEFAULT NULL,
  `start_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `end_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`choice_set_filter_id`),
  KEY `choice_set_id` (`choice_set_id`),
  KEY `choice_set_id_2` (`choice_set_id`,`end_dt`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `choice_set_filters`
--

LOCK TABLES `choice_set_filters` WRITE;
/*!40000 ALTER TABLE `choice_set_filters` DISABLE KEYS */;
INSERT INTO `choice_set_filters` VALUES (1,1,1,'all',NULL,'2013-06-28 17:28:36',NULL),(2,2,2,'all',NULL,'2013-06-28 17:28:36',NULL),(3,3,3,'IL',NULL,'2013-06-28 17:28:36',NULL),(4,3,4,'MA',NULL,'2013-06-28 17:28:36',NULL),(5,3,5,'CA',NULL,'2013-06-28 17:28:36',NULL),(6,3,6,'NY',NULL,'2013-06-28 17:28:36',NULL);
/*!40000 ALTER TABLE `choice_set_filters` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `choice_set_meta`
--

DROP TABLE IF EXISTS `choice_set_meta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `choice_set_meta` (
  `choice_set_meta_id` int(11) NOT NULL AUTO_INCREMENT,
  `choice_set_id` int(11) DEFAULT NULL,
  `name` varchar(256) DEFAULT NULL,
  `value` varchar(1024) DEFAULT NULL,
  `start_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `end_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`choice_set_meta_id`),
  KEY `choice_set_id` (`choice_set_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `choice_set_meta`
--

LOCK TABLES `choice_set_meta` WRITE;
/*!40000 ALTER TABLE `choice_set_meta` DISABLE KEYS */;
/*!40000 ALTER TABLE `choice_set_meta` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `choice_sets`
--

DROP TABLE IF EXISTS `choice_sets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `choice_sets` (
  `choice_set_id` int(11) NOT NULL AUTO_INCREMENT,
  `client_id` int(11) DEFAULT NULL,
  `name` varchar(256) DEFAULT NULL,
  `description` varchar(1024) DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT '0',
  `create_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `delete_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`choice_set_id`),
  KEY `client_id` (`client_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `choice_sets`
--

LOCK TABLES `choice_sets` WRITE;
/*!40000 ALTER TABLE `choice_sets` DISABLE KEYS */;
INSERT INTO `choice_sets` VALUES (1,1,'edgeflip default','Default element created by edgeflip',0,'2013-06-28 17:28:36',NULL),(2,1,'Mayors States',NULL,0,'2013-06-28 17:28:36',NULL),(3,1,'OFA Enviro States',NULL,0,'2013-06-28 17:28:36',NULL);
/*!40000 ALTER TABLE `choice_sets` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `client_content`
--

DROP TABLE IF EXISTS `client_content`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `client_content` (
  `content_id` int(11) NOT NULL AUTO_INCREMENT,
  `client_id` int(11) DEFAULT NULL,
  `name` varchar(256) DEFAULT NULL,
  `description` varchar(1024) DEFAULT NULL,
  `url` varchar(2048) DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT '0',
  `create_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `delete_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`content_id`),
  KEY `client_id` (`client_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `client_content`
--

LOCK TABLES `client_content` WRITE;
/*!40000 ALTER TABLE `client_content` DISABLE KEYS */;
INSERT INTO `client_content` VALUES (1,1,'Support Gun Control',NULL,'http://mockclient.edgeflip.com:5000/guncontrol',0,'2013-06-28 17:28:36',NULL),(2,1,'Support Immigration Reform',NULL,'http://mockclient.edgeflip.com:5000/immigration',0,'2013-06-28 17:28:36',NULL),(3,1,'OFA Enviro pages',NULL,'http://mockclient.edgeflip.com:5000/ofa_landing?state={{choice_set_slug}}',0,'2013-06-28 17:28:36',NULL);
/*!40000 ALTER TABLE `client_content` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `client_defaults`
--

DROP TABLE IF EXISTS `client_defaults`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `client_defaults` (
  `client_default_id` int(11) NOT NULL AUTO_INCREMENT,
  `client_id` int(11) DEFAULT NULL,
  `button_style_id` int(11) DEFAULT NULL,
  `faces_style_id` int(11) DEFAULT NULL,
  `propensity_model_id` int(11) DEFAULT NULL,
  `proximity_model_id` int(11) DEFAULT NULL,
  `mix_model_id` int(11) DEFAULT NULL,
  `filter_id` int(11) DEFAULT NULL,
  `choice_set_id` int(11) DEFAULT NULL,
  `choice_set_algorithm_id` int(11) DEFAULT NULL,
  `start_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `end_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`client_default_id`),
  KEY `client_id` (`client_id`),
  KEY `client_id_2` (`client_id`,`end_dt`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `client_defaults`
--

LOCK TABLES `client_defaults` WRITE;
/*!40000 ALTER TABLE `client_defaults` DISABLE KEYS */;
INSERT INTO `client_defaults` VALUES (1,1,NULL,NULL,NULL,NULL,NULL,1,1,NULL,'2013-06-28 17:28:36',NULL);
/*!40000 ALTER TABLE `client_defaults` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `clients`
--

DROP TABLE IF EXISTS `clients`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `clients` (
  `client_id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(256) DEFAULT NULL,
  `fb_app_name` varchar(256) DEFAULT NULL,
  `fb_app_id` varchar(256) DEFAULT NULL,
  `domain` varchar(256) DEFAULT NULL,
  `subdomain` varchar(256) DEFAULT NULL,
  `create_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`client_id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `domain` (`domain`,`subdomain`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `clients`
--

LOCK TABLES `clients` WRITE;
/*!40000 ALTER TABLE `clients` DISABLE KEYS */;
INSERT INTO `clients` VALUES (1,'mockclient','sharing-social-good','471727162864364','edgeflip.com:8080','local','2013-06-28 17:28:36');
/*!40000 ALTER TABLE `clients` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `edges`
--

DROP TABLE IF EXISTS `edges`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `edges` (
  `fbid_source` bigint(20) NOT NULL DEFAULT '0',
  `fbid_target` bigint(20) NOT NULL DEFAULT '0',
  `post_likes` int(11) DEFAULT NULL,
  `post_comms` int(11) DEFAULT NULL,
  `stat_likes` int(11) DEFAULT NULL,
  `stat_comms` int(11) DEFAULT NULL,
  `wall_posts` int(11) DEFAULT NULL,
  `wall_comms` int(11) DEFAULT NULL,
  `tags` int(11) DEFAULT NULL,
  `photos_target` int(11) DEFAULT NULL,
  `photos_other` int(11) DEFAULT NULL,
  `mut_friends` int(11) DEFAULT NULL,
  `updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`fbid_source`,`fbid_target`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `edges`
--

LOCK TABLES `edges` WRITE;
/*!40000 ALTER TABLE `edges` DISABLE KEYS */;
/*!40000 ALTER TABLE `edges` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `events`
--

DROP TABLE IF EXISTS `events`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `events` (
  `session_id` varchar(128) DEFAULT NULL,
  `campaign_id` int(11) DEFAULT NULL,
  `content_id` int(11) DEFAULT NULL,
  `ip` varchar(32) DEFAULT NULL,
  `fbid` bigint(20) DEFAULT NULL,
  `friend_fbid` bigint(20) DEFAULT NULL,
  `type` varchar(64) DEFAULT NULL,
  `appid` bigint(20) DEFAULT NULL,
  `content` varchar(128) DEFAULT NULL,
  `activity_id` bigint(20) DEFAULT NULL,
  `updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY `session_id` (`session_id`),
  KEY `campaign_id` (`campaign_id`),
  KEY `content_id` (`content_id`),
  KEY `fbid` (`fbid`),
  KEY `friend_fbid` (`friend_fbid`),
  KEY `activity_id` (`activity_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `events`
--

LOCK TABLES `events` WRITE;
/*!40000 ALTER TABLE `events` DISABLE KEYS */;
/*!40000 ALTER TABLE `events` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `face_exclusions`
--

DROP TABLE IF EXISTS `face_exclusions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `face_exclusions` (
  `fbid` bigint(20) NOT NULL DEFAULT '0',
  `campaign_id` int(11) NOT NULL DEFAULT '0',
  `content_id` int(11) NOT NULL DEFAULT '0',
  `friend_fbid` bigint(20) NOT NULL DEFAULT '0',
  `reason` varchar(512) DEFAULT NULL,
  `updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`fbid`,`campaign_id`,`content_id`,`friend_fbid`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `face_exclusions`
--

LOCK TABLES `face_exclusions` WRITE;
/*!40000 ALTER TABLE `face_exclusions` DISABLE KEYS */;
/*!40000 ALTER TABLE `face_exclusions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `faces_style_files`
--

DROP TABLE IF EXISTS `faces_style_files`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `faces_style_files` (
  `faces_style_file_id` int(11) NOT NULL AUTO_INCREMENT,
  `faces_style_id` int(11) DEFAULT NULL,
  `html_template` varchar(128) DEFAULT NULL,
  `css_file` varchar(128) DEFAULT NULL,
  `start_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `end_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`faces_style_file_id`),
  KEY `faces_style_id` (`faces_style_id`),
  KEY `faces_style_id_2` (`faces_style_id`,`end_dt`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `faces_style_files`
--

LOCK TABLES `faces_style_files` WRITE;
/*!40000 ALTER TABLE `faces_style_files` DISABLE KEYS */;
/*!40000 ALTER TABLE `faces_style_files` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `faces_style_meta`
--

DROP TABLE IF EXISTS `faces_style_meta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `faces_style_meta` (
  `faces_style_meta_id` int(11) NOT NULL AUTO_INCREMENT,
  `faces_style_id` int(11) DEFAULT NULL,
  `name` varchar(256) DEFAULT NULL,
  `value` varchar(1024) DEFAULT NULL,
  `start_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `end_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`faces_style_meta_id`),
  KEY `faces_style_id` (`faces_style_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `faces_style_meta`
--

LOCK TABLES `faces_style_meta` WRITE;
/*!40000 ALTER TABLE `faces_style_meta` DISABLE KEYS */;
/*!40000 ALTER TABLE `faces_style_meta` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `faces_styles`
--

DROP TABLE IF EXISTS `faces_styles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `faces_styles` (
  `faces_style_id` int(11) NOT NULL AUTO_INCREMENT,
  `client_id` int(11) DEFAULT NULL,
  `name` varchar(256) DEFAULT NULL,
  `description` varchar(1024) DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT '0',
  `create_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `delete_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`faces_style_id`),
  KEY `client_id` (`client_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `faces_styles`
--

LOCK TABLES `faces_styles` WRITE;
/*!40000 ALTER TABLE `faces_styles` DISABLE KEYS */;
/*!40000 ALTER TABLE `faces_styles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `fb_object_attributes`
--

DROP TABLE IF EXISTS `fb_object_attributes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `fb_object_attributes` (
  `fb_object_attributes_id` int(11) NOT NULL AUTO_INCREMENT,
  `fb_object_id` int(11) DEFAULT NULL,
  `og_action` varchar(64) DEFAULT NULL,
  `og_type` varchar(64) DEFAULT NULL,
  `og_title` varchar(128) DEFAULT NULL,
  `og_image` varchar(2096) DEFAULT NULL,
  `og_description` varchar(1024) DEFAULT NULL,
  `page_title` varchar(256) DEFAULT NULL,
  `sharing_prompt` varchar(2096) DEFAULT NULL,
  `msg1_pre` varchar(1024) DEFAULT NULL,
  `msg1_post` varchar(1024) DEFAULT NULL,
  `msg2_pre` varchar(1024) DEFAULT NULL,
  `msg2_post` varchar(1024) DEFAULT NULL,
  `url_slug` varchar(64) DEFAULT NULL,
  `start_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `end_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`fb_object_attributes_id`),
  KEY `fb_object_id` (`fb_object_id`),
  KEY `fb_object_id_2` (`fb_object_id`,`end_dt`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `fb_object_attributes`
--

LOCK TABLES `fb_object_attributes` WRITE;
/*!40000 ALTER TABLE `fb_object_attributes` DISABLE KEYS */;
INSERT INTO `fb_object_attributes` VALUES (1,1,'support','cause','Gun Control','http://local.edgeflip.com:8080/static/logo.jpg','Senators who opposed gun reform have seen their job approval plummet. Check out this infographic to learn more.','Support Gun Control','Ask your Facebook friends in key states to learn more about gun reform.','Hi there ',' -- Have you seen this amazing infographic about gun control?','Help keep the pressure on Congress to pass gun control, ','!',NULL,'2013-06-28 17:28:36',NULL),(2,2,'support','cause','Immigration Reform','http://local.edgeflip.com:8080/static/logo.jpg','President Obama supports common sense reforms to fix our broken immigration system. Learn more and show your support.','Support Immigration Reform','Ask your Facebook friends to learn more about immigration reform.','Hi there ',' -- Check out these details about the President\'s blueprint for immigration reform.','Help keep the pressure on Congress to pass immigration reform, ','!',NULL,'2013-06-28 17:28:36',NULL),(3,3,'support','cause','Climate Legislation','http://local.edgeflip.com:8080/static/logo.jpg','The time has come for real climate legislation in America. Tell Senator Rowlf the Dog that you stand with President Obama and Organizing for Action on this important issue.','Tell Sen. Rowlf the Dog We\'re Putting Denial on Trial!','Ask your Facebook friends in Illinois to let Senator Rowlf the Dog know we\'re putting climate denial on trial!','Hi there ',' -- Contact Sen. Rowlf the Dog to say you stand with the president on climate legislation!','Now is the time for real climate legislation, ','!',NULL,'2013-06-28 17:28:36',NULL),(4,4,'support','cause','Climate Legislation','http://local.edgeflip.com:8080/static/logo.jpg','The time has come for real climate legislation in America. Tell Senator Kermit the Frog that you stand with President Obama and Organizing for Action on this important issue.','Tell Sen. Kermit the Frog We\'re Putting Denial on Trial!','Ask your Facebook friends in Massachusetts to let Senator Kermit the Frog know we\'re putting climate denial on trial!','Hi there ',' -- Contact Sen. Kermit the Frog to say you stand with the president on climate legislation!','Now is the time for real climate legislation, ','!',NULL,'2013-06-28 17:28:36',NULL),(5,5,'support','cause','Climate Legislation','http://local.edgeflip.com:8080/static/logo.jpg','The time has come for real climate legislation in America. Tell Senator Fozzie Bear that you stand with President Obama and Organizing for Action on this important issue.','Tell Sen. Fozzie Bear We\'re Putting Denial on Trial!','Ask your Facebook friends in California to let Senator Fozzie Bear know we\'re putting climate denial on trial!','Hi there ',' -- Contact Sen. Fozzie Bear to say you stand with the president on climate legislation!','Now is the time for real climate legislation, ','!',NULL,'2013-06-28 17:28:36',NULL),(6,6,'support','cause','Climate Legislation','http://local.edgeflip.com:8080/static/logo.jpg','The time has come for real climate legislation in America. Tell Senator Miss Piggy that you stand with President Obama and Organizing for Action on this important issue.','Tell Sen. Miss Piggy We\'re Putting Denial on Trial!','Ask your Facebook friends in New York to let Senator Miss Piggy know we\'re putting climate denial on trial!','Hi there ',' -- Contact Sen. Miss Piggy to say you stand with the president on climate legislation!','Now is the time for real climate legislation, ','!',NULL,'2013-06-28 17:28:36',NULL),(7,7,'support','cause','Climate Legislation','http://local.edgeflip.com:8080/static/logo.jpg','The time has come for real climate legislation in America. Tell your Senator that you stand with President Obama and Organizing for Action on this important issue.','Tell your Senator We\'re Putting Denial on Trial!','Ask your Facebook friends to let their Senators know we\'re putting climate denial on trial!','Hi there ',' -- Contact your Senator to say you stand with the president on climate legislation!','Now is the time for real climate legislation, ','!',NULL,'2013-06-28 17:28:36',NULL);
/*!40000 ALTER TABLE `fb_object_attributes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `fb_object_meta`
--

DROP TABLE IF EXISTS `fb_object_meta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `fb_object_meta` (
  `fb_object_meta_id` int(11) NOT NULL AUTO_INCREMENT,
  `fb_object_id` int(11) DEFAULT NULL,
  `name` varchar(256) DEFAULT NULL,
  `value` varchar(1024) DEFAULT NULL,
  `start_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `end_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`fb_object_meta_id`),
  KEY `fb_object_id` (`fb_object_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `fb_object_meta`
--

LOCK TABLES `fb_object_meta` WRITE;
/*!40000 ALTER TABLE `fb_object_meta` DISABLE KEYS */;
/*!40000 ALTER TABLE `fb_object_meta` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `fb_objects`
--

DROP TABLE IF EXISTS `fb_objects`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `fb_objects` (
  `fb_object_id` int(11) NOT NULL AUTO_INCREMENT,
  `client_id` int(11) DEFAULT NULL,
  `name` varchar(256) DEFAULT NULL,
  `description` varchar(1024) DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT '0',
  `create_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `delete_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`fb_object_id`),
  KEY `client_id` (`client_id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `fb_objects`
--

LOCK TABLES `fb_objects` WRITE;
/*!40000 ALTER TABLE `fb_objects` DISABLE KEYS */;
INSERT INTO `fb_objects` VALUES (1,1,'Gun Control Infographic',NULL,0,'2013-06-28 17:28:36',NULL),(2,1,'Immigration Reform Blueprint',NULL,0,'2013-06-28 17:28:36',NULL),(3,1,'OFA Enviro - IL',NULL,0,'2013-06-28 17:28:36',NULL),(4,1,'OFA Enviro - MA',NULL,0,'2013-06-28 17:28:36',NULL),(5,1,'OFA Enviro - CA',NULL,0,'2013-06-28 17:28:36',NULL),(6,1,'OFA Enviro - NY',NULL,0,'2013-06-28 17:28:36',NULL),(7,1,'OFA Enviro - Generic',NULL,0,'2013-06-28 17:28:36',NULL);
/*!40000 ALTER TABLE `fb_objects` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `filter_features`
--

DROP TABLE IF EXISTS `filter_features`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `filter_features` (
  `filter_feature_id` int(11) NOT NULL AUTO_INCREMENT,
  `filter_id` int(11) DEFAULT NULL,
  `feature` varchar(64) DEFAULT NULL,
  `operator` varchar(32) DEFAULT NULL,
  `value` varchar(1024) DEFAULT NULL,
  `value_type` varchar(32) DEFAULT NULL,
  `start_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `end_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`filter_feature_id`),
  KEY `filter_id` (`filter_id`),
  KEY `filter_id_2` (`filter_id`,`end_dt`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `filter_features`
--

LOCK TABLES `filter_features` WRITE;
/*!40000 ALTER TABLE `filter_features` DISABLE KEYS */;
INSERT INTO `filter_features` VALUES (1,2,'state','in','Illinois||California||Massachusetts||New York','list','2013-06-28 17:28:36',NULL),(2,3,'state','eq','Illinois','string','2013-06-28 17:28:36',NULL),(3,4,'state','eq','Massachusetts','string','2013-06-28 17:28:36',NULL),(4,5,'state','eq','California','string','2013-06-28 17:28:36',NULL),(5,6,'state','eq','New York','string','2013-06-28 17:28:36',NULL);
/*!40000 ALTER TABLE `filter_features` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `filter_meta`
--

DROP TABLE IF EXISTS `filter_meta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `filter_meta` (
  `filter_meta_id` int(11) NOT NULL AUTO_INCREMENT,
  `filter_id` int(11) DEFAULT NULL,
  `name` varchar(256) DEFAULT NULL,
  `value` varchar(1024) DEFAULT NULL,
  `start_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `end_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`filter_meta_id`),
  KEY `filter_id` (`filter_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `filter_meta`
--

LOCK TABLES `filter_meta` WRITE;
/*!40000 ALTER TABLE `filter_meta` DISABLE KEYS */;
/*!40000 ALTER TABLE `filter_meta` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `filters`
--

DROP TABLE IF EXISTS `filters`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `filters` (
  `filter_id` int(11) NOT NULL AUTO_INCREMENT,
  `client_id` int(11) DEFAULT NULL,
  `name` varchar(256) DEFAULT NULL,
  `description` varchar(1024) DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT '0',
  `create_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `delete_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`filter_id`),
  KEY `client_id` (`client_id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `filters`
--

LOCK TABLES `filters` WRITE;
/*!40000 ALTER TABLE `filters` DISABLE KEYS */;
INSERT INTO `filters` VALUES (1,1,'edgeflip default','Default element created by edgeflip',0,'2013-06-28 17:28:36',NULL),(2,1,'Target States',NULL,0,'2013-06-28 17:28:36',NULL),(3,1,'In Illinois',NULL,0,'2013-06-28 17:28:36',NULL),(4,1,'In Massachusetts',NULL,0,'2013-06-28 17:28:36',NULL),(5,1,'In California',NULL,0,'2013-06-28 17:28:36',NULL),(6,1,'In New York',NULL,0,'2013-06-28 17:28:36',NULL);
/*!40000 ALTER TABLE `filters` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `mix_model_definitions`
--

DROP TABLE IF EXISTS `mix_model_definitions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mix_model_definitions` (
  `mix_model_definition_id` int(11) NOT NULL AUTO_INCREMENT,
  `mix_model_id` int(11) DEFAULT NULL,
  `model_definition` varchar(4096) DEFAULT NULL,
  `start_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `end_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`mix_model_definition_id`),
  KEY `mix_model_id` (`mix_model_id`),
  KEY `mix_model_id_2` (`mix_model_id`,`end_dt`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `mix_model_definitions`
--

LOCK TABLES `mix_model_definitions` WRITE;
/*!40000 ALTER TABLE `mix_model_definitions` DISABLE KEYS */;
/*!40000 ALTER TABLE `mix_model_definitions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `mix_model_meta`
--

DROP TABLE IF EXISTS `mix_model_meta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mix_model_meta` (
  `mix_model_meta_id` int(11) NOT NULL AUTO_INCREMENT,
  `mix_model_id` int(11) DEFAULT NULL,
  `name` varchar(256) DEFAULT NULL,
  `value` varchar(1024) DEFAULT NULL,
  `start_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `end_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`mix_model_meta_id`),
  KEY `mix_model_id` (`mix_model_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `mix_model_meta`
--

LOCK TABLES `mix_model_meta` WRITE;
/*!40000 ALTER TABLE `mix_model_meta` DISABLE KEYS */;
/*!40000 ALTER TABLE `mix_model_meta` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `mix_models`
--

DROP TABLE IF EXISTS `mix_models`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mix_models` (
  `mix_model_id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(256) DEFAULT NULL,
  `description` varchar(1024) DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT '0',
  `create_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `delete_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`mix_model_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `mix_models`
--

LOCK TABLES `mix_models` WRITE;
/*!40000 ALTER TABLE `mix_models` DISABLE KEYS */;
/*!40000 ALTER TABLE `mix_models` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `propensity_model_definitions`
--

DROP TABLE IF EXISTS `propensity_model_definitions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `propensity_model_definitions` (
  `propensity_model_definition_id` int(11) NOT NULL AUTO_INCREMENT,
  `propensity_model_id` int(11) DEFAULT NULL,
  `propensity_model_type` varchar(64) DEFAULT NULL,
  `model_definition` varchar(4096) DEFAULT NULL,
  `start_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `end_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`propensity_model_definition_id`),
  KEY `propensity_model_id` (`propensity_model_id`),
  KEY `propensity_model_id_2` (`propensity_model_id`,`end_dt`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `propensity_model_definitions`
--

LOCK TABLES `propensity_model_definitions` WRITE;
/*!40000 ALTER TABLE `propensity_model_definitions` DISABLE KEYS */;
/*!40000 ALTER TABLE `propensity_model_definitions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `propensity_model_meta`
--

DROP TABLE IF EXISTS `propensity_model_meta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `propensity_model_meta` (
  `propensity_model_meta_id` int(11) NOT NULL AUTO_INCREMENT,
  `propensity_model_id` int(11) DEFAULT NULL,
  `name` varchar(256) DEFAULT NULL,
  `value` varchar(1024) DEFAULT NULL,
  `start_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `end_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`propensity_model_meta_id`),
  KEY `propensity_model_id` (`propensity_model_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `propensity_model_meta`
--

LOCK TABLES `propensity_model_meta` WRITE;
/*!40000 ALTER TABLE `propensity_model_meta` DISABLE KEYS */;
/*!40000 ALTER TABLE `propensity_model_meta` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `propensity_models`
--

DROP TABLE IF EXISTS `propensity_models`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `propensity_models` (
  `proximity_model_id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(256) DEFAULT NULL,
  `description` varchar(1024) DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT '0',
  `create_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `delete_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`proximity_model_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `propensity_models`
--

LOCK TABLES `propensity_models` WRITE;
/*!40000 ALTER TABLE `propensity_models` DISABLE KEYS */;
/*!40000 ALTER TABLE `propensity_models` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `proximity_model_definitions`
--

DROP TABLE IF EXISTS `proximity_model_definitions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `proximity_model_definitions` (
  `proximity_model_definition_id` int(11) NOT NULL AUTO_INCREMENT,
  `proximity_model_id` int(11) DEFAULT NULL,
  `model_definition` varchar(4096) DEFAULT NULL,
  `start_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `end_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`proximity_model_definition_id`),
  KEY `proximity_model_id` (`proximity_model_id`),
  KEY `proximity_model_id_2` (`proximity_model_id`,`end_dt`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `proximity_model_definitions`
--

LOCK TABLES `proximity_model_definitions` WRITE;
/*!40000 ALTER TABLE `proximity_model_definitions` DISABLE KEYS */;
/*!40000 ALTER TABLE `proximity_model_definitions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `proximity_model_meta`
--

DROP TABLE IF EXISTS `proximity_model_meta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `proximity_model_meta` (
  `proximity_model_meta_id` int(11) NOT NULL AUTO_INCREMENT,
  `proximity_model_id` int(11) DEFAULT NULL,
  `name` varchar(256) DEFAULT NULL,
  `value` varchar(1024) DEFAULT NULL,
  `start_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `end_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`proximity_model_meta_id`),
  KEY `proximity_model_id` (`proximity_model_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `proximity_model_meta`
--

LOCK TABLES `proximity_model_meta` WRITE;
/*!40000 ALTER TABLE `proximity_model_meta` DISABLE KEYS */;
/*!40000 ALTER TABLE `proximity_model_meta` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `proximity_models`
--

DROP TABLE IF EXISTS `proximity_models`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `proximity_models` (
  `proximity_model_id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(256) DEFAULT NULL,
  `description` varchar(1024) DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT '0',
  `create_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `delete_dt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`proximity_model_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `proximity_models`
--

LOCK TABLES `proximity_models` WRITE;
/*!40000 ALTER TABLE `proximity_models` DISABLE KEYS */;
/*!40000 ALTER TABLE `proximity_models` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `share_messages`
--

DROP TABLE IF EXISTS `share_messages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `share_messages` (
  `activity_id` bigint(20) NOT NULL DEFAULT '0',
  `fbid` bigint(20) DEFAULT NULL,
  `campaign_id` int(11) DEFAULT NULL,
  `content_id` int(11) DEFAULT NULL,
  `message` varchar(4096) DEFAULT NULL,
  `updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`activity_id`),
  KEY `fbid` (`fbid`),
  KEY `campaign_id` (`campaign_id`),
  KEY `content_id` (`content_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `share_messages`
--

LOCK TABLES `share_messages` WRITE;
/*!40000 ALTER TABLE `share_messages` DISABLE KEYS */;
/*!40000 ALTER TABLE `share_messages` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tokens`
--

DROP TABLE IF EXISTS `tokens`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tokens` (
  `fbid` bigint(20) NOT NULL DEFAULT '0',
  `appid` bigint(20) NOT NULL DEFAULT '0',
  `ownerid` bigint(20) NOT NULL DEFAULT '0',
  `token` varchar(512) DEFAULT NULL,
  `expires` datetime DEFAULT NULL,
  `updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`fbid`,`appid`,`ownerid`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tokens`
--

LOCK TABLES `tokens` WRITE;
/*!40000 ALTER TABLE `tokens` DISABLE KEYS */;
/*!40000 ALTER TABLE `tokens` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_clients`
--

DROP TABLE IF EXISTS `user_clients`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_clients` (
  `fbid` bigint(20) NOT NULL DEFAULT '0',
  `client_id` int(11) NOT NULL DEFAULT '0',
  `create_dt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`fbid`,`client_id`),
  KEY `fbid` (`fbid`),
  KEY `client_id` (`client_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_clients`
--

LOCK TABLES `user_clients` WRITE;
/*!40000 ALTER TABLE `user_clients` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_clients` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users` (
  `fbid` bigint(20) NOT NULL DEFAULT '0',
  `fname` varchar(128) DEFAULT NULL,
  `lname` varchar(128) DEFAULT NULL,
  `email` varchar(256) DEFAULT NULL,
  `gender` varchar(8) DEFAULT NULL,
  `birthday` date DEFAULT NULL,
  `city` varchar(32) DEFAULT NULL,
  `state` varchar(32) DEFAULT NULL,
  `updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`fbid`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2013-06-28 12:28:50
