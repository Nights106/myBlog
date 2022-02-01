drop database if exists myblog;

create database myblog;

use myblog;

-- grant select, insert, update, delete on awesome.* to 'www-data'@'localhost' identified by 'www-data';

create table users (
    `id` varchar(100) not null,
    `email` varchar(100) not null,
    `password` varchar(100) not null,
    `admin` bool not null,
    `name` varchar(100) not null,
    `image` varchar(500) not null,
    `created_at` real not null,
    unique key `idx_email` (`email`),
    key `idx_created_at` (`created_at`),
    primary key (`id`)
) engine=innodb default charset=utf8;

create table blogs (
    `id` varchar(100) not null,
    `user_id` varchar(100) not null,
    `user_name` varchar(100) not null,
    `user_image` varchar(500) not null,
    `name` varchar(100) not null,
    `summary` varchar(200) not null,
    `content` mediumtext not null,
    `created_at` real not null,
    key `idx_created_at` (`created_at`),
    primary key (`id`)
) engine=innodb default charset=utf8;

create table comments (
    `id` varchar(100) not null,
    `blog_id` varchar(100) not null,
    `user_id` varchar(100) not null,
    `user_name` varchar(100) not null,
    `user_image` varchar(500) not null,
    `content` mediumtext not null,
    `created_at` real not null,
    key `idx_created_at` (`created_at`),
    primary key (`id`)
) engine=innodb default charset=utf8;