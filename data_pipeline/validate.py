"""Validate and compact licensed GeoJSON snapshots before release."""
import gzip,hashlib,json
from pathlib import Path
from shapely.geometry import shape
from shapely import transform as vector_transform
def transform(fn,g): return vector_transform(g,fn,interleaved=False)
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
    # Retained CLI entry point: compact delivery, never compact analytical geometry.
    from .flood import build
    return build(ROOT)
def report():
    registry=json.loads((ROOT/'data/dataset_registry.json').read_text())
    results={}
    for r in registry:
        p=ROOT/'data'/f"{r['id']}.geojson"
        if not p.exists():p=p.with_suffix('.geojson.gz')
        if not p.exists():continue
        content=gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes()
        fc=json.loads(content.decode('utf-8-sig'));count=validate(fc)
        r['feature_count']=count;r['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
        if r['id']=='flood_zones':
            r['transformations']='Download all pages; repair invalid source geometry; clip to district in EPSG:4326; retain all polygon components and holes without simplification or area filtering. Losslessly compress analytical GeoJSON. Generate separate quantised vector display tiles and unsimplified analytical cells.'
            r['limitations']='Public snapshot of rivers and sea planning flood zones, not a property-level flood assessment or all-source flood risk. District clipping uses a historical generalised boundary. Display tiles are quantised by zoom; analytical intersections use source-detail geometry. Consult the official Flood Map for Planning for actual decisions.'
            r['analysis_generalisation_m']=0
        results[r['id']]={'status':'pass','feature_count':count,'sha256':r['sha256']}
    (ROOT/'data/dataset_registry.json').write_text(json.dumps(registry,indent=2),encoding='utf-8')
    (ROOT/'data/data_quality_report.json').write_text(json.dumps({'status':'pass','checks':['required identifiers','unique identifiers','valid nonempty geometry','WGS84 bounds'],'layers':results},indent=2),encoding='utf-8')
if __name__=='__main__':
    import sys
    if '--compact-flood' in sys.argv:compact_flood()
    report()
