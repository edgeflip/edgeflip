CREATE DATABASE IF NOT EXISTS edgeflip;
GRANT ALL PRIVILEGES ON edgeflip.* TO edgeflip@localhost;
GRANT ALL PRIVILEGES ON edgeflip.* TO edgeflip@localhost IDENTIFIED BY 'edgeflip';
USE edgeflip;
CREATE TABLE IF NOT EXISTS `celery_taskmeta` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `task_id` varchar(255) DEFAULT NULL,
      `status` varchar(50) DEFAULT NULL,
      `result` longblob,
      `date_done` datetime DEFAULT NULL,
      `traceback` text,
      PRIMARY KEY (`id`),
      UNIQUE KEY `task_id` (`task_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=latin1;
COMMIT;
