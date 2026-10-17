"""RKLLM C API demo contract tests, linked to an EXPLICIT fake runtime.

No real RK3588, NPU runtime, or model inference happens in this test.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[4]
BINARY=ROOT/"build/rkllm-fake/rkllm_stream_mock"

class RKLLMNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not BINARY.is_file():
            raise unittest.SkipTest("Build C++ mock binary first; required in CI step")
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.p=Path(self.tmp.name)
        self.model=self.p/"fake_model.rkllm"
        self.model.write_bytes(b"TEST FIXTURE NOT A REAL RKLLM MODEL")
        self.prompt=self.p/"prompt"
        self.prompt.write_text("What is 2 + 2?",encoding="utf8")
        self.report=self.p/"result.json"
    def run_demo(self,*args,env=None):
        config=os.environ.copy()
        for k in ("RKLLM_TEST_INIT_FAILURE","RKLLM_TEST_RUN_FAILURE","RKLLM_TEST_NO_PERF"):
            config.pop(k,None)
        config.update(env or {})
        return subprocess.run([str(BINARY),"--model",str(self.model),
              "--prompt-file",str(self.prompt),"--report",str(self.report),*args],
              capture_output=True,text=True,env=config,timeout=10)
    def test_stream_callback_and_sdk_tokens(self):
        p=self.run_demo()
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn("hello world",p.stdout)
        data=json.loads(self.report.read_text(encoding="utf8"))
        self.assertEqual(data["backend"],"RKLLM C API")
        self.assertEqual(data["max_new_tokens"],128)
        self.assertEqual(data["context_tokens"],2048)
        self.assertEqual(data["model_size_bytes"],self.model.stat().st_size)
        self.assertEqual(data["text_chunks"],2)
        self.assertEqual(data["output_utf8_bytes"],11)
        self.assertTrue(data["finished_callback"])
        self.assertGreaterEqual(data["first_text_chunk_ms"],0)
        self.assertEqual(data["sdk_generate_tokens"],5)
        self.assertEqual(data["sdk_tokens_per_sec"],50)
        self.assertEqual(data["sdk_peak_memory_mb"],128)
        self.assertNotIn("generated_text",data)
    def test_generated_text_requires_explicit_opt_in(self):
        self.assertEqual(self.run_demo("--save-text").returncode,0)
        data=json.loads(self.report.read_text(encoding="utf8"))
        self.assertEqual(data["generated_text"],"hello world")
    def test_zero_perf_must_not_fabricate_tokens(self):
        p=self.run_demo(env={"RKLLM_TEST_NO_PERF":"1"})
        self.assertEqual(p.returncode,0,p.stderr)
        data=json.loads(self.report.read_text(encoding="utf8"))
        self.assertIsNone(data["sdk_generate_tokens"])
        self.assertIsNone(data["sdk_tokens_per_sec"])
    def test_callback_runtime_error(self):
        p=self.run_demo(env={"RKLLM_TEST_RUN_FAILURE":"1"})
        self.assertNotEqual(p.returncode,0)
        data=json.loads(self.report.read_text(encoding="utf8"))
        self.assertTrue(data["callback_error"])
        self.assertFalse(data["finished_callback"])
        self.assertNotEqual(data["run_status"],0)
    def test_init_failure_and_missing_prompt(self):
        p=self.run_demo(env={"RKLLM_TEST_INIT_FAILURE":"1"})
        self.assertNotEqual(p.returncode,0)
        self.assertIn("rkllm_init",p.stderr)
        self.prompt.unlink()
        p=self.run_demo()
        self.assertNotEqual(p.returncode,0)
        self.assertIn("Prompt",p.stderr)
    def test_invalid_options(self):
        self.assertNotEqual(self.run_demo("--max-new","0").returncode,0)
        self.assertNotEqual(self.run_demo("--context","0").returncode,0)
        self.assertNotEqual(self.run_demo("--unknown","argument").returncode,0)
        result=subprocess.run([str(BINARY),"--help"],capture_output=True,text=True)
        self.assertEqual(result.returncode,0)
        self.assertIn("usage:",result.stdout)

if __name__=="__main__":
    unittest.main()
