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


def test_tiny_flood_polygon_is_retained_without_simplification():
 from shapely.geometry import box,mapping,shape
 from data_pipeline.flood import extract
 tiny=box(-1,53.3,-.999999,53.300001)
 result=extract([{'geometry':mapping(tiny),'properties':{'flood_zone':'FZ2'}}],box(-1.1,53.2,-.9,53.4))
 assert len(result['features'])==1
 assert shape(result['features'][0]['geometry']).equals(tiny)
 assert result['features'][0]['properties']['generalisation_m']==0
