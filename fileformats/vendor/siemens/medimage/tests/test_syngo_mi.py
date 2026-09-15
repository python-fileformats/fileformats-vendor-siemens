import pytest

from fileformats.core.exceptions import FormatMismatchError
from fileformats.vendor.siemens.medimage import SyngoMi_Vr20b_Sinogram


@pytest.mark.parametrize(
    "image_type",
    ["PET_EM_SINOGRAM", "PET_SINO_GATED_RESPIRATORY"],
)
def test_siemens_pet_sinogram_image_types(monkeypatch, image_type):
    sample = SyngoMi_Vr20b_Sinogram.sample()
    monkeypatch.setattr(
        SyngoMi_Vr20b_Sinogram,
        "read_tag",
        lambda self, tag: f"ORIGINAL\\PRIMARY\\{image_type}",
    )

    sinograms, unmatched = SyngoMi_Vr20b_Sinogram.from_paths([sample.fspath])

    assert not unmatched
    assert {sinogram.image_type for sinogram in sinograms} == {image_type}


def test_siemens_pet_sinogram_rejects_unknown_image_type(monkeypatch):
    sample = SyngoMi_Vr20b_Sinogram.sample()
    monkeypatch.setattr(
        SyngoMi_Vr20b_Sinogram,
        "read_tag",
        lambda self, tag: "ORIGINAL\\PRIMARY\\NOT_A_SINOGRAM",
    )

    with pytest.raises(FormatMismatchError):
        SyngoMi_Vr20b_Sinogram(sample.fspath)
