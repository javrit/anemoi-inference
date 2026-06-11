import logging

import earthkit.data as ekd
from anemoi.transform.fields import (
    new_field_from_numpy,
    new_fieldlist_from_list,
)
from anemoi.transform.filter import Filter

LOG = logging.getLogger(__name__)


class SetMember(Filter):
    """Set the member `number` value to a specific one. Defaults to 0."""

    # The version of the plugin API, used to ensure compatibility
    # with the plugin manager.

    api_version = "1.0.0"

    # The schema of the plugin, used to validate the parameters.
    # This is a Pydantic model.

    schema = None

    def __init__(self, *, number: int = 0):
        """Initialize the CropWithMask filter.

        Parameters
        ----------
        number : Number to set.
        """

        self._number = number

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
        result = []
        for f in data:
            new_field = new_field_from_numpy(
                f.to_numpy(), template=f, number=self._number
            )
            result.append(new_field)

        return new_fieldlist_from_list(result)

    def backward(self, data: ekd.FieldList) -> ekd.FieldList:
        return self.forward(data)
