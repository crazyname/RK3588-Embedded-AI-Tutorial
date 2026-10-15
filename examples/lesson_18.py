#!/usr/bin/env python3
"""第18讲：使用 AES128 Fernet 封装加密任意模型文件，明确非 RKNN 原生加密格式。"""
import argparse,os
from pathlib import Path
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("action",choices=("generate-key","encrypt","decrypt"))
    p.add_argument("--input",type=Path);p.add_argument("--output",type=Path)
    p.add_argument("--key-file",type=Path,required=True,help="测试密钥文件，不上传 Git")
    a=p.parse_args()
    try:from cryptography.fernet import Fernet,InvalidToken
    except ImportError:p.error("Install cryptography with: pip install cryptography")
    if a.action=="generate-key":
        if a.key_file.exists():p.error("Refusing to overwrite existing key")
        a.key_file.parent.mkdir(parents=True,exist_ok=True)
        fd=os.open(a.key_file,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,"wb") as f:f.write(Fernet.generate_key())
        print("Wrote protected test key:",a.key_file)
        return
    if a.input is None or a.output is None or not a.input.is_file():p.error("--input and --output required")
    if not a.key_file.is_file():p.error("key file missing")
    box=Fernet(a.key_file.read_bytes().strip())
    data=a.input.read_bytes()
    try:result=box.encrypt(data) if a.action=="encrypt" else box.decrypt(data)
    except InvalidToken:raise SystemExit("Authentication failed: wrong key or changed data")
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(result)
    print(f"{a.action} succeeded: {len(result)} bytes to {a.output}")
    print("This is an application-level envelope; encrypted file CANNOT be loaded directly by RKNN Runtime.")
if __name__=="__main__":main()
