CREATE TABLE `callback_register` (
   `register_id` bigint(20) unsigned NOT NULL auto_increment,
   `platform_id` bigint(20) NOT NULL DEFAULT '0' COMMENT '平台ID',
   `notice_url` varchar(255) not null default '' comment '通知URL',
   `notice_type` int(11) not null default '0' comment '1开通权限 2关闭权限',
   `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
   `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
   `status` tinyint(4) NOT NULL,
   PRIMARY KEY (`register_id`),
   KEY `idx_platformid` (`platform_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

alter table relate_user_platform
    add column notice_status_add int(11) not null default 0 comment '0未通知 1已通知' after platform_id,
    add column notice_status_del int(11) not null default 0 comment '0未通知 1已通知' after notice_status_add,
    add index idx_noticestatusadd(notice_status_add),
    add index idx_noticestatusdel_status(notice_status_del,status);


CREATE TABLE `callback_queue` (
     `queue_id` bigint(20) unsigned NOT NULL auto_increment,
     `platform_id` bigint(20) NOT NULL DEFAULT '0' COMMENT '平台ID',
     `notice_url` varchar(255) not null default '0' comment '通知url',
     `notice_type` int(11) not null default '0' comment '1开通权限 2关闭权限',
     `notice_comment` varchar(255) not null default '' comment '通知备注',
     `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
     `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
     `status` tinyint(4) NOT NULL,
     PRIMARY KEY (`queue_id`),
     KEY `idx_userid_platformid` (`user_id`,`platform_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

