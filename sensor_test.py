from conftest import wait
import time
import logging
from conftest import SensorInfo

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
