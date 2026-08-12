CREATE TABLE `audit_log` (
	`id` int AUTO_INCREMENT NOT NULL,
	`institution_id` int,
	`actor_user_id` int,
	`action` varchar(120) NOT NULL,
	`entity_type` varchar(80) NOT NULL,
	`entity_id` varchar(80),
	`outcome` enum('success','denied','failure') NOT NULL,
	`reason` text,
	`before_state` json,
	`after_state` json,
	`request_id` varchar(80),
	`created_at` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `audit_log_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `critical_alerts` (
	`id` int AUTO_INCREMENT NOT NULL,
	`institution_id` int NOT NULL,
	`result_id` int,
	`patient_id` int NOT NULL,
	`severity` enum('critical','high','medium','low') NOT NULL,
	`title` varchar(255) NOT NULL,
	`message` text NOT NULL,
	`status` enum('open','acknowledged','resolved') NOT NULL DEFAULT 'open',
	`acknowledged_by_user_id` int,
	`acknowledged_at` timestamp,
	`resolved_at` timestamp,
	`version` int NOT NULL DEFAULT 1,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	`updated_at` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `critical_alerts_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `institutions` (
	`id` int AUTO_INCREMENT NOT NULL,
	`code` varchar(32) NOT NULL,
	`name_ar` varchar(255) NOT NULL,
	`name_en` varchar(255) NOT NULL,
	`is_active` int NOT NULL DEFAULT 1,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	`updated_at` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `institutions_id` PRIMARY KEY(`id`),
	CONSTRAINT `institutions_code_unique` UNIQUE(`code`)
);
--> statement-breakpoint
CREATE TABLE `lab_order_tests` (
	`id` int AUTO_INCREMENT NOT NULL,
	`order_id` int NOT NULL,
	`test_code` varchar(64) NOT NULL,
	`test_name_ar` varchar(255) NOT NULL,
	`test_name_en` varchar(255) NOT NULL,
	`status` enum('not_started','entered','pending_review','approved','released','rejected') NOT NULL DEFAULT 'not_started',
	`created_at` timestamp NOT NULL DEFAULT (now()),
	`updated_at` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `lab_order_tests_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `lab_orders` (
	`id` int AUTO_INCREMENT NOT NULL,
	`institution_id` int NOT NULL,
	`laboratory_id` int NOT NULL,
	`patient_id` int NOT NULL,
	`ordering_physician_id` int NOT NULL,
	`order_number` varchar(64) NOT NULL,
	`priority` enum('routine','urgent','stat') NOT NULL DEFAULT 'routine',
	`clinical_notes` text,
	`status` enum('draft','submitted','sample_pending','in_progress','result_pending_review','completed','cancelled') NOT NULL DEFAULT 'draft',
	`version` int NOT NULL DEFAULT 1,
	`submitted_at` timestamp,
	`completed_at` timestamp,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	`updated_at` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `lab_orders_id` PRIMARY KEY(`id`),
	CONSTRAINT `lab_orders_institution_number_unique` UNIQUE(`institution_id`,`order_number`)
);
--> statement-breakpoint
CREATE TABLE `laboratories` (
	`id` int AUTO_INCREMENT NOT NULL,
	`institution_id` int NOT NULL,
	`code` varchar(32) NOT NULL,
	`name_ar` varchar(255) NOT NULL,
	`name_en` varchar(255) NOT NULL,
	`address` text,
	`is_active` int NOT NULL DEFAULT 1,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	`updated_at` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `laboratories_id` PRIMARY KEY(`id`),
	CONSTRAINT `laboratories_institution_code_unique` UNIQUE(`institution_id`,`code`)
);
--> statement-breakpoint
CREATE TABLE `notifications` (
	`id` int AUTO_INCREMENT NOT NULL,
	`recipient_user_id` int NOT NULL,
	`alert_id` int,
	`title` varchar(255) NOT NULL,
	`message` text NOT NULL,
	`status` enum('unread','read','archived') NOT NULL DEFAULT 'unread',
	`created_at` timestamp NOT NULL DEFAULT (now()),
	`read_at` timestamp,
	CONSTRAINT `notifications_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `patient_medical_records` (
	`id` int AUTO_INCREMENT NOT NULL,
	`patient_id` int NOT NULL,
	`authored_by_user_id` int NOT NULL,
	`summary` text NOT NULL,
	`allergies` text,
	`chronic_conditions` text,
	`medications` text,
	`version` int NOT NULL DEFAULT 1,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	`updated_at` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `patient_medical_records_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `patients` (
	`id` int AUTO_INCREMENT NOT NULL,
	`institution_id` int NOT NULL,
	`linked_user_id` int,
	`medical_record_number` varchar(64) NOT NULL,
	`national_id` varchar(64),
	`first_name` varchar(120) NOT NULL,
	`last_name` varchar(120) NOT NULL,
	`date_of_birth` timestamp,
	`sex` enum('female','male','other','unknown') NOT NULL DEFAULT 'unknown',
	`phone` varchar(32),
	`email` varchar(320),
	`address` text,
	`emergency_contact` varchar(255),
	`version` int NOT NULL DEFAULT 1,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	`updated_at` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `patients_id` PRIMARY KEY(`id`),
	CONSTRAINT `patients_institution_mrn_unique` UNIQUE(`institution_id`,`medical_record_number`)
);
--> statement-breakpoint
CREATE TABLE `result_review_events` (
	`id` int AUTO_INCREMENT NOT NULL,
	`result_id` int NOT NULL,
	`previous_status` enum('not_started','entered','pending_review','approved','released','rejected'),
	`next_status` enum('not_started','entered','pending_review','approved','released','rejected') NOT NULL,
	`comment` text,
	`performed_by_user_id` int NOT NULL,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `result_review_events_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `sample_status_events` (
	`id` int AUTO_INCREMENT NOT NULL,
	`sample_id` int NOT NULL,
	`previous_status` enum('expected','received','verified','processing','rejected','completed'),
	`next_status` enum('expected','received','verified','processing','rejected','completed') NOT NULL,
	`reason` text,
	`performed_by_user_id` int NOT NULL,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `sample_status_events_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `samples` (
	`id` int AUTO_INCREMENT NOT NULL,
	`order_id` int NOT NULL,
	`laboratory_id` int NOT NULL,
	`barcode` varchar(128) NOT NULL,
	`specimen_type` varchar(100) NOT NULL,
	`status` enum('expected','received','verified','processing','rejected','completed') NOT NULL DEFAULT 'expected',
	`collected_at` timestamp,
	`received_at` timestamp,
	`verified_at` timestamp,
	`rejected_reason` text,
	`version` int NOT NULL DEFAULT 1,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	`updated_at` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `samples_id` PRIMARY KEY(`id`),
	CONSTRAINT `samples_laboratory_barcode_unique` UNIQUE(`laboratory_id`,`barcode`)
);
--> statement-breakpoint
CREATE TABLE `test_results` (
	`id` int AUTO_INCREMENT NOT NULL,
	`order_test_id` int NOT NULL,
	`sample_id` int NOT NULL,
	`value` varchar(255),
	`unit` varchar(64),
	`reference_range` varchar(255),
	`interpretation` text,
	`is_critical` int NOT NULL DEFAULT 0,
	`status` enum('not_started','entered','pending_review','approved','released','rejected') NOT NULL DEFAULT 'not_started',
	`entered_by_user_id` int,
	`reviewed_by_user_id` int,
	`released_by_user_id` int,
	`entered_at` timestamp,
	`reviewed_at` timestamp,
	`released_at` timestamp,
	`version` int NOT NULL DEFAULT 1,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	`updated_at` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `test_results_id` PRIMARY KEY(`id`),
	CONSTRAINT `test_results_order_test_unique` UNIQUE(`order_test_id`)
);
--> statement-breakpoint
CREATE TABLE `user_role_assignments` (
	`id` int AUTO_INCREMENT NOT NULL,
	`user_id` int NOT NULL,
	`institution_id` int NOT NULL,
	`laboratory_id` int,
	`role` enum('patient','lab_staff','physician','institution_admin','system_admin') NOT NULL,
	`is_active` int NOT NULL DEFAULT 1,
	`assigned_by_user_id` int,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	`updated_at` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `user_role_assignments_id` PRIMARY KEY(`id`),
	CONSTRAINT `role_assignment_scope_unique` UNIQUE(`user_id`,`institution_id`,`laboratory_id`,`role`)
);
--> statement-breakpoint
ALTER TABLE `users` RENAME COLUMN `openId` TO `open_id`;--> statement-breakpoint
ALTER TABLE `users` RENAME COLUMN `createdAt` TO `created_at`;--> statement-breakpoint
ALTER TABLE `users` RENAME COLUMN `updatedAt` TO `updated_at`;--> statement-breakpoint
ALTER TABLE `users` RENAME COLUMN `lastSignedIn` TO `last_signed_in`;--> statement-breakpoint
ALTER TABLE `users` DROP INDEX `users_openId_unique`;--> statement-breakpoint
ALTER TABLE `users` MODIFY COLUMN `name` varchar(255);--> statement-breakpoint
ALTER TABLE `users` MODIFY COLUMN `role` enum('patient','lab_staff','physician','institution_admin','system_admin') NOT NULL DEFAULT 'patient';--> statement-breakpoint
ALTER TABLE `users` ADD `institution_id` int;--> statement-breakpoint
ALTER TABLE `users` ADD `laboratory_id` int;--> statement-breakpoint
ALTER TABLE `users` ADD `login_method` varchar(64);--> statement-breakpoint
ALTER TABLE `users` ADD `account_status` enum('active','suspended','pending') DEFAULT 'pending' NOT NULL;--> statement-breakpoint
ALTER TABLE `users` ADD `staff_identifier` varchar(80);--> statement-breakpoint
ALTER TABLE `users` ADD CONSTRAINT `users_open_id_unique` UNIQUE(`open_id`);--> statement-breakpoint
ALTER TABLE `users` ADD CONSTRAINT `users_institution_email_unique` UNIQUE(`institution_id`,`email`);--> statement-breakpoint
ALTER TABLE `audit_log` ADD CONSTRAINT `audit_log_institution_id_institutions_id_fk` FOREIGN KEY (`institution_id`) REFERENCES `institutions`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `audit_log` ADD CONSTRAINT `audit_log_actor_user_id_users_id_fk` FOREIGN KEY (`actor_user_id`) REFERENCES `users`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `critical_alerts` ADD CONSTRAINT `critical_alerts_institution_id_institutions_id_fk` FOREIGN KEY (`institution_id`) REFERENCES `institutions`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `critical_alerts` ADD CONSTRAINT `critical_alerts_result_id_test_results_id_fk` FOREIGN KEY (`result_id`) REFERENCES `test_results`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `critical_alerts` ADD CONSTRAINT `critical_alerts_patient_id_patients_id_fk` FOREIGN KEY (`patient_id`) REFERENCES `patients`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `critical_alerts` ADD CONSTRAINT `critical_alerts_acknowledged_by_user_id_users_id_fk` FOREIGN KEY (`acknowledged_by_user_id`) REFERENCES `users`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `lab_order_tests` ADD CONSTRAINT `lab_order_tests_order_id_lab_orders_id_fk` FOREIGN KEY (`order_id`) REFERENCES `lab_orders`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `lab_orders` ADD CONSTRAINT `lab_orders_institution_id_institutions_id_fk` FOREIGN KEY (`institution_id`) REFERENCES `institutions`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `lab_orders` ADD CONSTRAINT `lab_orders_laboratory_id_laboratories_id_fk` FOREIGN KEY (`laboratory_id`) REFERENCES `laboratories`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `lab_orders` ADD CONSTRAINT `lab_orders_patient_id_patients_id_fk` FOREIGN KEY (`patient_id`) REFERENCES `patients`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `lab_orders` ADD CONSTRAINT `lab_orders_ordering_physician_id_users_id_fk` FOREIGN KEY (`ordering_physician_id`) REFERENCES `users`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `laboratories` ADD CONSTRAINT `laboratories_institution_id_institutions_id_fk` FOREIGN KEY (`institution_id`) REFERENCES `institutions`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `notifications` ADD CONSTRAINT `notifications_recipient_user_id_users_id_fk` FOREIGN KEY (`recipient_user_id`) REFERENCES `users`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `notifications` ADD CONSTRAINT `notifications_alert_id_critical_alerts_id_fk` FOREIGN KEY (`alert_id`) REFERENCES `critical_alerts`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `patient_medical_records` ADD CONSTRAINT `patient_medical_records_patient_id_patients_id_fk` FOREIGN KEY (`patient_id`) REFERENCES `patients`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `patient_medical_records` ADD CONSTRAINT `patient_medical_records_authored_by_user_id_users_id_fk` FOREIGN KEY (`authored_by_user_id`) REFERENCES `users`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `patients` ADD CONSTRAINT `patients_institution_id_institutions_id_fk` FOREIGN KEY (`institution_id`) REFERENCES `institutions`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `patients` ADD CONSTRAINT `patients_linked_user_id_users_id_fk` FOREIGN KEY (`linked_user_id`) REFERENCES `users`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `result_review_events` ADD CONSTRAINT `result_review_events_result_id_test_results_id_fk` FOREIGN KEY (`result_id`) REFERENCES `test_results`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `result_review_events` ADD CONSTRAINT `result_review_events_performed_by_user_id_users_id_fk` FOREIGN KEY (`performed_by_user_id`) REFERENCES `users`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `sample_status_events` ADD CONSTRAINT `sample_status_events_sample_id_samples_id_fk` FOREIGN KEY (`sample_id`) REFERENCES `samples`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `sample_status_events` ADD CONSTRAINT `sample_status_events_performed_by_user_id_users_id_fk` FOREIGN KEY (`performed_by_user_id`) REFERENCES `users`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `samples` ADD CONSTRAINT `samples_order_id_lab_orders_id_fk` FOREIGN KEY (`order_id`) REFERENCES `lab_orders`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `samples` ADD CONSTRAINT `samples_laboratory_id_laboratories_id_fk` FOREIGN KEY (`laboratory_id`) REFERENCES `laboratories`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `test_results` ADD CONSTRAINT `test_results_order_test_id_lab_order_tests_id_fk` FOREIGN KEY (`order_test_id`) REFERENCES `lab_order_tests`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `test_results` ADD CONSTRAINT `test_results_sample_id_samples_id_fk` FOREIGN KEY (`sample_id`) REFERENCES `samples`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `test_results` ADD CONSTRAINT `test_results_entered_by_user_id_users_id_fk` FOREIGN KEY (`entered_by_user_id`) REFERENCES `users`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `test_results` ADD CONSTRAINT `test_results_reviewed_by_user_id_users_id_fk` FOREIGN KEY (`reviewed_by_user_id`) REFERENCES `users`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `test_results` ADD CONSTRAINT `test_results_released_by_user_id_users_id_fk` FOREIGN KEY (`released_by_user_id`) REFERENCES `users`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `user_role_assignments` ADD CONSTRAINT `user_role_assignments_user_id_users_id_fk` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `user_role_assignments` ADD CONSTRAINT `user_role_assignments_institution_id_institutions_id_fk` FOREIGN KEY (`institution_id`) REFERENCES `institutions`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `user_role_assignments` ADD CONSTRAINT `user_role_assignments_laboratory_id_laboratories_id_fk` FOREIGN KEY (`laboratory_id`) REFERENCES `laboratories`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `user_role_assignments` ADD CONSTRAINT `user_role_assignments_assigned_by_user_id_users_id_fk` FOREIGN KEY (`assigned_by_user_id`) REFERENCES `users`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
CREATE INDEX `audit_log_institution_created_idx` ON `audit_log` (`institution_id`,`created_at`);--> statement-breakpoint
CREATE INDEX `audit_log_actor_created_idx` ON `audit_log` (`actor_user_id`,`created_at`);--> statement-breakpoint
CREATE INDEX `audit_log_entity_idx` ON `audit_log` (`entity_type`,`entity_id`);--> statement-breakpoint
CREATE INDEX `critical_alerts_institution_status_idx` ON `critical_alerts` (`institution_id`,`status`);--> statement-breakpoint
CREATE INDEX `critical_alerts_patient_idx` ON `critical_alerts` (`patient_id`);--> statement-breakpoint
CREATE INDEX `lab_order_tests_order_idx` ON `lab_order_tests` (`order_id`);--> statement-breakpoint
CREATE INDEX `lab_orders_patient_idx` ON `lab_orders` (`patient_id`);--> statement-breakpoint
CREATE INDEX `lab_orders_laboratory_status_idx` ON `lab_orders` (`laboratory_id`,`status`);--> statement-breakpoint
CREATE INDEX `laboratories_institution_idx` ON `laboratories` (`institution_id`);--> statement-breakpoint
CREATE INDEX `notifications_recipient_status_idx` ON `notifications` (`recipient_user_id`,`status`);--> statement-breakpoint
CREATE INDEX `patient_records_patient_idx` ON `patient_medical_records` (`patient_id`);--> statement-breakpoint
CREATE INDEX `patients_institution_idx` ON `patients` (`institution_id`);--> statement-breakpoint
CREATE INDEX `patients_name_idx` ON `patients` (`last_name`,`first_name`);--> statement-breakpoint
CREATE INDEX `result_review_events_result_idx` ON `result_review_events` (`result_id`);--> statement-breakpoint
CREATE INDEX `sample_events_sample_idx` ON `sample_status_events` (`sample_id`);--> statement-breakpoint
CREATE INDEX `samples_order_idx` ON `samples` (`order_id`);--> statement-breakpoint
CREATE INDEX `samples_laboratory_status_idx` ON `samples` (`laboratory_id`,`status`);--> statement-breakpoint
CREATE INDEX `test_results_sample_idx` ON `test_results` (`sample_id`);--> statement-breakpoint
CREATE INDEX `test_results_status_idx` ON `test_results` (`status`);--> statement-breakpoint
CREATE INDEX `role_assignment_user_idx` ON `user_role_assignments` (`user_id`);--> statement-breakpoint
ALTER TABLE `users` ADD CONSTRAINT `users_institution_id_institutions_id_fk` FOREIGN KEY (`institution_id`) REFERENCES `institutions`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `users` ADD CONSTRAINT `users_laboratory_id_laboratories_id_fk` FOREIGN KEY (`laboratory_id`) REFERENCES `laboratories`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
CREATE INDEX `users_institution_idx` ON `users` (`institution_id`);--> statement-breakpoint
CREATE INDEX `users_laboratory_idx` ON `users` (`laboratory_id`);--> statement-breakpoint
ALTER TABLE `users` DROP COLUMN `loginMethod`;