CREATE TABLE `rooms` (
	`id` text PRIMARY KEY NOT NULL,
	`read_hash` text NOT NULL,
	`john_hash` text NOT NULL,
	`eddie_hash` text NOT NULL,
	`state` text NOT NULL,
	`revision` integer DEFAULT 0 NOT NULL,
	`created_at` integer NOT NULL
);
