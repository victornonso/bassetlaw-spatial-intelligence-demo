import {afterEach,beforeEach,expect,it,vi} from 'vitest';
import {collectionCache,community} from './api';

const ward={type:'FeatureCollection',features:[{type:'Feature',properties:{id:'ward',name:'Example',geography_date:'2024-05'},geometry:{type:'Polygon',coordinates:[[[-1,53],[-.8,53],[-.8,53.5],[-1,53.5],[-1,53]]]}}]};
const services={type:'FeatureCollection',features:[{type:'Feature',properties:{id:'school',phase:'Primary'},geometry:{type:'Point',coordinates:[-.9,53.3]}}]};
beforeEach(()=>Object.keys(collectionCache).forEach(key=>delete collectionCache[key]));
afterEach(()=>vi.unstubAllGlobals());
function fixture(failSchools=false){vi.stubGlobal('fetch',vi.fn(async(input:string)=>{
 const url=String(input);
 if(url.includes('/api/community'))throw Error('API unavailable');
 if(url.includes('dataset_registry'))return {ok:true,json:async()=>[{id:'services',loaded:true,feature_count:1}]};
 if(url.includes('wards'))return {ok:true,json:async()=>ward};
 if(url.includes('services')){if(failSchools)throw Error('Snapshot unavailable');return {ok:true,json:async()=>services};}
 throw Error('Unexpected request');
}));}
it('uses the same education labels, phase field and dated geography in browser fallback',async()=>{
 fixture();const profile=await community('ward');
 expect(profile.area.geography_date).toBe('2024-05');
 expect(profile.indicators).toHaveLength(2);
 expect(profile.indicators[1]).toMatchObject({label:'Schools and colleges in this ward',value:1});
 expect(profile.chart.items).toEqual([{label:'Primary',value:1}]);
 expect(profile.service_status).toBe('available');
 expect(profile.method?.mode).toBe('browser snapshot');
});
it('reports failed school evidence as unavailable rather than a zero count',async()=>{
 fixture(true);const profile=await community('ward');
 expect(profile.service_status).toBe('temporarily_unavailable');
 expect(profile.indicators[1].value).toBe('Temporarily unavailable');
 expect(profile.chart.items).toEqual([]);
});
