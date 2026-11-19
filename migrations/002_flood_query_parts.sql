-- Subdivision changes indexing granularity, never the analytical flood extent.
CREATE TABLE IF NOT EXISTS spatial_feature_parts (
    part_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    layer text NOT NULL,
    feature_id text NOT NULL,
    geom geometry(Geometry,4326) NOT NULL,
    FOREIGN KEY (layer,feature_id) REFERENCES spatial_features(layer,feature_id) ON DELETE CASCADE,
    CHECK (NOT ST_IsEmpty(geom) AND ST_IsValid(geom))
);
CREATE INDEX IF NOT EXISTS spatial_feature_parts_geom_idx ON spatial_feature_parts USING gist(geom);
CREATE INDEX IF NOT EXISTS spatial_feature_parts_parent_idx ON spatial_feature_parts(layer,feature_id);
INSERT INTO schema_migrations(version) VALUES ('002_flood_query_parts') ON CONFLICT DO NOTHING;
