import type {FeatureCollection} from 'geojson';

type AnalysisIndex={zoom:number;cells:string[];template:string;feature_count:number;revision:string};
export type FloodMap={tiles:string[];minzoom:number;maxzoom:number;bounds:[number,number,number,number];attribution:string};
let indexRequest:Promise<AnalysisIndex>|undefined;
const cells=new Map<string,Promise<FeatureCollection>>();
async function read<T>(url:string):Promise<T>{
 const response=await fetch(url);
 if(!response.ok)throw Error('Flood snapshot unavailable');
 return response.json();
}
export function floodIndex():Promise<AnalysisIndex>{
 if(!indexRequest)indexRequest=read<AnalysisIndex>('/data/flood-analysis.json').catch(error=>{indexRequest=undefined;throw error;});
 return indexRequest;
}
export async function floodMap():Promise<FloodMap>{
 const source=await read<FloodMap>('/data/flood-map.json');
 return {...source,tiles:source.tiles.map(url=>new URL(url,location.origin).href.replace(/%7B/gi,'{').replace(/%7D/gi,'}'))};
}
export async function floodAt(lat:number,lon:number):Promise<{collection:FeatureCollection;available:boolean}>{
 const index=await floodIndex();
 const scale=2**index.zoom;
 const x=Math.floor((lon+180)/360*scale);
 const y=Math.floor((1-Math.asinh(Math.tan(lat*Math.PI/180))/Math.PI)/2*scale);
 const key=`${x}/${y}`;
 if(!index.cells.includes(key))return {collection:{type:'FeatureCollection',features:[]},available:index.feature_count>0};
 const url=index.template.replace('{x}',String(x)).replace('{y}',String(y));
 let request=cells.get(url);
 if(!request){request=read<FeatureCollection>(url).catch(error=>{cells.delete(url);throw error;});cells.set(url,request);}
 return {collection:await request,available:index.feature_count>0};
}
