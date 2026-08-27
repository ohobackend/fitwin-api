import os
import sys
import threading
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
from typing import Iterator, Literal
from PIL import Image
from app.core.config import get_settings

OOTCategory = Literal["upperbody", "lowerbody", "dress"]
_cwd_lock = threading.Lock()

@contextmanager
def working_directory(path: Path) -> Iterator[None]:
    with _cwd_lock:
        previous = Path.cwd()
        os.chdir(path)
        try:
            yield
        finally:
            os.chdir(previous)

class OOTDiffusionRunner:
    """Thin wrapper around the official OOTDiffusion inference interface."""

    def __init__(self, repository_path: str | Path, gpu_id: int = 0, model_type: Literal["hd", "dc"] = "hd") -> None:
        self.root = Path(repository_path).resolve()
        self.run_dir = self.root / "run"
        if not (self.run_dir / "run_ootd.py").exists():
            raise RuntimeError(f"OOTDiffusion is not installed at {self.root}")
        for path in (self.root, self.run_dir):
            if str(path) not in sys.path:
                sys.path.insert(0, str(path))
        with working_directory(self.run_dir):
            from utils_ootd import get_mask_location
            from preprocess.openpose.run_openpose import OpenPose
            from preprocess.humanparsing.run_parsing import Parsing
            self.get_mask_location = get_mask_location
            self.openpose = OpenPose(gpu_id)
            self.parsing = Parsing(gpu_id)
            if model_type == "hd":
                from ootd.inference_ootd_hd import OOTDiffusionHD
                self.model = OOTDiffusionHD(gpu_id)
            else:
                from ootd.inference_ootd_dc import OOTDiffusionDC
                self.model = OOTDiffusionDC(gpu_id)
            self.model_type = model_type

    def infer(
        self, person_path: str | Path, garment_path: str | Path, *,
        model_type: Literal["hd", "dc"], category: OOTCategory,
        steps: int = 20, scale: float = 2.0, seed: int = -1,
    ) -> Image.Image:
        if model_type == "hd" and category != "upperbody":
            raise ValueError("OOTDiffusion HD supports upperbody garments only")
        if model_type != self.model_type:
            raise ValueError(f"Runner was initialized for {self.model_type}, not {model_type}")
        category_utils = {"upperbody": "upper_body", "lowerbody": "lower_body", "dress": "dresses"}
        with working_directory(self.run_dir):
            person = Image.open(person_path).convert("RGB").resize((768, 1024))
            garment = Image.open(garment_path).convert("RGB").resize((768, 1024))
            keypoints = self.openpose(person.resize((384, 512)))
            parsed, _ = self.parsing(person.resize((384, 512)))
            mask, mask_gray = self.get_mask_location(model_type, category_utils[category], parsed, keypoints)
            mask = mask.resize((768, 1024), Image.Resampling.NEAREST)
            mask_gray = mask_gray.resize((768, 1024), Image.Resampling.NEAREST)
            masked_person = Image.composite(mask_gray, person, mask)
            images = self.model(
                model_type=model_type, category=category, image_garm=garment,
                image_vton=masked_person, mask=mask, image_ori=person,
                num_samples=1, num_steps=steps, image_scale=scale, seed=seed,
            )
        if not images:
            raise RuntimeError("OOTDiffusion returned no images")
        return images[0]

@lru_cache(maxsize=1)
def get_ootdiffusion_runner(model_type: Literal["hd", "dc"]) -> OOTDiffusionRunner:
    settings = get_settings()
    return OOTDiffusionRunner(settings.ootdiffusion_path, settings.ootdiffusion_gpu_id, model_type)
