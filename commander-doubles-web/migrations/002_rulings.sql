CREATE TABLE ruling_entries (
  id text PRIMARY KEY CHECK(id ~ '^[a-z][a-z0-9-]{2,79}$'),
  published_version_id uuid,
  hidden boolean NOT NULL DEFAULT false,
  seed_hash text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE ruling_versions (
  id uuid PRIMARY KEY,
  ruling_id text NOT NULL REFERENCES ruling_entries(id),
  revision integer NOT NULL CHECK(revision > 0),
  content jsonb NOT NULL,
  actor text NOT NULL,
  change_note text NOT NULL,
  restored_from uuid REFERENCES ruling_versions(id) DEFERRABLE INITIALLY DEFERRED,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(ruling_id,revision),
  UNIQUE(ruling_id,id)
);
ALTER TABLE ruling_entries ADD CONSTRAINT ruling_published_version
  FOREIGN KEY(id,published_version_id) REFERENCES ruling_versions(ruling_id,id)
  DEFERRABLE INITIALLY DEFERRED;
CREATE INDEX ruling_history ON ruling_versions(ruling_id,revision DESC);
INSERT INTO migrations(version) VALUES(2);
