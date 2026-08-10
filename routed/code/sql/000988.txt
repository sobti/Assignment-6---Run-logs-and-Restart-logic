CREATE TABLE controller (
id BIGINT AUTO_INCREMENT,
`name` VARCHAR(85) NOT NULL COLLATE 'utf8_general_ci' UNIQUE,
ipv4 VARCHAR(15) NOT NULL COLLATE 'utf8_general_ci',
description VARCHAR(1000) COLLATE 'utf8_general_ci',
building_id BIGINT,
PRIMARY KEY (id)
);
CREATE INDEX KEY_name USING BTREE ON controller (`name`);
CREATE INDEX KEY_ipv4 USING BTREE ON controller (ipv4);

CREATE TABLE device (
id BIGINT AUTO_INCREMENT,
`name` VARCHAR(85) NOT NULL COLLATE 'utf8_bin' UNIQUE,
is_known TINYINT(1) NOT NULL,
description VARCHAR(1000) COLLATE 'utf8_general_ci',
controller_id BIGINT NOT NULL,
PRIMARY KEY (id),
FOREIGN KEY FK_device_controller (controller_id) REFERENCES controller (id) ON UPDATE CASCADE ON DELETE CASCADE
);
CREATE INDEX KEY_name USING BTREE ON device (`name`);

CREATE TABLE device_frequency (
  id BIGINT AUTO_INCREMENT,
  device_id BIGINT NOT NULL,
  frequency_mhz INT NOT NULL,
  PRIMARY KEY (id),
  FOREIGN KEY FK_device_frequency_device (device_id) REFERENCES device (id) ON UPDATE CASCADE ON DELETE CASCADE
);
ALTER TABLE device_frequency ADD UNIQUE UQ_device_id_frequency_mhz (device_id, frequency_mhz);

CREATE TABLE device_survey (
id BIGINT AUTO_INCREMENT,
frequency_id BIGINT NOT NULL,
`timestamp` INT NOT NULL,
is_enabled TINYINT(1) NOT NULL,
clients_sum INT NOT NULL,
cumulative BIGINT NOT NULL,
PRIMARY KEY (id),
FOREIGN KEY FK_device_survey_device_frequency (frequency_id) REFERENCES device_frequency (id) ON UPDATE CASCADE ON DELETE CASCADE
);
CREATE INDEX KEY_timestamp USING BTREE ON device_survey (`timestamp`);
ALTER TABLE device_survey ADD UNIQUE UQ_frequency_id_timestamp (frequency_id, `timestamp`);

CREATE TABLE hibernate_sequences (
sequence_name VARCHAR(255) COLLATE 'utf8_bin' NOT NULL,
next_val BIGINT NOT NULL,
PRIMARY KEY (sequence_name)
);

CREATE TABLE `user` (
id BIGINT AUTO_INCREMENT,
`name` VARCHAR(255) COLLATE 'utf8_general_ci' DEFAULT NULL UNIQUE,
secret VARBINARY(132) DEFAULT NULL,
is_activated TINYINT(1) NOT NULL,
is_blocked TINYINT(1) NOT NULL,
role ENUM('NORMAL', 'ADMIN', 'ROOT') NOT NULL,
PRIMARY KEY (id)
);
CREATE INDEX KEY_name USING BTREE ON `user` (`name`);
CREATE VIEW view_user AS SELECT id, `name`, HEX(MID(secret,5,1)) AS short_secret, is_activated, is_blocked, role FROM `user`;

CREATE TABLE token (
id BIGINT AUTO_INCREMENT,
secret VARBINARY(132) NOT NULL,
action ENUM('RESET_PASSWORD', 'ACTIVATE_ACCOUNT') NOT NULL,
user_id BIGINT NOT NULL,
PRIMARY KEY (id),
FOREIGN KEY FK_token_user (user_id) REFERENCES `user`(id) ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE VIEW view_token AS SELECT id, HEX(MID(secret,5,1)) AS short_secret, action, user_id FROM token;

CREATE TABLE unit (
id BIGINT AUTO_INCREMENT,
code VARCHAR(20) NOT NULL COLLATE 'utf8_general_ci' UNIQUE,
description VARCHAR(100) NOT NULL COLLATE 'utf8_general_ci' ,
PRIMARY KEY (id)
);
CREATE INDEX KEY_code USING BTREE ON unit (`code`);

CREATE TABLE building (
id BIGINT AUTO_INCREMENT,
code VARCHAR(20) NOT NULL COLLATE 'utf8_general_ci' UNIQUE,
name VARCHAR(100) NOT NULL COLLATE 'utf8_general_ci' ,
street VARCHAR(100) COLLATE 'utf8_general_ci',
city VARCHAR(100) COLLATE 'utf8_general_ci',
postal_code VARCHAR(6) COLLATE 'utf8_general_ci',
number VARCHAR(10) COLLATE 'utf8_general_ci',
latitude  NUMERIC(8,6),
longitude NUMERIC(8,6),
PRIMARY KEY (id)
);
CREATE INDEX KEY_code USING BTREE ON building (`code`);

CREATE TABLE link_unit_building (
id BIGINT AUTO_INCREMENT,
unit_id BIGINT NOT NULL,
building_id BIGINT NOT NULL,
PRIMARY KEY (id),
FOREIGN KEY FK_link_unit_building_unit (unit_id)	REFERENCES unit (id) ON DELETE CASCADE ON UPDATE CASCADE,
FOREIGN KEY FK_link_unit_building_building (building_id) REFERENCES building(id) ON DELETE CASCADE ON UPDATE CASCADE
);

ALTER TABLE controller ADD FOREIGN KEY FK_controller_building (building_id) REFERENCES building (id) ON DELETE CASCADE ON UPDATE CASCADE;