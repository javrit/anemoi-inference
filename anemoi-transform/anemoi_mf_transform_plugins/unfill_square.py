import logging

import earthkit.data as ekd
import numpy as np
import tqdm
from anemoi.transform.fields import (
    new_field_from_latitudes_longitudes,
    new_field_from_numpy,
    new_fieldlist_from_list,
)
from anemoi.transform.filter import Filter

LOG = logging.getLogger(__name__)


import logging
import numpy as np
import tqdm

from anemoi.transform.filter import Filter
from anemoi.transform.fields import (
    new_field_from_latitudes_longitudes,
    new_field_from_numpy,
    new_fieldlist_from_list,
)

LOG = logging.getLogger(__name__)


class UnfillSquareGribs(Filter):
    """
    Inverse of FillSquareGribs:
    removes fill_value (padding) and returns compact field.
    """

    api_version = "1.0.0"
    schema = None

    def __init__(self, fill_value=9999):
        self.fill_value = fill_value

    def forward(self, data):
        return data

    def backward(self, data):

        result = []

        LOG.info("🧠 Starting UnfillSquareGribs")
        LOG.info(f"📦 Number of fields: {len(data)}")

        for i, field in enumerate(tqdm.tqdm(data, desc=f"Unfill {self.fill_value}")):

            lons = field.state["longitudes"]
            lats = field.state["latitudes"]
            vals = field.to_numpy(flatten=True)

            # 📊 INPUT STATS
            n_input = len(vals)
            n_model_expected = len(lons)  # grille modèle (template field)

            LOG.info(f"--- Field {i} ---")
            LOG.info(f"📌 Expected model points : {n_model_expected}")
            LOG.info(f"📥 Input points         : {n_input}")
            LOG.info(f"📊 Input range          : min={vals.min():.3f}, max={vals.max():.3f}")

            # 🧹 mask valid points
            mask = vals != self.fill_value

            clean_vals = vals[mask]
            clean_lons = lons[mask]
            clean_lats = lats[mask]

            n_output = len(clean_vals)

            LOG.info(f"📤 Output points        : {n_output}")

            if n_output == 0:
                LOG.warning(f"⚠️ Field {i} became empty after unfill")
                continue

            # sanity checks
            ratio = n_output / n_input
            LOG.info(f"📉 Keep ratio           : {ratio:.3f}")

            result.append(
                new_field_from_latitudes_longitudes(
                    new_field_from_numpy(clean_vals, template=field),
                    latitudes=clean_lats,
                    longitudes=clean_lons,
                )
            )

        LOG.info(f"✅ Finished UnfillSquareGribs: {len(result)} fields returned")

        return new_fieldlist_from_list(result)
# class UnfillSquareGribs(Filter):
#     """
#     Inverse of FillSquareGribs:
#     removes fill_value (padding) and returns compact field.
#     """

#     api_version = "1.0.0"
#     schema = None

#     def __init__(
#         self,
#         fill_value=9999,

#     ):
#         self.fill_value = fill_value

        
#     def forward(self, data):
#         return data

#     def backward(self, data):

#         result = []

#         for field in tqdm.tqdm(data, desc=f"Unfill {self.fill_value}"):

#             lons = field.state["longitudes"]
#             lats = field.state["latitudes"]
#             vals = field.to_numpy(flatten=True)

#             # 🧹 mask valid points
#             mask = vals != self.fill_value

#             if not np.any(mask):
#                 continue

#             clean_vals = vals[mask]
#             clean_lons = lons[mask]
#             clean_lats = lats[mask]

#             result.append(
#                 new_field_from_latitudes_longitudes(
#                     new_field_from_numpy(clean_vals, template=field),
#                     latitudes=clean_lats,
#                     longitudes=clean_lons,
#                 )
#             )

#         return new_fieldlist_from_list(result)
    

