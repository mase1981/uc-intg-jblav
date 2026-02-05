"""
JBL AV Receiver device implementation for Unfolded Circle integration.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
from typing import Any
from ucapi_framework import PersistentConnectionDevice, DeviceEvents
from intg_jblav.config import JBLAVConfig
from intg_jblav.protocol import (
    JBLProtocol,
    JBLCommand,
    JBLResponseCode,
    JBLModel,
    JBLInputSource,
    JBLSurroundMode,
)

_LOG = logging.getLogger(__name__)


class JBLAV(PersistentConnectionDevice):
    """JBL MA Series AV Receiver implementation using PersistentConnectionDevice."""

    def __init__(
        self,
        device_config: JBLAVConfig,
        loop=None,
        backoff_max=300,
        config_manager=None,
        driver=None,
    ):
        super().__init__(
            device_config=device_config,
            loop=loop,
            backoff_max=backoff_max,
            config_manager=config_manager,
            driver=driver,
        )
        self._device_config = device_config
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._model: int | None = None
        self._model_name: str = "Unknown"
        self._power_state: bool = False
        self._volume: int = 0
        self._muted: bool = False
        self._source: int = JBLInputSource.TV_ARC
        self._surround_mode: int = JBLSurroundMode.NATIVE
        self._initialized: bool = False

    @property
    def identifier(self) -> str:
        return self._device_config.identifier

    @property
    def name(self) -> str:
        return self._device_config.name

    @property
    def address(self) -> str:
        return self._device_config.host

    @property
    def log_id(self) -> str:
        return f"{self.name} ({self.address})"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def power_state(self) -> bool:
        return self._power_state

    @property
    def volume(self) -> int:
        return self._volume

    @property
    def muted(self) -> bool:
        return self._muted

    @property
    def source(self) -> int:
        return self._source

    @property
    def source_name(self) -> str:
        return JBLProtocol.INPUT_SOURCE_NAMES.get(self._source, f"Source {self._source}")

    @property
    def surround_mode(self) -> int:
        return self._surround_mode

    @property
    def surround_mode_name(self) -> str:
        return JBLProtocol.SURROUND_MODE_NAMES.get(self._surround_mode, f"Mode {self._surround_mode}")

    async def establish_connection(self) -> Any:
        """Establish TCP connection to JBL receiver."""
        _LOG.info("[%s] Connecting to %s:%d", self.log_id, self._device_config.host, self._device_config.port)

        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self._device_config.host, self._device_config.port),
                timeout=10.0
            )

            _LOG.info("[%s] TCP connection established", self.log_id)

            self._initialized = True
            _LOG.info("[%s] Connection initialized", self.log_id)

            return (self._reader, self._writer)

        except asyncio.TimeoutError:
            _LOG.error("[%s] Connection timeout", self.log_id)
            raise ConnectionError(f"Connection timeout to {self._device_config.host}:{self._device_config.port}")
        except Exception as err:
            _LOG.error("[%s] Connection failed: %s", self.log_id, err)
            raise

    async def close_connection(self) -> None:
        """Close TCP connection."""
        _LOG.info("[%s] Closing connection", self.log_id)

        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception as err:
                _LOG.debug("[%s] Error closing writer: %s", self.log_id, err)

        self._reader = None
        self._writer = None
        self._initialized = False

    async def maintain_connection(self) -> None:
        """
        Maintain connection loop - read and process responses.

        This runs continuously while connected, processing all messages from the receiver.
        """
        _LOG.info("[%s] Starting message processing loop", self.log_id)

        # Send initialization command
        await self._send_command_raw(JBLProtocol.cmd_initialization())
        await asyncio.sleep(0.2)

        # Query initial state
        _LOG.info("[%s] Querying initial device state", self.log_id)
        await self._query_all_state()

        buffer = bytearray()

        while self._reader and not self._reader.at_eof():
            try:
                # Read data with timeout
                data = await asyncio.wait_for(
                    self._reader.read(1024),
                    timeout=120.0
                )

                if not data:
                    _LOG.warning("[%s] Connection closed by receiver", self.log_id)
                    break

                buffer.extend(data)
                _LOG.debug("[%s] Received %d bytes", self.log_id, len(data))

                # Process complete messages
                while True:
                    message = self._extract_message(buffer)
                    if message is None:
                        break

                    await self._process_response(message)

            except asyncio.TimeoutError:
                # Timeout is normal - send heartbeat to keep connection alive
                _LOG.debug("[%s] Read timeout - sending heartbeat", self.log_id)
                await self._send_command_raw(JBLProtocol.cmd_heartbeat())
                continue

            except Exception as err:
                _LOG.error("[%s] Error in message loop: %s", self.log_id, err)
                break

        _LOG.info("[%s] Message processing loop ended", self.log_id)

    def _extract_message(self, buffer: bytearray) -> bytes | None:
        """
        Extract a complete message from the buffer.

        JBL messages start with 0x02 0x23 and end with 0x0D.

        Returns:
            Complete message bytes or None if incomplete
        """
        if len(buffer) < 5:  # Minimum message size
            return None

        # Find start of message (0x02 0x23)
        start_idx = -1
        for i in range(len(buffer) - 1):
            if buffer[i] == 0x02 and buffer[i + 1] == 0x23:
                start_idx = i
                break

        if start_idx == -1:
            # No valid start found, clear garbage
            if len(buffer) > 100:
                _LOG.debug("[%s] Clearing %d bytes of garbage", self.log_id, len(buffer))
                buffer.clear()
            return None

        # Remove any garbage before start
        if start_idx > 0:
            del buffer[:start_idx]

        # Look for end byte (0x0D)
        try:
            end_idx = buffer.index(0x0D)
        except ValueError:
            # End not found yet
            return None

        # Extract complete message
        message = bytes(buffer[:end_idx + 1])
        del buffer[:end_idx + 1]

        return message

    async def _process_response(self, message: bytes) -> None:
        """Process a received response message."""
        parsed = JBLProtocol.parse_response(message)
        if parsed is None:
            _LOG.debug("[%s] Failed to parse response: %s", self.log_id, message.hex())
            return

        cmd_id = parsed["cmd_id"]
        rsp_code = parsed["rsp_code"]
        data = parsed["data"]

        _LOG.debug("[%s] Response: cmd=0x%02X rsp=0x%02X data=%s", self.log_id, cmd_id, rsp_code, [f"0x{b:02X}" for b in data])

        # Handle error responses
        if rsp_code != JBLResponseCode.STATUS_UPDATE:
            _LOG.warning("[%s] Command 0x%02X error: code=0x%02X", self.log_id, cmd_id, rsp_code)
            return

        # Process by command type
        if cmd_id == JBLCommand.INITIALIZATION:
            await self._handle_initialization(data)
        elif cmd_id == JBLCommand.POWER:
            await self._handle_power(data)
        elif cmd_id == JBLCommand.VOLUME:
            await self._handle_volume(data)
        elif cmd_id == JBLCommand.MUTE:
            await self._handle_mute(data)
        elif cmd_id == JBLCommand.INPUT_SOURCE:
            await self._handle_source(data)
        elif cmd_id == JBLCommand.SURROUND_MODE:
            await self._handle_surround_mode(data)
        elif cmd_id == JBLCommand.HEARTBEAT:
            _LOG.debug("[%s] Heartbeat acknowledged", self.log_id)
        else:
            _LOG.debug("[%s] Unhandled command: 0x%02X", self.log_id, cmd_id)

    async def _handle_initialization(self, data: list[int]) -> None:
        """Handle initialization response."""
        if len(data) > 0:
            self._model = data[0]
            self._model_name = JBLProtocol.MODEL_NAMES.get(self._model, f"Unknown (0x{self._model:02X})")
            _LOG.info("[%s] Model identified: %s", self.log_id, self._model_name)

    async def _handle_power(self, data: list[int]) -> None:
        """Handle power state update."""
        if len(data) > 0:
            old_state = self._power_state
            self._power_state = data[0] == 0x01
            _LOG.debug("[%s] Power: %s", self.log_id, "ON" if self._power_state else "OFF")

            if old_state != self._power_state:
                self._notify_entities()

    async def _handle_volume(self, data: list[int]) -> None:
        """Handle volume update."""
        if len(data) > 0:
            old_volume = self._volume
            self._volume = data[0]
            _LOG.debug("[%s] Volume: %d", self.log_id, self._volume)

            if old_volume != self._volume:
                self._notify_entities()

    async def _handle_mute(self, data: list[int]) -> None:
        """Handle mute state update."""
        if len(data) > 0:
            old_muted = self._muted
            self._muted = data[0] == 0x01
            _LOG.debug("[%s] Mute: %s", self.log_id, "ON" if self._muted else "OFF")

            if old_muted != self._muted:
                self._notify_entities()

    async def _handle_source(self, data: list[int]) -> None:
        """Handle source update."""
        if len(data) > 0:
            old_source = self._source
            self._source = data[0]
            _LOG.debug("[%s] Source: %s", self.log_id, self.source_name)

            if old_source != self._source:
                self._notify_entities()

    async def _handle_surround_mode(self, data: list[int]) -> None:
        """Handle surround mode update."""
        if len(data) > 0:
            old_mode = self._surround_mode
            self._surround_mode = data[0]
            _LOG.debug("[%s] Surround Mode: %s", self.log_id, self.surround_mode_name)

            if old_mode != self._surround_mode:
                self._notify_entities()

    def _notify_entities(self) -> None:
        """Notify entities of state changes - emit UPDATE events with entity_ids."""
        from ucapi.media_player import Attributes as MediaAttributes, States as MediaStates
        from ucapi.sensor import Attributes as SensorAttributes, States as SensorStates
        from ucapi.select import Attributes as SelectAttributes, States as SelectStates
        from ucapi.remote import Attributes as RemoteAttributes

        # Media Player Entity
        media_player_id = f"media_player.{self.identifier}"
        media_player_attrs = {
            MediaAttributes.STATE: MediaStates.ON if self._power_state else MediaStates.STANDBY,
            MediaAttributes.VOLUME: self._volume,
            MediaAttributes.MUTED: self._muted,
            MediaAttributes.SOURCE: self.source_name,
            MediaAttributes.SOURCE_LIST: list(JBLProtocol.INPUT_SOURCE_NAMES.values()),
            MediaAttributes.SOUND_MODE: self.surround_mode_name,
            MediaAttributes.SOUND_MODE_LIST: [
                JBLProtocol.SURROUND_MODE_NAMES[JBLSurroundMode.STEREO_2_0],
                JBLProtocol.SURROUND_MODE_NAMES[JBLSurroundMode.STEREO_2_1],
                JBLProtocol.SURROUND_MODE_NAMES[JBLSurroundMode.ALL_STEREO],
                JBLProtocol.SURROUND_MODE_NAMES[JBLSurroundMode.NATIVE],
            ],
        }
        self.events.emit(DeviceEvents.UPDATE, media_player_id, media_player_attrs)

        # Sensor: Model
        model_sensor_id = f"sensor.{self.identifier}.model"
        model_sensor_attrs = {
            SensorAttributes.STATE: SensorStates.ON if self._model_name != "Unknown" else SensorStates.UNAVAILABLE,
            SensorAttributes.VALUE: self._model_name,
        }
        self.events.emit(DeviceEvents.UPDATE, model_sensor_id, model_sensor_attrs)

        # Sensor: Volume
        volume_sensor_id = f"sensor.{self.identifier}.volume"
        volume_sensor_attrs = {
            SensorAttributes.STATE: SensorStates.ON,
            SensorAttributes.VALUE: self._volume,
            SensorAttributes.UNIT: "%",
        }
        self.events.emit(DeviceEvents.UPDATE, volume_sensor_id, volume_sensor_attrs)

        # Sensor: Input
        input_sensor_id = f"sensor.{self.identifier}.input"
        input_sensor_attrs = {
            SensorAttributes.STATE: SensorStates.ON,
            SensorAttributes.VALUE: self.source_name,
        }
        self.events.emit(DeviceEvents.UPDATE, input_sensor_id, input_sensor_attrs)

        # Sensor: Surround Mode
        surround_sensor_id = f"sensor.{self.identifier}.surround_mode"
        surround_sensor_attrs = {
            SensorAttributes.STATE: SensorStates.ON,
            SensorAttributes.VALUE: self.surround_mode_name,
        }
        self.events.emit(DeviceEvents.UPDATE, surround_sensor_id, surround_sensor_attrs)

        # Sensor: Muted
        muted_sensor_id = f"sensor.{self.identifier}.muted"
        muted_state_str = "Muted" if self._muted else "Unmuted"
        muted_sensor_attrs = {
            SensorAttributes.STATE: SensorStates.ON,
            SensorAttributes.VALUE: muted_state_str,
        }
        self.events.emit(DeviceEvents.UPDATE, muted_sensor_id, muted_sensor_attrs)

        # Sensor: Connection
        connection_sensor_id = f"sensor.{self.identifier}.connection"
        connection_attrs = {
            SensorAttributes.STATE: SensorStates.ON if self.is_connected else SensorStates.UNAVAILABLE,
            SensorAttributes.VALUE: "connected" if self.is_connected else "disconnected",
        }
        self.events.emit(DeviceEvents.UPDATE, connection_sensor_id, connection_attrs)

        # Select: Input Source
        input_select_id = f"select.{self.identifier}.input_source"
        input_select_attrs = {
            SelectAttributes.STATE: SelectStates.ON if self._power_state else SelectStates.UNAVAILABLE,
            SelectAttributes.CURRENT_OPTION: self.source_name,
            SelectAttributes.OPTIONS: list(JBLProtocol.INPUT_SOURCE_NAMES.values()),
        }
        self.events.emit(DeviceEvents.UPDATE, input_select_id, input_select_attrs)

        # Select: Surround Mode
        surround_select_id = f"select.{self.identifier}.surround_mode"
        surround_select_attrs = {
            SelectAttributes.STATE: SelectStates.ON if self._power_state else SelectStates.UNAVAILABLE,
            SelectAttributes.CURRENT_OPTION: self.surround_mode_name,
            SelectAttributes.OPTIONS: [
                JBLProtocol.SURROUND_MODE_NAMES[JBLSurroundMode.STEREO_2_0],
                JBLProtocol.SURROUND_MODE_NAMES[JBLSurroundMode.STEREO_2_1],
                JBLProtocol.SURROUND_MODE_NAMES[JBLSurroundMode.ALL_STEREO],
                JBLProtocol.SURROUND_MODE_NAMES[JBLSurroundMode.NATIVE],
            ],
        }
        self.events.emit(DeviceEvents.UPDATE, surround_select_id, surround_select_attrs)

        # Remote Entity
        remote_id = f"remote.{self.identifier}"
        remote_attrs = {
            RemoteAttributes.STATE: "ON" if self._power_state else "OFF"
        }
        self.events.emit(DeviceEvents.UPDATE, remote_id, remote_attrs)

    async def _send_command_raw(self, command: bytes) -> bool:
        """Send raw command bytes to receiver."""
        if not self._writer:
            _LOG.error("[%s] Cannot send command - not connected", self.log_id)
            return False

        try:
            _LOG.debug("[%s] Sending: %s", self.log_id, command.hex())
            self._writer.write(command)
            await self._writer.drain()
            return True
        except Exception as err:
            _LOG.error("[%s] Send error: %s", self.log_id, err)
            return False

    async def _query_all_state(self) -> None:
        """Query all device state after connection."""
        _LOG.info("[%s] Querying device state", self.log_id)

        commands = [
            JBLProtocol.cmd_power_query(),
            JBLProtocol.cmd_volume_query(),
            JBLProtocol.cmd_mute_query(),
            JBLProtocol.cmd_input_source_query(),
            JBLProtocol.cmd_surround_mode_query(),
        ]

        for cmd in commands:
            await self._send_command_raw(cmd)
            await asyncio.sleep(0.1)  # Small delay between commands

    # Public control methods
    async def turn_on(self) -> bool:
        """Turn receiver on."""
        _LOG.info("[%s] Turning on", self.log_id)
        return await self._send_command_raw(JBLProtocol.cmd_power_on())

    async def turn_off(self) -> bool:
        """Turn receiver off."""
        _LOG.info("[%s] Turning off", self.log_id)
        return await self._send_command_raw(JBLProtocol.cmd_power_off())

    async def set_volume(self, volume: int) -> bool:
        """Set volume (0-99)."""
        volume = max(0, min(99, volume))
        _LOG.info("[%s] Setting volume to %d", self.log_id, volume)
        return await self._send_command_raw(JBLProtocol.cmd_volume_set(volume))

    async def volume_up(self) -> bool:
        """Increase volume by 1."""
        new_volume = min(99, self._volume + 1)
        return await self.set_volume(new_volume)

    async def volume_down(self) -> bool:
        """Decrease volume by 1."""
        new_volume = max(0, self._volume - 1)
        return await self.set_volume(new_volume)

    async def mute_on(self) -> bool:
        """Mute audio."""
        _LOG.info("[%s] Muting", self.log_id)
        return await self._send_command_raw(JBLProtocol.cmd_mute_on())

    async def mute_off(self) -> bool:
        """Unmute audio."""
        _LOG.info("[%s] Unmuting", self.log_id)
        return await self._send_command_raw(JBLProtocol.cmd_mute_off())

    async def mute_toggle(self) -> bool:
        """Toggle mute state."""
        if self._muted:
            return await self.mute_off()
        else:
            return await self.mute_on()

    async def select_source(self, source: int) -> bool:
        """Select input source."""
        _LOG.info("[%s] Selecting source: %s", self.log_id, JBLProtocol.INPUT_SOURCE_NAMES.get(source, f"0x{source:02X}"))
        return await self._send_command_raw(JBLProtocol.cmd_input_source_set(source))

    async def select_surround_mode(self, mode: int) -> bool:
        """Select surround mode."""
        _LOG.info("[%s] Selecting surround mode: %s", self.log_id, JBLProtocol.SURROUND_MODE_NAMES.get(mode, f"0x{mode:02X}"))
        return await self._send_command_raw(JBLProtocol.cmd_surround_mode_set(mode))

    async def set_display_dim(self, level: int) -> bool:
        """Set display brightness (0=Off, 1=Dim, 2=Mid, 3=Bright)."""
        _LOG.info("[%s] Setting display brightness to %d", self.log_id, level)
        return await self._send_command_raw(JBLProtocol.cmd_display_dim_set(level))

    async def send_ir_command(self, ir_code: int) -> bool:
        """Send IR remote command."""
        _LOG.info("[%s] Sending IR command: 0x%06X", self.log_id, ir_code)
        return await self._send_command_raw(JBLProtocol.cmd_ir_simulate(ir_code))

    async def party_mode_on(self) -> bool:
        """Enable party mode (MA710+ only)."""
        _LOG.info("[%s] Enabling party mode", self.log_id)
        return await self._send_command_raw(JBLProtocol.cmd_party_mode_on())

    async def party_mode_off(self) -> bool:
        """Disable party mode (MA710+ only)."""
        _LOG.info("[%s] Disabling party mode", self.log_id)
        return await self._send_command_raw(JBLProtocol.cmd_party_mode_off())

    async def set_party_volume(self, volume: int) -> bool:
        """Set party mode volume 0-99 (MA710+ only)."""
        volume = max(0, min(99, volume))
        _LOG.info("[%s] Setting party volume to %d", self.log_id, volume)
        return await self._send_command_raw(JBLProtocol.cmd_party_volume_set(volume))

    async def set_treble_eq(self, level: int) -> bool:
        """Set treble EQ level (-6 to +6 dB)."""
        _LOG.info("[%s] Setting treble EQ to %d dB", self.log_id, level)
        return await self._send_command_raw(JBLProtocol.cmd_treble_eq_set(level))

    async def set_bass_eq(self, level: int) -> bool:
        """Set bass EQ level (-6 to +6 dB)."""
        _LOG.info("[%s] Setting bass EQ to %d dB", self.log_id, level)
        return await self._send_command_raw(JBLProtocol.cmd_bass_eq_set(level))

    async def room_eq_on(self) -> bool:
        """Enable room EQ."""
        _LOG.info("[%s] Enabling room EQ", self.log_id)
        return await self._send_command_raw(JBLProtocol.cmd_room_eq_on())

    async def room_eq_off(self) -> bool:
        """Disable room EQ."""
        _LOG.info("[%s] Disabling room EQ", self.log_id)
        return await self._send_command_raw(JBLProtocol.cmd_room_eq_off())

    async def dialog_enhanced_on(self) -> bool:
        """Enable dialog enhanced."""
        _LOG.info("[%s] Enabling dialog enhanced", self.log_id)
        return await self._send_command_raw(JBLProtocol.cmd_dialog_enhanced_on())

    async def dialog_enhanced_off(self) -> bool:
        """Disable dialog enhanced."""
        _LOG.info("[%s] Disabling dialog enhanced", self.log_id)
        return await self._send_command_raw(JBLProtocol.cmd_dialog_enhanced_off())

    async def dolby_audio_mode_on(self) -> bool:
        """Enable Dolby audio mode."""
        _LOG.info("[%s] Enabling Dolby audio mode", self.log_id)
        return await self._send_command_raw(JBLProtocol.cmd_dolby_audio_mode_on())

    async def dolby_audio_mode_off(self) -> bool:
        """Disable Dolby audio mode."""
        _LOG.info("[%s] Disabling Dolby audio mode", self.log_id)
        return await self._send_command_raw(JBLProtocol.cmd_dolby_audio_mode_off())

    async def drc_on(self) -> bool:
        """Enable DRC (MA710+ only)."""
        _LOG.info("[%s] Enabling DRC", self.log_id)
        return await self._send_command_raw(JBLProtocol.cmd_drc_on())

    async def drc_off(self) -> bool:
        """Disable DRC (MA710+ only)."""
        _LOG.info("[%s] Disabling DRC", self.log_id)
        return await self._send_command_raw(JBLProtocol.cmd_drc_off())

    async def query_streaming_state(self) -> bool:
        """Query streaming server state."""
        _LOG.info("[%s] Querying streaming state", self.log_id)
        return await self._send_command_raw(JBLProtocol.cmd_streaming_state_query())

    async def query_software_version(self, version_type: int = 0xF0) -> bool:
        """
        Query software version.

        Args:
            version_type: 0xF0=IP control, 0xF1=Host, 0xF2=DSP, 0xF3=OSD, 0xF4=NET
        """
        _LOG.info("[%s] Querying software version (type 0x%02X)", self.log_id, version_type)
        return await self._send_command_raw(JBLProtocol.cmd_version_query(version_type))

    async def reboot(self) -> bool:
        """Reboot the receiver."""
        _LOG.warning("[%s] Rebooting receiver", self.log_id)
        return await self._send_command_raw(JBLProtocol.cmd_reboot())

    async def factory_reset(self) -> bool:
        """Factory reset the receiver."""
        _LOG.warning("[%s] Factory resetting receiver", self.log_id)
        return await self._send_command_raw(JBLProtocol.cmd_factory_reset())

    # IR convenience methods for Remote entity
    async def ir_navigate_up(self) -> bool:
        """Navigate up."""
        return await self.send_ir_command(JBLProtocol.IR_UP)

    async def ir_navigate_down(self) -> bool:
        """Navigate down."""
        return await self.send_ir_command(JBLProtocol.IR_DOWN)

    async def ir_navigate_left(self) -> bool:
        """Navigate left."""
        return await self.send_ir_command(JBLProtocol.IR_LEFT)

    async def ir_navigate_right(self) -> bool:
        """Navigate right."""
        return await self.send_ir_command(JBLProtocol.IR_RIGHT)

    async def ir_navigate_ok(self) -> bool:
        """Navigate OK/Select."""
        return await self.send_ir_command(JBLProtocol.IR_OK)

    async def ir_menu(self) -> bool:
        """Open menu."""
        return await self.send_ir_command(JBLProtocol.IR_MENU)

    async def ir_back(self) -> bool:
        """Navigate back."""
        return await self.send_ir_command(JBLProtocol.IR_BACK)

    async def ir_display_dim(self) -> bool:
        """Toggle display brightness via IR."""
        return await self.send_ir_command(JBLProtocol.IR_DIM)
