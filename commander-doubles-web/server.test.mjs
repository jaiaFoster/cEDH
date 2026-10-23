import test from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import { handler, PRICES, normalizeName, loadPrices, deckIdFromURL, decodeMoxfield, parseExport, scoreDeck, scoreTeam } from './server.mjs';

test('v3 snapshot includes accepted distinct main and commander prices', () => {
  assert.equal(PRICES.get(normalizeName('Sol Ring')).main,15);
  assert.equal(PRICES.get(normalizeName('The Gitrog Monster')).command,6);
  assert.equal(PRICES.get(normalizeName('The Gitrog Monster')).main,1);
  assert.equal(PRICES.get(normalizeName('Acererak the Archlich')),undefined);
  assert.equal(PRICES.get(normalizeName('Aluren')).main,4);
});
test('MDFC alias and quoted CSV card-name parsing', () => {
  const lookup=loadPrices('Card,In deck (points),In command zone (points)\n"Glasspool Mimic // Glasspool Shore",1,\n"Talion, the Kindly Lord",5,8\n');
  assert.equal(lookup.get('glasspool shore').main,1);
  assert.equal(lookup.get('glasspool mimic').main,1);
  assert.equal(lookup.get('talion, the kindly lord').command,8);
});
test('only valid https moxfield IDs, no arbitrary network target', () => {
  assert.equal(deckIdFromURL('https://moxfield.com/decks/oEWXWHM5eEGMmopExLWRCA?foo=1'),'oEWXWHM5eEGMmopExLWRCA');
  assert.throws(()=>deckIdFromURL('http://moxfield.com/decks/oEWXWHM5eEGMmopExLWRCA'));
  assert.throws(()=>deckIdFromURL('https://evil.com/decks/oEWXWHM5eEGMmopExLWRCA'));
  assert.throws(()=>deckIdFromURL('https://moxfield.com@evil.com/decks/oEWXWHM5eEGMmopExLWRCA'));
});
test('decode Moxfield mainboard and commanders excluding sideboard', () => {
  const payload={name:'Example',mainboard:{x:{quantity:98,card:{name:'Island'}},y:{quantity:1,card:{name:'Sol Ring'}}},commanders:{z:{quantity:1,card:{name:'Shorikai, Genesis Engine'}}},sideboard:{unused:{quantity:1,card:{name:'Force of Will'}}}};
  const deck=decodeMoxfield(payload);
  const score=scoreDeck(deck);
  assert.equal(score.count,100);
  assert.equal(score.points,19);
  assert.equal(score.complete,true);
});
test('pasted export includes commander and skips sideboard', () => {
  const deck=parseExport('COMMANDER\n1 Shorikai, Genesis Engine\n\nMAINBOARD\n98 Plains\n1 Sol Ring (CMM) 12\n\nSIDEBOARD\n1 Force of Will\n');
  assert.equal(scoreDeck(deck).points,19);
  assert.equal(scoreDeck(deck).count,100);
  assert.throws(()=>parseExport('99 Island\n1 Sol Ring'));
});
test('one-player check and two-player team caps',()=>{
  const complete=true;
  assert.equal(scoreTeam([{points:65,complete}]).checked,false);
  assert.equal(scoreTeam([{points:72,complete},{points:48,complete}]).within,true);
  assert.equal(scoreTeam([{points:73,complete},{points:47,complete}]).within,false);
  assert.equal(scoreTeam([{points:69,complete},{points:52,complete}]).within,false);
  assert.equal(scoreTeam([{points:68,complete},{points:50,complete}]).within,true);
  assert.equal(scoreTeam([{points:60,complete:false},{points:60,complete}]).within,false);
});
test('local API serves bracket and scores export without external Moxfield calls',async()=>{
  const server=http.createServer((req,res)=>handler(req,res));
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const base='http://127.0.0.1:'+server.address().port;
  try {
    const health=await fetch(base+'/health');
    assert.equal(health.status,200);
    const bracket=await fetch(base+'/api/bracket');
    assert.equal(bracket.status,200);
    assert.ok(Array.isArray((await bracket.json()).rounds));
    const score=await fetch(base+'/api/score',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({decks:[{text:'COMMANDER\n1 Shorikai, Genesis Engine\nMAINBOARD\n98 Island\n1 Sol Ring'}]})});
    assert.equal(score.status,200);
    const body=await score.json();
    assert.equal(body.decks[0].points,19);
    assert.equal(body.decks[0].complete,true);
    assert.equal(body.team.checked,false);
  } finally { await new Promise(resolve=>server.close(resolve)); }
});