
(function(){
"use strict";
const db=window.COURSE_CATALOG||[],el=document.getElementById("lesson-data"),host=document.getElementById("app");
if(!el||!host)return;
let data;try{data=JSON.parse(el.textContent);}catch(e){host.textContent="课件数据读取失败";return;}
const m=db[data.id]||{title:data.title,duration:90,unit:"嵌入式 AI"},extra=(window.COURSE_EXTRA||{})[data.id]||{};
let depth={};try{const el=document.getElementById("lesson-depth");if(el)depth=JSON.parse(el.textContent);}catch(err){console.warn("Detailed lesson data could not be read",err);}
const esc=s=>String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
const fmt=s=>esc(s).replace(/\u0060([^\u0060]+)\u0060/g,"<code>$1</code>");
const list=a=>"<ul>"+(a||[]).map(t=>"<li>"+fmt(t)+"</li>").join("")+"</ul>";
const cards=a=>'<div class="columns">'+a.map(t=>'<div class="panel">'+t+'</div>').join("")+'</div>';
const stepList=(a,start)=>'<ol class="steps-list">'+a.map((s,i)=>'<li><span class="step-no">'+(start+i+1)+'</span><span class="step-body">'+fmt(s)+'<small>观察执行结果，并记录版本、输入、日志或数据。</small></span></li>').join("")+"</ol>";
const sectionNames={OPENING:"课程导入",SCENARIO:"工程问题",GOALS:"本讲目标",KEYWORDS:"关键术语",THEORY:"原理精讲","GUIDED LAB":"教师带做","CODE READING":"源码拆解",DIAGNOSTIC:"排障方法","CASE STUDY":"应用案例",CHECK:"课堂自测",READING:"参考资料",ACCEPT:"验收清单",SOURCE:"源码与手册"};
const slides=[];
function add(cat,title,body,note){slides.push({cat,title,body,note:note||"根据实际设备和软件版本判断，不要用未经验证的结果替代课堂证据。"});}
const name=data.title||m.title,intro=data.intro||"把理论、转换与运行验证连接成可重复的学习闭环。";
add("OPENING",name,'<p class="lesson-lead">'+fmt(intro)+'</p>',"说明本讲的输入、输出和实测边界。");
add("SCENARIO","先解决什么问题？",'<p class="scenario-question">'+fmt(extra.scene||intro)+'</p>',"让学习者先说出预期结果，再执行实验。");
add("GOALS","学完应该会什么",list(data.goals),"逐项对照后面的实验与验收。");
if(extra.terms&&extra.terms.length)
 add("KEYWORDS","必要术语",'<dl class="term-grid">'+extra.terms.map(x=>'<div><dt>'+esc(x[0])+'</dt><dd>'+fmt(x[1])+'</dd></div>').join("")+'</dl>',"术语与实际代码和数据对应，不单独记忆定义。");

if(Array.isArray(depth.concepts)&&depth.concepts.length){
 depth.concepts.forEach((c,i)=>add("THEORY",String(i+1)+". "+c.title,
   '<p>'+fmt(c.explain)+'</p><p class="concept-check"><strong>要点：</strong>'+fmt(c.takeaway)+'</p>',
   "说明原理怎样决定实际数据类型、接口或者硬件选择。"));
}else add("THEORY","关键原理",'<p>'+fmt(data.core||"参考对应 Markdown 教材的原理章节。")+'</p>');
const teach=depth.guidance;
if(teach&&Array.isArray(teach.phases)){
 teach.phases.forEach((phase,i)=>{
   const command=phase.command?'<div class="code-wrap"><button type="button" class="copy-code">复制</button><pre><code>'+esc(phase.command)+'</code></pre></div>':'';
   const observe='<p class="guide-observe"><strong>预期结果：</strong>'+fmt(phase.observe)+'</p>';
   const diagnose='<p class="guide-diagnose"><strong>没通过先查：</strong>'+fmt(phase.diagnose)+'</p>';
   add("GUIDED LAB",["步骤 1｜准备条件","步骤 2｜实际执行","步骤 3｜结果验收"][i]||phase.title,
     '<p class="lab-action">'+fmt(phase.action)+'</p>'+command+observe+diagnose,
     phase.teach||"结合真实输入和输出核对，不用示例数值冒充实测。");
 });
}else add("GUIDED LAB","实验操作",stepList(data.steps,0));
// Source-code guided explanation shared with the corresponding MD theory chapter.
// No external fetch: all detailed lesson data is embedded in the individual HTML file.
if(depth.walkthrough){
 const w=depth.walkthrough;
 const path=(w.flow||[]).map(x=>'<span>'+fmt(x)+'</span>').join('<b aria-hidden="true">→</b>');
 add("CODE READING","源码数据路径",
   '<p>'+fmt(w.intro)+'</p><div class="flow-inline" aria-label="数据处理路径">'+path+'</div>'+
   '<p class="worked-example"><strong>例题：</strong>'+fmt(w.example)+'</p>',
   "跟随数据形状和类型从输入走到最终结果。");
 (w.steps||[]).forEach((step,i)=>{
   add("CODE READING",String(i+1)+". "+step.api,
      '<dl class="api-contract"><dt>输入</dt><dd>'+fmt(step.input)+'</dd><dt>输出</dt><dd>'+fmt(step.output)+'</dd></dl>'+
      '<p>'+fmt(step.why)+'</p>'+
      (step.code?'<div class="code-wrap"><button type="button" class="copy-code">复制</button><pre><code>'+esc(step.code)+'</code></pre></div>':''),
      "先识别 API、参数、返回值，再查验它和模型契约是否相符。");
 });
}
if(Array.isArray(depth.diagnosis)&&depth.diagnosis.length){
 add("DIAGNOSTIC","错误定位",
 '<div class="diagnostic-list">'+depth.diagnosis.map(x=>
 '<div class="diagnostic-row"><strong>'+fmt(x.symptom)+'</strong>'+
 '<span><b>可能原因</b>　'+fmt(x.reason)+'</span>'+
 '<span><b>检查方法</b>　'+fmt(x.check)+'</span></div>').join("")+'</div>',
 "先确认症状和错误码，再做最小修改验证原因。");
}
if(depth.case){
 const c=depth.case;
 add("CASE STUDY","案例与分析",
  '<p><strong>问题：</strong>'+fmt(c.problem)+'</p>'+
  '<p><strong>分析：</strong>'+fmt(c.analysis)+'</p>'+
  '<p><strong>验收证据：</strong>'+fmt(c.evidence)+'</p>',
  "把场景与课程实验关联，避免只给抽象答案。");
}
if(extra.quiz){
 const q=extra.quiz;
 add("CHECK","随堂自测",
 '<p class="quiz-question">'+fmt(q[0])+'</p><div class="quiz-options">'+q[1].map((x,i)=>
 '<label class="quiz-option"><input type="radio" name="quiz" value="'+i+'">'+String.fromCharCode(65+i)+'. '+fmt(x)+'</label>').join("")+
 '</div><button id="checkQuiz" type="button" class="btn quiz-submit">检查答案</button><div id="quizFeedback" class="quiz-feedback" role="status"></div>',
 "先自己作答，核对后解释为什么其他答案不正确。");
}else add("CHECK","理解检查",list(data.goals.slice(0,2)));
if(Array.isArray(depth.refs)&&depth.refs.length){
 add("READING","参考资料",
 '<ul class="reference-list">'+depth.refs.map(r=>{
  const url=/^https:\/\/[a-zA-Z0-9.-]+\//.test(r[1])?r[1]:"#";
  return '<li><a href="'+esc(url)+'" target="_blank" rel="noopener noreferrer">'+esc(r[0])+' ↗</a></li>';
 }).join("")+'</ul>',
 "遇到版本差异时优先阅读所用 SDK 版本的官方说明。");
}

add("ACCEPT","完成标准",
 '<div id="checks">'+data.checks.map((x,i)=>
 '<label class="check-item"><input data-check="'+i+'" type="checkbox">'+fmt(x)+'</label>').join("")+'</div>'+
 '<p class="help-text">勾选仅保存在本机浏览器；实机验收仍需要实际日志与模型输出。</p>',
 "每项结论要对应实际操作或能够检查的证据。");

// One concise source reference; the actual commands and runbooks are shown below.
const prev=db[data.id-1],next=db[data.id+1];
const sectionId=i=>"lesson-section-"+(i+1);
function lessonLink(x,label){return x?'<a class="btn ghost" href="'+encodeURIComponent(x.slug).replaceAll("(","%28").replaceAll(")","%29")+'.html">'+label+'</a>':"";}
// The catalog id (0-34) is the source/example index, NOT the video lesson number
// after the three part lesson 30. Always use data.id for an example path.
const sourceIndex=String(data.id).padStart(2,"0");
const notePath=data.id===27?"examples/LESSON_27.md":"examples/notes/lesson_"+sourceIndex+".md";
const manualById={6:"board-inspection",9:"onnx-toolchain",24:"mobilenet-image",25:"cpp-rknn-classify",26:"cpp-zero-copy",27:"mobilenet-image",28:"mobilenet-camera",29:"official-yolo-and-export",32:"onnx-toolchain",33:"yolov8-camera",34:"rkllm-native"};
const manual=manualById[data.id];
add("SOURCE","源码和详细实验",
 '<p class="source-links"><a href="../../examples/lesson_'+sourceIndex+'.py">课程 Python 源码 ↗</a> · '+
 '<a href="../../'+notePath+'">操作说明 ↗</a>'+
 (manual?' · <a href="../../engineering/'+manual+'.md">工程手册 ↗</a>':'')+
 '</p>',
 "实际模型和设备依赖以对应工程手册为准。");
const toc=slides.map((s,i)=>'<a class="outline-item" href="#'+sectionId(i)+'" data-section="'+i+'"><span>'+String(i+1).padStart(2,"0")+'</span>'+esc(s.title)+'</a>').join("");
const content=slides.map((s,i)=>'<section id="'+sectionId(i)+'" data-kind="'+esc(s.cat)+'" class="slide lesson-section" aria-labelledby="section-heading-'+i+'">'+
 '<h2 id="section-heading-'+i+'">'+esc(s.title)+'</h2>'+s.body+
 '<div class="teacher-note"><strong>讲师提示：</strong> '+fmt(s.note)+'</div></section>').join("");
document.body.classList.add("continuous");
host.innerHTML='<header class="player-header"><div class="header-row"><a class="brand" href="../index.html">RK<b>3588</b> / COURSE</a><div class="lesson-name">'+esc(name)+'</div><div class="actions"><button class="btn ghost" id="menuBtn" type="button" aria-expanded="false" aria-controls="slideOutline">章节目录</button><button class="btn ghost" id="noteBtn" type="button" aria-pressed="false">讲师提示</button><button class="btn ghost" id="printBtn" type="button">打印全文</button></div></div><div class="player-progress"><i id="progressBar"></i></div></header><div class="player-layout"><nav id="slideOutline" class="slide-outline" aria-label="本节课目录"><h3>本节课程目录</h3>'+toc+'<p style="padding:12px"><a href="../../docs/'+encodeURIComponent(m.slug).replaceAll("(","%28").replaceAll(")","%29")+'.md">Markdown 详细讲义 ↗</a></p></nav><main class="player-main"><article id="lessonArticle" class="lesson-article">'+content+'</article><nav class="lesson-footer-nav" aria-label="课程导航">'+lessonLink(prev,"← 上一讲")+'<a class="btn ghost" href="../index.html">全部课程</a>'+lessonLink(next,"下一讲 →")+'</nav><p class="hotkeys">使用浏览器正常滚动阅读 · 点击目录跳转 · N 显示讲师提示 · P 打印整篇 · F 全屏</p></main></div><button id="backTop" class="back-top" type="button" aria-label="返回顶部">↑ 顶部</button>';
const nav=document.getElementById("slideOutline");
const menu=document.getElementById("menuBtn");
menu.onclick=()=>{
 const open=nav.classList.toggle("open");
 menu.setAttribute("aria-expanded",open?"true":"false");
};
nav.querySelectorAll(".outline-item").forEach(link=>{
 link.onclick=()=>{
   nav.classList.remove("open");
   menu.setAttribute("aria-expanded","false");
 };
});
const noteBtn=document.getElementById("noteBtn");
noteBtn.onclick=()=>{
 const on=document.body.classList.toggle("show-notes");
 noteBtn.setAttribute("aria-pressed",on?"true":"false");
};
document.getElementById("printBtn").onclick=()=>window.print();
const back=document.getElementById("backTop");
back.onclick=()=>window.scrollTo({top:0,behavior:"smooth"});
const lessonSections=[...document.querySelectorAll(".lesson-section")];
const tocLinks=[...nav.querySelectorAll(".outline-item")];
let rafPending=false;
function updateScrollState(){
 rafPending=false;
 const root=document.documentElement;
 const scrollable=Math.max(1,root.scrollHeight-root.clientHeight);
 const progress=Math.max(0,Math.min(100,100*window.scrollY/scrollable));
 document.getElementById("progressBar").style.width=progress+"%";
 back.classList.toggle("is-visible",window.scrollY>520);
 let active=0;
 for(let i=0;i<lessonSections.length;i++){
  if(lessonSections[i].getBoundingClientRect().top<180)active=i;
  else break;
 }
 tocLinks.forEach((link,i)=>{
  const current=i===active;
  link.classList.toggle("active",current);
  if(current)link.setAttribute("aria-current","location");
  else link.removeAttribute("aria-current");
 });
}
window.addEventListener("scroll",()=>{
 if(!rafPending){rafPending=true;window.requestAnimationFrame(updateScrollState);}
},{passive:true});
window.addEventListener("resize",updateScrollState);
updateScrollState();
document.querySelectorAll(".lesson-section").forEach(section=>{
 const quizBtn=section.querySelector("#checkQuiz");
 if(quizBtn&&extra.quiz){
  const q=extra.quiz;
  quizBtn.onclick=()=>{
   const chosen=section.querySelector('input[name="quiz"]:checked');
   const feedback=section.querySelector("#quizFeedback");
   if(!chosen)feedback.textContent="请先选择一个选项。";
   else{
    const okay=Number(chosen.value)===q[2];
    feedback.innerHTML=(okay?"<strong>回答正确。</strong> ":"<strong>再想一想。</strong> 正确选项："+String.fromCharCode(65+q[2])+"。 ")+fmt(q[3]);
   }
   feedback.classList.add("visible");
  };
 }
 section.querySelectorAll(".copy-code").forEach(button=>{
  button.onclick=async()=>{
   const code=button.closest(".code-wrap").querySelector("pre");
   if(!code)return;
   try{
    if(!navigator.clipboard?.writeText)throw new Error("Clipboard unavailable");
    await navigator.clipboard.writeText(code.textContent);
    button.textContent="已复制";
   }catch(err){
    const selection=window.getSelection();
    if(selection){
     const range=document.createRange();
     range.selectNodeContents(code);
     selection.removeAllRanges();
     selection.addRange(range);
    }
    button.textContent="已选中，请按 Ctrl+C";
   }
  };
 });
 section.querySelectorAll("input[data-check]").forEach(check=>{
  const key="rk3588:"+data.id+":"+check.dataset.check;
  try{check.checked=localStorage.getItem(key)==="1";}catch(err){}
  check.onchange=()=>{
   try{localStorage.setItem(key,check.checked?"1":"0");}catch(err){}
  };
 });
});
document.addEventListener("keydown",e=>{
 const tag=document.activeElement&&document.activeElement.tagName;
 if(/^(INPUT|TEXTAREA|SELECT)$/.test(tag))return;
 if(e.altKey||e.ctrlKey||e.metaKey)return;
 if(e.key.toLowerCase()==="n"){
  const on=document.body.classList.toggle("show-notes");
  noteBtn.setAttribute("aria-pressed",on?"true":"false");
 }else if(e.key.toLowerCase()==="p"){
  e.preventDefault();window.print();
 }else if(e.key.toLowerCase()==="f"){
  if(!document.fullscreenElement)document.documentElement.requestFullscreen?.();
  else document.exitFullscreen?.();
 }
});
// No pagination or duplicated print deck: the same article is read, interacted with, and printed in full.
})();