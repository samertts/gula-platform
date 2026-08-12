CREATE TABLE `gula_workspace_bindings` (
	`id` int AUTO_INCREMENT NOT NULL,
	`userId` int NOT NULL,
	`gulaSubjectId` int NOT NULL,
	`labId` int NOT NULL,
	`organizationId` int,
	`facilityId` int,
	`assignmentRoleId` varchar(128),
	`verifiedAt` timestamp NOT NULL,
	`verifiedByUserId` int NOT NULL,
	`status` enum('active','revoked') NOT NULL DEFAULT 'active',
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `gula_workspace_bindings_id` PRIMARY KEY(`id`),
	CONSTRAINT `gula_workspace_bindings_userId_unique` UNIQUE(`userId`)
);
