const el = id => document.getElementById(id);
const make = (tag, cls, value) => { const x=document.createElement(tag); if(cls)x.className=cls; if(value!==undefined)x.textContent=String(value); return x; };
const $results = el('results'), $error=el('error'), $button=el('score-button');
function renderResults(data) {
  $results.replaceChildren(); $results.hidden = false;
  const team = data.team;
  const summary=make('div','result-team '+(team.checked ? (team.within?'ok':'fail') : ''));
  summary.append(make('strong','', team.checked ? team.points+' / 120 points' : 'Single-deck check'),make('span','', team.checked ? (team.label+' · Transfer needed: '+team.transfer) : team.reason));
  $results.append(summary);
  for (const [index,deck] of data.decks.entries()){
    const card=make('div','result-card');
    const top=make('div','result-card-head');
    top.append(make('strong','',deck.name || 'Player '+(index+1)),make('span','points',deck.points+' pts'));
    card.append(top,make('small','',deck.count+' cards · '+deck.commandCount+' commander(s)'+(deck.complete?'':' · Incomplete list')));
    if(deck.warning) card.append(make('small','',deck.warning));
    if(deck.pointed.length){
      const details=make('details'),summary=make('summary','',deck.pointed.length+' cards with points — view breakdown');
      details.append(summary);
      for(const x of deck.pointed){
        const line=make('div','lineitem');
        line.append(make('span','',(x.count>1?x.count+'× ':'')+x.name+(x.zone==='command'?' [CZ]':'')),make('span','',x.points+' pts'));
        details.append(line);
      }
      card.append(details);
    }
    $results.append(card);
  }
}
el('score-form').addEventListener('submit',async e=>{
  e.preventDefault(); $error.hidden=true; $results.hidden=true;
  const decks=[{link:el('deck-a').value.trim(),text:el('text-a').value.trim()},{link:el('deck-b').value.trim(),text:el('text-b').value.trim()}];
  $button.disabled=true;$button.firstChild.textContent='Calculating points… ';
  try {
    const response=await fetch('/api/score',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({decks})});
    const data=await response.json();
    if(!response.ok)throw Error(data.error||'Unable to score this deck');
    renderResults(data);
  } catch(error){
    $error.textContent=error.message;$error.hidden=false;
    if(/Moxfield/.test(error.message)) el('paste-fallback').open=true;
  } finally { $button.disabled=false;$button.firstChild.textContent='Calculate points '; }
});
async function loadBracket(){
  const wrapper=el('bracket');wrapper.replaceChildren();
  try {
    const response=await fetch('/api/bracket');if(!response.ok)throw Error('Schedule unavailable');
    const data=await response.json();
    if(data.event)el('event-title').textContent=data.event;
    if(!data.rounds?.length || !data.rounds.some(x=>x.matches?.length)){
      wrapper.append(make('div','empty',data.note || 'No matchups posted yet.'));return;
    }
    for (const round of data.rounds){
      const section=make('section','round');
      section.append(make('div','round-title',round.name||'Round'));
      for(const match of round.matches||[]){
        const card=make('div','match'+(match.status==='next'?' next':''));
        const label=make('div','table');
        label.append(make('span','',match.table ? 'TABLE '+match.table : 'MATCHUP'),make('span','',match.status==='next'?'NEXT UP':(match.status||'UPCOMING').toUpperCase()));
        const teams=make('div','teams');
        teams.append(make('span','',match.teamA||'TBD'),make('span','vs','VS'),make('span','',match.teamB||'TBD'));
        card.append(label,teams);section.append(card);
      }
      wrapper.append(section);
    }
  } catch { wrapper.append(make('div','empty','Matchup information unavailable.')); }
}
loadBracket();