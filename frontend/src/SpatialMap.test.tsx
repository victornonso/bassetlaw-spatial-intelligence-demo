import {render,waitFor} from '@testing-library/react';
import {afterEach,expect,it,vi} from 'vitest';
const mocks=vi.hoisted(()=>({sources:new Map<string,unknown>(),layers:new Map<string,unknown>(),features:vi.fn()}));
vi.mock('./api',()=>({features:mocks.features,featureId:()=>''}));
vi.mock('./flood',()=>({floodMap:async()=>({tiles:['https://example.test/{z}/{x}/{y}.pbf'],minzoom:8,maxzoom:14,bounds:[-1.3,53.1,-.6,53.6],attribution:'Environment Agency'})}));
vi.mock('maplibre-gl',()=>({default:{
 Map:class{
  addControl(){} on(event:string,callback:()=>void){if(event==='load')queueMicrotask(callback);}
  getSource(id:string){return mocks.sources.get(id);} addSource(id:string,source:unknown){mocks.sources.set(id,source);}
  getLayer(id:string){return mocks.layers.get(id);} addLayer(layer:{id:string}){mocks.layers.set(layer.id,layer);}
  setLayoutProperty(){} remove(){}
 },NavigationControl:class{}
}}));
import {SpatialMap} from './SpatialMap';
afterEach(()=>{mocks.sources.clear();mocks.layers.clear();vi.clearAllMocks();});
it('loads flood as vector tiles without fetching analytical GeoJSON or drawing internal polygon outlines',async()=>{
 render(<SpatialMap layers={[{id:'flood_zones',name:'Flood zones',available:true,feature_count:2409}]} enabled={new Set(['flood_zones'])} onToggle={()=>{}} onSelect={()=>{}}/>);
 await waitFor(()=>expect(mocks.sources.get('flood_zones')).toMatchObject({type:'vector',maxzoom:14}));
 expect(mocks.features).not.toHaveBeenCalled();
 expect(mocks.layers.get('flood_zones-fill')).toMatchObject({'source-layer':'flood_zones'});
 expect(mocks.layers.has('flood_zones-line')).toBe(false);
});
