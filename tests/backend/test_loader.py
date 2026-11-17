import json

import pytest
from manage import load


@pytest.mark.parametrize('features', [
    [{'type': 'Feature', 'properties': {}, 'geometry': {'type': 'Point', 'coordinates': [-.9, 53.3]}}],
    [{'type': 'Feature', 'properties': {'id': 'same'}, 'geometry': {'type': 'Point', 'coordinates': [-.9, 53.3]}}] * 2,
    [{'type': 'Feature', 'properties': {'id': 'bng'}, 'geometry': {'type': 'Point', 'coordinates': [460000, 380000]}}],
    [{'type': 'Feature', 'properties': {'id': 'empty'}, 'geometry': {'type': 'Point', 'coordinates': []}}],
])
def test_invalid_snapshot_rejected_before_database_write(tmp_path, monkeypatch, features):
    (tmp_path / 'dataset_registry.json').write_text(json.dumps([{'layer': 'services'}]))
    (tmp_path / 'services.geojson').write_text(json.dumps({'type': 'FeatureCollection', 'features': features}))
    def must_not_connect(*args, **kwargs):
        pytest.fail('Invalid snapshots must fail before any database connection/write')
    monkeypatch.setattr('psycopg.connect', must_not_connect)
    with pytest.raises(ValueError):
        load('not-used', tmp_path)
