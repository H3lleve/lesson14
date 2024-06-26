from conftest import wait
import time
import logging
from conftest import SensorInfo
import pytest
from requests import post


METHOD_ERROR_CODE = -32000
METHOD_ERROR_MSG = "Method execution error"
PARSE_ERROR_CODE = -32700
PARSE_ERROR_MSG = "Parse error"
INVALID_REQUEST_CODE = -32600
INVALID_REQUEST_MSG = "Invalid request"
METHOD_NOT_FOUND_CODE = -32601
METHOD_NOT_FOUND_MSG = "Method not found"
INVALID_PARAMS_CODE = -32602
INVALID_PARAMS_MSG = "Invalid params"


log = logging.getLogger(__name__)


def test_sanity(get_sensor_info, get_sensor_reading):
    sensor_info = get_sensor_info()

    sensor_name = sensor_info.name
    assert isinstance(sensor_name, str), "Sensor name is not a string"

    sensor_hid = sensor_info.hid
    assert isinstance(sensor_hid, str), "Sensor hid is not a string"

    sensor_model = sensor_info.model
    assert isinstance(sensor_model, str), "Sensor model is not a string"

    sensor_firmware_version = sensor_info.firmware_version
    assert isinstance(
        sensor_firmware_version, int
    ), "Sensor firmware version is not a int"

    sensor_reading_interval = sensor_info.reading_interval
    assert isinstance(
        sensor_reading_interval, int
    ), "Sensor reading interval is not a string"

    sensor_reading = get_sensor_reading()
    assert isinstance(
        sensor_reading, float
    ), "Sensor doesn't seem to register temperature"

    print("Sanity test passed")


def test_reboot(get_sensor_info, reboot_sensor):
    """
    Steps:
        1. Get original sensor info.
        2. Reboot sensor.
        3. Wait for sensor to come back online.
        4. Get current sensor info.
        5. Validate that info from Step 1 is equal to info from Step 4.
    """
    log.info("Get original sensor info")
    sensor_info_before_reboot = get_sensor_info()

    log.info("Reboot sensor")
    reboot_response = reboot_sensor()
    assert (
        reboot_response == "rebooting"
    ), "Sensor did not return proper text in response to reboot request"

    log.info("Wait for sensor to come back online")
    sensor_info_after_reboot = wait(
        func=get_sensor_info,
        condition=lambda x: isinstance(x, SensorInfo), tries=10, timeout=1)

    log.info("Validate that info from Step 1 is equal to info from Step 4")
    assert (
        sensor_info_before_reboot == sensor_info_after_reboot
    ), "Sensor info after reboot doesn't match sensor info before reboot"


def test_set_sensor_name(get_sensor_info, set_sensor_name):
    """
    1. Set sensor name to "new_name".
    2. Get sensor_info.
    3. Validate that current sensor name matches the name set in Step 1.
    """
    expected_name = "new_name"
    log.info(f"Set sensor name to {expected_name}")
    set_sensor_name(expected_name)

    log.info("Get sensor info")
    sensor_info = get_sensor_info()

    log.info("Validate that current sensor name matches the name set in Step 1")
    assert sensor_info.name == expected_name, "Sensor didn't set its name correctly"


def test_set_sensor_reading_interval(
        get_sensor_info, set_sensor_reading_interval, get_sensor_reading
):
    """
    1. Set sensor reading interval to 1.
    2. Get sensor info.
    3. Validate that sensor reading interval is set to interval from Step 1.
    4. Get sensor reading.
    5. Wait for interval specified in Step 1.
    6. Get sensor reading.
    7. Validate that reading from Step 4 doesn't equal reading from Step 6.
    """
    new_sensor_reading_interval = 1

    log.info(f"Set sensor reading interval to {new_sensor_reading_interval}")
    set_sensor_reading_interval(new_sensor_reading_interval)

    log.info(f"Get sensor info")
    sensor_info_after_reading_interval_change = get_sensor_info()

    log.info(f"Validate that sensor reading interval is set to interval from Step 1")
    assert sensor_info_after_reading_interval_change.reading_interval == new_sensor_reading_interval

    log.info(f"Get sensor reading")
    sensor_reading_before_wait = get_sensor_reading()

    log.info(f"Wait for interval specified in Step 1")
    time.sleep(new_sensor_reading_interval)

    log.info(f"Get sensor reading")
    sensor_reading_after_wait = get_sensor_reading()

    log.info(f"Validate that reading from Step 4 doesn't equal reading from Step 6")
    assert sensor_reading_after_wait != sensor_reading_before_wait


# Максимальна версія прошивки сенсора -- 15
def test_update_sensor_firmware(get_sensor_info, update_sensor_firmware):
    """
    1. Get original sensor firmware version.
    2. Request firmware update.
    3. Get current sensor firmware version.
    4. Validate that current firmware version is +1 to original firmware version.
    5. Repeat steps 1-4 until sensor is at max_firmware_version - 1.
    6. Update sensor to max firmware version.
    7. Validate that sensor is at max firmware version.
    8. Request another firmware update.
    9. Validate that sensor doesn't update and responds appropriately.
    10. Validate that sensor firmware version doesn't change if it's at maximum value.
    """
    max_firmware_version = 15

    log.info(f"Get original sensor firmware version")
    current_sensor_fw_ver = get_sensor_info().firmware_version

    while current_sensor_fw_ver < max_firmware_version - 1:
        sensor_fw_ver_before_update = current_sensor_fw_ver

        log.info(f"Request firmware update")
        sensor_fw_update_request = update_sensor_firmware()
        assert sensor_fw_update_request == "updating"

        log.info(f"Get current sensor firmware version")
        current_sensor_fw_ver = wait(
            func=lambda: get_sensor_info().firmware_version,
            condition=lambda x: isinstance(x, int), tries=15, timeout=3)

        log.info(f"Validate that current firmware version is +1 to original firmware version")
        assert current_sensor_fw_ver == (sensor_fw_ver_before_update + 1)

    log.info(f"Update sensor to max firmware version")
    sensor_fw_update_request = update_sensor_firmware()
    assert sensor_fw_update_request == "updating"

    current_sensor_fw_ver = wait(
        func=lambda: get_sensor_info().firmware_version,
        condition=lambda x: isinstance(x, int), tries=15, timeout=3)

    log.info(f"Validate that sensor is at max firmware version")
    assert current_sensor_fw_ver == max_firmware_version

    log.info(f"Request another firmware update")
    sensor_fw_update_request = update_sensor_firmware()

    log.info(f"Validate that sensor doesn't update and responds appropriately")
    assert sensor_fw_update_request == "already at latest firmware version"

    log.info(f"Validate that sensor firmware version doesn't change if it's at maximum value")
    assert get_sensor_info().firmware_version == max_firmware_version


@pytest.mark.parametrize("invalid_interval", [0.4, -1])
def test_set_invalid_sensor_reading_interval(get_sensor_info, set_sensor_reading_interval, invalid_interval):
    """
    Test Steps:
        1. Get original sensor reading interval.
        2. Set interval to < 1
        3. Validate that sensor responds with an error.
        4. Get current sensor reading interval.
        5. Validate that sensor reading interval didn't change.
    """

    log.info(f"Get original sensor reading interval.")
    original_sensor_reading_interval = get_sensor_info().reading_interval

    log.info(f"Set interval to < 1")
    sensor_response = set_sensor_reading_interval(invalid_interval)

    log.info(f"Validate that sensor responds with an error.")
    assert sensor_response.get("code") and sensor_response.get("message"), "Sensor response doesn't seem to be an error"

    assert sensor_response.get("code") == METHOD_ERROR_CODE, "Error code doesn't match expected"
    assert sensor_response.get("message") == METHOD_ERROR_MSG, "Error message doesn't match expected"

    log.info(f"Get current sensor reading interval.")
    log.info("Validate that sensor reading interval didn't change.")
    assert original_sensor_reading_interval == get_sensor_info().reading_interval, \
        "Sensor reading interval changed when it shouldn't have"


def test_set_empty_sensor_name(get_sensor_info, set_sensor_name):
    """
    Test Steps:
        1. Get original sensor name.
        2. Set sensor name to an empty string.
        3. Validate that sensor responds with an error.
        4. Get current sensor name.
        5. Validate that sensor name didn't change.
    """
    log.info("Get original sensor name.")
    original_sensor_name = get_sensor_info().name

    log.info("Set sensor name to an empty string.")
    log.info("Validate that sensor responds with an error.")
    sensor_response = set_sensor_name("")

    assert sensor_response.get("code") and sensor_response.get("message"), "Sensor response doesn't seem to be an error"

    assert (sensor_response.get("code") == METHOD_ERROR_CODE), "Error code doesn't match expected"
    assert (sensor_response.get("message") == METHOD_ERROR_MSG), "Error message doesn't match expected"

    log.info("Get current sensor name.")
    log.info("Validate that sensor name didn't change.")
    assert original_sensor_name == get_sensor_info().name, "Sensor name changed to incorrect value"


@pytest.mark.parametrize(
    "payload,expected_error_code,expected_error_msg",
    [
        ('{"method": "get_methods" "jsonrpc": "2.0", "id": 1}',
         PARSE_ERROR_CODE,
         PARSE_ERROR_MSG),

        ('{"method": "get_methods", "jsonrpc": "two point zero", "id": 1}',
         INVALID_REQUEST_CODE,
         INVALID_REQUEST_MSG),

        ('{"method": "ged_methodses", "jsonrpc": "2.0", "id": 1}',
         METHOD_NOT_FOUND_CODE,
         METHOD_NOT_FOUND_MSG),

        ('{"method": "set_reading_interval", "jsonrpc": "2.0", "id": 1, "interval": "-4"}',
         INVALID_PARAMS_CODE,
         INVALID_PARAMS_MSG),

        ('{"method": "set_reading_interval", "jsonrpc": "2.0", "id": 1, "params": {"interval": ""}}',
         METHOD_ERROR_CODE,
         METHOD_ERROR_MSG),
    ],
)
def test_sensor_errors(
    sensor_host,
    sensor_port,
    sensor_pin,
    payload,
    expected_error_code,
    expected_error_msg,
):
    sensor_response = post(
        f"{sensor_host}:{sensor_port}/rpc",
        data=payload,
        headers={"authorization": sensor_pin})

    assert (sensor_response.status_code == 200), "Wrong status code from sensor in response to invalid request"

    sensor_response_json = sensor_response.json()
    assert ("error" in sensor_response_json), "Sensor didn't respond with error to invalid request"

    error_from_sensor = sensor_response_json["error"]

    assert (error_from_sensor.get("code") == expected_error_code), "Sensor didn't respond with correct error code"
    assert (error_from_sensor.get("message") == expected_error_msg), "Sensor didn't' respond with correct error message"
