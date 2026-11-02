-- Append-only import references/review records; a URL alone is never a deck version.
CREATE TABLE deck_import_attempts (
 id uuid PRIMARY KEY,
 team_id uuid NOT NULL REFERENCES teams(id),
 slot integer NOT NULL CHECK(slot IN(1,2)),
 source_url text,
 state text NOT NULL CHECK(state IN('awaiting_decklist','needs_review','imported','cancelled')),
 message text NOT NULL DEFAULT '',
 raw_deck jsonb,
 source_text text,
 issues jsonb NOT NULL DEFAULT '[]',
 deck_version_id uuid REFERENCES deck_versions(id),
 actor text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE INDEX deck_import_team_history ON deck_import_attempts(team_id,slot,created_at DESC);
INSERT INTO migrations(version) VALUES(3);
