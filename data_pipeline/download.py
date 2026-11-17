"""Refresh public extracts; do not infer values when a source fails."""
import argparse,csv,io,json,zipfile,urllib.request,urllib.parse
from datetime import datetime,timezone
from pathlib import Path
from shapely import make_valid
from shapely.geometry import shape,mapping,Point
from pyproj import Transformer
from .validate import ROOT,validate,compact_flood,report
CACHE=ROOT/'.cache/public-data'; CACHE.mkdir(parents=True,exist_ok=True)
def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 BassetlawIndependentPrototype/1.0'})
    with urllib.request.urlopen(req,timeout=120) as r:return r.read()
def write(layer,features):
    fc={'type':'FeatureCollection','features':features};validate(fc)
    (ROOT/'data'/f'{layer}.geojson').write_text(json.dumps(fc,separators=(',',':')),encoding='utf-8')
def feature(g,p):return {'type':'Feature','geometry':mapping(g),'properties':p}
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--use-cache',action='store_true');parser.add_argument('--gias-zip',type=Path);args=parser.parse_args()
    registry=json.loads((ROOT/'data/dataset_registry.json').read_text());sources={r['id']:r for r in registry}
    url=sources['admin_areas']['download_url']+'?'+urllib.parse.urlencode({'where':"LAD24CD='E07000171'",'outFields':'LAD24CD,LAD24NM','outSR':4326,'f':'geojson'})
    district=json.loads(fetch(url));f=district['features'][0];g=make_valid(shape(f['geometry']));write('admin_areas',[feature(g,{'id':'E07000171','name':'Bassetlaw','geography_date':'2024-12'})])
    bbox=','.join(map(str,g.bounds));url=sources['wards']['download_url']+'?'+urllib.parse.urlencode({'geometry':bbox,'geometryType':'esriGeometryEnvelope','inSR':4326,'spatialRel':'esriSpatialRelIntersects','outFields':'WD24CD,WD24NM','outSR':4326,'f':'geojson'})
    wards=json.loads(fetch(url));rows=[]
    for f in wards['features']:
        geom=make_valid(shape(f['geometry']))
        if g.buffer(.001).covers(geom.representative_point()):rows.append(feature(geom,{'id':f['properties']['WD24CD'],'name':f['properties']['WD24NM'],'geography_date':'2024-05'}))
    write('wards',rows)
    if not args.use_cache or not (CACHE/'flood.json').exists():
        url=sources['flood_zones']['download_url']+'?'+urllib.parse.urlencode({'bbox':bbox,'f':'json','limit':1000});rows=[]
        while url:
            doc=json.loads(fetch(url));rows.extend(doc['features']);url=next((l['href'] for l in doc.get('links',[]) if l.get('rel')=='next'),None)
        (CACHE/'flood.json').write_text(json.dumps(rows))
    compact_flood()
    transform=Transformer.from_crs(27700,4326,always_xy=True).transform
    csvbytes=fetch(sources['planning_context']['download_url']);rows=[]
    for r in csv.DictReader(io.StringIO(csvbytes.decode('utf-8-sig'))):
        if not r.get('GeoX') or not r.get('GeoY'):continue
        lon,lat=transform(float(r['GeoX']),float(r['GeoY']));point=Point(lon,lat)
        if not g.buffer(.001).covers(point):continue
        rows.append(feature(point,{'id':r['SiteReference'],'name':r['SiteNameAddress'].strip(" '\""),'planning_status':r.get('PlanningStatus'),'record_updated':r.get('LastUpdatedDate'),'geometry_role':'representative point, not site boundary','provider':'Bassetlaw District Council'}))
    write('planning_context',rows)
    archive=args.gias_zip or CACHE/'gias.zip'
    if not archive.exists():raise SystemExit('Download the official public GIAS ZIP from https://get-information-schools.service.gov.uk/Downloads and rerun with --gias-zip PATH. No school pages are scraped.')
    rows=[]
    with zipfile.ZipFile(archive) as z:
        file=next(n for n in z.namelist() if n.endswith('.csv'))
        for r in csv.DictReader(io.TextIOWrapper(z.open(file),encoding='cp1252')):
            if r.get('DistrictAdministrative (code)')!='E07000171' or r.get('EstablishmentStatus (code)')!='1':continue
            if not r.get('Easting') or not r.get('Northing'):continue
            lon,lat=transform(float(r['Easting']),float(r['Northing']));point=Point(lon,lat)
            if not g.buffer(.001).covers(point):continue
            rows.append(feature(point,{'id':r['URN'],'name':r['EstablishmentName'],'category':r['PhaseOfEducation (name)'],'provider':'Department for Education'}))
    write('services',rows)
    now=datetime.now(timezone.utc).isoformat()
    for r in registry:r['retrieved_at']=now;r['date_retrieved']=now[:10]
    (ROOT/'data/dataset_registry.json').write_text(json.dumps(registry,indent=2))
    report()
if __name__=='__main__':main()
