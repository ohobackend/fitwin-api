from uuid import UUID
from app.services.fitting_service import build_combination_hash

def test_same_fitting_inputs_have_same_cache_key() -> None:
    user_id = UUID("11111111-1111-1111-1111-111111111111")
    garment_id = UUID("22222222-2222-2222-2222-222222222222")
    first = build_combination_hash(user_id, garment_id, b"person-image", "upperbody", "hd")
    second = build_combination_hash(user_id, garment_id, b"person-image", "upperbody", "hd")
    assert first == second

def test_different_person_image_has_different_cache_key() -> None:
    user_id = UUID("11111111-1111-1111-1111-111111111111")
    garment_id = UUID("22222222-2222-2222-2222-222222222222")
    first = build_combination_hash(user_id, garment_id, b"person-a", "upperbody", "hd")
    second = build_combination_hash(user_id, garment_id, b"person-b", "upperbody", "hd")
    assert first != second
