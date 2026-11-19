import {afterEach,beforeEach,describe,expect,it,vi} from 'vitest';
import {snapshotInsight} from './api';

const empty={type:'FeatureCollection',features:[]};
const tiny={type:'FeatureCollection',features:[{type:'Feature',properties:{id:'tiny',name:'Flood Zone 2'},geometry:{type:'Polygon',coordinates:[[[-.9,53.3],[-.899999,53.3],[-.899999,53.300001],[-.9,53.300001],[-.9,53.3]]]}}]};
function cell(lat:number,lon:number){const n=2**13;return `${Math.floor((lon+180)/360*n)}/${Math.floor((1-Math.asinh(Math.tan(lat*Math.PI/180))/Math.PI)/2*n)}`;}
beforeEach(()=>vi.resetModules());
afterEach(()=>vi.unstubAllGlobals());
describe('Detailed flood snapshot',()=>{
 it('retains vector tile coordinate placeholders when resolving the source URL',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,json:async()=>({tiles:['/data/flood-map/rev/{z}/{x}/{y}.pbf']})})));
  const {floodMap}=await import('./flood');
  expect((await floodMap()).tiles[0]).toBe(`${location.origin}/data/flood-map/rev/{z}/{x}/{y}.pbf`);
 });
 it('requests only the selected analytical cell, retains tiny features and reuses it',async()=>{
  const key=cell(53.3000005,-.8999995);
  const fetcher=vi.fn(async(url:string)=>({ok:true,json:async()=>url.endsWith('.json')?{zoom:13,cells:[key],feature_count:1,template:'/data/flood-analysis/rev/{x}/{y}.geojson'}:tiny}));
  vi.stubGlobal('fetch',fetcher);
  const {floodAt}=await import('./flood');
  const first=await floodAt(53.3000005,-.8999995);
  expect(first.available).toBe(true);expect(first.collection).toEqual(tiny);
  await floodAt(53.3000005,-.8999995);
  expect(fetcher.mock.calls.map(c=>c[0])).toEqual(['/data/flood-analysis.json',`/data/flood-analysis/rev/${key}.geojson`]);
 });
 it('distinguishes a loaded empty cell from unavailable data',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,json:async()=>({zoom:13,cells:[],feature_count:2409,template:'/unused'})})));
  const {floodAt}=await import('./flood');
  expect(await floodAt(53.3,-.9)).toEqual({available:true,collection:empty});
 });
 it('does not silently treat a failed cell download as absence of flooding',async()=>{
  const key=cell(53.3,-.9);
  vi.stubGlobal('fetch',vi.fn(async(url:string)=>({ok:url.endsWith('.json'),json:async()=>({zoom:13,cells:[key],feature_count:1,template:'/cell/{x}/{y}.geojson'})})));
  const {floodAt}=await import('./flood');
  await expect(floodAt(53.3,-.9)).rejects.toThrow('Flood snapshot unavailable');
 });
 it('uses detailed cells for fallback classification and never requests the whole flood layer',async()=>{
  const key=cell(53.3000005,-.8999995);
  const fetcher=vi.fn(async(url:string)=>({ok:true,json:async()=>url==='/data/flood-analysis.json'?{zoom:13,cells:[key],feature_count:1,template:'/cell/{x}/{y}.geojson'}:url.startsWith('/cell/')?tiny:url.includes('dataset_registry')?[]:empty}));
  vi.stubGlobal('fetch',fetcher);
  const result=await snapshotInsight(53.3000005,-.8999995);
  expect(result.evidence.flood.status).toBe('available');
  expect(result.evidence.flood.summary).toContain('Flood Zone 2');
  expect(fetcher.mock.calls.some(c=>c[0].includes('flood_zones'))).toBe(false);
 });
});
