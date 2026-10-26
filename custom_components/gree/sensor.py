"""Support for Gree sensors."""

from __future__ import annotations

# Standard library imports
import logging
from dataclasses import dataclass

# Home Assistant imports
from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
)
from homeassistant.helpers.entity import EntityCategory


# Local imports
from .const import DOMAIN
from .entity import GreeEntity, GreeEntityDescription

_LOGGER = logging.getLogger(__name__)


@dataclass
class GreeSensorEntityDescription(GreeEntityDescription, SensorEntityDescription):
    """Describes Gree Sensor entity."""

    pass


SENSORS: tuple[GreeSensorEntityDescription, ...] = (
    GreeSensorEntityDescription(
        property_key="outside_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda device: device.outside_temperature if device._has_outside_temp_sensor else None,
        available_fn=lambda device: device.available and device._has_outside_temp_sensor,
    ),
    GreeSensorEntityDescription(
        property_key="room_humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        value_fn=lambda device: device.room_humidity if device._has_room_humidity_sensor else None,
        available_fn=lambda device: device.available and device._has_room_humidity_sensor,
    ),
    GreeSensorEntityDescription(
        property_key="error_code",
        icon="mdi:alert-circle-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: device._acOptions.get("AllErr") if device._has_error_code else None,
        available_fn=lambda device: device.available and bool(device._has_error_code),
    ),
    GreeSensorEntityDescription(
        property_key="rejected_command_fields",
        icon="mdi:cancel",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: (", ".join(sorted(device._unsupported_cmd_fields)) or "none") if device._unsupported_cmd_fields is not None else None,
        available_fn=lambda device: device._unsupported_cmd_fields is not None,
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Gree sensors from a config entry."""
    # Get the device that was created in __init__.py
    entry_data = hass.data[DOMAIN][entry.entry_id]
    device = entry_data["device"]

    sensors = []

    for description in SENSORS:
        if description.exists_fn(description, device):
            sensors.append(GreeSensor(hass, entry, description))
            _LOGGER.debug(f"Added {description.property_key} sensor")

    if sensors:
        async_add_entities(sensors)
        _LOGGER.info(f"Added {len(sensors)} Gree sensors")


class GreeSensor(GreeEntity, SensorEntity):
    """Gree sensor entity."""

    entity_description: GreeSensorEntityDescription

    def __init__(self, hass, entry, description: GreeSensorEntityDescription) -> None:
        """Initialize Gree sensor."""
        super().__init__(hass, entry, description)

        # Set temperature unit for temperature sensors
        if description.device_class == SensorDeviceClass.TEMPERATURE:
            self._attr_native_unit_of_measurement = self._device.temperature_unit

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        return self.entity_description.value_fn(self._device)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.entity_description.available_fn(self._device)
