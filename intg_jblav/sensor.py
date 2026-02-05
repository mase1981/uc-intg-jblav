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
