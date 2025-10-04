import os
import json
import base64
import hashlib
from typing import Dict, Any, Optional
import tempfile


def _get_secret() -> bytes:
    secret = os.getenv("CREDENTIALS_SECRET", "shrimp-dev-secret")
    return hashlib.sha256(secret.encode("utf-8")).digest()


def _xor_bytes(data: bytes, key: bytes) -> bytes:
    out = bytearray()
    for i, b in enumerate(data):
        out.append(b ^ key[i % len(key)])
    return bytes(out)


def encrypt_string(s: str) -> str:
    key = _get_secret()
    raw = s.encode("utf-8")
    xored = _xor_bytes(raw, key)
    return base64.urlsafe_b64encode(xored).decode("utf-8")


def decrypt_string(s: str) -> str:
    key = _get_secret()
    raw = base64.urlsafe_b64decode(s.encode("utf-8"))
    xored = _xor_bytes(raw, key)
    return xored.decode("utf-8")


def _cred_store_path() -> str:
    """获取加密凭据存储路径，带安全回退。

    优先使用项目下的 `./data/credentials.json.enc`，若无法创建目录
   （例如权限受限），回退到系统临时目录。
    """
    try:
        os.makedirs("./data", exist_ok=True)
        return os.path.join("./data", "credentials.json.enc")
    except Exception:
        tmpdir = tempfile.gettempdir()
        return os.path.join(tmpdir, "shrimp_credentials.json.enc")


def _cred_store_plain_path() -> str:
    """获取明文凭据存储路径（用于回退）。"""
    try:
        os.makedirs("./data", exist_ok=True)
        return os.path.join("./data", "credentials.json")
    except Exception:
        tmpdir = tempfile.gettempdir()
        return os.path.join(tmpdir, "shrimp_credentials.json")


def load_credentials(provider_id: str) -> Optional[Dict[str, Any]]:
    """加载凭据，支持加密与明文两种存储形式。"""
    # 先尝试加密存储
    path_enc = _cred_store_path()
    if os.path.exists(path_enc):
        try:
            with open(path_enc, "r", encoding="utf-8") as f:
                store = json.load(f)
            enc = store.get(provider_id)
            if enc:
                return json.loads(decrypt_string(enc))
        except Exception:
            pass
    # 回退尝试明文存储
    path_plain = _cred_store_plain_path()
    if os.path.exists(path_plain):
        try:
            with open(path_plain, "r", encoding="utf-8") as f:
                store_plain = json.load(f)
            plain = store_plain.get(provider_id)
            if plain:
                # 明文中保存的是 JSON 字符串
                return json.loads(plain)
        except Exception:
            pass
    return None


def save_credentials(provider_id: str, creds: Dict[str, Any]) -> bool:
    """保存凭据到安全存储。

    首选写入加密文件 `credentials.json.enc`，若失败则回退写入明文文件
    `credentials.json`，以避免环境文件系统限制导致 500 错误。
    """
    # 尝试读取已有加密存储
    path_enc = _cred_store_path()
    store_enc: Dict[str, str] = {}
    if os.path.exists(path_enc):
        try:
            with open(path_enc, "r", encoding="utf-8") as f:
                store_enc = json.load(f)
        except Exception:
            store_enc = {}

    # 先准备明文 JSON 字符串（可能包含非 ASCII）
    try:
        plaintext = json.dumps(creds, ensure_ascii=False)
    except Exception:
        # 序列化失败直接返回 False
        return False

    # 首选写入加密文件
    try:
        store_enc[provider_id] = encrypt_string(plaintext)
        with open(path_enc, "w", encoding="utf-8") as f:
            json.dump(store_enc, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        # 回退：写入明文文件，便于在受限环境下仍能持久化
        try:
            path_plain = _cred_store_plain_path()
            store_plain: Dict[str, str] = {}
            if os.path.exists(path_plain):
                try:
                    with open(path_plain, "r", encoding="utf-8") as f:
                        store_plain = json.load(f)
                except Exception:
                    store_plain = {}
            store_plain[provider_id] = plaintext
            with open(path_plain, "w", encoding="utf-8") as f:
                json.dump(store_plain, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False