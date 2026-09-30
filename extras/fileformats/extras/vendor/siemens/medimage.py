import os
import sys
import typing as ty
from collections import Counter
from pathlib import Path

import pydicom
from fileformats.core import FileSet, Loaded, SampleFileGenerator, extra_implementation
from fileformats.core.io import BinaryIOWindow
from fileformats.medimage.base import MedicalImagingData
from fileformats.medimage.dicom import DicomImage
from medimages4tests.dummy.raw.pet.siemens.biograph_vision.vr20b.pet_calibration import (
    get_data as get_pet_calibration_data,
)
from medimages4tests.dummy.raw.pet.siemens.biograph_vision.vr20b.pet_countrate import (
    get_data as get_pet_countrate_data,
)
from medimages4tests.dummy.raw.pet.siemens.biograph_vision.vr20b.pet_dynamics_sino import (
    get_data as get_pet_dynamics_sino_data,
)
from medimages4tests.dummy.raw.pet.siemens.biograph_vision.vr20b.pet_em_sino import (
    get_data as get_pet_sinogram_data,
)
from medimages4tests.dummy.raw.pet.siemens.biograph_vision.vr20b.pet_listmode import (
    get_data as get_pet_listmode_data,
)
from medimages4tests.dummy.raw.pet.siemens.biograph_vision.vr20b.pet_replay_param import (
    get_data as get_pet_replay_param_data,
)
from medimages4tests.dummy.raw.pet.siemens.biograph_vision.vr20b.petct_spl import (
    get_data as get_petct_spl_data,
)

from fileformats.vendor.siemens.medimage import (
    SyngoMi_Vr20b_CountRate,
    SyngoMi_Vr20b_CtSpl,
    SyngoMi_Vr20b_DynamicSinogramSeries,
    SyngoMi_Vr20b_LargeRawData,
    SyngoMi_Vr20b_ListMode,
    SyngoMi_Vr20b_Normalisation,
    SyngoMi_Vr20b_Parameterisation,
    SyngoMi_Vr20b_RawData,
    SyngoMi_Vr20b_Sinogram,
    SyngoMr_Xa_Puls,
    SyngoMr_Xa_Rda,
    SyngoMr_Xa_Twix,
)

if sys.version_info >= (3, 9):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

TagListType: TypeAlias = ty.Union[
    ty.List[int],
    ty.List[str],
    ty.List[ty.Tuple[int, int]],
    ty.List[pydicom.tag.BaseTag],
]


@extra_implementation(FileSet.read_metadata)
def siemens_pet_raw_data_read_metadata(
    pet_raw_data: SyngoMi_Vr20b_LargeRawData,
    specific_tags: ty.Optional[TagListType] = None,
    **kwargs: ty.Any,
) -> ty.Mapping[str, ty.Any]:

    with pet_raw_data.open() as f:
        window = BinaryIOWindow(
            f,  # type: ignore[arg-type]
            pet_raw_data.dicom_header_offset,
            pet_raw_data.dcm_hdr_size_int_offset,
        )
        dcm = pydicom.dcmread(window, specific_tags=specific_tags)
    return DicomImage.pydicom_to_dict(dcm)  # type: ignore[no-any-return]


@extra_implementation(SyngoMi_Vr20b_RawData.load_pydicom)
def siemens_pet_raw_data_load_pydicom(
    pet_raw_data: SyngoMi_Vr20b_LargeRawData,
    specific_tags: ty.Optional[TagListType] = None,
    **kwargs: ty.Any,
) -> pydicom.Dataset:

    with pet_raw_data.open() as f:
        window = BinaryIOWindow(
            f,  # type: ignore[arg-type]
            pet_raw_data.dicom_header_offset,
            pet_raw_data.dcm_hdr_size_int_offset,
        )
        dcm = pydicom.dcmread(window, specific_tags=specific_tags)
    return dcm


@extra_implementation(FileSet.read_metadata)
def siemens_petct_raw_data_read_metadata(
    pet_raw_data: SyngoMi_Vr20b_CtSpl,
    specific_tags: ty.Optional[TagListType] = None,
    **kwargs: ty.Any,
) -> ty.Mapping[str, ty.Any]:

    with pet_raw_data.open() as f:
        window = BinaryIOWindow(
            f,  # type: ignore[arg-type]
            *pet_raw_data.dicom_header_limits,
        )
        dcm = pydicom.dcmread(window, specific_tags=specific_tags)
    return DicomImage.pydicom_to_dict(dcm)  # type: ignore[no-any-return]


@extra_implementation(SyngoMi_Vr20b_RawData.load_pydicom)
def siemens_petct_raw_data_load_pydicom(
    pet_raw_data: SyngoMi_Vr20b_CtSpl,
    specific_tags: ty.Optional[TagListType] = None,
    **kwargs: ty.Any,
) -> pydicom.Dataset:

    with pet_raw_data.open() as f:
        window = BinaryIOWindow(
            f,  # type: ignore[arg-type]
            *pet_raw_data.dicom_header_limits,
        )
        dcm = pydicom.dcmread(window, specific_tags=specific_tags)
    return dcm


@extra_implementation(FileSet.read_metadata)
def siemens_pet_dynamic_sinogram_series_read_metadata(
    pet_raw_data: SyngoMi_Vr20b_DynamicSinogramSeries,
    specific_tags: ty.Optional[TagListType] = None,
    **kwargs: ty.Any,
) -> ty.Mapping[str, ty.Any]:

    # Collated DICOM headers across series
    collated: ty.Dict[str, ty.Any] = {}
    key_repeats: ty.Counter[str] = Counter()
    varying_keys = set()
    # We use the "contents" property implementation in TypeSet instead of the overload
    # in DicomCollection because we don't want the metadata to be read ahead of the
    # the `select_metadata` call below

    for ptd in pet_raw_data.contents:
        for key, val in ptd.metadata.items():
            try:
                prev_val = collated[key]
            except KeyError:
                collated[key] = (
                    val  # Insert initial value (should only happen on first iter)
                )
                key_repeats.update([key])
            else:
                if key in varying_keys:
                    collated[key].append(val)
                # Check whether the value is the same as the values in the previous
                # images in the series
                elif val != prev_val:
                    collated[key] = [prev_val] * key_repeats[key] + [val]
                    varying_keys.add(key)
                else:
                    key_repeats.update([key])
    return collated


@extra_implementation(FileSet.generate_sample_data)
def siemens_pet_listmode_generate_sample_data(
    pet_raw_data: SyngoMi_Vr20b_ListMode,
    generator: SampleFileGenerator,
) -> ty.List[Path]:
    return get_pet_listmode_data(out_dir=generator.dest_dir)  # type: ignore[no-any-return]


@extra_implementation(FileSet.generate_sample_data)
def siemens_pet_countrate_generate_sample_data(
    pet_raw_data: SyngoMi_Vr20b_CountRate,
    generator: SampleFileGenerator,
) -> ty.List[Path]:
    return get_pet_countrate_data(out_dir=generator.dest_dir)  # type: ignore[no-any-return]


@extra_implementation(FileSet.generate_sample_data)
def siemens_pet_sinogram_generate_sample_data(
    pet_raw_data: SyngoMi_Vr20b_Sinogram,
    generator: SampleFileGenerator,
) -> ty.List[Path]:
    return get_pet_sinogram_data(out_dir=generator.dest_dir)  # type: ignore[no-any-return]


@extra_implementation(FileSet.generate_sample_data)
def siemens_pet_dynamics_sino_generate_sample_data(
    pet_raw_data: SyngoMi_Vr20b_DynamicSinogramSeries,
    generator: SampleFileGenerator,
) -> ty.List[Path]:
    return get_pet_dynamics_sino_data(out_dir=generator.dest_dir)  # type: ignore[no-any-return]


@extra_implementation(FileSet.generate_sample_data)
def siemens_pet_normalisation_generate_sample_data(
    pet_raw_data: SyngoMi_Vr20b_Normalisation,
    generator: SampleFileGenerator,
) -> ty.List[Path]:
    return get_pet_calibration_data(out_dir=generator.dest_dir)  # type: ignore[no-any-return]


@extra_implementation(FileSet.generate_sample_data)
def siemens_petct_spl_generate_sample_data(
    pet_raw_data: SyngoMi_Vr20b_CtSpl,
    generator: SampleFileGenerator,
) -> ty.List[Path]:
    return get_petct_spl_data(out_dir=generator.dest_dir)  # type: ignore[no-any-return]


@extra_implementation(FileSet.generate_sample_data)
def siemens_pet_parameterisation_generate_sample_data(
    pet_raw_data: SyngoMi_Vr20b_Parameterisation,
    generator: SampleFileGenerator,
) -> ty.List[Path]:
    return get_pet_replay_param_data(out_dir=generator.dest_dir)  # type: ignore[no-any-return]


@extra_implementation(FileSet.read_metadata)
def siemens_rda_read_metadata(
    rda: SyngoMr_Xa_Rda,
    **kwargs: ty.Any,
) -> ty.Mapping[str, ty.Any]:
    HEADER_END = b">>> End of header <<<"
    raw = rda.read_contents()
    end_idx = raw.find(HEADER_END)
    if end_idx == -1:
        return {}
    header_text = raw[:end_idx].decode("latin-1")
    metadata: ty.Dict[str, ty.Any] = {}
    for line in header_text.splitlines():
        if line.startswith(">>>"):
            continue
        if ": " in line:
            key, value = line.split(": ", 1)
            metadata[key.strip()] = value.strip()
    return metadata


@extra_implementation(FileSet.read_metadata)
def siemens_puls_read_metadata(
    puls: SyngoMr_Xa_Puls,
    **kwargs: ty.Any,
) -> ty.Mapping[str, ty.Any]:
    text = puls.read_contents()
    metadata: ty.Dict[str, ty.Any] = {}
    for line in text.splitlines():
        line = line.strip()
        # Based off of one example file, ends in 6003
        if not line or line == "6003":
            continue
        if ": " in line:
            key, value = line.split(": ", 1)
            metadata[key.strip()] = value.strip()
    return metadata


@extra_implementation(SyngoMr_Xa_Twix.read_twix)
def twix_raw_data_read_twix(
    twix_data: SyngoMr_Xa_Twix,
    **kwargs: ty.Any,
) -> ty.Any:
    import twixtools

    return twixtools.read_twix(str(twix_data.fspath), **kwargs)


@extra_implementation(SyngoMr_Xa_Twix.map_twix)
def twix_raw_data_map_twix(
    twix_data: SyngoMr_Xa_Twix,
    **kwargs: ty.Any,
) -> ty.Any:
    import twixtools

    return twixtools.map_twix(str(twix_data.fspath), **kwargs)


@extra_implementation(FileSet.read_metadata)
def twix_raw_data_read_metadata(
    twix_data: SyngoMr_Xa_Twix,
    **kwargs: ty.Any,
) -> ty.Mapping[str, ty.Any]:
    import twixtools

    scans = twixtools.read_twix(str(twix_data.fspath), parse_data=False, verbose=False)
    # Return the parsed protocol headers from the last measurement (the actual scan)
    return scans[-1].get("hdr", {})  # type: ignore[no-any-return]


@extra_implementation(MedicalImagingData.deidentify)
def siemens_rda_read_deidentify(
    rda: SyngoMr_Xa_Rda,
    out_dir: os.PathLike[str],
    # TODO: narrow to the recipe format once implemented
    recipe: Loaded[FileSet] | None = None,
    **kwargs: ty.Any,
) -> SyngoMr_Xa_Rda:
    raise NotImplementedError


@extra_implementation(MedicalImagingData.deidentify)
def twix_raw_data_deidentify(
    twix_data: SyngoMr_Xa_Twix,
    out_dir: os.PathLike[str],
    # TODO: narrow to the recipe format once implemented
    recipe: Loaded[FileSet] | None = None,
    **kwargs: ty.Any,
) -> SyngoMr_Xa_Twix:
    raise NotImplementedError


@extra_implementation(MedicalImagingData.deidentify)
def siemens_puls_read_deidentify(
    puls: SyngoMr_Xa_Puls,
    out_dir: os.PathLike[str],
    # TODO: narrow to the recipe format once implemented
    recipe: Loaded[FileSet] | None = None,
    **kwargs: ty.Any,
) -> SyngoMr_Xa_Puls:
    raise NotImplementedError
