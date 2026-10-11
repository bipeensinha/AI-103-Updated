const $ = id => document.getElementById(id);
const API = "";
let inventory = [];
let activeType = "all";
const types = {
 "AKS Cluster":{icon:"⠿",css:"aks",label:"AKS Cluster"},
 "Azure SQL Database":{icon:"▤",css:"sql",label:"SQL Database"},
 "App Service":{icon:"◉",css:"app",label:"App Service"},
 "Virtual Machine":{icon:"▣",css:"vm",label:"Virtual Machine"},
 "Storage Account":{icon:"▤",css:"storage",label:"Storage Account"}
};
const stateClass = s => ({"Healthy":"healthy","Running":"running","Warning":"warning","Critical":"critical","Stopped":"stopped"}[s]||"stopped");
function esc(v){return String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
function notify(message){$("toast").textContent=message;$("toast").classList.add("show");setTimeout(()=>$("toast").classList.remove("show"),2400);}
function statusBadge(s){return `<span class="status-badge ${stateClass(s)}">${esc(s)}</span>`;}
function iconFor(r){return types[r.type]||{icon:"▦",css:"vm",label:r.type};}
function metricsLine(r){
 const d=r.details||{};
 if(r.type==="AKS Cluster"){const p=Number(d.cpu_percent||0);return `${esc(d.nodes_ready||"—")} nodes<br>CPU <b>${p}%</b> <span class="mini-bar ${p>75?"warning":""}"><i style="width:${Math.min(p,100)}%"></i></span>`;}
 if(r.type==="Azure SQL Database"){const p=Number(d.storage_used_percent||0);return `${p}% used<br>Connections ${esc(d.connections??"—")}`;}
 if(r.type==="App Service"){const p=Number(d.response_time_ms||0);return `${p.toLocaleString()} ms<br><span class="mini-bar ${p>1000?"critical":""}"><i style="width:${Math.min(p/20,100)}%"></i></span>`;}
 if(r.type==="Virtual Machine"){return `CPU ${esc(d.cpu_percent??"—")}%<br>Memory ${esc(d.memory_percent??"—")}%`;}
 return `${esc(d.capacity_used_gb??"—")} GB used<br>Public access: ${esc(d.public_access??"—")}`;
}
function renderRows(){
 const q=$("resourceSearch").value.toLowerCase().trim(), region=$("regionFilter").value;
 const filtered=inventory.filter(r=>(activeType==="all"||r.type===activeType)&&(!q||`${r.name} ${r.type} ${r.region} ${r.resource_group}`.toLowerCase().includes(q))&&(region==="all"||r.region===region));
 $("resourceRows").innerHTML=filtered.length?filtered.map(r=>{const m=iconFor(r);return `<tr data-name="${esc(r.name)}"><td><div class="resource-name-cell"><span class="row-icon ${m.css}">${m.icon}</span><span><strong>${esc(r.name)}</strong><small>${esc(r.type)}</small></span></div></td><td class="type-label">${esc(m.label)}</td><td>${statusBadge(r.status)}</td><td>${esc(r.region)}</td><td>${esc(r.resource_group)}</td><td class="metric-cell">${metricsLine(r)}</td><td><button class="row-action" data-detail="${esc(r.name)}" aria-label="Open resource details">•••</button></td></tr>`;}).join(""):`<tr><td colspan="7" style="padding:22px;color:#8190ad">No resources match your filters.</td></tr>`;
 $("resourceSummary").textContent=`Showing ${filtered.length} of ${inventory.length} resources`;
 document.querySelectorAll("#resourceRows tr[data-name]").forEach(row=>row.addEventListener("click",()=>openResource(row.dataset.name)));
 document.querySelectorAll("[data-detail]").forEach(b=>b.addEventListener("click",e=>{e.stopPropagation();openResource(b.dataset.detail);}));
}
function renderMetrics(){
 const total=inventory.length,healthy=inventory.filter(r=>["Healthy","Running"].includes(r.status)).length,warn=inventory.filter(r=>r.status==="Warning").length,crit=inventory.filter(r=>r.status==="Critical").length;
 $("metricTotal").textContent=total;$("metricHealthy").textContent=healthy;$("metricAttention").textContent=warn+crit;$("metricCritical").textContent=crit;$("navTotal").textContent=total;
 $("tabAll").textContent=total;$("tabAks").textContent=inventory.filter(r=>r.type==="AKS Cluster").length;$("tabSql").textContent=inventory.filter(r=>r.type==="Azure SQL Database").length;$("tabApp").textContent=inventory.filter(r=>r.type==="App Service").length;
 $("healthCount").textContent=healthy;$("warningCount").textContent=warn;$("criticalCount").textContent=crit;$("healthyPercent").textContent=total?Math.round(healthy/total*100)+"%":"0%";
 const hp=total?healthy/total*100:0,wp=total?warn/total*100:0,cp=total?crit/total*100:0;
 $("healthDonut").style.background=`conic-gradient(#0db486 0 ${hp}%,#ffa900 ${hp}% ${hp+wp}%,#f04456 ${hp+wp}% ${hp+wp+cp}%)`;
 $("distributionTotal").textContent=total;
 const typeColors={"AKS Cluster":"#3168ff","Azure SQL Database":"#7543ed","App Service":"#0db486","Virtual Machine":"#16a6b8","Storage Account":"#ffa900"};
 const unique=Object.keys(types);
 let cursor=0,segments=[];
 unique.forEach(t=>{const n=inventory.filter(r=>r.type===t).length;const start=cursor;cursor+=total?n/total*100:0;segments.push(`${typeColors[t]} ${start}% ${cursor}%`);});
 $("distributionDonut").style.background=`conic-gradient(${segments.join(",")})`;
 $("distributionLegend").innerHTML=unique.map(t=>{const n=inventory.filter(r=>r.type===t).length;if(!n)return "";return `<div><i style="background:${typeColors[t]}"></i><span>${esc(types[t].label==="AKS Cluster"?"AKS Clusters":types[t].label==="SQL Database"?"SQL Databases":types[t].label==="App Service"?"App Services":types[t].label==="Virtual Machine"?"Virtual Machines":"Storage Accounts")}</span><b>${n} (${Math.round(n/(total||1)*100)}%)</b></div>`;}).join("");
 $("typeHealth").innerHTML=unique.map(t=>{const subset=inventory.filter(r=>r.type===t);if(!subset.length)return "";const ok=subset.filter(r=>["Healthy","Running"].includes(r.status)).length,w=subset.filter(r=>r.status==="Warning").length,c=subset.filter(r=>r.status==="Critical").length;return `<div class="type-health-row"><span class="kind" style="color:${typeColors[t]}">${types[t].icon}</span><span>${esc(t==="AKS Cluster"?"AKS Clusters":t==="Azure SQL Database"?"SQL Databases":t==="App Service"?"App Services":t==="Virtual Machine"?"Virtual Machines":"Storage Accounts")}</span><div class="stack-bar"><i class="ok" style="width:${ok/subset.length*100}%"></i><i class="warn" style="width:${w/subset.length*100}%"></i><i class="crit" style="width:${c/subset.length*100}%"></i></div><b>${ok}/${subset.length}</b></div>`;}).join("");
}
function renderRegions(){
 const counts={};inventory.forEach(r=>counts[r.region]=(counts[r.region]||0)+1);
 const colors=["#386aff","#a045ff","#138eff","#0db486"];
 $("regionList").innerHTML=Object.entries(counts).map(([name,count],i)=>`<div><i style="background:${colors[i%colors.length]}"></i>${esc(name)}<b>${count}</b></div>`).join("");
}
function renderActivities(){
 const list=[
  {name:"aks-prod-01",desc:"Cluster scaled successfully",time:"5 mins ago",color:"#0db486"},
  {name:"sql-analytics-dev",desc:"Storage usage above 90%",time:"12 mins ago",color:"#ffa900"},
  {name:"app-inventory-api",desc:"High response time detected",time:"18 mins ago",color:"#f04456"},
  {name:"vm-test-01",desc:"CPU usage spike",time:"25 mins ago",color:"#386aff"}
 ];
 $("activityList").innerHTML=list.map(a=>`<div class="activity-row"><i class="activity-marker" style="background:${a.color}"></i><div class="activity-text"><strong>${esc(a.name)}</strong><small>${esc(a.desc)}</small></div><span class="activity-time">${esc(a.time)}</span></div>`).join("");
}
function openResource(name){
 const r=inventory.find(x=>x.name===name);if(!r)return;const m=iconFor(r);
 const detailHtml=Object.entries(r.details||{}).map(([k,v])=>`<div class="modal-field"><small>${esc(k.replaceAll("_"," "))}</small><strong>${esc(v)}</strong></div>`).join("");
 $("modalBody").innerHTML=`<div class="modal-title"><span class="row-icon ${m.css}">${m.icon}</span><div><h2>${esc(r.name)}</h2><p>${esc(r.type)} · ${esc(r.environment)}</p></div>${statusBadge(r.status)}</div><div class="modal-grid"><div class="modal-field"><small>Region</small><strong>${esc(r.region)}</strong></div><div class="modal-field"><small>Resource group</small><strong>${esc(r.resource_group)}</strong></div><div class="modal-field"><small>Subscription</small><strong>${esc(r.subscription||"Demo Subscription")}</strong></div><div class="modal-field"><small>Resource ID</small><strong>${esc(r.id)}</strong></div>${detailHtml}</div><p style="font-size:9px;color:#8796b5;margin-top:14px">Simulated inventory record · Read-only demo</p><button class="button-primary" style="margin-top:4px" id="askResource">✧ Ask AI about this resource →</button>`;
 $("resourceModal").classList.remove("hidden");$("askResource").addEventListener("click",()=>{$("resourceModal").classList.add("hidden");$("chatInput").value=`Inspect ${r.name}. Explain its status and what I should investigate.`;sendChat($("chatInput").value);});
}
function addUserMessage(text){const el=document.createElement("div");el.className="chat-row user-row";const bubble=document.createElement("div");bubble.className="user-bubble";bubble.textContent=text;el.appendChild(bubble);$("chatLog").appendChild(el);$("chatLog").scrollTop=$("chatLog").scrollHeight;}
function addAssistantMessage(text,events=[]){
 const row=document.createElement("div");row.className="chat-row bot-row";row.innerHTML='<div class="chat-spark">✦</div><div class="chat-bubble"></div>';const bubble=row.querySelector(".chat-bubble");const p=document.createElement("p");p.textContent=text;bubble.appendChild(p);
 if($("showToolCalls").checked&&events.length){events.forEach(ev=>{const d=document.createElement("details");d.className="tool-event";const s=document.createElement("summary");s.textContent=`⚙ MCP: ${ev.tool} · ${ev.success===false?"error":"completed"}`;const pre=document.createElement("pre");pre.textContent=JSON.stringify({arguments:ev.arguments,result:ev.result},null,2);d.append(s,pre);bubble.appendChild(d);});}
 else if(events.length){const summary=document.createElement("div");summary.className="tool-event";const d=document.createElement("details");const s=document.createElement("summary");s.textContent=`⚙ ${events.length} MCP tool call(s) · click to inspect`;const pre=document.createElement("pre");pre.textContent=JSON.stringify(events.map(ev=>({tool:ev.tool,arguments:ev.arguments,result:ev.result})),null,2);d.append(s,pre);summary.appendChild(d);bubble.appendChild(summary);}
 $("chatLog").appendChild(row);const time=document.createElement("div");time.className="chat-time";time.textContent=new Date().toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"});$("chatLog").appendChild(time);$("chatLog").scrollTop=$("chatLog").scrollHeight;
}
async function sendChat(raw){
 const message=(raw||"").trim();if(!message)return;
 addUserMessage(message);$("chatInput").value="";const waiting=document.createElement("div");waiting.className="chat-row bot-row";waiting.id="thinkingRow";waiting.innerHTML='<div class="chat-spark">✦</div><div class="chat-bubble">Checking the inventory and consulting MCP tools…</div>';$("chatLog").appendChild(waiting);$("chatLog").scrollTop=$("chatLog").scrollHeight;
 const send=$("chatForm").querySelector(".send-button");send.disabled=true;
 try{
  const res=await fetch(`${API}/api/chat`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message})});const data=await res.json();if(!res.ok)throw new Error(data.detail||`Request failed (${res.status})`);
  waiting.remove();addAssistantMessage(`${data.answer}\n\nDemo note: these results use simulated inventory, not live Azure resources.`,data.tool_events||[]);
 }catch(err){waiting.remove();addAssistantMessage(`I couldn't complete that request: ${err.message}\n\nCheck that the backend is running and backend/.env has the correct Foundry endpoint, key and deployment name.`);}
 finally{send.disabled=false;}
}
$("chatForm").addEventListener("submit",e=>{e.preventDefault();sendChat($("chatInput").value);});
$("chatInput").addEventListener("keydown",e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();$("chatForm").requestSubmit();}});
document.querySelectorAll("[data-prompt]").forEach(b=>b.addEventListener("click",()=>{sendChat(b.dataset.prompt);}));
document.querySelectorAll("[data-tab]").forEach(b=>b.addEventListener("click",()=>{activeType=b.dataset.tab;document.querySelectorAll("[data-tab]").forEach(x=>x.classList.toggle("active",x===b));renderRows();}));
document.querySelectorAll("[data-type]").forEach(b=>b.addEventListener("click",()=>{activeType=b.dataset.type;document.querySelectorAll("[data-tab]").forEach(x=>x.classList.toggle("active",x.dataset.tab===activeType));renderRows();$("resources").scrollIntoView({behavior:"smooth",block:"start"});}));
document.querySelectorAll("[data-section]").forEach(b=>b.addEventListener("click",()=>{document.querySelectorAll("[data-section]").forEach(x=>x.classList.toggle("active",x===b));$(b.dataset.section==="assistant"?"assistant":b.dataset.section==="resources"?"resources":"overview").scrollIntoView({behavior:"smooth",block:"start"});}));
$("resourceSearch").addEventListener("input",renderRows);$("regionFilter").addEventListener("change",renderRows);
$("globalSearch").addEventListener("keydown",e=>{if(e.key==="Enter"){const q=e.target.value.trim();if(q){if(inventory.some(r=>r.name.toLowerCase().includes(q.toLowerCase()))){const r=inventory.find(r=>r.name.toLowerCase().includes(q.toLowerCase()));openResource(r.name);}else{sendChat(q);}}}});
$("globalSearch").addEventListener("input",e=>{$("resourceSearch").value=e.target.value;renderRows();});
$("heroAsk").addEventListener("click",()=>{$("chatInput").focus();$("assistant").scrollIntoView({behavior:"smooth"});});
$("heroResources").addEventListener("click",()=>{$("resources").scrollIntoView({behavior:"smooth",block:"start"});});
$("showAll").addEventListener("click",()=>{activeType="all";$("resourceSearch").value="";$("regionFilter").value="all";document.querySelectorAll("[data-tab]").forEach(x=>x.classList.toggle("active",x.dataset.tab==="all"));renderRows();});
$("reportButton").addEventListener("click",()=>{const report={generated_at:new Date().toISOString(),simulated:true,resources:inventory};const blob=new Blob([JSON.stringify(report,null,2)],{type:"application/json"});const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download="cloudops-demo-report.json";a.click();URL.revokeObjectURL(a.href);notify("Demo resource report downloaded");});
$("settingsButton").addEventListener("click",()=>notify("Configure the Foundry endpoint and deployment in backend/.env"));
$("resourceMenu").addEventListener("click",()=>notify("Use the filters to inspect specific resources."));
$("viewActivity").addEventListener("click",()=>notify("Recent activity shown is illustrative demo data."));
$("attachButton").addEventListener("click",()=>notify("File attachments are not enabled in this demo."));
$("webButton").addEventListener("click",()=>notify("This demo uses local inventory tools only."));
$("closeResourceModal").addEventListener("click",()=>$("resourceModal").classList.add("hidden"));
$("resourceModal").addEventListener("click",e=>{if(e.target===$("resourceModal"))$("resourceModal").classList.add("hidden");});
function updateClock(){$("clock").textContent=new Date().toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"});}
async function loadInventory(){
 try{
  const [r,h]=await Promise.all([fetch("/api/resources"),fetch("/api/health")]);if(!r.ok)throw new Error("Resource API unavailable");const data=await r.json();inventory=data.resources||[];renderMetrics();renderRows();renderRegions();renderActivities();
  if(h.ok){const health=await h.json();$("connectionLabel").textContent=health.foundry_configured?"Foundry Connected":"Inventory Online · Configure Foundry";}
 }catch(e){$("connectionLabel").textContent="API Offline";$("resourceRows").innerHTML=`<tr><td colspan="7" style="padding:20px;color:#d94355">Cannot load inventory. Start FastAPI and check backend/.env.</td></tr>`;$("resourceSummary").textContent="Inventory unavailable";}
}
updateClock();loadInventory();
