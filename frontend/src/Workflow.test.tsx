import {describe,it,expect,vi,afterEach} from 'vitest';
import {render,screen,fireEvent,waitFor} from '@testing-library/react';
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

