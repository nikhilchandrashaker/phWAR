const pptxgen = require('pptxgenjs');
const dims = require('./data/figdims.json'); const R = require('./data/results.json');
const pres = new pptxgen(); pres.layout = 'LAYOUT_WIDE'; pres.title = 'phWAR: pinch-hit value, 2010–2025';
const NAVY='1F3A5F', ORG='E07A1F', INK='13202B', MUTE='586873', BG='F7F8FA', TEAL='2A9D8F';
const H='Calibri', W=13.33;
function base(title, sub){ const s=pres.addSlide(); s.background={color:BG};
  s.addText(title,{x:0.6,y:0.35,w:W-1.2,h:0.8,fontFace:H,fontSize:30,bold:true,color:NAVY,margin:0,isTextBox:true});
  if(sub) s.addText(sub,{x:0.6,y:1.1,w:W-1.2,h:0.45,fontFace:H,fontSize:16,color:MUTE,margin:0,isTextBox:true}); return s;}
function img(s,f,x,y,w,h){ const [iw,ih]=dims[f]; const r=Math.min(w/iw,h/ih); const dw=iw*r, dh=ih*r;
  s.addImage({path:'figures/'+f,x:x+(w-dw)/2,y:y+(h-dh)/2,w:dw,h:dh,altText:f.replace(/_/g,' ').replace('.png','')}); }
function bullets(s,items,x,y,w,h,fs=18){ s.addText(items.map((t,i)=>({text:t,options:{bullet:true,breakLine:i<items.length-1,paraSpaceAfter:10}})),{x,y,w,h,fontFace:H,fontSize:fs,color:INK,valign:'top',margin:0,isTextBox:true}); }
const f2=(v,d=2)=>Number(v).toFixed(d);
// 1 title
let s=pres.addSlide(); s.background={color:NAVY};
s.addText('phWAR',{x:0.8,y:2.0,w:11,h:1.3,fontFace:H,fontSize:72,bold:true,color:'FFFFFF',margin:0,isTextBox:true});
s.addText('A leverage-aware value metric for pinch hitters',{x:0.8,y:3.3,w:11,h:0.7,fontFace:H,fontSize:30,color:'FFFFFF',margin:0,isTextBox:true});
s.addText(`Built from ${R.n_pa_total.toLocaleString()} Retrosheet plate appearances, 2010–2025`,{x:0.8,y:4.3,w:11,h:0.5,fontFace:H,fontSize:18,color:'C9D6E6',margin:0,isTextBox:true});
s.addNotes('Overview: dataset, metric, and what it reveals about pinch hitting.');
// 2 method
s=base('Pinch hitting has no WAR of its own','phWAR values each appearance in runs, then in the leverage of the moment');
img(s,'fig01_pipeline.png',0.6,1.8,8.2,4.9);
bullets(s,['phWAR-N: Σ (r − replacement) / runs per win','phWAR: the same, weighted by leverage index','Replacement: −20 runs per 600 PA','Batting only: no baserunning or defense'],9.1,2.1,3.7,4,17);
s.addNotes('r is the park-adjusted linear-weight run value of each plate appearance.');
// 3 data
s=base('Real play-by-play, checked against league totals');
const stats=[[R.n_games.toLocaleString(),'games parsed'],[R.n_ph.toLocaleString(),'pinch-hit plate appearances'],[R.n_player_seasons.toLocaleString(),'player-seasons scored']];
stats.forEach((t,i)=>{ s.addText(t[0],{x:0.6+i*4.1,y:1.7,w:3.8,h:1.0,fontFace:H,fontSize:52,bold:true,color:ORG,margin:0,isTextBox:true}); s.addText(t[1],{x:0.6+i*4.1,y:2.7,w:3.8,h:0.5,fontFace:H,fontSize:18,color:MUTE,margin:0,isTextBox:true}); });
bullets(s,['Custom parser tracks base-out state, score and substitutions in every game','2023 parse: 5,868 home runs and 41,843 strikeouts, matching the official totals','Runs per team-game within about 1% of official in each season','Win-expectancy model: Brier 0.159 vs 0.250 baseline on held-out 2023–25'],0.6,3.9,12,3,19);
// 4 leverage
s=base('Pinch hitters bat when the game is on the line',`Mean leverage ${f2(R.ph_li_mean)}; ${Math.round(R.ph_late_share*100)}% of appearances come in the 7th or later`);
img(s,'fig04_leverage.png',0.6,1.8,12.1,5.0);
// 5 profile
s=base('What a pinch-hit appearance looks like');
img(s,'fig05_profile.png',0.6,1.5,12.1,4.1);
s.addText(`Pinch hitters strike out ${f2(R.ph_k_rate*100,1)}% of the time vs ${f2(R.non_k_rate*100,1)}% for everyone else, and hit homers less often (${f2(R.ph_hr_rate*100,1)}% vs ${f2(R.non_hr_rate*100,1)}%).`,{x:0.6,y:5.9,w:12.1,h:0.8,fontFace:H,fontSize:18,color:INK,margin:0,isTextBox:true});
// 6 leaders
s=base('Who has been worth the most off the bench','Career leaders are long-serving bench specialists');
img(s,'fig08_leaderboards.png',0.6,1.7,12.1,5.2);
// 7 cold
const c=R.cold;
s=base('Why pinch hitters trail: mostly relievers and the cold bench',`Paired design on ${c.n_players} hitters, runs per 100 PA`);
img(s,'fig06_cold_bench.png',0.6,1.7,7.6,5.1);
bullets(s,[`Selection: ${f2(c.selection*100)}`,`Facing relievers: ${f2(c.reliever*100)}`,`Cold off the bench: ${f2(c.cold*100)} (≈ ${Math.abs(Math.round(c.cold_per600))} runs per 600 PA)`,'Likely understated: managers pick favorable platoon matchups'],8.5,2.0,4.4,4.5,18);
// 8 noise
s=base('A single season is mostly noise',`Split-half reliability ${f2(R.reliability.ph_full)}; a 40-PA season carries ±${f2(R.noise.se_phwar_40pa)} wins of sampling error`);
img(s,'fig07_reliability.png',0.6,1.8,12.1,4.2);
s.addText('Report phWAR over several seasons, or with an interval.',{x:0.6,y:6.2,w:12.1,h:0.6,fontFace:H,fontSize:20,bold:true,color:NAVY,margin:0,isTextBox:true});
// 9 takeaways
s=base('Takeaways');
bullets(s,['Pinch hitting adds modest value in total: about +87 phWAR league-wide over 16 seasons','Managers do send better hitters into higher-leverage spots, but only modestly','The cold-bench penalty is real, around 6 runs per 600 PA, but smaller than the reliever effect','Treat single-season phWAR as an estimate, not a verdict','Dataset, code, dashboard and paper are in the project folder'],0.6,1.6,12,5,22);
pres.writeFile({fileName:'/mnt/user-data/outputs/phwar_slides.pptx'}).then(()=>console.log('deck ok'));
