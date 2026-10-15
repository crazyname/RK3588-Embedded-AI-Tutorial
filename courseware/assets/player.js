
(function(){
"use strict";
const db=window.COURSE_CATALOG||[],el=document.getElementById("lesson-data"),host=document.getElementById("app");
if(!el||!host)return;
let data;try{data=JSON.parse(el.textContent);}catch(e){host.textContent="课件数据读取失败";return;}
const m=db[data.id]||{title:data.title,duration:90,unit:"嵌入式 AI"},extra=(window.COURSE_EXTRA||{})[data.id]||{};
const esc=s=>String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
const fmt=s=>esc(s).replace(/\u0060([^\u0060]+)\u0060/g,"<code>$1</code>");
const list=a=>"<ul>"+(a||[]).map(t=>"<li>"+fmt(t)+"</li>").join("")+"</ul>";
const cards=a=>'<div class="columns">'+a.map(t=>'<div class="panel">'+t+'</div>').join("")+'</div>';
const stepList=(a,start)=>'<ol class="steps-list">'+a.map((s,i)=>'<li><span class="step-no">'+(start+i+1)+'</span><span class="step-body">'+fmt(s)+'<small>观察执行结果，并记录版本、输入、日志或数据。</small></span></li>').join("")+"</ol>";
const slides=[];
function add(cat,title,body,note){slides.push({cat,title,body,note:note||"根据实际设备和软件版本判断，不要用未经验证的结果替代课堂证据。"});}
const name=data.title||m.title,intro=data.intro||"把理论、转换与运行验证连接成可重复的学习闭环。";
add("OPENING","本讲课程介绍",'<div class="eyebrow">'+esc(m.unit)+'</div><h1>'+esc(name)+'</h1><p class="big">'+fmt(intro)+'</p><div class="stats"><div><strong>'+m.duration+'<small> 分钟</small></strong><small>建议课堂时间</small></div><div><strong>'+data.goals.length+'</strong><small>目标数量</small></div><div><strong>'+data.steps.length+'</strong><small>实践步骤</small></div></div><p class="footnote">方向键 / 空格翻页 · N 切换讲师提示 · P 打印</p>',"问学生：本节课最想解决的一个实际工程问题是什么？");
add("SCENARIO","从一个工程问题出发",'<div class="panel good"><span class="pill">课堂情境</span><h2>'+fmt(extra.scene||intro)+'</h2></div>'+cards(['<h3>学前预测</h3><p>如果跳过本讲，后续模型部署最可能在什么环节失败？</p>','<h3>如何证明成功</h3><p>除了程序退出码，还应保留输入、输出、版本及过程日志。</p>']),"用思维实验引导学生讨论，需要可观察结果而非猜测。");
add("GOALS","学习目标与验收方向",'<div class="panel">'+list(data.goals)+'</div><p class="footnote">每个目标对应可被检查的解释、操作、图示或运行证据。</p>',"把目标转为三个问题：知道什么、能够做什么、如何验证。");
add("CLASS","课堂安排",'<div class="three-cols">'+[["10%","问题引导","从工程场景切入"],["30%","原理与架构","术语、机制和限制"],["40%","教师演示 / 学生实操","对照步骤逐一验证"],["10%","排障与提问","反事实推理"],["10%","验收与作业","保留证据并迁移"]].map(x=>'<div class="panel soft"><span class="pill">'+x[0]+'</span><h3 style="margin-top:12px">'+x[1]+'</h3><p>'+x[2]+'</p></div>').join("")+'</div>',"原则：先验证一个基线，再改变一个变量，不要多项同时修改。");
if(extra.terms&&extra.terms.length)add("KEYWORDS","术语与接口",'<div class="three-cols">'+extra.terms.map(x=>'<div class="panel"><div class="eyebrow">KEY TERM</div><h3>'+esc(x[0])+'</h3><p>'+fmt(x[1])+'</p></div>').join("")+'</div>',"逐一说明术语对应哪个软件层、数据或硬件资源。");
const flow=extra.flow&&extra.flow.length?extra.flow:data.steps.slice(0,5).map(s=>s.slice(0,18));
add("FLOW","核心技术路线",'<div class="flow">'+flow.map((s,i)=>(i?'<div class="arrow">→</div>':"")+'<div class="flow-box"><span class="count">STEP '+(i+1)+'</span><span>'+fmt(s)+'</span></div>').join("")+'</div><div class="panel soft"><h3>沿数据路径检查</h3><p>每个节点的输入是什么、输出是什么、失败时可以检查哪些证据？</p></div>',"请学生指出哪些步骤发生在主机、哪些发生在目标板上。");
const core=(data.core||"").trim(),ss=core.match(/[^。！？；]+[。！？；]?/g)||[core],half=Math.max(1,Math.ceil(ss.length/2));
const p1=ss.slice(0,half).join(""),p2=ss.slice(half).join("")||core;
add("THEORY","核心原理 · 机制",'<div class="panel"><h3>技术解释</h3><p class="big">'+fmt(p1)+'</p></div>'+cards(['<h3>输入侧要核对</h3><p>来源、类型、格式、尺寸和版本。</p>','<h3>输出侧要核对</h3><p>结果是否能解释、能量化、能复现。</p>']),"引导学生把术语说成可观察的接口行为。");
add("THEORY","核心原理 · 工程约束",'<div class="panel"><p class="big">'+fmt(p2)+'</p></div>'+cards(['<h3>先建立基线</h3><p>在明确测试条件下保存一个正确结果。</p>','<h3>再判断取舍</h3><p>根据精度、时间、资源与兼容性评估方案。</p>']),"不能把模型转换成功、速度变快与业务精度合格混为一谈。");
const mid=Math.ceil(data.steps.length/2);
add("LAB","实践 01 · 准备与运行",'<p>先核对运行环境、输入文件和所需依赖，再按照下面的步骤开始实验。</p>'+stepList(data.steps.slice(0,mid),0),"先有稳定的最小可运行路径；涉及刷机或设备写操作要有回退方案。");
add("LAB","实践 02 · 运行与检查",'<p>继续完成实验，对照预期结果逐项核验，并记录失败的真实现象。</p>'+stepList(data.steps.slice(mid),mid),"每一步让学生说明：运行了什么、看到了什么、凭什么认为成功。");
if(data.code)add("EXAMPLE","参考命令或代码",'<div class="code-wrap"><button type="button" class="copy-code">复制片段</button><pre><code>'+esc(data.code)+'</code></pre></div><p class="footnote">代码取自对应教学讲义，只作参考；实际运行前核对 SDK 版本、资源路径与模型格式。</p>',"对关键参数、返回值和资源释放逐行讲解。");
else add("DEMO","示范操作 · 观察清单",cards(['<h3>演示前</h3>'+list(["确认型号、SDK 与板端驱动版本",data.steps[0]||"准备测试输入","确定预期输出和日志位置"]),'<h3>演示后</h3>'+list([data.steps[data.steps.length-1]||"核对程序结果","保存输入、输出与截图","列出未通过的验证项"])]),"缺少完整官方实验工程时用可复现的官方示例或概念演示，不编造运行证据。");
add("RECORD","实验报告需要记录什么？",'<div class="three-cols"><div class="panel"><div class="eyebrow">INPUT</div><h3>条件</h3><p>模型、硬件、版本、输入张量、启动参数。</p></div><div class="panel"><div class="eyebrow">PROCESS</div><h3>过程</h3><p>执行动作、返回码、输出日志与阶段耗时。</p></div><div class="panel"><div class="eyebrow">RESULT</div><h3>结论</h3><p>实际现象、与基线差异、待解决的问题。</p></div></div>',"请学生保存可共享的结果，而非仅回答“成功了”。");
add("DEBUG","常见问题与错误诊断",'<div class="three-cols">'+data.pitfalls.slice(0,3).map((s,i)=>'<div class="panel warn"><div class="eyebrow">RISK 0'+(i+1)+'</div><h3>典型误区</h3><p>'+fmt(s)+'</p><small class="muted">复现 → 缩小范围 → 单变量修改 → 重新验证</small></div>').join("")+'</div>',"每个误区尝试列出最小复现步骤和一个可检查的证据。");
if(extra.quiz){
const q=extra.quiz;
add("CHECK","课堂互动测验",'<div class="panel"><h3>'+fmt(q[0])+'</h3><div class="quiz-options">'+q[1].map((x,i)=>'<label class="quiz-option"><input type="radio" name="quiz" value="'+i+'">'+String.fromCharCode(65+i)+'. '+fmt(x)+'</label>').join("")+'</div><button id="checkQuiz" type="button" class="btn">提交并解释</button><div id="quizFeedback" class="quiz-feedback" role="status"></div></div>',"先让学生独立作答，再请一位同学解释原因。");
}else add("CHECK","课堂讨论",'<div class="panel"><h3>从下面的目标中选一项，用自己的话解释其工作原理和验证方式。</h3>'+list(data.goals.slice(0,2))+'</div>',"讨论的目标是解释因果，而非复述术语。");
add("ACCEPT","本节验收标准",'<p>以下勾选仅用于辅助复习，实际完成请提供可观察的证据。</p><div id="checks">'+data.checks.map((s,i)=>'<label class="check-item"><input data-check="'+i+'" type="checkbox">'+fmt(s)+'</label>').join("")+'</div><p class="footnote">学习进度仅存储在当前浏览器本地；不会上传到服务器。</p>',"未达标的部分对应哪一张幻灯片？请学生指出具体位置。");
add("TRANSFER","课后练习与知识迁移",'<div class="panel">'+list(data.homework)+'</div><div class="panel soft"><h3>提交建议</h3><p>提交版本说明、数据与模型来源、关键步骤、结果截图、问题记录和复盘。涉及代码时提供可运行的最小示例。</p></div>',"下节课尽可能沿用本节的模型、日志和环境记录。");
const nx=db[data.id+1];
add("SUMMARY","本节总结",cards(['<h3>三件需要记住的事</h3>'+list(data.goals),'<h3>下一步学习</h3><p>'+(nx?"下一讲："+esc(nx.title):"本系列课程已经完成，请整理项目成果。")+'</p><p>在下一次实验前，请确认本讲的完成标准。</p>']),"闭环复盘：输入是什么、发生了什么、有什么证据。");
let pos=0;
const prev=db[data.id-1],next=db[data.id+1];
function other(x,label){return x?'<a class="btn ghost" href="'+encodeURIComponent(x.slug).replaceAll("(","%28").replaceAll(")","%29")+'.html">'+label+'</a>':"";}
host.innerHTML='<header class="player-header"><div class="header-row"><a class="brand" href="../index.html">RK<b>3588</b> / COURSE</a><div class="lesson-name">'+esc(name)+'</div><div class="actions"><button class="btn ghost" id="menuBtn">目录</button><button class="btn ghost" id="noteBtn">讲师提示</button><button class="btn ghost" id="printBtn">打印</button></div></div><div class="player-progress"><i id="progressBar"></i></div></header><div class="player-layout"><aside id="slideOutline" class="slide-outline"><h3>SLIDE OUTLINE</h3>'+slides.map((s,i)=>'<button class="outline-item" data-i="'+i+'"><span>'+String(i+1).padStart(2,"0")+'</span>'+esc(s.title)+'</button>').join("")+'<p style="padding:12px"><a href="../../docs/'+encodeURIComponent(m.slug).replaceAll("(","%28").replaceAll(")","%29")+'.md">Markdown 详细讲义 ↗</a></p></aside><main class="player-main"><section class="slide active" id="slideView"></section><div class="controls"><div class="actions">'+other(prev,"← 上一讲")+'<button id="prevBtn" type="button" class="btn ghost">← 上一页</button></div><span id="counter" class="middle"></span><div class="actions"><button id="nextBtn" type="button" class="btn">下一页 →</button>'+other(next,"下一讲 →")+'</div></div><div class="hotkeys">快捷键：← / → / 空格翻页 · N 显示讲师提示 · F 全屏 · P 打印</div></main></div>';
function show(){
const slide=slides[pos],v=document.getElementById("slideView");
v.innerHTML='<span class="kicker">'+esc(slide.cat)+' / '+String(pos+1).padStart(2,"0")+'</span><h2>'+esc(slide.title)+'</h2>'+slide.body+'<div class="teacher-note"><strong>讲师提示：</strong>'+fmt(slide.note)+'</div>';
document.getElementById("counter").textContent=(pos+1)+" / "+slides.length;
document.getElementById("progressBar").style.width=(100*(pos+1)/slides.length)+"%";
document.getElementById("prevBtn").disabled=pos===0;
document.getElementById("nextBtn").textContent=pos===slides.length-1?"返回总目录":"下一页 →";
document.querySelectorAll(".outline-item").forEach((n,i)=>n.classList.toggle("active",i===pos));
const quizBtn=document.getElementById("checkQuiz");if(quizBtn){quizBtn.onclick=function(){const chosen=document.querySelector('input[name="quiz"]:checked'),f=document.getElementById("quizFeedback"),q=extra.quiz;if(!chosen)f.textContent="请先选择一个选项。";else{const ok=Number(chosen.value)===q[2];f.innerHTML=(ok?"<strong>回答正确。</strong> ":"<strong>再想一想。</strong> 正确选项："+String.fromCharCode(65+q[2])+"。 ")+fmt(q[3]);}f.classList.add("visible");};}
const copy=v.querySelector(".copy-code");if(copy)copy.onclick=function(){if(navigator.clipboard)navigator.clipboard.writeText(data.code).then(()=>{copy.textContent="已复制";}).catch(()=>{copy.textContent="请手动选择复制";});};
v.querySelectorAll("input[data-check]").forEach(ch=>{const key="rk3588:"+data.id+":"+ch.dataset.check;try{ch.checked=localStorage.getItem(key)==="1";}catch(e){}ch.onchange=function(){try{localStorage.setItem(key,ch.checked?"1":"0");}catch(e){}};});
try{localStorage.setItem("rk3588:"+data.id+":last",String(pos));}catch(e){}
}
function jump(n){if(n<0||n>=slides.length)return;pos=n;show();window.scrollTo(0,0);}
document.querySelectorAll(".outline-item").forEach(b=>b.onclick=()=>{jump(Number(b.dataset.i));document.getElementById("slideOutline").classList.remove("open");});
document.getElementById("prevBtn").onclick=()=>jump(pos-1);
document.getElementById("nextBtn").onclick=()=>pos===slides.length-1?location.href="../index.html":jump(pos+1);
document.getElementById("menuBtn").onclick=()=>document.getElementById("slideOutline").classList.toggle("open");
document.getElementById("noteBtn").onclick=()=>document.body.classList.toggle("show-notes");
document.getElementById("printBtn").onclick=()=>window.print();
document.addEventListener("keydown",e=>{if(/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName))return;if(e.key==="ArrowRight"||e.key===" "){e.preventDefault();jump(pos+1);}else if(e.key==="ArrowLeft")jump(pos-1);else if(e.key==="Home")jump(0);else if(e.key==="End")jump(slides.length-1);else if(e.key.toLowerCase()==="n")document.body.classList.toggle("show-notes");else if(e.key.toLowerCase()==="p")window.print();else if(e.key.toLowerCase()==="f"){if(!document.fullscreenElement)document.documentElement.requestFullscreen&&document.documentElement.requestFullscreen();else document.exitFullscreen&&document.exitFullscreen();}});
try{const last=Number(localStorage.getItem("rk3588:"+data.id+":last"));if(Number.isFinite(last)&&last>=0&&last<slides.length)pos=last;}catch(e){}

(function setupPrintDeck(){
const container=document.createElement("div");
container.id="printDeck";
container.innerHTML=slides.map(function(s,i){return '<section class="slide"><span class="kicker">'+esc(s.cat)+' / '+String(i+1).padStart(2,"0")+'</span><h2>'+esc(s.title)+'</h2>'+s.body+'</section>';}).join("");
document.body.appendChild(container);
const style=document.createElement("style");
style.textContent="#printDeck{display:none}@media print{#app{display:none!important}#printDeck{display:block!important}#printDeck .slide{display:flex!important;break-after:page;page-break-after:always}#printDeck button{display:none!important}#printDeck .quiz-feedback{display:none!important}}";
document.head.appendChild(style);
})();
show();
})();
