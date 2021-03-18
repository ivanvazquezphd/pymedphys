# Copyright (C) 2019 Cancer Care Associates
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import collections
import copy
import datetime
import random
from typing import Iterable

from pymedphys._imports import pydicom  # pylint: disable = unused-import

from pymedphys._dicom.constants.uuid import PYMEDPHYS_ROOT_UID


def extend(ct_datasets: Iterable["pydicom.Dataset"], number_of_slices: int):
    """Duplicates the superior and inferior slices of a Series of CT Datasets.




    Parameters
    ----------
    ct_datasets : An iterable of ``pydicom.Dataset``s
        [description]
    number_of_slices : int
        [description]

    Returns
    -------
    [type]
        [description]
    """

    ct_datasets = _convert_datasets_to_deque(ct_datasets)
    _extend_datasets(ct_datasets, 0, number_of_slices)
    _extend_datasets(ct_datasets, -1, number_of_slices)

    return ct_datasets


def _extend_datasets(dicom_datasets, index_to_copy, number_of_slices, uids=None):
    _copy_slices_and_append(dicom_datasets, index_to_copy, number_of_slices)
    _refresh_instance_numbers(dicom_datasets)
    _generate_new_uids(dicom_datasets, uids=uids)


def _convert_datasets_to_deque(datasets):
    dicom_datasets = collections.deque()

    for dicom_dataset in sorted(datasets, key=_slice_location):
        dicom_datasets.append(dicom_dataset)

    return dicom_datasets


def _slice_location(dicom_dataset):
    return float(dicom_dataset.SliceLocation)


def _copy_slices_and_append(dicom_datasets, index_to_copy, number_of_slices):
    append_method = _get_append_method(dicom_datasets, index_to_copy)
    new_slice_locations = _generate_new_slice_locations(
        dicom_datasets, index_to_copy, number_of_slices
    )

    dataset_to_copy = copy.deepcopy(dicom_datasets[index_to_copy])

    append = getattr(dicom_datasets, append_method)

    for a_slice_location in new_slice_locations:
        new_slice = copy.deepcopy(dataset_to_copy)

        new_slice.SliceLocation = str(a_slice_location)

        image_position_patient_to_copy = copy.deepcopy(
            dicom_datasets[index_to_copy].ImagePositionPatient
        )
        image_position_patient_to_copy[-1] = str(a_slice_location)
        new_slice.ImagePositionPatient = image_position_patient_to_copy

        append(new_slice)


def _refresh_instance_numbers(dicom_datasets):
    for i, dicom_dataset in enumerate(dicom_datasets):
        dicom_dataset.InstanceNumber = str(i)


def _generate_new_uids(dicom_datasets, uids=None):
    if uids is None:
        uids = _generate_uids(len(dicom_datasets))

    for dicom_dataset, uid in zip(dicom_datasets, uids):
        dicom_dataset.SOPInstanceUID = uid


def _generate_new_slice_locations(dicom_datasets, index_to_copy, number_of_slices):
    if index_to_copy == 0:
        slice_diff = dicom_datasets[0].SliceLocation - dicom_datasets[1].SliceLocation
    elif index_to_copy == len(dicom_datasets) or index_to_copy == -1:
        slice_diff = dicom_datasets[-1].SliceLocation - dicom_datasets[-2].SliceLocation
    else:
        raise ValueError("index_to_copy must be first or last slice")

    new_slice_locations = [dicom_datasets[index_to_copy].SliceLocation + slice_diff]
    for _ in range(number_of_slices - 1):
        new_slice_locations.append(new_slice_locations[-1] + slice_diff)

    return new_slice_locations


def _get_append_method(dicom_datasets, index_to_copy):
    if index_to_copy == 0:
        return "appendleft"

    if index_to_copy == len(dicom_datasets) or index_to_copy == -1:
        return "append"

    raise ValueError("index_to_copy must be first or last slice")


def _generate_uids(number_of_uids, randomisation_length=10, root=PYMEDPHYS_ROOT_UID):
    num_of_digits = len(str(number_of_uids))

    middle_item = str(random.randint(0, 10 ** randomisation_length)).zfill(
        randomisation_length
    )
    time_stamp_item = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S%f")

    last_item = [str(i).zfill(num_of_digits) for i in range(number_of_uids)]

    uids = [".".join([root, middle_item, time_stamp_item, item]) for item in last_item]

    return uids
