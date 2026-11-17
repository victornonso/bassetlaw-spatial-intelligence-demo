import pytest
from data_pipeline.validate import validate

def fc(ids):
 return {'type':'FeatureCollection','features':[{'type':'Feature','geometry':{'type':'Point','coordinates':[-1,53.3]},'properties':{'id':i}} for i in ids]}
def test_valid():assert validate(fc(['x']))==1
def test_duplicate():
 with pytest.raises(ValueError):validate(fc(['x','x']))
def test_missing_id():
 with pytest.raises(ValueError):validate(fc([None]))
def test_bad_coordinates():
 f=fc(['x']);f['features'][0]['geometry']['coordinates']=[500000,300000]
 with pytest.raises(ValueError):validate(f)
def test_empty():
 f=fc(['x']);f['features'][0]['geometry']={'type':'Polygon','coordinates':[]}
 with pytest.raises(ValueError):validate(f)


def test_generalisation_omits_collapsed_polygon(tmp_path,monkeypatch):
 import json
 import data_pipeline.validate as module
 from shapely.geometry import box,mapping
 monkeypatch.setattr(module,'ROOT',tmp_path)
 (tmp_path/'data').mkdir()
 (tmp_path/'.cache/public-data').mkdir(parents=True)
 boundary={'type':'FeatureCollection','features':[{'geometry':mapping(box(-1.1,53.2,-.9,53.4))}]}
 (tmp_path/'data/admin_areas.geojson').write_text(json.dumps(boundary))
 raw=[{'geometry':mapping(box(-1,53.3,-.999999,53.300001)),'properties':{'flood_zone':'FZ2'}}]
 (tmp_path/'.cache/public-data/flood.json').write_text(json.dumps(raw))
 module.compact_flood()
 result=json.loads((tmp_path/'data/flood_zones.geojson').read_text())
 assert result['features']==[]
