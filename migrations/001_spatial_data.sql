-- Independent public-data interview prototype. Run against an empty project database.
BEGIN;
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE TABLE IF NOT EXISTS schema_migrations (
  version text PRIMARY KEY,
  applied_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS dataset_registry (
  layer text PRIMARY KEY,
  metadata jsonb NOT NULL,
  loaded_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS spatial_features (
  layer text NOT NULL REFERENCES dataset_registry(layer),
  feature_id text NOT NULL,
  properties jsonb NOT NULL,
  geom geometry(Geometry,4326) NOT NULL,
  PRIMARY KEY(layer,feature_id),
  CONSTRAINT valid_geometry CHECK (ST_IsValid(geom)),
  CONSTRAINT nonempty_geometry CHECK (NOT ST_IsEmpty(geom))
);
CREATE INDEX IF NOT EXISTS spatial_features_geom_idx ON spatial_features USING gist(geom);
CREATE INDEX IF NOT EXISTS spatial_features_bng_idx ON spatial_features USING gist(ST_Transform(geom,27700));
INSERT INTO schema_migrations(version) VALUES ('001_spatial_data') ON CONFLICT DO NOTHING;
COMMIT;
