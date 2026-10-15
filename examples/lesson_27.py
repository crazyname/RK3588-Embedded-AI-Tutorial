#!/usr/bin/env python3
"""Lesson 27: REAL MobileNet-style image classification with ONNX Runtime or RKNNLite.

Examples:
  python examples/lesson_27.py --backend onnx --model mobilenetv2-12.onnx \
      --image bell.jpg --labels synset.txt
  python examples/lesson_27.py --backend rknn --model mobilenetv2-12.rknn \
      --image bell.jpg --labels synset.txt

No pretrained weights or predictions are hardcoded. Requires the user's actual model.
ONNX runs on a host with numpy, Pillow, onnxruntime. RKNN requires a supported board,
matching RKNN-Toolkit-Lite2, NPU runtime/driver, and a compatible .rknn model.
"""
import argparse
import json
import math
from pathlib import Path
import statistics
import sys
import time


IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--backend", choices=("onnx", "rknn"), required=True,
                   help="ONNX Runtime on PC or RKNNLite on Rockchip board")
    p.add_argument("--model", type=Path, required=True, help="Real .onnx / .rknn classifier model")
    p.add_argument("--image", type=Path, required=True, help="Real image (.jpg/.png...)")
    p.add_argument("--labels", type=Path, help="Model's labels, one line per class")
    p.add_argument("--label-offset", type=int, default=0,
                   help="Label-file index offset; normally 0, sometimes 1 if file has background")
    p.add_argument("--width", type=int, default=224)
    p.add_argument("--height", type=int, default=224)
    p.add_argument("--resize", choices=("squash", "center-crop"), default="squash",
                   help="squash = resize directly like Model Zoo; center-crop = aspect preserving")
    p.add_argument("--color", choices=("RGB", "BGR"), default="RGB",
                   help="Explicit channel order; use the one matching your model conversion")
    p.add_argument("--layout", choices=("auto", "NCHW", "NHWC"), default="auto")
    p.add_argument("--normalize", choices=("auto", "imagenet", "none"), default="auto",
                   help="auto: ImageNet float for ONNX; raw uint8 for RKNN (configured in converter)")
    p.add_argument("--scores", choices=("logits", "probabilities", "auto"), default="logits",
                   help="How to interpret one-output classifier vector")
    p.add_argument("--topk", type=int, default=5)
    p.add_argument("--warmup", type=int, default=2)
    p.add_argument("--runs", type=int, default=5)
    p.add_argument("--output-json", type=Path, help="Save machine-readable result")
    p.add_argument("--output-npz", type=Path, help="Save actual raw output tensors")
    a = p.parse_args(argv)
    suffix = ".onnx" if a.backend == "onnx" else ".rknn"
    if a.model.suffix.lower() != suffix:
        p.error(f"{a.backend} backend requires a {suffix} model")
    if not a.model.is_file() or not a.image.is_file():
        p.error("The model and image must both exist")
    if a.labels is not None and not a.labels.is_file():
        p.error("The labels file does not exist")
    if a.topk < 1 or a.runs < 1 or a.warmup < 0 or a.width < 1 or a.height < 1:
        p.error("topk/runs/width/height must be positive; warmup must be nonnegative")
    if a.label_offset < 0:
        p.error("label-offset must be nonnegative")
    return a


def prepare_image(path, width, height, resize, color, layout, normalize, backend):
    """Read image and return contiguous model input, with explicit numeric transform."""
    import numpy as np
    from PIL import Image, ImageOps

    # Resolve the two deployment conventions explicitly, not by guessing tensor metadata.
    if layout == "auto":
        layout = "NCHW" if backend == "onnx" else "NHWC"
    if normalize == "auto":
        normalize = "imagenet" if backend == "onnx" else "none"

    with Image.open(path) as original:
        rgb = original.convert("RGB")
        if resize == "squash":
            rgb = rgb.resize((width, height), Image.Resampling.BILINEAR)
        else:
            rgb = ImageOps.fit(rgb, (width, height), method=Image.Resampling.BILINEAR,
                               centering=(0.5, 0.5))
        arr = np.asarray(rgb, dtype=np.uint8)
    if color == "BGR":
        arr = arr[:, :, ::-1]

    if normalize == "imagenet":
        if backend == "rknn":
            # Permitted for special RKNN models expecting float input, never presumed safe.
            raise ValueError("RKNN default expects raw uint8; use --normalize none or "
                             "prepare a specifically verified float-input model separately.")
        arr = arr.astype(np.float32) / np.float32(255.0)
        arr = (arr - np.asarray(IMAGENET_MEAN, dtype=np.float32)) / np.asarray(
            IMAGENET_STD, dtype=np.float32)
    elif backend == "onnx":
        # Tiny/experimental ONNX graphs may use raw float32 pixels.
        arr = arr.astype(np.float32)
    else:
        arr = np.ascontiguousarray(arr, dtype=np.uint8)

    if layout == "NCHW":
        arr = arr.transpose(2, 0, 1)
    return np.ascontiguousarray(arr[None, ...])


def read_labels(path, n_classes, offset=0):
    if path is None:
        return [str(i) for i in range(n_classes)]
    labels = [x.strip() for x in path.read_text(encoding="utf-8-sig").splitlines()]
    if len(labels) != n_classes + offset:
        raise ValueError(f"Label count {len(labels)} is incompatible with {n_classes} "
                         f"model classes and label-offset={offset}; do not guess labels")
    return labels[offset:]


def probabilities(values, mode="logits"):
    """Produce validated probabilities, never invent classes or confidence values."""
    import numpy as np
    v = np.asarray(values, dtype=np.float64)
    if v.ndim == 2 and v.shape[0] == 1:
        v = v[0]
    if v.ndim != 1 or v.size == 0:
        raise ValueError(f"Expected a [C] or [1,C] output, got {v.shape}")
    if not np.all(np.isfinite(v)):
        raise ValueError("Output scores contain NaN or infinity")
    looks_like_probs = bool(np.all(v >= 0) and abs(float(v.sum()) - 1.0) < 1e-4)
    if mode == "auto":
        mode = "probabilities" if looks_like_probs else "logits"
    if mode == "probabilities":
        if np.any(v < 0) or not np.isclose(v.sum(), 1.0, atol=1e-3):
            raise ValueError("Selected probabilities, but scores are not nonnegative and sum≈1")
        return v / v.sum()
    ex = np.exp(v - np.max(v))
    return ex / np.sum(ex)


def run_model(args, x):
    """Return real output tensors, inference-call latency samples, model I/O metadata."""
    import numpy as np

    if args.backend == "onnx":
        try:
            import onnxruntime as ort
        except ImportError as exc:
            raise RuntimeError("Install ONNX Runtime: pip install onnxruntime") from exc
        sess = ort.InferenceSession(str(args.model), providers=["CPUExecutionProvider"])
        ins = sess.get_inputs()
        if len(ins) != 1:
            raise ValueError("This standalone lesson supports one-input classifiers only")
        spec = ins[0]
        expected_type = "tensor(float)" if x.dtype == np.float32 else "tensor(uint8)"
        if spec.type != expected_type:
            raise ValueError(f"Model expects {spec.type} but input is {expected_type}")
        for dim, got in zip(spec.shape, x.shape):
            if isinstance(dim, int) and dim > 0 and dim != got:
                raise ValueError(f"Model expects input {spec.shape}, got {x.shape}")
        infer = lambda: sess.run(None, {spec.name: x})
        io = {"input_name": spec.name, "input_shape": list(x.shape),
              "output_names": [out.name for out in sess.get_outputs()]}
        release = lambda: None
    else:
        try:
            from rknnlite.api import RKNNLite
        except ImportError as exc:
            raise RuntimeError("RKNNLite unavailable. Run on supported Rockchip board "
                               "with matching Toolkit-Lite2/Runtime/driver.") from exc
        lite = RKNNLite()
        try:
            rc = lite.load_rknn(str(args.model))
            if rc != 0:
                raise RuntimeError(f"load_rknn failed, code {rc}")
            rc = lite.init_runtime()
            if rc != 0:
                raise RuntimeError(f"init_runtime failed, code {rc}")
        except BaseException:
            lite.release()
            raise
        infer = lambda: lite.inference(inputs=[x])
        io = {"input_shape": list(x.shape), "input_dtype": str(x.dtype),
              "note": "RKNN input tensor details must match the exact conversion config"}
        release = lite.release

    try:
        for _ in range(args.warmup):
            if infer() is None:
                raise RuntimeError("Warm-up inference returned None")
        samples = []
        outputs = None
        for _ in range(args.runs):
            t0 = time.perf_counter()
            outputs = infer()
            samples.append((time.perf_counter() - t0) * 1000.0)
            if outputs is None:
                raise RuntimeError("Model inference returned None")
        if len(outputs) != 1:
            raise ValueError(f"Expected one classifier output, got {len(outputs)} tensors")
        return [np.asarray(o).copy() for o in outputs], samples, io
    finally:
        release()


def classify(args):
    import numpy as np
    t0 = time.perf_counter()
    tensor = prepare_image(args.image, args.width, args.height, args.resize,
                           args.color, args.layout, args.normalize, args.backend)
    preprocess_ms = (time.perf_counter() - t0) * 1000
    raw, samples, io = run_model(args, tensor)
    prob = probabilities(raw[0], args.scores)
    labels = read_labels(args.labels, int(prob.size), args.label_offset)
    order = np.argsort(-prob, kind="stable")[:min(args.topk, int(prob.size))]
    topk = [{"class_id": int(i), "label": labels[int(i)], "score": float(prob[i])}
            for i in order]
    report = {
        "backend": args.backend, "model": str(args.model), "image": str(args.image),
        "input_shape": list(tensor.shape), "input_dtype": str(tensor.dtype),
        "resize": args.resize, "color": args.color,
        "layout": args.layout if args.layout != "auto" else (
            "NCHW" if args.backend == "onnx" else "NHWC"),
        "normalization": args.normalize if args.normalize != "auto" else (
            "imagenet" if args.backend == "onnx" else "none"),
        "model_io": io, "topk": topk, "preprocess_ms": preprocess_ms,
        "inference_call_ms": {
            "runs": len(samples), "mean": statistics.mean(samples),
            "median": statistics.median(samples),
            "min": min(samples), "max": max(samples)
        },
        "timing_note": "Inference-call only, not total camera/display FPS"
    }
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                                    encoding="utf-8")
    if args.output_npz:
        args.output_npz.parent.mkdir(parents=True, exist_ok=True)
        np.savez(args.output_npz, **{f"output_{i}": o for i, o in enumerate(raw)})
    return report


def main(argv=None):
    args = parse_args(argv)
    try:
        report = classify(args)
    except (OSError, RuntimeError, ValueError, ImportError) as exc:
        print(f"Lesson 27 failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
