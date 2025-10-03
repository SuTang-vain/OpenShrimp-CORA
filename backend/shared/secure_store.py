import os
import json
import base64
import hashlib
from typing import Dict, Any, Optional


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
    os.makedirs("./data", exist_ok=True)
    return os.path.join("./data", "credentials.json.enc")


def load_credentials(provider_id: str) -> Optional[Dict[str, Any]]:
    path = _cred_store_path()
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            store = json.load(f)
        enc = store.get(provider_id)
        if not enc:
            return None
        return json.loads(decrypt_string(enc))
    except Exception:
        return None


def save_credentials(provider_id: str, creds: Dict[str, Any]) -> bool:
    path = _cred_store_path()
    store: Dict[str, str] = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                store = json.load(f)
        except Exception:
            store = {}
    try:
        plaintext = json.dumps(creds, ensure_ascii=False)
        store[provider_id] = encrypt_string(plaintext)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(store, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False