import json
import struct
import pytest
from app.services.glb_validator import InvalidGLBError, validate_glb

def make_glb(document: dict) -> bytes:
    payload = json.dumps(document).encode()
    payload += b" " * ((4 - len(payload) % 4) % 4)
    length = 20 + len(payload)
    return b"glTF" + struct.pack("<II", 2, length) + struct.pack("<II", len(payload), 0x4E4F534A) + payload

def test_web_compatible_glb_is_accepted(tmp_path) -> None:
    path = tmp_path / "asset.glb"
    path.write_bytes(make_glb({"asset": {"version": "2.0"}, "meshes": [{"primitives": [{}]}]}))
    assert validate_glb(path)["meshes"] == 1

def test_glb_without_mesh_is_rejected(tmp_path) -> None:
    path = tmp_path / "empty.glb"
    path.write_bytes(make_glb({"asset": {"version": "2.0"}}))
    with pytest.raises(InvalidGLBError):
        validate_glb(path)
