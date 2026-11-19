import fs from 'node:fs';
import path from 'node:path';
const input=path.resolve('../data'),output=path.resolve('public/data');fs.mkdirSync(output,{recursive:true});
// Detailed flood GeoJSON belongs to the backend. The browser receives vector
// display tiles and requests one unsimplified analysis cell only when needed.
fs.rmSync(path.join(output,'flood_zones.geojson'),{force:true});
for(const name of fs.readdirSync(input)){
 if(name.endsWith('.geojson')||['dataset_registry.json','flood-map.json','flood-analysis.json'].includes(name))fs.copyFileSync(path.join(input,name),path.join(output,name));
 if(['flood-map','flood-analysis'].includes(name))fs.cpSync(path.join(input,name),path.join(output,name),{recursive:true});
}
