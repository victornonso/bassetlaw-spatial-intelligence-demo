import React from 'react';
import type {Community,Dataset,Insight} from './api';
import {calculationLabel,displayDate,evidenceText,evidenceTitles,sourceDate} from './presentation';

const sourceUrl=(source:Dataset)=>String(source.source_url||source.official_url||source.url||'');
export function SourceLinks({sources}:{sources:Dataset[]}){
 return <ul className="source-links">{sources.filter(s=>sourceUrl(s).startsWith('https://')).map((source,index)=>
  <li key={`${source.id}-${index}`}><a href={sourceUrl(source)} target="_blank" rel="noreferrer">{source.name||source.provider||source.id}</a>
   {sourceDate(source)&&<small>{sourceDate(source)}</small>}
   {displayDate(source.retrieved_at||source.retrieved)&&<small>Downloaded: {displayDate(source.retrieved_at||source.retrieved)}</small>}
  </li>)}</ul>;
}
export function LocationInsight({insight,loading,error}:{insight:Insight|null;loading:boolean;error:string}){
 const wardDate=insight&&(displayDate(insight.area.ward_date)||displayDate(insight.sources.find(s=>s.id==='wards')?.update_date));
 return <aside className="insight" aria-labelledby="insight-title" aria-live="polite">
  <div className="panel-head"><span className="eyebrow">Evidence record</span><h2 id="insight-title">Location Insight</h2></div>
  {loading?<p role="status">Checking evidence for the selected location…</p>:error?<p className="error" role="alert">Location evidence is temporarily unavailable. {error}</p>:!insight?
   <div className="empty-insight"><h3>A location is the starting point</h3><p>Click the map or choose a named place to see the available evidence.</p><ol><li>Select a location</li><li>Review the evidence</li><li>Follow the sources</li></ol><p className="muted">The application supports professional judgement. It does not make planning recommendations.</p></div>:
   <><section><h3>Selected location</h3><p className="coordinates">{Math.abs(insight.location.lat).toFixed(5)}° {insight.location.lat<0?'S':'N'}, {Math.abs(insight.location.lon).toFixed(5)}° {insight.location.lon<0?'W':'E'}</p>
    <dl className="location-details"><dt>District</dt><dd>{insight.area.district||'Outside the included district boundary'}</dd><dt>Ward{wardDate&&` — ${wardDate} boundaries`}</dt><dd><strong>{insight.area.ward||'Ward could not be identified'}</strong></dd></dl></section>
    <section><h3>Evidence to consider</h3><p className="muted">Evidence from the available public datasets. Missing data does not establish the absence of a risk or constraint.</p></section>
    {['planning','flood','services','greenspace','growth'].map(key=>{
     const evidence=insight.evidence[key];
     if(!evidence||(['greenspace','growth'].includes(key)&&evidence.status!=='available'&&evidence.unavailable_reason!=='temporarily_unavailable'))return null;
     const recordDate=displayDate(evidence.nearest?.record_updated);
     return <section key={key}><h3>{evidenceTitles[key]}</h3><p className={evidence.status==='available'?'':'muted'}>{evidenceText(key,evidence)}</p>
      {evidence.status==='available'&&<>
       {evidence.distance_m!=null&&<p><strong>Approximately {Math.round(evidence.distance_m).toLocaleString()} m</strong> straight-line distance</p>}
       {key==='planning'&&<><p className="muted">Distance is to the register’s mapped point, not the site boundary. Current planning permission and availability have not been verified.</p>{recordDate&&<p className="muted">Register record updated: {recordDate}</p>}</>}
       {key==='services'&&<>{evidence.count_within_2km!=null&&<p>{evidence.count_within_2km} schools and colleges in the loaded dataset within 2 km.</p>}<p className="muted">Distances are to published establishment locations. Only establishments in the Bassetlaw extract are included. Admissions eligibility, available places and travel routes are not assessed.</p>{recordDate&&<p className="muted">Establishment record updated: {recordDate}</p>}</>}
       {key==='flood'&&<p className="muted">This is river and sea planning flood-zone evidence. Other sources of flooding are not assessed here.</p>}
      </>}
     </section>;
    })}
    <section><h3>How this was calculated</h3><p>Distances are measured in a straight line, not along walking or driving routes.</p><p className="status-line">{calculationLabel(insight.method.mode)}</p></section>
    <section><h3>Data sources</h3><SourceLinks sources={insight.sources}/></section>
   </>}
 </aside>;
}

export function CommunityProfile({profile,error}:{profile:Community|null;error:string}){
 const date=displayDate(profile?.area.geography_date)||displayDate(profile?.sources.find(s=>s.id==='wards')?.update_date);
 return <aside className="insight" aria-labelledby="community-title"><span className="eyebrow">Schools and colleges by ward</span><h2 id="community-title">{profile?.area.name||'Ward education profile'}</h2>
  {error?<p role="alert">{error}</p>:!profile?<p role="status">Loading ward education profile…</p>:<>
   {date&&<p className="muted">Ward boundaries: {date}</p>}
   <table className="statistics"><caption className="sr-only">Ward area and included educational establishments</caption><tbody>{profile.indicators.map((indicator,index)=><tr key={index}><th scope="row">{indicator.label}<small>{indicator.description}</small></th><td>{typeof indicator.value==='number'?indicator.value.toLocaleString():indicator.value} {indicator.unit}</td></tr>)}</tbody></table>
   <section><h3>{profile.chart.title}</h3>{profile.service_status==='temporarily_unavailable'?<p role="status">School and college evidence is temporarily unavailable. Please retry.</p>:profile.service_status==='not_included'?<p>School and college data is not included in this prototype.</p>:profile.chart.items.length?<><div className="bars">{profile.chart.items.map((item,index)=><div key={index}><span>{item.label}</span><b>{item.value}</b><div className="bar" style={{width:`${Math.max(1,item.value/Math.max(...profile.chart.items.map(x=>x.value))*100)}%`}}/></div>)}</div>{profile.chart.items.some(x=>x.label==='Not applicable')&&<p className="muted">“Not applicable” is the education-phase classification in the source; it does not mean that an establishment is closed.</p>}</>:<p>No schools or colleges in the loaded dataset fall within this ward boundary.</p>}</section>
   <section><h3>How to read this profile</h3><p>This shows the distribution of included schools and colleges. It does not measure demand, available places, quality or travel accessibility.</p>{profile.limitations.map((limit,index)=><p key={index} className="muted">{limit}</p>)}<p className="status-line">{calculationLabel(profile.method?.mode)}</p></section>
   <section><h3>Data sources</h3><SourceLinks sources={profile.sources}/></section>
  </>}
 </aside>;
}
