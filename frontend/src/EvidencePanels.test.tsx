import {render,screen,within} from '@testing-library/react';
import {describe,expect,it} from 'vitest';
import {CommunityProfile,LocationInsight} from './EvidencePanels';
import type {Community,Insight} from './api';

const insight:Insight={location:{lat:53.3,lon:-1},area:{district:'Bassetlaw',ward:'Example',ward_date:'2024-05'},evidence:{
 planning:{status:'available',summary:'Old generic context wording with 128 m',distance_m:128,nearest:{name:'Example register site',record_updated:'25/03/2020'}},
 services:{status:'available',summary:'Old generic feature wording with 415 m',distance_m:415,nearest:{name:'Example College',record_updated:'13-11-2026'},count_within_2km:10},
 flood:{status:'available',summary:'Old intersection wording',features:[{flood_zone:'FZ2'}]},
 greenspace:{status:'unavailable',summary:'Dataset not included',unavailable_reason:'not_included'},
 growth:{status:'unavailable',summary:'Dataset not included',unavailable_reason:'not_included'}},sources:[{id:'wards',name:'Ward boundaries',source_url:'https://example.test/wards',update_date:'2024-05',retrieved_at:'2026-11-17T10:03:58Z'}],method:{mode:'postgis',distance:'EPSG:27700'}};
const profile:Community={area:{id:'example',name:'Example ward',geography_date:'2024-05'},indicators:[{label:'Ward area',value:5,unit:'km²'},{label:'Schools and colleges in this ward',value:2,unit:'establishments'}],chart:{title:'Schools and colleges by education phase',items:[{label:'Not applicable',value:1},{label:'Primary',value:1}]},sources:[],limitations:[],service_status:'available',method:{mode:'postgis'}};

describe('Plain-language location evidence',()=>{
 it('names the actual datasets, shows record and boundary dates, and displays each distance once',()=>{
  render(<LocationInsight insight={insight} loading={false} error=""/>);
  expect(screen.getByRole('heading',{name:'Nearby brownfield register site'})).toBeInTheDocument();
  expect(screen.getByRole('heading',{name:'Nearby schools and colleges'})).toBeInTheDocument();
  expect(screen.getByText(/Ward — May 2024 boundaries/)).toBeInTheDocument();
  expect(screen.getByText('Register record updated: 25 March 2020')).toBeInTheDocument();
  expect(screen.getByText('Downloaded: 17 November 2026')).toBeInTheDocument();
  const text=screen.getByRole('complementary').textContent||'';
  expect(text.match(/128 m/g)).toHaveLength(1);expect(text.match(/415 m/g)).toHaveLength(1);
  expect(text).toContain('10 schools and colleges in the loaded dataset within 2 km');
  expect(text).toContain('not the site boundary');
  expect(text).not.toContain('Old generic');
  expect(screen.queryByRole('heading',{name:'Nearby green space'})).toBeNull();
  expect(screen.queryByRole('heading',{name:'Strategic development sites'})).toBeNull();
 });
 it('keeps failed evidence visible and distinct from a dataset excluded from the prototype',()=>{
  render(<LocationInsight insight={{...insight,evidence:{...insight.evidence,flood:{status:'unavailable',summary:'',unavailable_reason:'temporarily_unavailable'},planning:{status:'unavailable',summary:'',unavailable_reason:'not_included'}}}} loading={false} error=""/>);
  expect(screen.getByText('Evidence temporarily unavailable. Please retry.')).toBeInTheDocument();
  expect(screen.getByText('Dataset not included in this prototype.')).toBeInTheDocument();
 });
 it('does not call an outside-flood-zone result no risk or imply that browser calculation is a live database connection',()=>{
  render(<LocationInsight insight={{...insight,evidence:{flood:{status:'available',summary:'',features:[]}},method:{mode:'browser snapshot',distance:'geodesic'}}} loading={false} error=""/>);
  expect(screen.getByText(/does not establish that there is no flood risk/)).toBeInTheDocument();
  expect(screen.getByText('Calculated in your browser from the published data snapshot')).toBeInTheDocument();
  expect(screen.queryByText('Calculated using PostgreSQL/PostGIS')).toBeNull();
 });
});
describe('Ward education profile',()=>{
 it('explains phase classification and dated geography without implying a full community or accessibility profile',()=>{
  render(<CommunityProfile profile={profile} error=""/>);
  expect(screen.getByText('Ward boundaries: May 2024')).toBeInTheDocument();
  expect(screen.getByText(/education-phase classification in the source/)).toBeInTheDocument();
  expect(screen.getByText(/does not measure demand, available places, quality or travel accessibility/)).toBeInTheDocument();
  expect(screen.queryByText(/reference point/)).toBeNull();
 });
 it('distinguishes zero included schools from a failed school-data request',()=>{
  render(<CommunityProfile profile={{...profile,service_status:'temporarily_unavailable',indicators:[{label:'Schools and colleges in this ward',value:'Temporarily unavailable'}],chart:{...profile.chart,items:[]}}} error=""/>);
  expect(screen.getByRole('status')).toHaveTextContent('School and college evidence is temporarily unavailable');
  expect(within(screen.getByRole('table')).queryByText('0')).toBeNull();
  expect(screen.queryByText(/No schools or colleges/)).toBeNull();
 });
 it('describes a genuine empty ward subset without claiming that services do not exist',()=>{
  render(<CommunityProfile profile={{...profile,chart:{...profile.chart,items:[]}}} error=""/>);
  expect(screen.getByText('No schools or colleges in the loaded dataset fall within this ward boundary.')).toBeInTheDocument();
 });
});
