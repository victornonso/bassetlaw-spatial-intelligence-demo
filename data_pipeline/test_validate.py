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
