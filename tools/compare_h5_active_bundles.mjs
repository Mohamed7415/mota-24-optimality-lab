/** Statically compare active compressed literals with the separately fetched source.
 * Helper declarations and function bodies are never executed. */
import fs from 'node:fs';
import path from 'node:path';
import {parse} from 'acorn';
import {literal, member, sha} from '../src/import.mjs';
const [bundleDir, structuredFile, outFile] = process.argv.slice(2);
if (!outFile) throw Error('Usage: node tools/compare_h5_active_bundles.mjs BUNDLE_DIR STRUCTURED_JSON OUT');
const reference = JSON.parse(fs.readFileSync(structuredFile));
const parsed = {};
const fingerprints = [];
const provenance = JSON.parse(fs.readFileSync(path.join(bundleDir,'provenance.json')));
for (const filename of ['project.min.js', 'floors.min.js']) {
  const bytes = fs.readFileSync(path.join(bundleDir, filename));
  const source = bytes.toString('utf8');
  const record = provenance.find(x => x.file === filename);
  if (!record || record.sha256 !== sha(bytes) || record.bytes !== bytes.length) throw Error('Bundle fingerprint mismatch');
  fingerprints.push({filename, url:record.url, finalURL:record.finalURL, sha256:sha(bytes), bytes:bytes.length});
  const ast = parse(source, {ecmaVersion:'latest'});
  const values = {};
  for (const node of ast.body) {
    if (filename === 'project.min.js' && node.type === 'FunctionDeclaration') continue;
    if (filename === 'project.min.js' && node.type === 'VariableDeclaration') {
      for (const declaration of node.declarations) {
        if (declaration.id.type !== 'Identifier') throw Error('Nonliteral binding');
        const name = declaration.id.name.split('_')[0];
        if (!['data','enemys','icons','maps','items','functions','events','plugins'].includes(name) || Object.hasOwn(values,name)) throw Error('Unexpected/duplicate binding');
        values[name] = literal(declaration.init, source);
      }
    } else if (filename === 'floors.min.js' && node.type === 'ExpressionStatement' && node.expression.type === 'AssignmentExpression' && node.expression.operator === '=') {
      const assignment = node.expression;
      const name = member(assignment.left);
      if (!/^main\.floors\.MT(?:\d+[wes]?|_1)$/.test(name)) throw Error('Unexpected floor assignment');
      const id = name.slice('main.floors.'.length);
      if (Object.hasOwn(values,id)) throw Error('Duplicate floor');
      values[id] = literal(assignment.right, source);
    } else throw Error('Unexpected top-level syntax: '+node.type);
  }
  parsed[filename] = values;
}
const differences = [];
let comparedLeaves = 0;
function compare(a,b,p) {
  if (a && typeof a === 'object' && a.$opaque) throw Error('Opaque function in literal comparison '+p);
  if (a === null || b === null || typeof a !== 'object' || typeof b !== 'object') {
    comparedLeaves++;
    if (a !== b) differences.push({path:p, sourceType:typeof a, bundleType:typeof b});
    return;
  }
  if (Array.isArray(a) !== Array.isArray(b)) {differences.push({path:p,reason:'array/object mismatch'});return;}
  for (const k of new Set([...Object.keys(a),...Object.keys(b)])) {
    if (!Object.hasOwn(a,k) || !Object.hasOwn(b,k)) differences.push({path:p+'/'+k,reason:'missing key'});
    else compare(a[k],b[k],p+'/'+k);
  }
}
for (const [name,value] of Object.entries(reference.inputs)) compare(value,parsed['project.min.js'][name],'/inputs/'+name);
compare(Object.fromEntries(Object.entries(reference.floors).map(([id,entry]) => [id,entry.data])),parsed['floors.min.js'],'/floors');
const receipt = {schemaVersion:1, scope:'Static literal comparison only; no JavaScript evaluation, no behavioral or historical leaderboard build equivalence proof', sourceSetSHA256:reference.sourceSetSHA256, bundles:fingerprints, comparedInputs:Object.keys(reference.inputs), floorCount:Object.keys(reference.floors).length, comparedLeaves, differences, equal: differences.length===0, opaqueRuntimeObjectsExcluded:['functions','plugins'], limitations:'Top-level helper declarations skipped; opaque functions/plugins and libs engine are not compared. Code strings remain inert text; exact string equality does not model effects.'};
fs.writeFileSync(outFile,JSON.stringify(receipt,null,2)+'\n');
console.log(JSON.stringify({equal:receipt.equal, comparedLeaves, differences: differences.slice(0,10), floorCount:receipt.floorCount}));
