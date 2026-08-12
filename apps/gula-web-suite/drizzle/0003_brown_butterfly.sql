CREATE TABLE `clinic_consultations` (
	`id` int AUTO_INCREMENT NOT NULL,
	`institution_id` int NOT NULL,
	`patient_id` int NOT NULL,
	`physician_id` int NOT NULL,
	`chief_complaint` text NOT NULL,
	`diagnosis` text,
	`soap_notes` text,
	`prescription_summary` text,
	`status` enum('scheduled','in_progress','completed','cancelled') NOT NULL DEFAULT 'scheduled',
	`consulted_at` timestamp NOT NULL DEFAULT (now()),
	`version` int NOT NULL DEFAULT 1,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	`updated_at` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `clinic_consultations_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `emergency_triage` (
	`id` int AUTO_INCREMENT NOT NULL,
	`institution_id` int NOT NULL,
	`patient_id` int NOT NULL,
	`triage_level` enum('resuscitation','emergent','urgent','less_urgent','non_urgent') NOT NULL DEFAULT 'urgent',
	`presenting_chief_complaint` text NOT NULL,
	`vital_signs_json` text,
	`disposition` enum('admitted','discharged','transferred','deceased') NOT NULL DEFAULT 'admitted',
	`triaged_at` timestamp NOT NULL DEFAULT (now()),
	`created_at` timestamp NOT NULL DEFAULT (now()),
	`updated_at` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `emergency_triage_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `hospital_admissions` (
	`id` int AUTO_INCREMENT NOT NULL,
	`institution_id` int NOT NULL,
	`patient_id` int NOT NULL,
	`ward` varchar(100) NOT NULL,
	`bed_number` varchar(32) NOT NULL,
	`admitting_physician_id` int NOT NULL,
	`status` enum('admitted','transferred','discharged') NOT NULL DEFAULT 'admitted',
	`admitted_at` timestamp NOT NULL DEFAULT (now()),
	`discharged_at` timestamp,
	`notes` text,
	`version` int NOT NULL DEFAULT 1,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	`updated_at` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `hospital_admissions_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `pharmacy_dispensations` (
	`id` int AUTO_INCREMENT NOT NULL,
	`institution_id` int NOT NULL,
	`patient_id` int NOT NULL,
	`pharmacist_id` int NOT NULL,
	`drug_name` varchar(255) NOT NULL,
	`dosage` varchar(120) NOT NULL,
	`quantity` int NOT NULL DEFAULT 1,
	`status` enum('prescribed','dispensed','cancelled') NOT NULL DEFAULT 'prescribed',
	`dispensed_at` timestamp,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	`updated_at` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `pharmacy_dispensations_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `public_health_reports` (
	`id` int AUTO_INCREMENT NOT NULL,
	`institution_id` int NOT NULL,
	`disease_code` varchar(64) NOT NULL,
	`disease_name` varchar(255) NOT NULL,
	`confirmed_cases_count` int NOT NULL DEFAULT 1,
	`notes` text,
	`reported_at` timestamp NOT NULL DEFAULT (now()),
	`created_at` timestamp NOT NULL DEFAULT (now()),
	`updated_at` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `public_health_reports_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `radiology_orders` (
	`id` int AUTO_INCREMENT NOT NULL,
	`institution_id` int NOT NULL,
	`patient_id` int NOT NULL,
	`ordering_physician_id` int NOT NULL,
	`modality` varchar(64) NOT NULL,
	`body_part` varchar(120) NOT NULL,
	`clinical_indication` text,
	`radiologist_report` text,
	`status` enum('ordered','imaging_in_progress','reported','cancelled') NOT NULL DEFAULT 'ordered',
	`reported_at` timestamp,
	`version` int NOT NULL DEFAULT 1,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	`updated_at` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `radiology_orders_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
ALTER TABLE `clinic_consultations` ADD CONSTRAINT `clinic_consultations_institution_id_institutions_id_fk` FOREIGN KEY (`institution_id`) REFERENCES `institutions`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `clinic_consultations` ADD CONSTRAINT `clinic_consultations_patient_id_patients_id_fk` FOREIGN KEY (`patient_id`) REFERENCES `patients`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `clinic_consultations` ADD CONSTRAINT `clinic_consultations_physician_id_users_id_fk` FOREIGN KEY (`physician_id`) REFERENCES `users`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `emergency_triage` ADD CONSTRAINT `emergency_triage_institution_id_institutions_id_fk` FOREIGN KEY (`institution_id`) REFERENCES `institutions`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `emergency_triage` ADD CONSTRAINT `emergency_triage_patient_id_patients_id_fk` FOREIGN KEY (`patient_id`) REFERENCES `patients`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `hospital_admissions` ADD CONSTRAINT `hospital_admissions_institution_id_institutions_id_fk` FOREIGN KEY (`institution_id`) REFERENCES `institutions`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `hospital_admissions` ADD CONSTRAINT `hospital_admissions_patient_id_patients_id_fk` FOREIGN KEY (`patient_id`) REFERENCES `patients`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `hospital_admissions` ADD CONSTRAINT `hospital_admissions_admitting_physician_id_users_id_fk` FOREIGN KEY (`admitting_physician_id`) REFERENCES `users`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `pharmacy_dispensations` ADD CONSTRAINT `pharmacy_dispensations_institution_id_institutions_id_fk` FOREIGN KEY (`institution_id`) REFERENCES `institutions`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `pharmacy_dispensations` ADD CONSTRAINT `pharmacy_dispensations_patient_id_patients_id_fk` FOREIGN KEY (`patient_id`) REFERENCES `patients`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `pharmacy_dispensations` ADD CONSTRAINT `pharmacy_dispensations_pharmacist_id_users_id_fk` FOREIGN KEY (`pharmacist_id`) REFERENCES `users`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `public_health_reports` ADD CONSTRAINT `public_health_reports_institution_id_institutions_id_fk` FOREIGN KEY (`institution_id`) REFERENCES `institutions`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `radiology_orders` ADD CONSTRAINT `radiology_orders_institution_id_institutions_id_fk` FOREIGN KEY (`institution_id`) REFERENCES `institutions`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `radiology_orders` ADD CONSTRAINT `radiology_orders_patient_id_patients_id_fk` FOREIGN KEY (`patient_id`) REFERENCES `patients`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `radiology_orders` ADD CONSTRAINT `radiology_orders_ordering_physician_id_users_id_fk` FOREIGN KEY (`ordering_physician_id`) REFERENCES `users`(`id`) ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
CREATE INDEX `clinic_consultations_patient_idx` ON `clinic_consultations` (`patient_id`);--> statement-breakpoint
CREATE INDEX `emergency_triage_institution_idx` ON `emergency_triage` (`institution_id`);--> statement-breakpoint
CREATE INDEX `hospital_admissions_institution_status_idx` ON `hospital_admissions` (`institution_id`,`status`);--> statement-breakpoint
CREATE INDEX `pharmacy_dispensations_patient_idx` ON `pharmacy_dispensations` (`patient_id`);--> statement-breakpoint
CREATE INDEX `public_health_reports_institution_idx` ON `public_health_reports` (`institution_id`);--> statement-breakpoint
CREATE INDEX `radiology_orders_patient_idx` ON `radiology_orders` (`patient_id`);