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
    chunks: list[tuple[int, bytes]] = []
    offset = 12
    while offset < len(data):
        if offset + 8 > len(data):
            raise InvalidGLBError("GLB chunk header is truncated")
        chunk_length, chunk_type = struct.unpack_from("<II", data, offset)
        chunk_end = offset + 8 + chunk_length
        if chunk_length % 4 or chunk_end > len(data):
            raise InvalidGLBError("GLB chunk is truncated or misaligned")
        chunks.append((chunk_type, data[offset + 8:chunk_end]))
        offset = chunk_end
    if not chunks or chunks[0][0] != 0x4E4F534A:
        raise InvalidGLBError("GLB JSON chunk is missing")
    try:
        document = json.loads(chunks[0][1].decode("utf-8").rstrip(" \t\r\n\0"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidGLBError("GLB JSON chunk is corrupt") from exc
    if not str(document.get("asset", {}).get("version", "")).startswith("2"):
        raise InvalidGLBError("Asset is not glTF 2.0")
    meshes = document.get("meshes", [])
    if not meshes or not any(mesh.get("primitives") for mesh in meshes):
        raise InvalidGLBError("Asset contains no renderable mesh primitives")
    accessors = document.get("accessors", [])
    for mesh in meshes:
        for primitive in mesh.get("primitives", []):
            position_index = primitive.get("attributes", {}).get("POSITION")
            if not isinstance(position_index, int) or position_index >= len(accessors):
                raise InvalidGLBError("Mesh primitive has no valid POSITION accessor")
            if accessors[position_index].get("count", 0) < 3:
                raise InvalidGLBError("Mesh primitive has insufficient vertices")
    binary_chunks = [payload for kind, payload in chunks if kind == 0x004E4942]
    embedded_buffers = [item for item in document.get("buffers", []) if "uri" not in item]
    if embedded_buffers and (
        not binary_chunks or embedded_buffers[0].get("byteLength", 0) > len(binary_chunks[0])
    ):
        raise InvalidGLBError("Embedded binary buffer is missing or truncated")
    unsupported = set(document.get("extensionsRequired", [])) - {
        "KHR_materials_unlit", "KHR_materials_clearcoat", "KHR_materials_transmission",
        "KHR_materials_ior", "KHR_materials_specular", "KHR_texture_transform",
    }
    if unsupported:
        raise InvalidGLBError(f"Unsupported required extensions: {sorted(unsupported)}")
    return {"version": "2.0", "meshes": len(meshes), "materials": len(document.get("materials", []))}
