import http from "node:http";
import worker from "./src/worker.js";

const port = Number(process.env.PORT || 3000);
const rooms = new Map();
const users = new Map();
const streams = new Map();
const recent = new Map();
const predictions = new Map();

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "Content-Type",
  "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
};

const MAX_LEVEL = 200;
const rewards = [
  { level:1, type:"stadium", id:"campo_bairro", name:"Campo do Bairro" },
  { level:5, type:"gear", id:"chuteira_cinza", name:"Chuteira Cinza" },
  { level:10, type:"stadium", id:"arquibancada_local", name:"Arquibancada Local" },
  { level:20, type:"gear", id:"camisa_promessa", name:"Camisa da Promessa" },
  { level:30, type:"stadium", id:"estadio_municipal", name:"Estádio Municipal" },
  { level:40, type:"gear", id:"chuteira_verde", name:"Chuteira Verde" },
  { level:50, type:"stadium", id:"arena_regional", name:"Arena Regional" },
  { level:65, type:"gear", id:"faixa_destaque", name:"Faixa de Destaque" },
  { level:80, type:"stadium", id:"arena_moderna", name:"Arena Moderna" },
  { level:100, type:"gear", id:"camisa_craque", name:"Camisa de Craque" },
  { level:120, type:"stadium", id:"estadio_internacional", name:"Estádio Internacional" },
  { level:150, type:"gear", id:"faixa_idolo", name:"Faixa de Ídolo" },
  { level:170, type:"stadium", id:"arena_lendaria", name:"Arena Lendária" },
  { level:190, type:"gear", id:"camisa_lendaria", name:"Camisa Lendária" },
  { level:200, type:"stadium", id:"arena_final_mundial", name:"Arena da Final Mundial" },
  { level:200, type:"gear", id:"kit_superestrela", name:"Kit Superestrela" },
];

function json(res, status, body) {
  res.writeHead(status, { "Content-Type": "application/json; charset=utf-8", ...cors });
  res.end(JSON.stringify(body));
}
function safeText(value, max = 280) {
  return String(value ?? "").replace(/[\u0000-\u001f\u007f]/g, " ").replace(/\s+/g, " ").trim().slice(0, max);
}
function levelFloor(level) { return Math.pow(Math.max(0, level - 1), 2) * 40; }
function levelCeil(level) { return Math.pow(level, 2) * 40; }
function levelFromXp(xp) { return Math.min(MAX_LEVEL, Math.max(1, Math.floor(Math.sqrt(Math.max(0, xp) / 40)) + 1)); }
function stageFor(level) {
  if (level >= 200) return { key:"superestrela", name:"Superestrela", tier:9 };
  if (level >= 151) return { key:"lendario", name:"Lendário", tier:8 };
  if (level >= 101) return { key:"idolo", name:"Ídolo", tier:7 };
  if (level >= 81) return { key:"craque", name:"Craque", tier:6 };
  if (level >= 51) return { key:"destaque", name:"Destaque", tier:5 };
  if (level >= 31) return { key:"titular", name:"Titular", tier:4 };
  if (level >= 21) return { key:"potencial", name:"Potencial", tier:3 };
  if (level >= 11) return { key:"promessa", name:"Promessa", tier:2 };
  return { key:"iniciante", name:"Iniciante", tier:1 };
}
function ensureUser(userId) {
  let u = users.get(userId);
  if (!u) {
    u = { xp:0, messages:0, coins:0, equipped:{ stadium:"campo_bairro", gear:"" } };
    users.set(userId, u);
  }
  return u;
}
function publicUser(userId) {
  const u = ensureUser(userId);
  const level = levelFromXp(u.xp);
  const floor = levelFloor(level);
  const ceil = level >= MAX_LEVEL ? floor : levelCeil(level);
  const unlocked = rewards.filter(r => level >= r.level);
  return {
    xp:u.xp,
    level,
    maxLevel:MAX_LEVEL,
    stage:stageFor(level),
    currentLevelXp:u.xp-floor,
    nextLevelXp:Math.max(0, ceil-floor),
    progress:level >= MAX_LEVEL ? 1 : Math.max(0, Math.min(1, (u.xp-floor)/Math.max(1, ceil-floor))),
    messages:u.messages,
    coins:u.coins,
    equipped:u.equipped,
    unlocked,
  };
}
function grant(userId, xp=0, coins=0) {
  const u = ensureUser(userId);
  u.xp = Math.min(levelFloor(MAX_LEVEL) + 999999, Math.max(0, u.xp + xp));
  u.coins = Math.max(0, u.coins + coins);
  users.set(userId, u);
  return publicUser(userId);
}
function pushRoom(fixtureId, message) {
  const list = rooms.get(fixtureId) || [];
  list.push(message);
  if (list.length > 150) list.splice(0, list.length - 150);
  rooms.set(fixtureId, list);
  const clients = streams.get(fixtureId);
  if (clients) {
    const payload = `event: message\ndata: ${JSON.stringify(message)}\n\n`;
    for (const res of clients) { try { res.write(payload); } catch { clients.delete(res); } }
  }
}
function parseFixture(pathname, prefix) {
  return decodeURIComponent(pathname.slice(prefix.length)).replace(/[^a-zA-Z0-9_.:-]/g, "").slice(0, 80);
}
async function readJson(req) {
  const chunks=[]; let size=0;
  for await (const chunk of req) { size+=chunk.length; if(size>16384) throw new Error("payload_too_large"); chunks.push(chunk); }
  return chunks.length ? JSON.parse(Buffer.concat(chunks).toString("utf8")) : {};
}
function outcome(h,a){ return h===a ? "draw" : h>a ? "home" : "away"; }

const server = http.createServer(async (req,res)=>{
  try {
    const host=req.headers.host||`localhost:${port}`;
    const protocol=req.headers["x-forwarded-proto"]||"http";
    const url=new URL(`${protocol}://${host}${req.url||"/"}`);
    if(req.method==="OPTIONS"){ res.writeHead(204,cors); return res.end(); }

    if(url.pathname.startsWith("/chat/messages/")){
      const fixtureId=parseFixture(url.pathname,"/chat/messages/");
      if(!fixtureId)return json(res,400,{error:"fixture_required"});
      if(req.method==="GET")return json(res,200,{fixtureId,messages:rooms.get(fixtureId)||[]});
      if(req.method==="POST"){
        const body=await readJson(req); const userId=safeText(body.userId,80); const nickname=safeText(body.nickname,24)||"Torcedor"; const text=safeText(body.text,280);
        if(!userId||text.length<2)return json(res,400,{error:"invalid_message"});
        const now=Date.now(); const key=`${fixtureId}:${userId}`; const last=recent.get(key)||{at:0,text:""};
        if(now-last.at<2500)return json(res,429,{error:"cooldown"});
        const normalized=text.toLocaleLowerCase("pt-BR"); const duplicate=normalized===last.text; recent.set(key,{at:now,text:normalized});
        const u=ensureUser(userId); u.messages+=1; let earnedXp=0;
        if(!duplicate){ earnedXp=8+(u.messages%5===0?5:0); u.xp+=earnedXp; }
        const profile=publicUser(userId);
        const message={id:`${now}-${Math.random().toString(36).slice(2,8)}`,fixtureId,userId,nickname,text,createdAt:new Date(now).toISOString(),level:profile.level,stage:profile.stage.name,xp:profile.xp};
        pushRoom(fixtureId,message); return json(res,201,{message,earnedXp,profile});
      }
    }

    if(url.pathname.startsWith("/chat/stream/")){
      const fixtureId=parseFixture(url.pathname,"/chat/stream/"); if(!fixtureId)return json(res,400,{error:"fixture_required"});
      res.writeHead(200,{"Content-Type":"text/event-stream; charset=utf-8","Cache-Control":"no-cache, no-transform",Connection:"keep-alive",...cors});
      res.write(`event: ready\ndata: ${JSON.stringify({fixtureId})}\n\n`); const set=streams.get(fixtureId)||new Set(); set.add(res); streams.set(fixtureId,set);
      const ping=setInterval(()=>{try{res.write(": ping\n\n")}catch{clearInterval(ping)}},20000);
      req.on("close",()=>{clearInterval(ping);set.delete(res);if(!set.size)streams.delete(fixtureId)}); return;
    }

    if(url.pathname.startsWith("/chat/profile/")){
      const userId=parseFixture(url.pathname,"/chat/profile/"); if(!userId)return json(res,400,{error:"user_required"});
      return json(res,200,{userId,profile:publicUser(userId),battlePass:{free:true,maxLevel:MAX_LEVEL,rewards}});
    }

    if(url.pathname.startsWith("/chat/equip/" ) && req.method==="POST"){
      const userId=parseFixture(url.pathname,"/chat/equip/"); const body=await readJson(req); const type=safeText(body.type,20); const id=safeText(body.id,80);
      const profile=publicUser(userId); const item=profile.unlocked.find(r=>r.type===type&&r.id===id); if(!item)return json(res,403,{error:"reward_locked"});
      const u=ensureUser(userId); u.equipped[type]=id; return json(res,200,{profile:publicUser(userId)});
    }

    if(url.pathname.startsWith("/predictions/") && !url.pathname.startsWith("/predictions/settle/")){
      const fixtureId=parseFixture(url.pathname,"/predictions/"); if(!fixtureId)return json(res,400,{error:"fixture_required"});
      if(req.method==="GET"){ const list=[...(predictions.get(fixtureId)||new Map()).values()].map(p=>({...p,userId:undefined})); return json(res,200,{fixtureId,predictions:list}); }
      if(req.method==="POST"){
        const body=await readJson(req); const userId=safeText(body.userId,80); const home=Number(body.home); const away=Number(body.away);
        if(!userId||!Number.isInteger(home)||!Number.isInteger(away)||home<0||away<0||home>20||away>20)return json(res,400,{error:"invalid_prediction"});
        const map=predictions.get(fixtureId)||new Map(); const old=map.get(userId); if(old?.settled)return json(res,409,{error:"prediction_already_settled"});
        map.set(userId,{userId,home,away,createdAt:new Date().toISOString(),settled:false}); predictions.set(fixtureId,map); return json(res,201,{ok:true,prediction:{home,away}});
      }
    }

    if(url.pathname.startsWith("/predictions/settle/") && req.method==="POST"){
      const fixtureId=parseFixture(url.pathname,"/predictions/settle/"); const body=await readJson(req); const home=Number(body.home); const away=Number(body.away);
      if(!Number.isInteger(home)||!Number.isInteger(away))return json(res,400,{error:"invalid_score"});
      const map=predictions.get(fixtureId)||new Map(); const settled=[];
      for(const p of map.values()){
        if(p.settled)continue; const exact=p.home===home&&p.away===away; const correct=outcome(p.home,p.away)===outcome(home,away); let xp=0,coins=0;
        if(exact){xp=120;coins=80}else if(correct){xp=60;coins=35}
        if(xp||coins)grant(p.userId,xp,coins); p.settled=true; p.reward={exact,correct,xp,coins}; settled.push({userId:p.userId,...p.reward});
      }
      return json(res,200,{fixtureId,score:{home,away},settled});
    }

    if(url.pathname.startsWith("/chat/leaderboard/")){
      const fixtureId=parseFixture(url.pathname,"/chat/leaderboard/"); const ids=new Set((rooms.get(fixtureId)||[]).map(m=>m.userId));
      const ranking=[...ids].map(userId=>({userId,...publicUser(userId)})).sort((a,b)=>b.xp-a.xp).slice(0,30); return json(res,200,{fixtureId,ranking});
    }

    const request=new Request(url.toString(),{method:req.method,headers:req.headers}); const response=await worker.fetch(request,process.env,{});
    res.statusCode=response.status; for(const [key,value] of response.headers.entries())res.setHeader(key,value); const body=await response.arrayBuffer(); res.end(Buffer.from(body));
  } catch(error){ json(res,500,{error:String(error?.message||error)}); }
});

server.listen(port,"0.0.0.0",()=>console.log(`MatchScope backend listening on port ${port}`));
