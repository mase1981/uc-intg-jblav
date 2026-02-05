"""
JBL AV Receiver Media Player entity.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any
from ucapi import StatusCodes
from ucapi.media_player import (
    Attributes,
    Commands,
    DeviceClasses,
    Features,
    MediaPlayer,
    States,
    Options,
)
from intg_jblav.config import JBLAVConfig
from intg_jblav.device import JBLAV
from intg_jblav.protocol import JBLInputSource, JBLSurroundMode, JBLProtocol

_LOG = logging.getLogger(__name__)


class JBLAVMediaPlayer(MediaPlayer):
    """Media player entity for JBL AV Receiver."""

    def __init__(self, device_config: JBLAVConfig, device: JBLAV):
        """Initialize with device reference."""
        self._device = device
        self._device_config = device_config

        entity_id = f"media_player.{device_config.identifier}"

        # Build source list based on common sources (all models support these)
        source_list = [
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

        # Build sound mode list (common modes)
        sound_mode_list = [
            JBLProtocol.SURROUND_MODE_NAMES[JBLSurroundMode.STEREO_2_0],
            JBLProtocol.SURROUND_MODE_NAMES[JBLSurroundMode.STEREO_2_1],
            JBLProtocol.SURROUND_MODE_NAMES[JBLSurroundMode.ALL_STEREO],
            JBLProtocol.SURROUND_MODE_NAMES[JBLSurroundMode.NATIVE],
        ]

        super().__init__(
            entity_id,
            device_config.name,
            [
                Features.ON_OFF,
                Features.VOLUME,
                Features.VOLUME_UP_DOWN,
                Features.MUTE,
                Features.MUTE_TOGGLE,
                Features.SELECT_SOURCE,
                Features.SELECT_SOUND_MODE,
            ],
            {
                Attributes.STATE: States.UNAVAILABLE,
                Attributes.VOLUME: 0,
                Attributes.MUTED: False,
                Attributes.SOURCE: source_list[0],
                Attributes.SOURCE_LIST: source_list,
                Attributes.SOUND_MODE: sound_mode_list[0],
                Attributes.SOUND_MODE_LIST: sound_mode_list,
            },
            device_class=DeviceClasses.RECEIVER,
            cmd_handler=self.handle_command,
        )

    async def handle_command(
        self, entity: MediaPlayer, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        """Handle media player commands."""
        _LOG.info("[%s] Command: %s %s", self.id, cmd_id, params or "")

        try:
            if cmd_id == Commands.ON:
                success = await self._device.turn_on()
                if success:
                    # Optimistically update state
                    self.attributes[Attributes.STATE] = States.ON
                    return StatusCodes.OK
                return StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.OFF:
                success = await self._device.turn_off()
                if success:
                    # Optimistically update state
                    self.attributes[Attributes.STATE] = States.STANDBY
                    return StatusCodes.OK
                return StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.VOLUME:
                if params and "volume" in params:
                    volume = int(params["volume"])
                    success = await self._device.set_volume(volume)
                    return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
                return StatusCodes.BAD_REQUEST

            elif cmd_id == Commands.VOLUME_UP:
                success = await self._device.volume_up()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.VOLUME_DOWN:
                success = await self._device.volume_down()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.MUTE:
                success = await self._device.mute_on()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.UNMUTE:
                success = await self._device.mute_off()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.MUTE_TOGGLE:
                success = await self._device.mute_toggle()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.SELECT_SOURCE:
                if params and "source" in params:
                    source_name = params["source"]
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
                return StatusCodes.BAD_REQUEST

            elif cmd_id == Commands.SELECT_SOUND_MODE:
                if params and "mode" in params:
                    mode_name = params["mode"]
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
                        _LOG.warning("[%s] Unknown sound mode: %s", self.id, mode_name)
                        return StatusCodes.BAD_REQUEST
                return StatusCodes.BAD_REQUEST

            return StatusCodes.NOT_IMPLEMENTED

        except Exception as err:
            _LOG.error("[%s] Command error: %s", self.id, err, exc_info=True)
            return StatusCodes.SERVER_ERROR

    def emit_update(self) -> None:
        """Emit entity update to Remote."""
        if self.api:
            self.api.configured_entities.update(self)
