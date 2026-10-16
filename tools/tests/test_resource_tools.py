import hashlib
from pathlib import Path
import tempfile
import unittest

from tools.verify_assets import assess
from tools.bootstrap_host import OPTIONS,python_in_venv

class AssetTests(unittest.TestCase):
    def test_hash_and_missing(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);sample=root/"sample.bin";sample.write_bytes(b"fixture")
            expected=hashlib.sha256(sample.read_bytes()).hexdigest()
            record={"id":"fixture","local_path":"sample.bin","sha256":expected}
            self.assertTrue(assess(record,root)["trusted_hash_verified"])
            record["sha256"]="0"*64
            self.assertEqual(assess(record,root)["state"],"hash-mismatch")
            record["local_path"]="missing.bin"
            self.assertEqual(assess(record,root)["state"],"missing")
    def test_unsafe_relative_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                assess({"id":"unsafe","local_path":"../outside","sha256":None},Path(temp))
    def test_pc_requirements_exist(self):
        self.assertIn("core",OPTIONS)
        self.assertTrue(OPTIONS["core"].is_file())
        self.assertTrue(str(python_in_venv(Path(".venv"))).endswith(("python","python.exe")))

if __name__=="__main__":
    unittest.main()
