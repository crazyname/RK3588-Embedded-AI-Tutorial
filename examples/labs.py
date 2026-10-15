#!/usr/bin/env python3
"""35 RK3588 self-study experiments. Python >=3.9; standard library only.

These are executable calculations, validators and read-only diagnostics.
They are NOT a substitute for genuine RKNN inference or board benchmarking.
See examples/hardware/ for RKNN SDK-dependent workflows.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import statistics
import subprocess
import sys
import tempfile
import time

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()

def percentiles(values):
    if not values:
        raise ValueError("at least one sample required")
    a = sorted(values)
    return {"n": len(a), "min": a[0], "p50": statistics.median(a),
            "p95_nearest_rank": a[max(0, math.ceil(.95 * len(a))-1)],
            "mean": statistics.mean(a), "max": a[-1]}

def iou(a, b):
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[2], b[2]), min(a[3], b[3])
    area = max(0, x2-x1) * max(0, y2-y1)
    aa = max(0, a[2]-a[0]) * max(0, a[3]-a[1])
    bb = max(0, b[2]-b[0]) * max(0, b[3]-b[1])
    return area / (aa+bb-area) if aa+bb-area else 0.0

def nms(detections, threshold=.5):
    """Each detection: dict with box=[x1,y1,x2,y2], score and class_id."""
    selected = []
    for d in sorted(detections, key=lambda z: z["score"], reverse=True):
        if all(d["class_id"] != k["class_id"] or iou(d["box"], k["box"]) <= threshold
               for k in selected):
            selected.append(d)
    return selected

def letterbox_transform(width, height, target=640):
    if min(width, height, target) <= 0:
        raise ValueError("image dimensions must be positive")
    scale = min(target/width, target/height)
    return {"scale": scale, "pad_x": (target-width*scale)/2,
            "pad_y": (target-height*scale)/2, "target": target}

def from_letterbox(box, transform, width, height):
    r = transform["scale"]
    px, py = transform["pad_x"], transform["pad_y"]
    return [max(0, min(width, (box[0]-px)/r)),
            max(0, min(height, (box[1]-py)/r)),
            max(0, min(width, (box[2]-px)/r)),
            max(0, min(height, (box[3]-py)/r))]

def quantize(x, scale, zero_point=0):
    if scale <= 0:
        raise ValueError("scale must be positive")
    raw = math.floor(x / scale + .5) + zero_point
    q = max(-128, min(127, raw))
    return {"int8": q, "dequantized": (q-zero_point)*scale}

def require_file(name, ext=None):
    if not name:
        raise ValueError("Provide --input PATH for this example")
    p = Path(name).expanduser()
    if not p.is_file():
        raise FileNotFoundError(str(p))
    if ext and p.suffix.lower() != ext:
        raise ValueError("Expected file ending with "+ext)
    return p

def command_version(command):
    import shutil
    return shutil.which(command)

def read_frequency_nodes():
    roots = [Path("/sys/devices/system/cpu"), Path("/sys/class/devfreq")]
    results = []
    for root in roots:
        if not root.is_dir():
            continue
        for p in root.rglob("*freq"):
            if not p.is_file() or len(results) >= 40:
                continue
            try:
                results.append({"path": str(p), "value": p.read_text().strip()[:70]})
            except (OSError, UnicodeError):
                pass
    return results

def check_yolo_labels(path):
    problems, labels = [], 0
    for p in sorted(path.rglob("*.txt")):
        for ln, row in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if not row.strip():
                continue
            fields = row.split()
            if len(fields) != 5:
                problems.append(f"{p}:{ln}: expected class,x,y,w,h")
                continue
            try:
                cls = int(fields[0])
                vals = [float(v) for v in fields[1:]]
                ok = cls >= 0 and all(math.isfinite(v) for v in vals)
                ok = ok and all(0 <= v <= 1 for v in vals)
                ok = ok and vals[2] > 0 and vals[3] > 0
                ok = ok and vals[0]-vals[2]/2 >= -1e-6
                ok = ok and vals[1]-vals[3]/2 >= -1e-6
                ok = ok and vals[0]+vals[2]/2 <= 1+1e-6
                ok = ok and vals[1]+vals[3]/2 <= 1+1e-6
            except ValueError:
                ok = False
            if not ok:
                problems.append(f"{p}:{ln}: invalid normalized box/class")
            else:
                labels += 1
    return {"valid_labels": labels, "errors": problems, "passed": not problems}

def exec_lesson(number, args):
    p = args.input
    if number == 0:
        return {"python": sys.version.split()[0], "platform": platform.platform(),
                "arch": platform.machine(), "cwd": str(Path.cwd()),
                "next": "record your actual RK3588 board model and tool versions"}
    if number == 1:
        return {"system": platform.system(), "machine": platform.machine(),
                "cores": os.cpu_count(), "linux_cpuinfo_present": Path("/proc/cpuinfo").exists()}
    if number == 2:
        h, w, cin, cout, k = 64, 64, 32, 64, 3
        mac = h*w*cin*cout*k*k
        return {"case": [h,w,cin,cout,k], "mac": mac, "gops": 2*mac/1e9}
    if number == 3:
        return {"deployment": ["source model", "ONNX", "RKNN Toolkit2",
                                ".rknn", "RKNN Runtime", "NPU driver", "NPU result"],
                "check": "conversion, loading and task-level validation are separate"}
    if number == 4:
        return {"official": {
            "rknn_toolkit2": "https://github.com/airockchip/rknn-toolkit2",
            "rknn_model_zoo": "https://github.com/airockchip/rknn_model_zoo",
            "rknn_llm": "https://github.com/airockchip/rknn-llm"},
                "note": "record exact upstream commit/tag, not only main"}
    if number == 5:
        return {"python": sys.version.split()[0], "arch": platform.machine(),
                "venv_active": sys.prefix != sys.base_prefix,
                "pip_hint": [sys.executable, "-m", "pip", "--version"]}
    if number == 6:
        return {"kernel": platform.release(), "npu_candidates":
                [str(x) for x in (Path("/dev/rknpu"),Path("/dev/rknpu0")) if x.exists()],
                "note": "device paths vary by BSP; this read-only check never flashes firmware"}
    if number == 7:
        return {"read_only_frequency_nodes": read_frequency_nodes(),
                "note": "values/units depend on your BSP"}
    if number == 8:
        scores = [.05, .82, .1, .03]
        return {"demo_top_class": max(range(len(scores)), key=scores.__getitem__),
                "scores": scores, "note": "synthetic output; NOT an RKNN demo inference"}
    if number == 9:
        path = require_file(p, ".onnx")
        return {"onnx": str(path), "bytes": path.stat().st_size, "sha256": sha256(path),
                "next": "run examples/hardware/convert_onnx.py with RKNN-Toolkit2"}
    if number == 10:
        pix=[0.,128.,255.]
        return {"pixel_rgb": pix, "normalized": [(v/255-.5)/.5 for v in pix],
                "bgr": list(reversed(pix))}
    if number == 11:
        path = require_file(p)
        return {"artifact": str(path), "sha256": sha256(path),
                "bytes": path.stat().st_size}
    if number == 12:
        path = require_file(p, ".onnx")
        try:
            import onnx
        except ImportError as exc:
            raise RuntimeError("Install onnx: python -m pip install onnx") from exc
        model = onnx.load(str(path))
        onnx.checker.check_model(model)
        return {"nodes": len(model.graph.node),
                "inputs": [v.name for v in model.graph.input],
                "outputs": [v.name for v in model.graph.output],
                "opsets": [z.version for z in model.opset_import]}
    if number == 13:
        return {"rknn": "Use examples/hardware/lite_infer.py on RK3588",
                "requirements": ["a matching .rknn model", "RKNNLite on board", "NumPy input"],
                "note": "simulator timing is not NPU timing"}
    if number == 14:
        return {"scale": .1, "zero_point": 0, "samples":
                [{"original": x, **quantize(x, .1)} for x in (.26, 1.04, -.26)]}
    if number == 15:
        samples=[]
        for _ in range(24):
            start=time.perf_counter()
            sum(i*i for i in range(20000))
            samples.append((time.perf_counter()-start)*1000)
        return {"cpu_demo_ms": percentiles(samples), "warning": "not RK3588 NPU FPS"}
    if number == 16:
        usage = __import__("resource").getrusage(__import__("resource").RUSAGE_SELF)
        return {"pid": os.getpid(), "ru_maxrss_platform_units": usage.ru_maxrss,
                "memory_kib": Path("/proc/meminfo").read_text().splitlines()[0]
                if Path("/proc/meminfo").exists() else "Linux only"}
    if number == 17:
        weights=[[1,0,0],[0,0,0],[2,1,3],[0,0,0]]
        keep=[row for row in weights if any(row)]
        return {"original_out_channels": len(weights), "pruned_out_channels": len(keep),
                "weights": keep, "note": "structural toy example, not NPU benchmark"}
    if number == 18:
        path = require_file(p)
        return {"file": str(path), "sha256": sha256(path),
                "purpose": "integrity only, NOT encryption",
                "next": "use RKNN official encryption API only if supported"}
    if number == 19:
        images=[[[i]*3 for _ in range(2)] for i in range(4)]
        return {"batch_size": len(images), "sample_shape": [2,3],
                "input": images, "note": "tensor illustration, no NPU execution"}
    if number == 20:
        temperature, image_feature = 24.0, .8
        score = .3*image_feature + .7*(temperature/40)
        return {"image_feature": image_feature, "temperature_C": temperature,
                "fusion_score": score, "note": "toy multi-input arithmetic, not trained model"}
    if number == 21:
        shapes=[(320,320),(640,640)]
        return {"nhwc_uint8_bytes": [{"shape": [1,h,w,3], "bytes": h*w*3}
                                     for h,w in shapes],
                "note": "memory comparison; RKNN dynamic shape support must be checked"}
    if number == 22:
        if not p:
            return {"transpose_permutation": [0,2,3,1],
                    "before_nchw": [1,3,224,224], "after_nhwc": [1,224,224,3],
                    "note": "for real ONNX validation pass --input model.onnx"}
        path = require_file(p, ".onnx")
        try:
            import onnx
        except ImportError as exc:
            raise RuntimeError("Install onnx: python -m pip install onnx") from exc
        m=onnx.load(str(path))
        onnx.checker.check_model(m)
        return {"model":str(path),"transpose_nodes":sum(n.op_type=="Transpose" for n in m.graph.node)}
    if number == 23:
        code='#include <iostream>\nint main(){std::cout << "RK3588 host code generation OK" << std::endl;}\n'
        dest=Path(args.output or (Path(tempfile.gettempdir())/"rk3588_generated_demo.cpp"))
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(code,encoding="utf-8")
        return {"generated_cpp": str(dest), "compile": f"g++ {dest} -o /tmp/rk3588_demo"}
    if number == 24:
        return {"sdk": "rknn-toolkit-lite2", "environment": "RK3588 board",
                "real_code": "examples/hardware/lite_infer.py",
                "not_mock_inference": True}
    if number == 25:
        return {"sdk": "rknpu2 C API", "real_code": "examples/hardware/rknn_classify.cpp",
                "lifecycle": ["rknn_init","rknn_query","rknn_inputs_set","rknn_run",
                              "rknn_outputs_get","rknn_outputs_release","rknn_destroy"]}
    if number == 26:
        return {"sdk": "rknpu2 zero-copy", "requirements":
                ["rknn_create_mem","rknn_set_io_mem","tensor strides","cache coherence"],
                "next": "official SDK zero-copy example; platform-specific hardware validation"}
    if number == 27:
        s=[.1,.9,.4,.05]
        return {"top2": sorted(enumerate(s),key=lambda x:x[1],reverse=True)[:2],
                "real_board_model": "examples/hardware/lite_infer.py"}
    if number == 28:
        return {"modules":["decode_image","preprocess","rknn_inference","topk","labels"],
                "contract": "outputs are indexed exactly by model-specific label file"}
    if number == 29:
        demo=[{"box":[10,10,90,80],"score":.90,"class_id":0},
              {"box":[14,14,88,78],"score":.70,"class_id":0},
              {"box":[14,14,88,78],"score":.85,"class_id":1}]
        return {"iou_0_1":iou(demo[0]["box"],demo[1]["box"]),
                "nms_result":nms(demo), "letterbox":letterbox_transform(1280,720)}
    if number == 30:
        try:
            import importlib.metadata as im
            pkgs={k:im.version(k) for k in ("torch","ultralytics") if any(
                  d.metadata.get("Name","").lower()==k for d in im.distributions())}
        except (ImportError, OSError):
            pkgs={}
        return {"python":sys.version.split()[0],"training_packages":pkgs,
                "next":"examples/hardware/export_yolo_onnx.py --weights best.pt"}
    if number == 31:
        if not p:
            with tempfile.TemporaryDirectory() as tmp:
                f=Path(tmp)/"example.txt"
                f.write_text("0 0.5 0.5 0.4 0.3\n",encoding="utf-8")
                return {"example": check_yolo_labels(Path(tmp)),
                        "note":"pass --input dataset/labels for your actual labels"}
        return check_yolo_labels(require_file(p) if Path(p).is_file() else Path(p))
    if number == 32:
        if not p:
            return {"real_export_code":"examples/hardware/export_yolo_onnx.py",
                    "steps":["PyTorch export", "ONNX checker", "RKNN conversion", "board verification"]}
        f=require_file(p,".onnx")
        return {"onnx":str(f),"sha256":sha256(f),"bytes":f.stat().st_size}
    if number == 33:
        before=[43.0,42.3,45.2,44.0,43.5]
        after=[35.5,34.8,36.0,36.3,35.1]
        return {"before_ms":percentiles(before),"after_ms":percentiles(after),
                "mean_speedup":statistics.mean(before)/statistics.mean(after),
                "note":"synthetic latency inputs; NOT measured RK3588 FPS"}
    if number == 34:
        return {"models":[{"params_billion":p,"bits":b,
                            "weight_only_theoretical_GB":p*b/8}
                           for p,b in ((1.5,4),(3,4),(7,4))],
                "caveat":"excludes KV cache, scales, runtime workspace and Linux"}
    raise ValueError("unknown lesson: "+str(number))

def main(number=None):
    ap=argparse.ArgumentParser(description="RK3588 course runnable lab (not hardware benchmark)")
    if number is None:
        ap.add_argument("lesson",type=int,choices=range(35))
    ap.add_argument("--input",help="real file/directory for lessons that require it")
    ap.add_argument("--output",help="output file for code-generation lesson")
    args=ap.parse_args()
    n=number if number is not None else args.lesson
    try:
        result=exec_lesson(n,args)
        print(json.dumps({"lesson":n,"status":"ok","result":result},indent=2,
                         ensure_ascii=False,default=str))
    except (OSError,ValueError,RuntimeError) as exc:
        print(f"Lesson {n:02d} failed: {exc}",file=sys.stderr)
        sys.exit(2)

if __name__=="__main__":
    main()
