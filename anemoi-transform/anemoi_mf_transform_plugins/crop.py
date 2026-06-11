import logging
from pathlib import Path
from typing import TypedDict

import earthkit.data as ekd
import numpy as np
import tqdm
from anemoi.transform.fields import (
    new_field_from_latitudes_longitudes,
    new_field_from_numpy,
    new_fieldlist_from_list,
)
from anemoi.transform.filter import Filter
from anemoi.transform.spatial import cropping_mask

LOG = logging.getLogger(__name__)


class Area(TypedDict):
    north: int
    west: int
    south: int
    east: int


class CropFilter(Filter):
    """A filter to do something on fields."""

    # The version of the plugin API, used to ensure compatibility
    # with the plugin manager.

    api_version = "1.0.0"

    # The schema of the plugin, used to validate the parameters.
    # This is a Pydantic model.

    schema = None

    def __init__(self, *, area: Area | None = None, mask: str | None = None):
        """Initialize the CropWithMask filter.

        Parameters
        ----------
        area : Area | None, optional
            The north-west-south-east boundaries of the mask as a dict.
        mask : str | None, optional
            The path to a mask
        """

        self._area: Area = area or {"north": 90, "west": 0, "south": -90, "east": 360}
        self._mask_path = Path(mask) if mask else None
        self._latitudes: np.ndarray | None = None
        self._longitudes: np.ndarray | None = None
        self._mask: np.ndarray | None = None

    def mask_lat_long(
        self, data: ekd.FieldList
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        if (
            self._mask is not None
            and self._latitudes is not None
            and self._longitudes is not None
        ):
            return (self._mask, self._latitudes, self._longitudes)

        first = data[0]
        data = first.to_numpy(flatten=True)

        origin_latitudes, origin_longitudes = first.grid_points()

        if self._mask_path is not None:
            self._mask = np.load(self._mask_path)
        else:
            self._mask = cropping_mask(
                origin_latitudes,
                origin_longitudes,
                self._area["north"],
                self._area["west"],
                self._area["south"],
                self._area["east"],
            )
        self._latitudes = origin_latitudes[self._mask]
        self._longitudes = origin_longitudes[self._mask]
        return (self._mask, self._latitudes, self._longitudes)

    def forward(self, data: ekd.FieldList) -> ekd.FieldList:
        """Crop each of the fields with a mask deduced from the first field.
        Parameters
        ----------
        fields : ekd.FieldList
            List of fields to be processed.
        Returns
        -------
        ekd.FieldList
            List of fields with NaNs masked out.
        """
        mask, latitudes, longitudes = self.mask_lat_long(data)

        result = []
        for field in tqdm.tqdm(data, desc="Cropping with Mask"):
            data = field.to_numpy(flatten=True)
            result.append(
                new_field_from_latitudes_longitudes(
                    new_field_from_numpy(data[mask], template=field),
                    latitudes=latitudes,
                    longitudes=longitudes,
                )
            )

        return new_fieldlist_from_list(result)
