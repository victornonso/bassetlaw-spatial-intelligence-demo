import {describe,it,expect,vi,afterEach} from 'vitest';
import {render,screen,fireEvent,waitFor,act} from '@testing-library/react';
import {App} from './main';
vi.mock('./SpatialMap',()=>({SpatialMap:({onSelect,onToggle,enabled}:{onSelect:(lat:number,lon:number)=>void;onToggle:(id:string)=>void;enabled:Set<string>})=><div aria-label="Map component"><button onClick={()=>onSelect(53.3044,-1.1249)}>Inspect point</button><button aria-pressed={enabled.has('wards')} onClick={()=>onToggle('wards')}>Ward layer</button></div>}));
const result={location:{lat:53.3044,lon:-1.1249},area:{district:'Bassetlaw',ward:'Worksop'},evidence:{flood:{status:'unavailable',summary:'No data loaded for this indicator.'}},sources:[],method:{mode:'snapshot',distance:'Straight-line'}};
afterEach(()=>{vi.unstubAllGlobals();location.hash='';});
function fetchFixture(){vi.stubGlobal('fetch',vi.fn(async(input:string)=>{const u=String(input);const data=u.includes('/api/layers')?{layers:[{id:'wards',name:'Ward boundaries',available:true,feature_count:1}],mode:'snapshot'}:u.includes('/api/features/')?{type:'FeatureCollection',features:[]}:u.includes('/api/site-insight')?result:u.includes('dataset_registry')?[]:{};return {ok:true,json:async()=>data};}));}
describe('Application workflow',()=>{
 it('renders independent prototype and main navigation',async()=>{fetchFixture();render(<App/>);expect(screen.getAllByText(/Independent interview prototype by Victor Okeke/).length).toBeGreaterThan(0);expect(screen.getByRole('navigation')).toBeInTheDocument();await waitFor(()=>expect(screen.getByRole('button',{name:'Inspect point'})).toBeInTheDocument());});
 it('passes real selected point evidence into the insight record',async()=>{fetchFixture();render(<App/>);fireEvent.click(screen.getByRole('button',{name:'Planning & Growth'}));await waitFor(()=>expect(screen.getByRole('button',{name:'Inspect point'})).toBeInTheDocument());fireEvent.click(screen.getByRole('button',{name:'Inspect point'}));await waitFor(()=>expect(screen.getByText('Worksop')).toBeInTheDocument());expect(screen.getByText('Analysis mode: snapshot')).toBeInTheDocument();});
 it('updates layer visibility state at the map boundary',async()=>{fetchFixture();render(<App/>);fireEvent.click(screen.getByRole('button',{name:'Planning & Growth'}));const toggle=await screen.findByRole('button',{name:'Ward layer'});expect(toggle).toHaveAttribute('aria-pressed','true');fireEvent.click(toggle);expect(toggle).toHaveAttribute('aria-pressed','false');});
});


describe('Concurrent location requests',()=>{
 it('keeps the latest selected location when an older response arrives late',async()=>{
  fetchFixture();const baseFetch=globalThis.fetch;const pending:Array<(value:Response)=>void>=[];
  vi.stubGlobal('fetch',vi.fn((input:RequestInfo|URL,init?:RequestInit)=>String(input).includes('/api/site-insight')?new Promise<Response>(resolve=>pending.push(resolve)):baseFetch(input,init)));
  render(<App/>);fireEvent.click(screen.getByRole('button',{name:'Planning & Growth'}));
  const places=screen.getByRole('combobox',{name:'Start with a place'});
  fireEvent.change(places,{target:{value:'Worksop town centre'}});
  fireEvent.change(places,{target:{value:'Retford town centre'}});
  await waitFor(()=>expect(pending).toHaveLength(2));
  await act(async()=>{pending[1]({ok:true,json:async()=>({...result,area:{district:'Bassetlaw',ward:'Latest selection'}})} as Response);});
  expect(await screen.findByText('Latest selection')).toBeInTheDocument();
  await act(async()=>{pending[0]({ok:true,json:async()=>({...result,area:{district:'Bassetlaw',ward:'Stale selection'}})} as Response);});
  expect(screen.queryByText('Stale selection')).toBeNull();expect(screen.getByText('Latest selection')).toBeInTheDocument();
 });
});
