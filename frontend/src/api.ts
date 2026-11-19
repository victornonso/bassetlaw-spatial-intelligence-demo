import type {FeatureCollection,Feature,Point,Polygon,MultiPolygon} from 'geojson';
import {booleanPointInPolygon,point,distance,area as turfArea,centroid} from '@turf/turf';
import {floodAt,floodIndex} from './flood';
export type Dataset={id:string;name?:string;provider?:string;url?:string;official_url?:string;source_url?:string;licence?:string;retrieved_at?:string;retrieved?:string;limitations?:string|string[];[key:string]:unknown};
export type UnavailableReason='not_included'|'temporarily_unavailable';
export type Layer={id:string;name:string;available:boolean;feature_count:number;source?:Dataset;unavailable_reason?:UnavailableReason};
export type Evidence={status:string;summary:string;unavailable_reason?:UnavailableReason;distance_m?:number|null;nearest?:Record<string,unknown>|null;features?:Record<string,unknown>[];count_within_2km?:number|null};
export type Insight={location:{lat:number;lon:number};area:{district:string|null;ward:string|null;ward_date?:string};evidence:Record<string,Evidence>;sources:Dataset[];method:{mode:string;distance:string}};
export type Community={area:{id:string;name:string;geography_date?:string};indicators:{label:string;value:number|string;unit?:string;description?:string}[];chart:{title:string;items:{label:string;value:number}[]};sources:Dataset[];limitations:string[];service_status?:'available'|UnavailableReason;method?:{mode:string}};
const base=import.meta.env.VITE_API_BASE_URL?.replace(/\/$/,'')||(import.meta.env.PROD?'https://bassetlaw-spatial-intelligence-demo.onrender.com':'');
export const layerNames:Record<string,string>={admin_areas:'District boundary',wards:'Wards (May 2024)',services:'Schools and colleges',green_spaces:'Green space',flood_zones:'River and sea flood zones',planning_context:'Brownfield register sites',strategic_sites:'Strategic development sites'};
const empty=():FeatureCollection=>({type:'FeatureCollection',features:[]});
export async function getJSON<T>(path:string):Promise<T>{const response=await fetch(`${base}${path}`,{signal:AbortSignal.timeout(10000)});if(!response.ok)throw Error(`Request failed (${response.status})`);return response.json();}
export const collectionCache:Record<string,FeatureCollection>={};
export async function features(id:string):Promise<FeatureCollection>{
 if(collectionCache[id])return collectionCache[id];
 try{const collection=await getJSON<FeatureCollection>(`/api/features/${id}`);if(collection.type!=='FeatureCollection')throw Error('Invalid data');return collectionCache[id]=collection;}
 catch{const response=await fetch(`/data/${id}.geojson`);if(!response.ok)throw Error('Dataset unavailable');const collection=await response.json();if(collection.type!=='FeatureCollection')throw Error('Invalid data');return collectionCache[id]=collection;}
}
export function featureName(feature:Feature):string{const p=feature.properties||{};return String(p.name||p.ward_name||p.WD24NM||p.WD25NM||p.WD23NM||p.WD22NM||p.LAD24NM||p.LAD25NM||p.NAME||p.Name||Object.entries(p).find(([key])=>key.toLowerCase().endsWith('nm'))?.[1]||'Unnamed location');}
export function featureId(feature:Feature):string{const p=feature.properties||{};return String(p.id||p.code||p.ward_code||p.WD24CD||p.WD25CD||p.WD23CD||p.WD22CD||feature.id||featureName(feature));}
export async function loadLayers():Promise<{layers:Layer[];mode:string}>{
 try{const result=await getJSON<{layers:Layer[];mode:string}>('/api/layers');return {...result,layers:result.layers.map(layer=>({...layer,name:layerNames[layer.id]||layer.name}))};}
 catch{const sources=await registry();const layers=await Promise.all(Object.keys(layerNames).map(async id=>{
  if(['green_spaces','strategic_sites'].includes(id)&&!sources.some(s=>s.id===id&&s.loaded))return {id,name:layerNames[id],available:false,feature_count:0,unavailable_reason:'not_included' as const};
  try{const count=id==='flood_zones'?(await floodIndex()).feature_count:(await features(id)).features.length;return {id,name:layerNames[id],available:count>0,feature_count:count,...(!count?{unavailable_reason:'not_included' as const}:{})};}
  catch{return {id,name:layerNames[id],available:false,feature_count:0,unavailable_reason:'temporarily_unavailable' as const};}
 }));return {layers,mode:'browser snapshot'};}
}
export async function registry():Promise<Dataset[]>{try{const response=await fetch('/data/dataset_registry.json');if(!response.ok)return [];const data=await response.json();return Array.isArray(data)?data:(data.datasets||Object.values(data));}catch{return [];}}
function contains(feature:Feature,lat:number,lon:number){return ['Polygon','MultiPolygon'].includes(feature.geometry.type)&&booleanPointInPolygon(point([lon,lat]),feature as Feature<Polygon|MultiPolygon>);}
function closest(collection:FeatureCollection,lat:number,lon:number){return collection.features.map(feature=>({feature,distance:distance(point([lon,lat]),feature.geometry.type==='Point'?feature as Feature<Point>:centroid(feature),{units:'meters'})})).sort((a,b)=>a.distance-b.distance);}
async function readLayer(id:string,sources:Dataset[]):Promise<{collection:FeatureCollection;state:'available'|UnavailableReason}>{
 const source=sources.find(s=>s.id===id);
 if(['green_spaces','strategic_sites'].includes(id)&&!source?.loaded)return {collection:empty(),state:'not_included'};
 try{const collection=await features(id);return {collection,state:collection.features.length?'available':Number(source?.feature_count)>0?'temporarily_unavailable':'not_included'};}
 catch{return {collection:empty(),state:'temporarily_unavailable'};}
}
function unavailable(reason:UnavailableReason):Evidence{return {status:'unavailable',unavailable_reason:reason,summary:reason==='not_included'?'Dataset not included in this prototype.':'Evidence temporarily unavailable. Please retry.'};}
export async function snapshotInsight(lat:number,lon:number):Promise<Insight>{
 const sources=await registry();
 const ids=['admin_areas','wards','services','planning_context','green_spaces','strategic_sites'];
 const results=await Promise.all(ids.map(id=>readLayer(id,sources)));
 const [district,wards,services,planning,greenspace,growth]=results;
 if(district.state!=='available')throw Error('District boundary temporarily unavailable.');
 if(!district.collection.features.some(feature=>contains(feature,lat,lon)))throw Error('Select a point inside the included Bassetlaw boundary.');
 const ward=wards.collection.features.find(feature=>contains(feature,lat,lon));
 const evidence:Record<string,Evidence>={};
 for(const [key,result,label] of [['planning',planning,'brownfield register site'],['services',services,'school or college'],['greenspace',greenspace,'green space'],['growth',growth,'strategic development site']] as const){
  if(result.state!=='available'){evidence[key]=unavailable(result.state);continue;}
  const nearest=closest(result.collection,lat,lon);
  evidence[key]={status:'available',summary:`Nearest ${label} in the loaded dataset: ${featureName(nearest[0].feature)}.`,nearest:nearest[0].feature.properties,distance_m:Math.round(nearest[0].distance),features:[],...(key==='services'?{count_within_2km:nearest.filter(item=>item.distance<=2000).length}:{})};
 }
 try{
  const flood=await floodAt(lat,lon);
  if(!flood.available)evidence.flood=unavailable('not_included');
  else{
   const hits=flood.collection.features.filter(feature=>contains(feature,lat,lon));
   const zones=[...new Set(hits.map(feature=>String(feature.properties?.flood_zone||featureName(feature).replace('Flood Zone ',''))).map(zone=>zone.replace('FZ','')))].sort();
   evidence.flood={status:'available',features:hits.map(feature=>feature.properties||{}),summary:hits.length?`The selected point falls within Environment Agency Flood ${zones.length===1?'Zone':'Zones'} ${zones.join(' and ')} in this dataset.`:'The selected point is outside the Flood Zone 2 and 3 polygons in this dataset. This does not establish that there is no flood risk.'};
  }
 }catch{evidence.flood=unavailable('temporarily_unavailable');}
 return {location:{lat,lon},area:{district:'Bassetlaw',ward:ward?featureName(ward):null,ward_date:ward?.properties?.geography_date},evidence,sources:sources.filter(source=>['admin_areas','wards'].includes(source.id)||results.some((result,index)=>ids[index]===source.id&&result.state==='available')||(source.id==='flood_zones'&&evidence.flood.status==='available')),method:{mode:'browser snapshot',distance:'Straight-line geodesic distances to published locations.'}};
}
export async function siteInsight(lat:number,lon:number):Promise<Insight>{try{return await getJSON(`/api/site-insight?lat=${lat}&lon=${lon}`);}catch{return snapshotInsight(lat,lon);}}
export async function community(id:string):Promise<Community>{
 try{return await getJSON(`/api/community/${encodeURIComponent(id)}`);}
 catch{
  const sources=await registry();const wards=await features('wards');const ward=wards.features.find(feature=>featureId(feature)===id);if(!ward)throw Error('Ward boundary unavailable.');
  const services=await readLayer('services',sources);
  const inside=services.collection.features.filter(feature=>feature.geometry.type==='Point'&&contains(ward,(feature.geometry as Point).coordinates[1],(feature.geometry as Point).coordinates[0]));
  const groups:Record<string,number>={};inside.forEach(feature=>{const phase=String(feature.properties?.phase||feature.properties?.category||'Not recorded');groups[phase]=(groups[phase]||0)+1;});
  return {area:{id,name:featureName(ward),geography_date:ward.properties?.geography_date},indicators:[{label:'Ward area',value:Number((turfArea(ward)/1e6).toFixed(2)),unit:'km²',description:'Calculated from the included ward boundary.'},{label:'Schools and colleges in this ward',value:services.state==='available'?inside.length:services.state==='not_included'?'Not included':'Temporarily unavailable',unit:services.state==='available'?'establishments':undefined,description:'Establishments recorded as open in the downloaded dataset, located within this ward boundary.'}],chart:{title:'Schools and colleges by education phase',items:Object.entries(groups).sort(([a],[b])=>a.localeCompare(b)).map(([label,value])=>({label,value}))},sources:sources.filter(source=>['wards','services'].includes(source.id)),limitations:['Population, deprivation and housing-need data are not included in this profile.','This dataset includes establishments within Bassetlaw; facilities outside the district are not included.'],service_status:services.state,method:{mode:'browser snapshot'}};
 }
}
