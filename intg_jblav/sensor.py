"""
JBL AV Receiver Sensor entities.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any
from ucapi.sensor import Sensor, Attributes, DeviceClasses
from ucapi_framework.entity import Entity
from intg_jblav.config import JBLAVConfig
from intg_jblav.device import JBLAV

_LOG = logging.getLogger(__name__)


class JBLAVModelSensor(Sensor, Entity):
    """Sensor for receiver model information."""

    def __init__(self, device_config: JBLAVConfig, device: JBLAV):
        """Initialize the model sensor."""
        self._device = device
        self._device_config = device_config

        entity_id = f"sensor.{device_config.identifier}.model"

        super().__init__(
            entity_id,
            f"{device_config.name} Model",
            [],  # No features
            {
                Attributes.STATE: "Unknown",
                Attributes.VALUE: None,
                Attributes.UNIT: None,
            },
            device_class=DeviceClasses.CUSTOM,
        )

        # Subscribe to device events
        device.events.on(device.identifier, self._on_device_update)

        # Set initial value if already connected
        if device.model_name != "Unknown":
            self.attributes[Attributes.STATE] = device.model_name
            self.attributes[Attributes.VALUE] = device.model_name

    def _on_device_update(self, entity_id: str, attributes: dict[str, Any]) -> None:
        """Handle device state updates."""
        # Model is set during initialization - update if we get it
        model = self._device.model_name
        if model != "Unknown" and model != self.attributes[Attributes.STATE]:
            self.attributes[Attributes.STATE] = model
            self.attributes[Attributes.VALUE] = model
            self.emit_update()

    def emit_update(self) -> None:
        """Emit entity update to Remote."""
        if hasattr(self, 'api') and self.api:
            self.api.configured_entities.update(self)


class JBLAVVolumeSensor(Sensor, Entity):
    """Sensor for current volume level (0-99)."""

    def __init__(self, device_config: JBLAVConfig, device: JBLAV):
        """Initialize the volume sensor."""
        self._device = device
        self._device_config = device_config

        entity_id = f"sensor.{device_config.identifier}.volume"

        super().__init__(
            entity_id,
            f"{device_config.name} Volume",
            [],  # No features
            {
                Attributes.STATE: "Unknown",
                Attributes.VALUE: None,
                Attributes.UNIT: "%",
            },
            device_class=DeviceClasses.CUSTOM,
        )

        # Subscribe to device events
        device.events.on(device.identifier, self._on_device_update)

    def _on_device_update(self, entity_id: str, attributes: dict[str, Any]) -> None:
        """Handle device state updates."""
        if "volume" in attributes:
            volume = attributes["volume"]
            self.attributes[Attributes.STATE] = str(volume)
            self.attributes[Attributes.VALUE] = volume
            self.emit_update()

    def emit_update(self) -> None:
        """Emit entity update to Remote."""
        if hasattr(self, 'api') and self.api:
            self.api.configured_entities.update(self)


class JBLAVInputSensor(Sensor, Entity):
    """Sensor for current input source."""

    def __init__(self, device_config: JBLAVConfig, device: JBLAV):
        """Initialize the input sensor."""
        self._device = device
        self._device_config = device_config

        entity_id = f"sensor.{device_config.identifier}.input"

        super().__init__(
            entity_id,
            f"{device_config.name} Input",
            [],  # No features
            {
                Attributes.STATE: "Unknown",
                Attributes.VALUE: None,
                Attributes.UNIT: None,
            },
        )

        # Subscribe to device events
        device.events.on(device.identifier, self._on_device_update)

    def _on_device_update(self, entity_id: str, attributes: dict[str, Any]) -> None:
        """Handle device state updates."""
        if "source_name" in attributes:
            source_name = attributes["source_name"]
            self.attributes[Attributes.STATE] = source_name
            self.attributes[Attributes.VALUE] = source_name
            self.emit_update()

    def emit_update(self) -> None:
        """Emit entity update to Remote."""
        if hasattr(self, 'api') and self.api:
            self.api.configured_entities.update(self)


class JBLAVSurroundModeSensor(Sensor, Entity):
    """Sensor for current surround mode."""

    def __init__(self, device_config: JBLAVConfig, device: JBLAV):
        """Initialize the surround mode sensor."""
        self._device = device
        self._device_config = device_config

        entity_id = f"sensor.{device_config.identifier}.surround_mode"

        super().__init__(
            entity_id,
            f"{device_config.name} Surround Mode",
            [],  # No features
            {
                Attributes.STATE: "Unknown",
                Attributes.VALUE: None,
                Attributes.UNIT: None,
            },
        )

        # Subscribe to device events
        device.events.on(device.identifier, self._on_device_update)

    def _on_device_update(self, entity_id: str, attributes: dict[str, Any]) -> None:
        """Handle device state updates."""
        if "surround_mode_name" in attributes:
            mode_name = attributes["surround_mode_name"]
            self.attributes[Attributes.STATE] = mode_name
            self.attributes[Attributes.VALUE] = mode_name
            self.emit_update()

    def emit_update(self) -> None:
        """Emit entity update to Remote."""
        if hasattr(self, 'api') and self.api:
            self.api.configured_entities.update(self)


class JBLAVMutedSensor(Sensor, Entity):
    """Sensor for mute status."""

    def __init__(self, device_config: JBLAVConfig, device: JBLAV):
        """Initialize the muted sensor."""
        self._device = device
        self._device_config = device_config

        entity_id = f"sensor.{device_config.identifier}.muted"

        super().__init__(
            entity_id,
            f"{device_config.name} Muted",
            [],  # No features
            {
                Attributes.STATE: "Unknown",
                Attributes.VALUE: None,
                Attributes.UNIT: None,
            },
            device_class=DeviceClasses.CUSTOM,
        )

        # Subscribe to device events
        device.events.on(device.identifier, self._on_device_update)

    def _on_device_update(self, entity_id: str, attributes: dict[str, Any]) -> None:
        """Handle device state updates."""
        if "muted" in attributes:
            muted = attributes["muted"]
            state_str = "Muted" if muted else "Unmuted"
            self.attributes[Attributes.STATE] = state_str
            self.attributes[Attributes.VALUE] = state_str
            self.emit_update()

    def emit_update(self) -> None:
        """Emit entity update to Remote."""
        if hasattr(self, 'api') and self.api:
            self.api.configured_entities.update(self)


class JBLAVConnectionSensor(Sensor, Entity):
    """Sensor for connection state."""

    def __init__(self, device_config: JBLAVConfig, device: JBLAV):
        """Initialize the connection sensor."""
        self._device = device
        self._device_config = device_config

        entity_id = f"sensor.{device_config.identifier}.connection"

        super().__init__(
            entity_id,
            f"{device_config.name} Connection",
            [],  # No features
            {
                Attributes.STATE: "Disconnected",
                Attributes.VALUE: "disconnected",
                Attributes.UNIT: None,
            },
            device_class=DeviceClasses.CUSTOM,
        )

        # Subscribe to device connection events
        from ucapi_framework import DeviceEvents
        device.events.on(DeviceEvents.CONNECTED, self._on_connected)
        device.events.on(DeviceEvents.DISCONNECTED, self._on_disconnected)

    def _on_connected(self, device_id: str) -> None:
        """Handle device connected event."""
        self.attributes[Attributes.STATE] = "Connected"
        self.attributes[Attributes.VALUE] = "connected"
        self.emit_update()

    def _on_disconnected(self, device_id: str) -> None:
        """Handle device disconnected event."""
        self.attributes[Attributes.STATE] = "Disconnected"
        self.attributes[Attributes.VALUE] = "disconnected"
        self.emit_update()

    def emit_update(self) -> None:
        """Emit entity update to Remote."""
        if hasattr(self, 'api') and self.api:
            self.api.configured_entities.update(self)
