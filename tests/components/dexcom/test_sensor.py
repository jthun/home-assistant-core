"""The sensor tests for the griddy platform."""

from unittest.mock import patch

from pydexcom import GlucoseReading
from pydexcom.errors import SessionError

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_component import async_update_entity
from homeassistant.util import dt as dt_util

from . import GLUCOSE_READING, init_integration


async def test_sensors(hass: HomeAssistant) -> None:
    """Test we get sensor data."""
    await init_integration(hass)

    test_username_glucose_value = hass.states.get("sensor.test_username_glucose_value")
    assert test_username_glucose_value.state == str(GLUCOSE_READING.value)
    test_username_glucose_trend = hass.states.get("sensor.test_username_glucose_trend")
    assert test_username_glucose_trend.state == GLUCOSE_READING.trend_description
    measurement_time = hass.states.get("sensor.test_username_glucose_measurement_time")
    assert measurement_time.state == dt_util.as_utc(GLUCOSE_READING.datetime).isoformat(
        timespec="seconds"
    )
    assert measurement_time.attributes["device_class"] == SensorDeviceClass.TIMESTAMP


async def test_sensors_unknown(hass: HomeAssistant) -> None:
    """Test we handle sensor state unknown."""
    await init_integration(hass)

    with patch(
        "homeassistant.components.dexcom.Dexcom.get_current_glucose_reading",
        return_value=None,
    ):
        await async_update_entity(hass, "sensor.test_username_glucose_value")
        await async_update_entity(hass, "sensor.test_username_glucose_trend")

    test_username_glucose_value = hass.states.get("sensor.test_username_glucose_value")
    assert test_username_glucose_value.state == STATE_UNKNOWN
    test_username_glucose_trend = hass.states.get("sensor.test_username_glucose_trend")
    assert test_username_glucose_trend.state == STATE_UNKNOWN
    measurement_time = hass.states.get("sensor.test_username_glucose_measurement_time")
    assert measurement_time.state == STATE_UNKNOWN


async def test_sensors_update_failed(hass: HomeAssistant) -> None:
    """Test we handle sensor update failed."""
    await init_integration(hass)

    with patch(
        "homeassistant.components.dexcom.Dexcom.get_current_glucose_reading",
        side_effect=SessionError,
    ):
        await async_update_entity(hass, "sensor.test_username_glucose_value")
        await async_update_entity(hass, "sensor.test_username_glucose_trend")

    test_username_glucose_value = hass.states.get("sensor.test_username_glucose_value")
    assert test_username_glucose_value.state == STATE_UNAVAILABLE
    test_username_glucose_trend = hass.states.get("sensor.test_username_glucose_trend")
    assert test_username_glucose_trend.state == STATE_UNAVAILABLE
    measurement_time = hass.states.get("sensor.test_username_glucose_measurement_time")
    assert measurement_time.state == STATE_UNAVAILABLE


async def test_measurement_time_updates_with_same_glucose(hass: HomeAssistant) -> None:
    """Test a new reading updates measurement time even when glucose is unchanged."""
    await init_integration(hass)
    reading = GlucoseReading({**GLUCOSE_READING.json, "DT": "Date(1745082213085-0400)"})

    with patch(
        "homeassistant.components.dexcom.Dexcom.get_current_glucose_reading",
        return_value=reading,
    ) as get_reading:
        await async_update_entity(hass, "sensor.test_username_glucose_value")

    get_reading.assert_called_once_with()
    glucose = hass.states.get("sensor.test_username_glucose_value")
    assert glucose.state == str(GLUCOSE_READING.value)
    measurement_time = hass.states.get("sensor.test_username_glucose_measurement_time")
    assert measurement_time.state == dt_util.as_utc(reading.datetime).isoformat(
        timespec="seconds"
    )
    assert measurement_time.state != dt_util.as_utc(GLUCOSE_READING.datetime).isoformat(
        timespec="seconds"
    )
