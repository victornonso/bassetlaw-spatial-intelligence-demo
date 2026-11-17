import fs from 'node:fs';
import path from 'node:path';
const input=path.resolve('../data'),output=path.resolve('public/data');fs.mkdirSync(output,{recursive:true});
for(const name of fs.readdirSync(input)){if(name.endsWith('.geojson')||name==='dataset_registry.json')fs.copyFileSync(path.join(input,name),path.join(output,name));}
