"""
JBL AV Receiver Remote entity for comprehensive control.

This entity exposes all receiver commands through organized UI pages.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any
from ucapi import StatusCodes
from ucapi.remote import Attributes, Commands, Features, Remote, States
from ucapi.ui import Buttons, DeviceButtonMapping, create_btn_mapping, UiPage
from ucapi_framework.entity import Entity
from intg_jblav.config import JBLAVConfig
from intg_jblav.device import JBLAV
from intg_jblav.protocol import JBLProtocol

_LOG = logging.getLogger(__name__)


class JBLAVRemote(Remote, Entity):
    """Remote entity for JBL AV receiver with comprehensive controls."""

    def __init__(self, device_config: JBLAVConfig, device: JBLAV):
        """Initialize remote entity."""
        self._device = device
        self._device_config = device_config

        entity_id = f"remote.{device_config.identifier}"
        entity_name = f"{device_config.name} Remote"

        # Define UI pages
        ui_pages = self._create_ui_pages()

        # Define simple commands for activity integration
        simple_commands = self._create_simple_commands()

        # Create button mappings
        button_mapping = self._create_button_mapping()

        attributes = {
            Attributes.STATE: States.UNAVAILABLE,
        }

        features = [
            Features.SEND_CMD,
            Features.ON_OFF,
        ]

        super().__init__(
            entity_id,
            entity_name,
            features,
            attributes,
            simple_commands=simple_commands,
            button_mapping=button_mapping,
            ui_pages=ui_pages,
            cmd_handler=self.handle_command,
        )

        # Subscribe to device events
        device.events.on(device.identifier, self._on_device_update)

        _LOG.info("[%s] Remote entity initialized", self.id)

    def _create_simple_commands(self) -> list[str]:
        """Create list of simple commands for activity integration."""
        return [
            # Power
            "POWER_ON",
            "POWER_OFF",
            "POWER_TOGGLE",
            # Volume
            "VOLUME_UP",
            "VOLUME_DOWN",
            "MUTE_TOGGLE",
            # Navigation
            "CURSOR_UP",
            "CURSOR_DOWN",
            "CURSOR_LEFT",
            "CURSOR_RIGHT",
            "CURSOR_ENTER",
            "BACK",
            "MENU",
            # Sources - Discrete
            "TV",
            "HDMI_1",
            "HDMI_2",
            "HDMI_3",
            "HDMI_4",
            "HDMI_5",
            "HDMI_6",
            "COAX",
            "OPTICAL",
            "ANALOG_1",
            "ANALOG_2",
            "PHONO",
            "BLUETOOTH",
            "NETWORK",
            # Surround Modes
            "SURROUND_MODE_STEREO_2_0",
            "SURROUND_MODE_STEREO_2_1",
            "SURROUND_MODE_ALL_STEREO",
            "SURROUND_MODE_NATIVE",
            "SURROUND_MODE_DOLBY_SURROUND",
            "SURROUND_MODE_DTS_NEURAL_X",
        ]

    def _create_button_mapping(self) -> list[DeviceButtonMapping]:
        """Create button mapping for standard remote buttons."""
        return [
            create_btn_mapping(Buttons.POWER, "POWER_TOGGLE"),
            create_btn_mapping(Buttons.VOLUME_UP, "VOLUME_UP"),
            create_btn_mapping(Buttons.VOLUME_DOWN, "VOLUME_DOWN"),
            create_btn_mapping(Buttons.MUTE, "MUTE_TOGGLE"),
            create_btn_mapping(Buttons.DPAD_UP, "CURSOR_UP"),
            create_btn_mapping(Buttons.DPAD_DOWN, "CURSOR_DOWN"),
            create_btn_mapping(Buttons.DPAD_LEFT, "CURSOR_LEFT"),
            create_btn_mapping(Buttons.DPAD_RIGHT, "CURSOR_RIGHT"),
            create_btn_mapping(Buttons.DPAD_MIDDLE, "CURSOR_ENTER"),
            create_btn_mapping(Buttons.BACK, "BACK"),
            create_btn_mapping(Buttons.HOME, "MENU"),
        ]

    def _create_ui_pages(self) -> list[dict[str, Any]]:
        """Create UI pages for remote control."""
        return [
            # Page 1: Navigation & Basic Controls
            {
                "page_id": "navigation",
                "name": "Navigation",
                "grid": {"columns": 3, "rows": 4},
                "items": [
                    {"command": "MENU", "location": {"x": 0, "y": 0}, "size": {"width": 1, "height": 1}, "icon": "uc:menu", "text": "Menu"},
                    {"command": "CURSOR_UP", "location": {"x": 1, "y": 0}, "size": {"width": 1, "height": 1}, "icon": "uc:up-arrow-bold"},
                    {"command": "BACK", "location": {"x": 2, "y": 0}, "size": {"width": 1, "height": 1}, "icon": "uc:back", "text": "Back"},
                    {"command": "CURSOR_LEFT", "location": {"x": 0, "y": 1}, "size": {"width": 1, "height": 1}, "icon": "uc:left-arrow-bold"},
                    {"command": "CURSOR_ENTER", "location": {"x": 1, "y": 1}, "size": {"width": 1, "height": 1}, "icon": "uc:circle", "text": "OK"},
                    {"command": "CURSOR_RIGHT", "location": {"x": 2, "y": 1}, "size": {"width": 1, "height": 1}, "icon": "uc:right-arrow-bold"},
                    {"command": "CURSOR_DOWN", "location": {"x": 1, "y": 2}, "size": {"width": 1, "height": 1}, "icon": "uc:down-arrow-bold"},
                    {"command": "VOLUME_UP", "location": {"x": 0, "y": 3}, "size": {"width": 1, "height": 1}, "icon": "uc:volume-up", "text": "Vol+"},
                    {"command": "MUTE_TOGGLE", "location": {"x": 1, "y": 3}, "size": {"width": 1, "height": 1}, "icon": "uc:mute", "text": "Mute"},
                    {"command": "VOLUME_DOWN", "location": {"x": 2, "y": 3}, "size": {"width": 1, "height": 1}, "icon": "uc:volume-down", "text": "Vol-"},
                ],
            },
            # Page 2: Input Sources
            {
                "page_id": "sources",
                "name": "Inputs",
                "grid": {"columns": 3, "rows": 5},
                "items": [
                    {"command": "TV", "location": {"x": 0, "y": 0}, "size": {"width": 1, "height": 1}, "icon": "uc:tv", "text": "TV/ARC"},
                    {"command": "HDMI_1", "location": {"x": 1, "y": 0}, "size": {"width": 1, "height": 1}, "icon": "uc:source", "text": "HDMI 1"},
                    {"command": "HDMI_2", "location": {"x": 2, "y": 0}, "size": {"width": 1, "height": 1}, "icon": "uc:source", "text": "HDMI 2"},
                    {"command": "HDMI_3", "location": {"x": 0, "y": 1}, "size": {"width": 1, "height": 1}, "icon": "uc:source", "text": "HDMI 3"},
                    {"command": "HDMI_4", "location": {"x": 1, "y": 1}, "size": {"width": 1, "height": 1}, "icon": "uc:source", "text": "HDMI 4"},
                    {"command": "HDMI_5", "location": {"x": 2, "y": 1}, "size": {"width": 1, "height": 1}, "icon": "uc:source", "text": "HDMI 5"},
                    {"command": "HDMI_6", "location": {"x": 0, "y": 2}, "size": {"width": 1, "height": 1}, "icon": "uc:source", "text": "HDMI 6"},
                    {"command": "COAX", "location": {"x": 1, "y": 2}, "size": {"width": 1, "height": 1}, "icon": "uc:source", "text": "Coax"},
                    {"command": "OPTICAL", "location": {"x": 2, "y": 2}, "size": {"width": 1, "height": 1}, "icon": "uc:source", "text": "Optical"},
                    {"command": "ANALOG_1", "location": {"x": 0, "y": 3}, "size": {"width": 1, "height": 1}, "icon": "uc:source", "text": "Analog 1"},
                    {"command": "ANALOG_2", "location": {"x": 1, "y": 3}, "size": {"width": 1, "height": 1}, "icon": "uc:source", "text": "Analog 2"},
                    {"command": "PHONO", "location": {"x": 2, "y": 3}, "size": {"width": 1, "height": 1}, "icon": "uc:source", "text": "Phono"},
                    {"command": "BLUETOOTH", "location": {"x": 0, "y": 4}, "size": {"width": 1, "height": 1}, "icon": "uc:bluetooth", "text": "Bluetooth"},
                    {"command": "NETWORK", "location": {"x": 1, "y": 4}, "size": {"width": 1, "height": 1}, "icon": "uc:network", "text": "Network"},
                ],
            },
            # Page 3: Surround Modes
            {
                "page_id": "surround",
                "name": "Surround",
                "grid": {"columns": 2, "rows": 3},
                "items": [
                    {"command": "SURROUND_MODE_NATIVE", "location": {"x": 0, "y": 0}, "size": {"width": 1, "height": 1}, "text": "Native"},
                    {"command": "SURROUND_MODE_STEREO_2_0", "location": {"x": 1, "y": 0}, "size": {"width": 1, "height": 1}, "text": "Stereo 2.0"},
                    {"command": "SURROUND_MODE_STEREO_2_1", "location": {"x": 0, "y": 1}, "size": {"width": 1, "height": 1}, "text": "Stereo 2.1"},
                    {"command": "SURROUND_MODE_ALL_STEREO", "location": {"x": 1, "y": 1}, "size": {"width": 1, "height": 1}, "text": "All Stereo"},
                    {"command": "SURROUND_MODE_DOLBY_SURROUND", "location": {"x": 0, "y": 2}, "size": {"width": 1, "height": 1}, "text": "Dolby"},
                    {"command": "SURROUND_MODE_DTS_NEURAL_X", "location": {"x": 1, "y": 2}, "size": {"width": 1, "height": 1}, "text": "DTS:X"},
                ],
            },
            # Page 4: Audio Settings
            {
                "page_id": "audio",
                "name": "Audio",
                "grid": {"columns": 2, "rows": 4},
                "items": [
                    {"command": "TREBLE_UP", "location": {"x": 0, "y": 0}, "size": {"width": 1, "height": 1}, "icon": "uc:plus", "text": "Treble+"},
                    {"command": "TREBLE_DOWN", "location": {"x": 1, "y": 0}, "size": {"width": 1, "height": 1}, "icon": "uc:minus", "text": "Treble-"},
                    {"command": "BASS_UP", "location": {"x": 0, "y": 1}, "size": {"width": 1, "height": 1}, "icon": "uc:plus", "text": "Bass+"},
                    {"command": "BASS_DOWN", "location": {"x": 1, "y": 1}, "size": {"width": 1, "height": 1}, "icon": "uc:minus", "text": "Bass-"},
                    {"command": "ROOM_EQ_ON", "location": {"x": 0, "y": 2}, "size": {"width": 1, "height": 1}, "text": "Room EQ On"},
                    {"command": "ROOM_EQ_OFF", "location": {"x": 1, "y": 2}, "size": {"width": 1, "height": 1}, "text": "Room EQ Off"},
                    {"command": "DIALOG_ON", "location": {"x": 0, "y": 3}, "size": {"width": 1, "height": 1}, "text": "Dialog On"},
                    {"command": "DIALOG_OFF", "location": {"x": 1, "y": 3}, "size": {"width": 1, "height": 1}, "text": "Dialog Off"},
                ],
            },
            # Page 5: Advanced & System
            {
                "page_id": "system",
                "name": "System",
                "grid": {"columns": 2, "rows": 4},
                "items": [
                    {"command": "DISPLAY_DIM", "location": {"x": 0, "y": 0}, "size": {"width": 1, "height": 1}, "icon": "uc:brightness", "text": "Dim"},
                    {"command": "DOLBY_MODE_TOGGLE", "location": {"x": 1, "y": 0}, "size": {"width": 1, "height": 1}, "text": "Dolby Mode"},
                    {"command": "PARTY_ON", "location": {"x": 0, "y": 1}, "size": {"width": 1, "height": 1}, "text": "Party On"},
                    {"command": "PARTY_OFF", "location": {"x": 1, "y": 1}, "size": {"width": 1, "height": 1}, "text": "Party Off"},
                    {"command": "DRC_ON", "location": {"x": 0, "y": 2}, "size": {"width": 1, "height": 1}, "text": "DRC On"},
                    {"command": "DRC_OFF", "location": {"x": 1, "y": 2}, "size": {"width": 1, "height": 1}, "text": "DRC Off"},
                    {"command": "REBOOT", "location": {"x": 0, "y": 3}, "size": {"width": 1, "height": 1}, "icon": "uc:refresh", "text": "Reboot"},
                    {"command": "FACTORY_RESET", "location": {"x": 1, "y": 3}, "size": {"width": 1, "height": 1}, "icon": "uc:warning", "text": "Factory Reset"},
                ],
            },
        ]

    def _on_device_update(self, entity_id: str, attributes: dict[str, Any]) -> None:
        """Handle device state updates."""
        if "power" in attributes:
            self.attributes[Attributes.STATE] = States.ON if attributes["power"] else States.OFF
            self.emit_update()

    async def handle_command(
        self, entity: Remote, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        """Handle remote commands."""
        _LOG.info("[%s] Command: %s %s", self.id, cmd_id, params or "")

        try:
            # Power commands
            if cmd_id == Commands.ON or cmd_id == "POWER_ON":
                success = await self._device.turn_on()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == Commands.OFF or cmd_id == "POWER_OFF":
                success = await self._device.turn_off()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "POWER_TOGGLE":
                if self._device.power_state:
                    success = await self._device.turn_off()
                else:
                    success = await self._device.turn_on()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            # Volume commands
            if cmd_id == "VOLUME_UP":
                success = await self._device.volume_up()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "VOLUME_DOWN":
                success = await self._device.volume_down()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "MUTE_TOGGLE":
                success = await self._device.mute_toggle()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            # Navigation commands
            if cmd_id == "CURSOR_UP":
                success = await self._device.ir_navigate_up()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "CURSOR_DOWN":
                success = await self._device.ir_navigate_down()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "CURSOR_LEFT":
                success = await self._device.ir_navigate_left()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "CURSOR_RIGHT":
                success = await self._device.ir_navigate_right()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "CURSOR_ENTER":
                success = await self._device.ir_navigate_ok()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "BACK":
                success = await self._device.ir_back()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "MENU":
                success = await self._device.ir_menu()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            # Input source commands
            if cmd_id == "TV":
                success = await self._device.send_ir_command(JBLProtocol.IR_TV)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "HDMI_1":
                success = await self._device.send_ir_command(JBLProtocol.IR_HDMI1)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "HDMI_2":
                success = await self._device.send_ir_command(JBLProtocol.IR_HDMI2)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "HDMI_3":
                success = await self._device.send_ir_command(JBLProtocol.IR_HDMI3)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "HDMI_4":
                success = await self._device.send_ir_command(JBLProtocol.IR_HDMI4)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "HDMI_5":
                success = await self._device.send_ir_command(JBLProtocol.IR_HDMI5)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "HDMI_6":
                success = await self._device.send_ir_command(JBLProtocol.IR_HDMI6)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "COAX":
                success = await self._device.send_ir_command(JBLProtocol.IR_COAX)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "OPTICAL":
                success = await self._device.send_ir_command(JBLProtocol.IR_OPTICAL)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "ANALOG_1":
                success = await self._device.send_ir_command(JBLProtocol.IR_ANALOG1)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "ANALOG_2":
                success = await self._device.send_ir_command(JBLProtocol.IR_ANALOG2)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "PHONO":
                success = await self._device.send_ir_command(JBLProtocol.IR_PHONO)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "BLUETOOTH":
                success = await self._device.send_ir_command(JBLProtocol.IR_BLUETOOTH)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "NETWORK":
                success = await self._device.send_ir_command(JBLProtocol.IR_NETWORK)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            # Surround mode commands
            if cmd_id == "SURROUND_MODE_NATIVE":
                success = await self._device.select_surround_mode(0x06)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "SURROUND_MODE_STEREO_2_0":
                success = await self._device.select_surround_mode(0x03)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "SURROUND_MODE_STEREO_2_1":
                success = await self._device.select_surround_mode(0x04)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "SURROUND_MODE_ALL_STEREO":
                success = await self._device.select_surround_mode(0x05)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "SURROUND_MODE_DOLBY_SURROUND":
                success = await self._device.select_surround_mode(0x01)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "SURROUND_MODE_DTS_NEURAL_X":
                success = await self._device.select_surround_mode(0x02)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            # Audio settings
            if cmd_id == "TREBLE_UP":
                success = await self._device.set_treble_eq(3)  # +3dB
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "TREBLE_DOWN":
                success = await self._device.set_treble_eq(-3)  # -3dB
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "BASS_UP":
                success = await self._device.set_bass_eq(3)  # +3dB
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "BASS_DOWN":
                success = await self._device.set_bass_eq(-3)  # -3dB
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "ROOM_EQ_ON":
                success = await self._device.room_eq_on()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "ROOM_EQ_OFF":
                success = await self._device.room_eq_off()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "DIALOG_ON":
                success = await self._device.dialog_enhanced_on()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "DIALOG_OFF":
                success = await self._device.dialog_enhanced_off()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            # System & Advanced
            if cmd_id == "DISPLAY_DIM":
                success = await self._device.ir_display_dim()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "DOLBY_MODE_TOGGLE":
                # Toggle - would need state tracking for proper toggle
                success = await self._device.dolby_audio_mode_on()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "PARTY_ON":
                success = await self._device.party_mode_on()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "PARTY_OFF":
                success = await self._device.party_mode_off()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "DRC_ON":
                success = await self._device.drc_on()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "DRC_OFF":
                success = await self._device.drc_off()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "REBOOT":
                success = await self._device.reboot()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == "FACTORY_RESET":
                success = await self._device.factory_reset()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            # Send command (generic)
            if cmd_id == Commands.SEND_CMD:
                if params and "command" in params:
                    # Recursive call with the actual command
                    return await self.handle_command(entity, params["command"], None)
                return StatusCodes.BAD_REQUEST

            _LOG.warning("[%s] Unhandled command: %s", self.id, cmd_id)
            return StatusCodes.NOT_IMPLEMENTED

        except Exception as err:
            _LOG.error("[%s] Command error: %s", self.id, err)
            return StatusCodes.SERVER_ERROR

    def emit_update(self) -> None:
        """Emit entity update to Remote."""
        if hasattr(self, 'api') and self.api:
            self.api.configured_entities.update(self)
