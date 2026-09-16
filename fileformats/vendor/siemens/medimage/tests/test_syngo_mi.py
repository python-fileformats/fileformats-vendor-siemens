import pytest

from fileformats.core.exceptions import FormatMismatchError
from fileformats.vendor.siemens.medimage import (
    SyngoMi_Vr20b_RespiratoryGatedSinogram,
    SyngoMi_Vr20b_Sinogram,
)


def test_siemens_respiratory_gated_sinogram_grouping(monkeypatch):
    sample = SyngoMi_Vr20b_Sinogram.sample()
    monkeypatch.setattr(
        SyngoMi_Vr20b_RespiratoryGatedSinogram,
        "read_tag",
        lambda self, tag: "ORIGINAL\\PRIMARY\\PET_SINO_GATED_RESPIRATORY",
    )

    sinograms, unmatched = SyngoMi_Vr20b_RespiratoryGatedSinogram.from_paths(
        [sample.fspath]
    )

    assert not unmatched
    assert {type(sinogram) for sinogram in sinograms} == {
        SyngoMi_Vr20b_RespiratoryGatedSinogram
    }


def test_siemens_pet_sinogram_rejects_respiratory_gated_type(monkeypatch):
    sample = SyngoMi_Vr20b_Sinogram.sample()
    monkeypatch.setattr(
        SyngoMi_Vr20b_Sinogram,
        "read_tag",
        lambda self, tag: "ORIGINAL\\PRIMARY\\PET_SINO_GATED_RESPIRATORY",
    )

    with pytest.raises(FormatMismatchError):
        SyngoMi_Vr20b_Sinogram(sample.fspath)
