
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
add("OPENING","本讲课程介绍",'<div class="eyebrow">'+esc(m.unit)+'</div><h1>'+esc(name)+'</h1><p class="big">'+fmt(intro)+'</p><p class="footnote">上下滚动阅读 · N 切换讲师提示 · P 打印</p>',"问学生：本节课最想解决的一个实际工程问题是什么？");
add("SCENARIO","工程问题",'<div class="panel good"><h3>'+fmt(extra.scene||intro)+'</h3></div>',"先让学习者说出输入、预期结果和失败现象。");
add("GOALS","学习目标与验收方向",'<div class="panel">'+list(data.goals)+'</div><p class="footnote">每个目标对应可被检查的解释、操作、图示或运行证据。</p>',"把目标转为三个问题：知道什么、能够做什么、如何验证。");
if(extra.terms&&extra.terms.length)add("KEYWORDS","术语与接口",'<div class="three-cols">'+extra.terms.map(x=>'<div class="panel"><div class="eyebrow">KEY TERM</div><h3>'+esc(x[0])+'</h3><p>'+fmt(x[1])+'</p></div>').join("")+'</div>',"逐一说明术语对应哪个软件层、数据或硬件资源。");

if(Array.isArray(depth.concepts)&&depth.concepts.length){
 depth.concepts.forEach((c,i)=>{
  add("THEORY","讲透原理 "+(i+1)+" · "+c.title,
    '<div class="panel"><h3>'+fmt(c.title)+'</h3><p>'+fmt(c.explain)+'</p></div>'+
    '<div class="panel soft"><strong>检查理解</strong><p>'+fmt(c.takeaway)+'</p></div>',
    "请学生画出输入与输出关系，再用真实张量或一个数值例子验证。");
 });
}else{
 add("THEORY","原理与工程约束",'<div class="panel"><p>'+fmt(data.core||"请阅读对应 Markdown 讲义。")+'</p></div>');
}
const teach=depth.guidance;
if(teach&&Array.isArray(teach.phases)){
 teach.phases.forEach((phase,i)=>{
  const command=phase.command?'<div class="code-wrap"><button type="button" class="copy-code">复制命令</button><pre><code>'+esc(phase.command)+'</code></pre></div>':'';
  add("GUIDED LAB",["准备：明确实验条件","演示：运行真实程序","验收：解释实际结果"][i]||phase.title,
    '<div class="panel good"><h3>'+fmt(phase.title)+'</h3><p>'+fmt(phase.action)+'</p></div>'+command+
    '<div class="panel"><strong>观察与判断</strong><p>'+fmt(phase.observe)+'</p></div>'+
    '<div class="panel soft"><strong>未达到时排查</strong><p>'+fmt(phase.diagnose)+'</p></div>',
    phase.teach||"让学生展示输出并解释原因后进入下一步。");
 });
}else{
 add("GUIDED LAB","本节动手实践",stepList(data.steps,0));
}
// Source-code guided explanation shared with the corresponding MD theory chapter.
// No external fetch: all detailed lesson data is embedded in the individual HTML file.
if(depth.walkthrough){
 const w=depth.walkthrough;
 const path=(w.flow||[]).map((part,i)=>(i?'<span class="arrow">→</span>':'')+
   '<div class="flow-box"><span>'+fmt(part)+'</span></div>').join('');
 add("CODE READING","源码精读 · 输入如何到达输出",
   '<div class="panel good"><p>'+fmt(w.intro)+'</p></div>'+
   '<div class="flow">'+path+'</div>'+
   '<div class="panel soft"><h3>本讲需要理解的张量/协议</h3><p>'+fmt(w.example)+'</p></div>',
   "沿输入→关键 API→输出读源码，先看张量的 dtype/shape，再讨论是否得到真实模型结果。");
 (w.steps||[]).forEach((step,i)=>{
   add("CODE READING","关键函数 "+(i+1)+" · "+step.api,
      '<div class="panel"><h3>'+fmt(step.api)+'</h3>'+
      '<p><strong>输入：</strong>'+fmt(step.input)+'</p>'+
      '<p><strong>输出：</strong>'+fmt(step.output)+'</p>'+
      '<p>'+fmt(step.why)+'</p></div>'+
      (step.code?'<div class="code-wrap"><button type="button" class="copy-code">复制片段</button><pre><code>'+esc(step.code)+'</code></pre></div>':''),
      "把代码中的变量对应到模型输入、API 的返回值、缓冲区或坐标单位；片段用于理解，完整运行入口见工程手册。");
 });
 
}

if(Array.isArray(depth.diagnosis)&&depth.diagnosis.length){
 add("DIAGNOSTIC","具体报错与定位路径",
 '<div class="three-cols">'+depth.diagnosis.map((x,i)=>'<div class="panel warn"><span class="eyebrow">ISSUE 0'+(i+1)+'</span><h3>'+fmt(x.symptom)+'</h3><p><strong>可能原因：</strong>'+fmt(x.reason)+'</p><p><strong>如何查证：</strong>'+fmt(x.check)+'</p></div>').join("")+'</div>',
 "帮助学生区分现象、假设和验证动作；从最小改动开始排查。");
}
if(depth.case){
 const c=depth.case;
 add("CASE STUDY","情境分析 · 从症状到证据",
  '<div class="panel"><h3>情境题</h3><p class="big">'+fmt(c.problem)+'</p></div>'+cards(['<h3>建议推理过程</h3><p>'+fmt(c.analysis)+'</p>','<h3>需提交的证据</h3><p>'+fmt(c.evidence)+'</p>']),
  "先隐藏讲解答案让学生讨论，再用诊断链逐步收束。");
}

if(extra.quiz){
const q=extra.quiz;
add("CHECK","课堂互动测验",'<div class="panel"><h3>'+fmt(q[0])+'</h3><div class="quiz-options">'+q[1].map((x,i)=>'<label class="quiz-option"><input type="radio" name="quiz" value="'+i+'">'+String.fromCharCode(65+i)+'. '+fmt(x)+'</label>').join("")+'</div><button id="checkQuiz" type="button" class="btn">提交并解释</button><div id="quizFeedback" class="quiz-feedback" role="status"></div></div>',"先让学生独立作答，再请一位同学解释原因。");
}else add("CHECK","课堂讨论",'<div class="panel"><h3>从下面的目标中选一项，用自己的话解释其工作原理和验证方式。</h3>'+list(data.goals.slice(0,2))+'</div>',"讨论的目标是解释因果，而非复述术语。");

if(Array.isArray(depth.refs)&&depth.refs.length){
add("READING","学习资料与权威参考",
'<div class="panel"><h3>按照主题选择阅读资料</h3><ul>'+depth.refs.map(r=>{
const safeUrl=/^https:\/\/[a-zA-Z0-9.-]+\//.test(r[1])?r[1]:"#";
return '<li><a href="'+esc(safeUrl)+'" target="_blank" rel="noopener noreferrer">'+esc(r[0])+' ↗</a></li>';
}).join("")+'</ul><p>先以 RKNN 官方 SDK 与示例确定版本兼容性，再读理论书籍理解算子、张量与优化原理。外部网页需联网。</p></div>',
"请学生辨别：官方工具与版本契约、模型框架文档、原理教材分别解决不同问题。");
}

add("ACCEPT","本节验收标准",'<p>以下勾选仅用于辅助复习，实际完成请提供可观察的证据。</p><div id="checks">'+data.checks.map((s,i)=>'<label class="check-item"><input data-check="'+i+'" type="checkbox">'+fmt(s)+'</label>').join("")+'</div><p class="footnote">学习进度仅存储在当前浏览器本地；不会上传到服务器。</p>',"未达标的部分对应哪一张幻灯片？请学生指出具体位置。");

// One concise source reference; the actual commands and runbooks are shown below.
const codeFile="lesson_"+String(data.id).padStart(2,"0")+".py";
const prev=db[data.id-1],next=db[data.id+1];
const sectionId=i=>"lesson-section-"+(i+1);
function lessonLink(x,label){return x?'<a class="btn ghost" href="'+encodeURIComponent(x.slug).replaceAll("(","%28").replaceAll(")","%29")+'.html">'+label+'</a>':"";}
// The catalog id (0-34) is the source/example index, NOT the video lesson number
// after the three part lesson 30. Always use data.id for an example path.
const sourceIndex=String(data.id).padStart(2,"0");
const notePath=data.id===27?"examples/LESSON_27.md":"examples/notes/lesson_"+sourceIndex+".md";
const manualById={6:"board-inspection",9:"onnx-toolchain",24:"mobilenet-image",25:"cpp-rknn-classify",26:"cpp-zero-copy",27:"mobilenet-image",28:"mobilenet-camera",29:"official-yolo-and-export",32:"onnx-toolchain",33:"yolov8-camera",34:"rkllm-native"};
const manual=manualById[data.id];
add("SOURCE","源码与工程实验说明",
 '<div class="panel"><p><a href="../../examples/lesson_'+sourceIndex+'.py">Python 课程源码 ↗</a> · '+
 '<a href="../../'+notePath+'">独立实验手册 ↗</a>'+
 (manual?' · <a href="../../engineering/'+manual+'.md">板端工程指南 ↗</a>':'')+
 '</p><p>先完成前面的准备、演示和验收，再阅读完整源码；需要第三方模型、图片或 SDK 的项目须准备真实文件。</p></div>');
const toc=slides.map((s,i)=>'<a class="outline-item" href="#'+sectionId(i)+'" data-section="'+i+'"><span>'+String(i+1).padStart(2,"0")+'</span>'+esc(s.title)+'</a>').join("");
const content=slides.map((s,i)=>'<section id="'+sectionId(i)+'" class="slide lesson-section" aria-labelledby="section-heading-'+i+'"><div class="kicker">'+esc(s.cat)+' / '+String(i+1).padStart(2,"0")+'</div><h2 id="section-heading-'+i+'">'+esc(s.title)+'</h2>'+s.body+'<div class="teacher-note"><strong>讲师提示：</strong> '+fmt(s.note)+'</div></section>').join("");
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