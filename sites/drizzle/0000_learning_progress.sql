CREATE TABLE sites_learning_progress (
  owner_id TEXT NOT NULL,
  topic TEXT NOT NULL,
  section_id TEXT NOT NULL,
  PRIMARY KEY (owner_id, topic, section_id)
);
