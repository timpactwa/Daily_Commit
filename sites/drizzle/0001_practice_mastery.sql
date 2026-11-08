CREATE TABLE sites_practice_sessions (
  owner_id TEXT NOT NULL,
  lesson_id TEXT NOT NULL,
  day TEXT NOT NULL,
  data TEXT NOT NULL,
  completed INTEGER NOT NULL DEFAULT 0,
  locked_until INTEGER NOT NULL DEFAULT 0,
  lock_token TEXT,
  PRIMARY KEY (owner_id, lesson_id)
);
--> statement-breakpoint
CREATE INDEX sites_practice_pending ON sites_practice_sessions (owner_id, completed, day);
