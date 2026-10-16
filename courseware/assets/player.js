
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
const slides=[];
function add(cat,title,body,note){slides.push({cat,title,body,note:note||"根据实际设备和软件版本判断，不要用未经验证的结果替代课堂证据。"});}
const name=data.title||m.title,intro=data.intro||"把理论、转换与运行验证连接成可重复的学习闭环。";
add("OPENING","本讲课程介绍",'<div class="eyebrow">'+esc(m.unit)+'</div><h1>'+esc(name)+'</h1><p class="big">'+fmt(intro)+'</p><div class="stats"><div><strong>'+m.duration+'<small> 分钟</small></strong><small>建议课堂时间</small></div><div><strong>'+data.goals.length+'</strong><small>目标数量</small></div><div><strong>'+data.steps.length+'</strong><small>实践步骤</small></div></div><p class="footnote">上下滚动阅读 · N 切换讲师提示 · P 打印</p>',"问学生：本节课最想解决的一个实际工程问题是什么？");
add("SCENARIO","从一个工程问题出发",'<div class="panel good"><span class="pill">课堂情境</span><h2>'+fmt(extra.scene||intro)+'</h2></div>'+cards(['<h3>学前预测</h3><p>如果跳过本讲，后续模型部署最可能在什么环节失败？</p>','<h3>如何证明成功</h3><p>除了程序退出码，还应保留输入、输出、版本及过程日志。</p>']),"用思维实验引导学生讨论，需要可观察结果而非猜测。");
add("GOALS","学习目标与验收方向",'<div class="panel">'+list(data.goals)+'</div><p class="footnote">每个目标对应可被检查的解释、操作、图示或运行证据。</p>',"把目标转为三个问题：知道什么、能够做什么、如何验证。");
add("CLASS","课堂安排",'<div class="three-cols">'+[["10%","问题引导","从工程场景切入"],["30%","原理与架构","术语、机制和限制"],["40%","教师演示 / 学生实操","对照步骤逐一验证"],["10%","排障与提问","反事实推理"],["10%","验收与作业","保留证据并迁移"]].map(x=>'<div class="panel soft"><span class="pill">'+x[0]+'</span><h3 style="margin-top:12px">'+x[1]+'</h3><p>'+x[2]+'</p></div>').join("")+'</div>',"原则：先验证一个基线，再改变一个变量，不要多项同时修改。");
if(extra.terms&&extra.terms.length)add("KEYWORDS","术语与接口",'<div class="three-cols">'+extra.terms.map(x=>'<div class="panel"><div class="eyebrow">KEY TERM</div><h3>'+esc(x[0])+'</h3><p>'+fmt(x[1])+'</p></div>').join("")+'</div>',"逐一说明术语对应哪个软件层、数据或硬件资源。");
const flow=extra.flow&&extra.flow.length?extra.flow:data.steps.slice(0,5).map(s=>s.slice(0,18));
add("FLOW","核心技术路线",'<div class="flow">'+flow.map((s,i)=>(i?'<div class="arrow">→</div>':"")+'<div class="flow-box"><span class="count">STEP '+(i+1)+'</span><span>'+fmt(s)+'</span></div>').join("")+'</div><div class="panel soft"><h3>沿数据路径检查</h3><p>每个节点的输入是什么、输出是什么、失败时可以检查哪些证据？</p></div>',"请学生指出哪些步骤发生在主机、哪些发生在目标板上。");
const core=(data.core||"").trim(),ss=core.match(/[^。！？；]+[。！？；]?/g)||[core],half=Math.max(1,Math.ceil(ss.length/2));
const p1=ss.slice(0,half).join(""),p2=ss.slice(half).join("")||core;
if(!Array.isArray(depth.concepts)||!depth.concepts.length){
add("THEORY","核心原理 · 机制",'<div class="panel"><h3>技术解释</h3><p class="big">'+fmt(p1)+'</p></div>'+cards(['<h3>输入侧要核对</h3><p>来源、类型、格式、尺寸和版本。</p>','<h3>输出侧要核对</h3><p>结果是否能解释、能量化、能复现。</p>']),"引导学生把术语说成可观察的接口行为。");
add("THEORY","核心原理 · 工程约束",'<div class="panel"><p class="big">'+fmt(p2)+'</p></div>'+cards(['<h3>先建立基线</h3><p>在明确测试条件下保存一个正确结果。</p>','<h3>再判断取舍</h3><p>根据精度、时间、资源与兼容性评估方案。</p>']),"不能把模型转换成功、速度变快与业务精度合格混为一谈。");

if(Array.isArray(depth.concepts)){
depth.concepts.forEach((c,i)=>{
 add("DEEP DIVE","专题精讲 "+(i+1)+" · "+c.title,
   '<div class="panel good"><h3>'+fmt(c.title)+'</h3><p class="big">'+fmt(c.explain)+'</p></div>'+
   '<div class="panel soft"><h3>理解要点 / 判断标准</h3><p>'+fmt(c.takeaway)+'</p></div>',
   "引导学生说明概念如何影响真实工程中的输入、输出或资源使用；鼓励举反例。");
});
}

}
const mid=Math.ceil(data.steps.length/2);
add("LAB","实践 01 · 准备与运行",'<p>先核对运行环境、输入文件和所需依赖，再按照下面的步骤开始实验。</p>'+stepList(data.steps.slice(0,mid),0),"先有稳定的最小可运行路径；涉及刷机或设备写操作要有回退方案。");
add("LAB","实践 02 · 运行与检查",'<p>继续完成实验，对照预期结果逐项核验，并记录失败的真实现象。</p>'+stepList(data.steps.slice(mid),mid),"每一步让学生说明：运行了什么、看到了什么、凭什么认为成功。");
if(data.code)add("EXAMPLE","参考命令或代码",'<div class="code-wrap"><button type="button" class="copy-code">复制片段</button><pre><code>'+esc(data.code)+'</code></pre></div><p class="footnote">代码取自对应教学讲义，只作参考；实际运行前核对 SDK 版本、资源路径与模型格式。</p>',"对关键参数、返回值和资源释放逐行讲解。");
else add("DEMO","示范操作 · 观察清单",cards(['<h3>演示前</h3>'+list(["确认型号、SDK 与板端驱动版本",data.steps[0]||"准备测试输入","确定预期输出和日志位置"]),'<h3>演示后</h3>'+list([data.steps[data.steps.length-1]||"核对程序结果","保存输入、输出与截图","列出未通过的验证项"])]),"缺少完整官方实验工程时用可复现的官方示例或概念演示，不编造运行证据。");

if(Array.isArray(depth.lab)&&depth.lab.length){
 add("LAB PLUS","细化实验 · 操作与预期",
  '<div class="three-cols">'+depth.lab.map((s,i)=>'<div class="panel"><span class="eyebrow">TASK 0'+(i+1)+'</span><h3>'+fmt(s.title)+'</h3><p>'+fmt(s.action)+'</p><div class="panel good" style="margin-top:12px"><strong>验证证据</strong><p>'+fmt(s.verify)+'</p></div></div>').join("")+'</div>',
  "每组保留实际观察值；未运行的示例写“未验证”，不要填写虚构截图。");
}
if(depth.snippet){
 add("LAB PLUS","补充实验片段与解释",'<div class="code-wrap"><button type="button" class="copy-code">复制片段</button><pre><code>'+esc(depth.snippet)+'</code></pre></div><p class="footnote">实验片段为教学示例。核对路径、Python/SDK/驱动和模型属性后再使用；不要在未知硬件上执行写入或更新系统的命令。</p>',
 "这一片段主要用于辅助理解；清楚说明依赖、可观察输出和修改范围。");
}

add("RECORD","实验报告需要记录什么？",'<div class="three-cols"><div class="panel"><div class="eyebrow">INPUT</div><h3>条件</h3><p>模型、硬件、版本、输入张量、启动参数。</p></div><div class="panel"><div class="eyebrow">PROCESS</div><h3>过程</h3><p>执行动作、返回码、输出日志与阶段耗时。</p></div><div class="panel"><div class="eyebrow">RESULT</div><h3>结论</h3><p>实际现象、与基线差异、待解决的问题。</p></div></div>',"请学生保存可共享的结果，而非仅回答“成功了”。");
add("DEBUG","常见问题与错误诊断",'<div class="three-cols">'+data.pitfalls.slice(0,3).map((s,i)=>'<div class="panel warn"><div class="eyebrow">RISK 0'+(i+1)+'</div><h3>典型误区</h3><p>'+fmt(s)+'</p><small class="muted">复现 → 缩小范围 → 单变量修改 → 重新验证</small></div>').join("")+'</div>',"每个误区尝试列出最小复现步骤和一个可检查的证据。");

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

const codeFile="lesson_"+String(data.id).padStart(2,"0")+".py";
const hardwareByLesson={
9:["convert_onnx.py"],11:["convert_onnx.py"],12:["onnx_reference.py"],
13:["onnx_reference.py"],23:["rknn_classify.cpp"],
24:["lite_infer.py"],25:["rknn_classify.cpp","CMakeLists.txt"],
26:[],27:["lite_infer.py","prepare_image.py"],28:["rknn_classify.cpp"],
29:["lite_infer.py","prepare_image.py"],30:["export_yolo_onnx.py"],31:["export_yolo_onnx.py"],
32:["export_yolo_onnx.py","convert_onnx.py","onnx_reference.py"],33:["lite_infer.py","compare_outputs.py"],
34:[]
};
const sdkFiles=hardwareByLesson[data.id]||[];
const boardCameraCode=data.id===27?'<li><a href="../../boards/radxa-rock5b/apps/camera_mobilenet_lite.py">ROCK 5B：USB摄像头→RKNNLite MobileNet实时分类</a></li><li><a href="../../boards/radxa-rock5b/CAMERA_MOBILENET.md">实机接线、命令、测量与排障手册</a></li>':'';
const practicalNote=data.id===27?"LESSON_27.md":("notes/lesson_"+String(data.id).padStart(2,"0")+".md");
const codeLinks='<ul><li><a href="../../examples/'+codeFile+
'">打开本讲实操源码：'+codeFile+'</a></li>'+
sdkFiles.map(f=>'<li><a href="../../examples/hardware/'+f+
'">查看配套 SDK 示例：'+f+'</a></li>').join("")+boardCameraCode+
'<li><a href="../../examples/'+practicalNote+'">本讲操作MD（不重复理论）</a></li><li><a href="../../examples/README.md">代码运行环境、依赖和验证说明</a></li><li><a href="../../examples/CODE_STATUS.md">35节代码真实完成度审计</a></li></ul>';
add("SOURCE CODE","本讲可执行源码与运行环境",
'<div class="panel good"><h3>先运行，再对照讲义</h3>'+codeLinks+
'<p>35 个编号入口已重写为对应的实操程序；验证时请区分 PC 可测的算法、SDK 工具调用和 RK3588 上板验收。SDK 代码需要真实模型、匹配 Runtime 与开发板，模拟结果不得作为 NPU 实测。</p></div>'+
'<div class="panel soft"><h3>第一条运行命令</h3><div class="code-wrap"><pre><code>python3 examples/'+codeFile+
' --help</code></pre></div><p>从仓库根目录执行，再根据 README 提供真实输入。Python 通用实现集中在 examples/labs.py。</p></div>',
"必须确认课件代码是算法实验还是板端完整推理。遇到缺少模型、SDK 或驱动时应明确记录阻塞项。");

add("TRANSFER","课后练习与知识迁移",'<div class="panel">'+list(data.homework)+'</div><div class="panel soft"><h3>提交建议</h3><p>提交版本说明、数据与模型来源、关键步骤、结果截图、问题记录和复盘。涉及代码时提供可运行的最小示例。</p></div>',"下节课尽可能沿用本节的模型、日志和环境记录。");
const nx=db[data.id+1];
add("SUMMARY","本节总结",cards(['<h3>三件需要记住的事</h3>'+list(data.goals),'<h3>下一步学习</h3><p>'+(nx?"下一讲："+esc(nx.title):"本系列课程已经完成，请整理项目成果。")+'</p><p>在下一次实验前，请确认本讲的完成标准。</p>']),"闭环复盘：输入是什么、发生了什么、有什么证据。");

const prev=db[data.id-1],next=db[data.id+1];
const sectionId=i=>"lesson-section-"+(i+1);
function lessonLink(x,label){return x?'<a class="btn ghost" href="'+encodeURIComponent(x.slug).replaceAll("(","%28").replaceAll(")","%29")+'.html">'+label+'</a>':"";}
const toc=slides.map((s,i)=>'<a class="outline-item" href="#'+sectionId(i)+'" data-section="'+i+'"><span>'+String(i+1).padStart(2,"0")+'</span>'+esc(s.title)+'</a>').join("");
const content=slides.map((s,i)=>'<section id="'+sectionId(i)+'" class="slide lesson-section" aria-labelledby="section-heading-'+i+'"><div class="kicker">'+esc(s.cat)+' / '+String(i+1).padStart(2,"0")+'</div><h2 id="section-heading-'+i+'">'+esc(s.title)+'</h2>'+s.body+'<div class="teacher-note"><strong>讲师提示：</strong> '+fmt(s.note)+'</div></section>').join("");
document.body.classList.add("continuous");
host.innerHTML='<header class="player-header"><div class="header-row"><a class="brand" href="../index.html">RK<b>3588</b> / COURSE</a><div class="lesson-name">'+esc(name)+'</div><div class="actions"><button class="btn ghost" id="menuBtn" type="button" aria-expanded="false" aria-controls="slideOutline">章节目录</button><button class="btn ghost" id="noteBtn" type="button" aria-pressed="false">讲师提示</button><button class="btn ghost" id="printBtn" type="button">打印全文</button></div></div><div class="player-progress"><i id="progressBar"></i></div></header><div class="player-layout"><nav id="slideOutline" class="slide-outline" aria-label="本节课目录"><h3>本节课程目录</h3>'+toc+'<p style="padding:12px"><a href="../../docs/'+encodeURIComponent(m.slug).replaceAll("(","%28").replaceAll(")","%29")+'.md">Markdown 详细讲义 ↗</a></p></nav><main class="player-main"><div class="longform-intro"><span class="eyebrow">CONTINUOUS READING</span><p>本节课的全部内容已展开在同一页面。向下滚动阅读，或点击左侧目录快速定位；课堂测验、代码复制和验收清单可直接操作。</p></div><article id="lessonArticle" class="lesson-article">'+content+'</article><nav class="lesson-footer-nav" aria-label="课程导航">'+lessonLink(prev,"← 上一讲")+'<a class="btn ghost" href="../index.html">全部课程</a>'+lessonLink(next,"下一讲 →")+'</nav><p class="hotkeys">使用浏览器正常滚动阅读 · 点击目录跳转 · N 显示讲师提示 · P 打印整篇 · F 全屏</p></main></div><button id="backTop" class="back-top" type="button" aria-label="返回顶部">↑ 顶部</button>';
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