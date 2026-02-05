"""
JBL AV Receiver Select entities for input source and surround mode selection.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any
from ucapi import StatusCodes
from ucapi.select import Attributes, Select, States
from ucapi_framework.entity import Entity
from intg_jblav.config import JBLAVConfig
from intg_jblav.device import JBLAV
from intg_jblav.protocol import JBLProtocol, JBLInputSource, JBLSurroundMode

_LOG = logging.getLogger(__name__)


class JBLAVInputSelect(Select, Entity):
    """Select entity for input source selection."""

    def __init__(self, device_config: JBLAVConfig, device: JBLAV):
        """Initialize select entity."""
        self._device = device
        self._device_config = device_config

        entity_id = f"select.{device_config.identifier}.input_source"
        entity_name = f"{device_config.name} Input Source"

        # Build input source options (all models support these)
        source_options = [
            JBLProtocol.INPUT_SOURCE_NAMES[JBLInputSource.TV_ARC],
            JBLProtocol.INPUT_SOURCE_NAMES[JBLInputSource.HDMI_1],
            JBLProtocol.INPUT_SOURCE_NAMES[JBLInputSource.HDMI_2],
            JBLProtocol.INPUT_SOURCE_NAMES[JBLInputSource.HDMI_3],
            JBLProtocol.INPUT_SOURCE_NAMES[JBLInputSource.HDMI_4],
            JBLProtocol.INPUT_SOURCE_NAMES[JBLInputSource.COAX],
            JBLProtocol.INPUT_SOURCE_NAMES[JBLInputSource.OPTICAL],
            JBLProtocol.INPUT_SOURCE_NAMES[JBLInputSource.ANALOG_1],
            JBLProtocol.INPUT_SOURCE_NAMES[JBLInputSource.ANALOG_2],
            JBLProtocol.INPUT_SOURCE_NAMES[JBLInputSource.BLUETOOTH],
            JBLProtocol.INPUT_SOURCE_NAMES[JBLInputSource.NETWORK],
        ]

        attributes = {
            Attributes.STATE: States.UNAVAILABLE,
            Attributes.CURRENT_OPTION: source_options[0],
            Attributes.OPTIONS: source_options,
        }

        super().__init__(
            entity_id,
            entity_name,
            attributes,
            cmd_handler=self.handle_command,
        )

        _LOG.info("[%s] Input select entity initialized", self.id)

    async def handle_command(
        self, entity: Select, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        """Handle select commands."""
        _LOG.info("[%s] Command: %s %s", self.id, cmd_id, params or "")

        try:
            if cmd_id == "select_option" and params and "option" in params:
                source_name = params["option"]

                # Find source ID by name
                source_id = None
                for sid, sname in JBLProtocol.INPUT_SOURCE_NAMES.items():
                    if sname == source_name:
                        source_id = sid
                        break

                if source_id is not None:
                    success = await self._device.select_source(source_id)
                    return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
                else:
                    _LOG.warning("[%s] Unknown source: %s", self.id, source_name)
                    return StatusCodes.BAD_REQUEST

            return StatusCodes.NOT_IMPLEMENTED

        except Exception as err:
            _LOG.error("[%s] Command error: %s", self.id, err)
            return StatusCodes.SERVER_ERROR


class JBLAVSurroundModeSelect(Select, Entity):
    """Select entity for surround mode selection."""

    def __init__(self, device_config: JBLAVConfig, device: JBLAV):
        """Initialize select entity."""
        self._device = device
        self._device_config = device_config

        entity_id = f"select.{device_config.identifier}.surround_mode"
        entity_name = f"{device_config.name} Surround Mode"

        # Build surround mode options (common modes for all models)
        mode_options = [
            JBLProtocol.SURROUND_MODE_NAMES[JBLSurroundMode.STEREO_2_0],
            JBLProtocol.SURROUND_MODE_NAMES[JBLSurroundMode.STEREO_2_1],
            JBLProtocol.SURROUND_MODE_NAMES[JBLSurroundMode.ALL_STEREO],
            JBLProtocol.SURROUND_MODE_NAMES[JBLSurroundMode.NATIVE],
        ]

        attributes = {
            Attributes.STATE: States.UNAVAILABLE,
            Attributes.CURRENT_OPTION: mode_options[0],
            Attributes.OPTIONS: mode_options,
        }

        super().__init__(
            entity_id,
            entity_name,
            attributes,
            cmd_handler=self.handle_command,
        )

        _LOG.info("[%s] Surround mode select entity initialized", self.id)

    async def handle_command(
        self, entity: Select, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        """Handle select commands."""
        _LOG.info("[%s] Command: %s %s", self.id, cmd_id, params or "")

        try:
            if cmd_id == "select_option" and params and "option" in params:
                mode_name = params["option"]

                # Find mode ID by name
                mode_id = None
                for mid, mname in JBLProtocol.SURROUND_MODE_NAMES.items():
                    if mname == mode_name:
                        mode_id = mid
                        break

                if mode_id is not None:
                    success = await self._device.select_surround_mode(mode_id)
                    return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
                else:
                    _LOG.warning("[%s] Unknown surround mode: %s", self.id, mode_name)
                    return StatusCodes.BAD_REQUEST

            return StatusCodes.NOT_IMPLEMENTED

        except Exception as err:
            _LOG.error("[%s] Command error: %s", self.id, err)
            return StatusCodes.SERVER_ERROR
