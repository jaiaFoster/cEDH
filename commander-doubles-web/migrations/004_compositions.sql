CREATE TABLE composition_entries (
 id text PRIMARY KEY CHECK(id ~ '^[a-z][a-z0-9-]{2,79}$'),
 pair_key text NOT NULL UNIQUE,
 published_version_id uuid,
 hidden boolean NOT NULL DEFAULT false,
 seed_hash text,
 created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE composition_versions (
 id uuid PRIMARY KEY,
 composition_id text NOT NULL REFERENCES composition_entries(id),
 revision integer NOT NULL CHECK(revision>0),
 content jsonb NOT NULL,
 actor text NOT NULL,
 change_note text NOT NULL,
 restored_from uuid REFERENCES composition_versions(id) DEFERRABLE INITIALLY DEFERRED,
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(composition_id,revision), UNIQUE(composition_id,id)
);
ALTER TABLE composition_entries ADD CONSTRAINT composition_published_version
 FOREIGN KEY(id,published_version_id) REFERENCES composition_versions(composition_id,id) DEFERRABLE INITIALLY DEFERRED;
CREATE INDEX composition_history ON composition_versions(composition_id,revision DESC);
INSERT INTO migrations(version) VALUES(4);
