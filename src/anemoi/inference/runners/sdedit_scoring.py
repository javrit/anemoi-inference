# (C) Copyright 2024 Anemoi contributors.
# SPDX-License-Identifier: Apache-2.0


import datetime
from datetime import timedelta
import itertools
import logging
import warnings
from typing import TYPE_CHECKING
from typing import Any

from anemoi.utils.config import DotDict
from anemoi.utils.dates import frequency_to_timedelta as to_timedelta
from pydantic import BaseModel

from anemoi.inference.config.run import RunConfiguration
from anemoi.inference.input import Input
from anemoi.inference.output import Output
from anemoi.inference.processor import Processor
from anemoi.inference.types import IntArray

from ..outputs import create_output

from . import runner_registry

from .default import DefaultRunner

LOG = logging.getLogger(__name__)


@runner_registry.register("sdedit_scoring")
class SDEditScoringRunner(DefaultRunner):
    """
    Runner to be used when using SDEdit method. The major difference with other runners is that at each "forecast" step,
    the real analysis is the input instead of the previous forecasted step. SDEdit method is not meant to forecast, but 
    to generate a similar (perturbed) state.
    """

    def __init__(
        self,
        config: RunConfiguration,
        noise_scheduler_params: dict | None = None,
        sampler_params: dict | None = None,
        condition_files: dict | None = None,
    ):
        if isinstance(config, dict):
            config = DotDict(config)

        if isinstance(config, BaseModel):
            config = DotDict(config.model_dump())

        self.config = config
        self.reference_date = self.config.date if hasattr(self.config, "date") else None

        super().__init__(
            config
        )

        # Overrides for predictions, defined in yaml config
        self.noise_scheduler_params = noise_scheduler_params if noise_scheduler_params is not None else {}
        self.sampler_params = sampler_params if sampler_params is not None else {}
        self.condition_files= condition_files if condition_files is not None else {}

    def execute(self) -> None:

        lead_time = to_timedelta(self.config.lead_time)
        self.lead_time = lead_time
        self.time_step = self.checkpoint.timestep

        date_start = self.config.date
        if not isinstance(date_start, datetime.datetime):
            date_start = datetime.datetime.fromisoformat(str(date_start))
        date_end = date_start + lead_time
        timestep = to_timedelta(self.checkpoint.timestep)

        self.reference_date = date_start

        output_gen = self.create_output()

        first        = True
        current_date = date_start

        while current_date < date_end:

            LOG.info("=== SDEdit scoring: forecast from %s ===", current_date)

            self.config.date = current_date

            prognostic_state = self.create_prognostics_input().create_input_state(date=current_date)
            self._check_state(prognostic_state, "prognostics")

            constants_state = self.create_constant_coupled_forcings_input().create_input_state(date=current_date)
            self._check_state(constants_state, "constant_forcings")

            forcings_state = self.create_dynamic_forcings_input().create_input_state(date=current_date)
            self._check_state(forcings_state, "dynamic_forcings")

            input_state = self._combine_states(prognostic_state, constants_state, forcings_state)
            self.input_state_hook(constants_state)

            initial_state = Output.reduce(
                self._initial_state(prognostic_state, constants_state, forcings_state)
            )
            for processor in self.post_processors:
                initial_state = processor.process(initial_state)

            if first:
                output_gen.open(initial_state)
                output_gen.write_initial_state(initial_state)
                first = False

            for state in self.run(input_state=input_state, lead_time=self.checkpoint.timestep):
                for processor in self.post_processors:
                    state = processor.process(state)

                validity = current_date + timestep
                state["step"] = validity - date_start

                output_gen.write_state(state)

            current_date += timestep

        output_gen.close()

    def predict_step(self, model, input_tensor_torch, **kwargs):

        if not hasattr(model, '_condition_files_patched'):
            model.model.model_config["model"]["condition_files"] = self.condition_files
            model._condition_files_patched = True

        return model.predict_step(
            input_tensor_torch,
            noise_scheduler_params=self.noise_scheduler_params,
            sampler_params=self.sampler_params,
            **kwargs
        )
