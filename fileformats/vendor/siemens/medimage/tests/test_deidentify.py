import pytest
from fileformats.core.exceptions import FileFormatsExtrasError
from fileformats.vendor.siemens.medimage import SyngoMi_Vr20b_Sinogram


@pytest.mark.xfail(reason="Deidentification not implemented yet", strict=True)
def test_raw_pet_data_deidentify(tmp_path):
    raw_pet = SyngoMi_Vr20b_Sinogram.sample()
    raw_pet.deidentify(tmp_path)
