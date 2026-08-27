import json
import struct
from pathlib import Path

class InvalidGLBError(ValueError): pass

def validate_glb(path: str | Path) -> dict[str, int | str]:
    data = Path(path).read_bytes()
    if len(data) < 20 or data[:4] != b"glTF":
        raise InvalidGLBError("Missing GLB magic header")
    version, declared_length = struct.unpack_from("<II", data, 4)
    if version != 2 or declared_length != len(data):
        raise InvalidGLBError("GLB must be a complete glTF 2.0 binary")
    json_length, chunk_type = struct.unpack_from("<II", data, 12)
    if chunk_type != 0x4E4F534A or 20 + json_length > len(data):
        raise InvalidGLBError("GLB JSON chunk is invalid")
    document = json.loads(data[20:20 + json_length].decode("utf-8").rstrip(" \t\r\n\0"))
    if not str(document.get("asset", {}).get("version", "")).startswith("2"):
        raise InvalidGLBError("Asset is not glTF 2.0")
    meshes = document.get("meshes", [])
    if not meshes or not any(mesh.get("primitives") for mesh in meshes):
        raise InvalidGLBError("Asset contains no renderable mesh primitives")
    unsupported = set(document.get("extensionsRequired", [])) - {
        "KHR_materials_unlit", "KHR_materials_clearcoat", "KHR_materials_transmission",
        "KHR_materials_ior", "KHR_materials_specular", "KHR_texture_transform",
    }
    if unsupported:
        raise InvalidGLBError(f"Unsupported required extensions: {sorted(unsupported)}")
    return {"version": "2.0", "meshes": len(meshes), "materials": len(document.get("materials", []))}
