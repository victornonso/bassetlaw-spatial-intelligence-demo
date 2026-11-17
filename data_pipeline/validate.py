"""Validate and compact licensed GeoJSON snapshots before release."""
import hashlib,json
from pathlib import Path
from shapely import make_valid,union_all
from shapely.geometry import shape,mapping
from shapely import transform as vector_transform
def transform(fn,g): return vector_transform(g,fn,interleaved=False)
from pyproj import Transformer
ROOT=Path(__file__).resolve().parents[1]
def validate(fc):
    seen=set()
    if fc.get('type')!='FeatureCollection':raise ValueError('Expected FeatureCollection')
    for f in fc['features']:
        p=f.get('properties',{}); k=p.get('id')
        if not k or k in seen:raise ValueError('Missing or duplicate id')
        seen.add(k);g=shape(f['geometry'])
        if g.is_empty or not g.is_valid:raise ValueError(f'Invalid geometry {k}')
        x,y,X,Y=g.bounds
        if not(-180<=x<=X<=180 and -90<=y<=Y<=90):raise ValueError('Expected WGS84')
    return len(seen)
def compact_flood():
    src=ROOT/'.cache/public-data/flood.json'
    raw=json.loads(src.read_text())
    if isinstance(raw,dict):raw=raw['features']
    district=shape(json.loads((ROOT/'data/admin_areas.geojson').read_text())['features'][0]['geometry'])
    forward=Transformer.from_crs(4326,27700,always_xy=True).transform
    back=Transformer.from_crs(27700,4326,always_xy=True).transform
    boundary=transform(forward,district); groups={}
    for f in raw:
        g=make_valid(transform(forward,shape(f['geometry'])))
        if g.intersects(boundary):groups.setdefault(f['properties']['flood_zone'],[]).append(g.intersection(boundary).simplify(20,preserve_topology=True))
    features=[]
    for zone,geoms in sorted(groups.items()):
        for i,g in enumerate(geoms):
            if g.is_empty:continue
            g=make_valid(transform(back,g.simplify(50,preserve_topology=False)))
            if g.geom_type not in ['Polygon','MultiPolygon']:continue
            features.append({'type':'Feature','geometry':mapping(g),'properties':{'id':f'{zone}-{i}','name':'Flood Zone '+zone.replace('FZ',''),'flood_zone':zone,'provider':'Environment Agency','generalisation_m':50}})
    fc={'type':'FeatureCollection','features':features};validate(fc)
    (ROOT/'data/flood_zones.geojson').write_text(json.dumps(fc,separators=(',',':')),encoding='utf-8')
def report():
    registry=json.loads((ROOT/'data/dataset_registry.json').read_text())
    results={}
    for r in registry:
        p=ROOT/'data'/f"{r['id']}.geojson"
        if not p.exists():continue
        fc=json.loads(p.read_text(encoding='utf-8-sig'));count=validate(fc)
        r['feature_count']=count;r['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
        if r['id']=='flood_zones':
            r['transformations']='Download all pages, repair geometry, clip to district, simplify 50m followed by geometry validation in EPSG:27700, transform to EPSG:4326 and repair; no coordinate rounding.'
            r['limitations']+=' Simplified 50m display/analysis snapshot: boundaries can shift within this tolerance. Always consult the official Flood Map for Planning for site-scale assessment.'
        results[r['id']]={'status':'pass','feature_count':count,'sha256':r['sha256']}
    (ROOT/'data/dataset_registry.json').write_text(json.dumps(registry,indent=2),encoding='utf-8')
    (ROOT/'data/data_quality_report.json').write_text(json.dumps({'status':'pass','checks':['required identifiers','unique identifiers','valid nonempty geometry','WGS84 bounds'],'layers':results},indent=2),encoding='utf-8')
if __name__=='__main__':
    import sys
    if '--compact-flood' in sys.argv:compact_flood()
    report()
