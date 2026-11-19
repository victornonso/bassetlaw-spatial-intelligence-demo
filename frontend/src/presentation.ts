import type {Dataset, Evidence} from './api';

const months=['January','February','March','April','May','June','July','August','September','October','November','December'];
export function displayDate(value:unknown):string|undefined{
 if(typeof value!=='string'||!value.trim())return undefined;
 const text=value.trim();
 const iso=/^(\d{4})-(\d{2})(?:-(\d{2}))?(?:T.*)?$/.exec(text);
 const uk=/^(\d{2})[/-](\d{2})[/-](\d{4})$/.exec(text);
 if(!iso&&!uk)return text;
 const year=iso?iso[1]:uk![3],month=Number(iso?iso[2]:uk![2]),day=iso?iso[3]:uk![1];
 if(month<1||month>12)return text;
 return `${day?`${Number(day)} `:''}${months[month-1]} ${year}`;
}
export function calculationLabel(mode?:string):string{
 if(mode==='postgis')return 'Calculated using PostgreSQL/PostGIS';
 if(mode==='browser snapshot')return 'Calculated in your browser from the published data snapshot';
 if(mode==='snapshot')return 'Calculated by the server from the published data snapshot';
 return 'Calculation method unavailable';
}
export function sourceDate(source:Dataset):string|undefined{
 if(typeof source.update_date!=='string')return undefined;
 const date=displayDate(source.update_date.split(' (')[0]);
 const kind=['wards','admin_areas'].includes(source.id)?'Boundary date':source.id==='planning_context'?'Catalogue update':'Dataset update';
 return date?`${kind}: ${date}`:undefined;
}
export const evidenceTitles:Record<string,string>={planning:'Nearby brownfield register site',flood:'River and sea flood zones',services:'Nearby schools and colleges',greenspace:'Nearby green space',growth:'Strategic development sites'};
export function evidenceText(key:string,evidence:Evidence):string{
 if(evidence.status!=='available'){
  if(evidence.unavailable_reason==='not_included')return 'Dataset not included in this prototype.';
  return 'Evidence temporarily unavailable. Please retry.';
 }
 const name=evidence.nearest?.name;
 if(key==='planning'&&name)return `Nearest site in the loaded brownfield register: ${name}.`;
 if(key==='services'&&name)return `Nearest school or college in the loaded dataset: ${name}.`;
 if(key==='flood'&&evidence.features){
  if(!evidence.features.length)return 'The selected point is outside the Flood Zone 2 and 3 polygons in this dataset. This does not establish that there is no flood risk.';
  const zones=[...new Set(evidence.features.map(f=>String(f.flood_zone||f.zone||'').replace('FZ','')).filter(Boolean))].sort();
  if(zones.length)return `The selected point falls within Environment Agency Flood ${zones.length===1?'Zone':'Zones'} ${zones.join(' and ')} in this dataset.`;
 }
 return evidence.summary;
}
