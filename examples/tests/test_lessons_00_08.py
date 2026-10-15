"""Functional tests for rewritten lessons 00–08. No network/NPU/flash writes."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
def run_lesson(num,*args):
    return subprocess.run(
        [sys.executable,str(ROOT/"examples"/f"lesson_{num:02d}.py"),*map(str,args)],
        cwd=ROOT,text=True,capture_output=True,check=True,timeout=25)

class RewrittenEarlyLessons(unittest.TestCase):
    def test_00_environment_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"environment.json"
            model=Path(tmp)/"sample.rknn"
            model.write_bytes(b"synthetic fixture for hashing only")
            result=run_lesson(0,"--output",path,"--model",model)
            record=json.loads(path.read_text(encoding="utf8"))
            self.assertIn("Saved environment manifest",result.stdout)
            self.assertEqual(record["model"]["bytes"],model.stat().st_size)
            self.assertEqual(len(record["model"]["sha256"]),64)

    def test_01_board_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"board.json"
            run_lesson(1,"--output",path)
            record=json.loads(path.read_text(encoding="utf8"))
            self.assertIn("machine",record)
            self.assertIn("kernel",record)
            self.assertIn("meminfo",record)

    def test_02_convolution_numbers(self):
        result=run_lesson(2,"--height","4","--width","4",
                          "--in-channels","4","--out-channels","8",
                          "--kernel","3","--stride","1","--padding","1")
        data=json.loads(result.stdout)
        self.assertEqual(data["standard_conv"]["output"],[4,4,8])
        self.assertEqual(data["standard_conv"]["mac"],4*4*8*4*3*3)
        self.assertLess(data["depthwise_separable_mac"],data["standard_conv"]["mac"])

    def test_03_dependency_graph(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            status=p/"status.json"
            status.write_text('{"onnx":true,"convert":false}',encoding="utf8")
            output=p/"plan.dot"
            result=run_lesson(3,"--status",status,"--dot",output)
            self.assertIn("convert",json.JSONDecoder().raw_decode(result.stdout.lstrip())[0]["remaining"])
            graph=output.read_text(encoding="utf8")
            self.assertIn("digraph RKNN",graph)
            self.assertIn("onnx -> convert;",graph)

    def test_04_offline_repository_aliases(self):
        from examples import lesson_04
        self.assertIn("toolkit2",lesson_04.REPOS)
        self.assertIn("airockchip/rknn-toolkit2",lesson_04.REPOS["toolkit2"])
        result=run_lesson(4,"--help")
        self.assertIn("--repo",result.stdout)

    def test_05_toolkit_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"sdk.json"
            run_lesson(5,"--output",path)
            data=json.loads(path.read_text(encoding="utf8"))
            self.assertIn("abi",data)
            self.assertIn("rknn_module_found",data)

    def test_06_runtime_readonly(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"runtime.json"
            run_lesson(6,"--output",path)
            data=json.loads(path.read_text(encoding="utf8"))
            self.assertIn("runtime",data)
            self.assertIn("device_nodes",data)

    def test_07_frequency_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"measure.csv"
            run_lesson(7,"--samples","2","--interval","0","--output",path)
            content=path.read_text(encoding="utf8")
            self.assertIn("unix_time,sysfs_path,raw_value",content)

    @unittest.skipIf(sys.platform == "win32","Fixture executable relies on POSIX shebang")
    def test_08_executes_vendor_command_wrapper(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            fake=p/"fake_rknn_demo"
            fake.write_text("#!/usr/bin/env python3\nprint('fixture invocation successful')\n",
                            encoding="utf8")
            fake.chmod(0o755)
            model=p/"model.rknn"
            model.write_bytes(b"not a real model; command control flow fixture")
            image=p/"image.png"
            image.write_bytes(b"not a real image; command control flow fixture")
            output=p/"run.json"
            run_lesson(8,"--program",fake,"--model",model,
                       "--image",image,"--output",output)
            report=json.loads(output.read_text(encoding="utf8"))
            self.assertEqual(report["exit_code"],0)
            self.assertIn("fixture invocation successful",report["stdout"])
            self.assertTrue(report["is_real_external_execution"])

if __name__=="__main__":
    unittest.main()
