import sys
from functools import lru_cache
from pathlib import Path
from PIL import Image
from app.core.config import get_settings

class TrellisRunner:
    """Wrapper for Microsoft's official TRELLIS image-to-3D pipeline."""

    def __init__(self, repository_path: str | Path, model_id: str) -> None:
        root = Path(repository_path).resolve()
        if not (root / "trellis").is_dir():
            raise RuntimeError(f"TRELLIS is not installed at {root}")
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from trellis.pipelines import TrellisImageTo3DPipeline
        self.pipeline = TrellisImageTo3DPipeline.from_pretrained(model_id)
        self.pipeline.cuda()

    def generate_glb(
        self, image_path: str | Path, output_path: str | Path, *, seed: int,
        simplify: float, texture_size: int,
    ) -> Path:
        from trellis.utils import postprocessing_utils
        image = Image.open(image_path).convert("RGBA")
        outputs = self.pipeline.run(image, seed=seed)
        glb = postprocessing_utils.to_glb(
            outputs["gaussian"][0], outputs["mesh"][0],
            simplify=simplify, texture_size=texture_size,
        )
        target = Path(output_path)
        glb.export(str(target))
        return target

@lru_cache(maxsize=1)
def get_trellis_runner() -> TrellisRunner:
    settings = get_settings()
    return TrellisRunner(settings.trellis_path, settings.trellis_model_id)
