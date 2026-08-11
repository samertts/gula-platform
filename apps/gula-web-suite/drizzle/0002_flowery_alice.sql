CREATE TABLE `approval_requests` (
	`id` int AUTO_INCREMENT NOT NULL,
	`requester_user_id` int NOT NULL,
	`reviewer_user_id` int,
	`institution_id` int,
	`title` varchar(255) NOT NULL,
	`description` text,
	`entity_type` varchar(80) NOT NULL,
	`entity_id` varchar(80) NOT NULL,
	`status` enum('pending','approved','rejected','cancelled') NOT NULL DEFAULT 'pending',
	`created_at` timestamp NOT NULL DEFAULT (now()),
	`updated_at` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `approval_requests_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `system_messages` (
	`id` int AUTO_INCREMENT NOT NULL,
	`recipient_user_id` int NOT NULL,
	`sender_user_id` int,
	`subject` varchar(255) NOT NULL,
	`body` text NOT NULL,
	`status` enum('unread','read','archived') NOT NULL DEFAULT 'unread',
	`created_at` timestamp NOT NULL DEFAULT (now()),
	`read_at` timestamp,
	CONSTRAINT `system_messages_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `universal_tasks` (
	`id` int AUTO_INCREMENT NOT NULL,
	`assignee_user_id` int NOT NULL,
	`institution_id` int,
	`title` varchar(255) NOT NULL,
	`description` text,
	`task_type` varchar(80) NOT NULL,
	`priority` enum('routine','urgent','critical') NOT NULL DEFAULT 'routine',
	`status` enum('pending','in_progress','completed','cancelled') NOT NULL DEFAULT 'pending',
	`entity_type` varchar(80),
	`entity_id` varchar(80),
	`due_at` timestamp,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	`updated_at` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `universal_tasks_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
ALTER TABLE `approval_requests` ADD CONSTRAINT `approval_requests_requester_user_id_users_id_fk` FOREIGN KEY (`requester_user_id`) REFERENCES `users`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `approval_requests` ADD CONSTRAINT `approval_requests_reviewer_user_id_users_id_fk` FOREIGN KEY (`reviewer_user_id`) REFERENCES `users`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `approval_requests` ADD CONSTRAINT `approval_requests_institution_id_institutions_id_fk` FOREIGN KEY (`institution_id`) REFERENCES `institutions`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `system_messages` ADD CONSTRAINT `system_messages_recipient_user_id_users_id_fk` FOREIGN KEY (`recipient_user_id`) REFERENCES `users`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `system_messages` ADD CONSTRAINT `system_messages_sender_user_id_users_id_fk` FOREIGN KEY (`sender_user_id`) REFERENCES `users`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `universal_tasks` ADD CONSTRAINT `universal_tasks_assignee_user_id_users_id_fk` FOREIGN KEY (`assignee_user_id`) REFERENCES `users`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `universal_tasks` ADD CONSTRAINT `universal_tasks_institution_id_institutions_id_fk` FOREIGN KEY (`institution_id`) REFERENCES `institutions`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
CREATE INDEX `approval_requests_reviewer_status_idx` ON `approval_requests` (`reviewer_user_id`,`status`);--> statement-breakpoint
CREATE INDEX `approval_requests_institution_idx` ON `approval_requests` (`institution_id`);--> statement-breakpoint
CREATE INDEX `system_messages_recipient_status_idx` ON `system_messages` (`recipient_user_id`,`status`);--> statement-breakpoint
CREATE INDEX `universal_tasks_assignee_status_idx` ON `universal_tasks` (`assignee_user_id`,`status`);--> statement-breakpoint
CREATE INDEX `universal_tasks_institution_idx` ON `universal_tasks` (`institution_id`);