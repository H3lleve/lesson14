from conftest import wait


def test_sanity(get_sensor_info, get_sensor_reading):
    sensor_info = get_sensor_info()

    sensor_name = sensor_info.get("name")
    assert isinstance(sensor_name, str), "Sensor name is not a string"

    sensor_hid = sensor_info.get("hid")
    assert isinstance(sensor_hid, str), "Sensor hid is not a string"

    sensor_model = sensor_info.get("model")
    assert isinstance(sensor_model, str), "Sensor model is not a string"

    sensor_firmware_version = sensor_info.get("firmware_version")
    assert isinstance(
        sensor_firmware_version, int
    ), "Sensor firmware version is not a int"

    sensor_reading_interval = sensor_info.get("reading_interval")
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
    print("Get original sensor info")
    sensor_info_before_reboot = get_sensor_info()

    print("Reboot sensor")
    reboot_response = reboot_sensor()
    assert reboot_response == "rebooting", "Sensor did not return proper text in response to reboot request"

    print("Wait for sensor to come back online")
    sensor_info_after_reboot = wait(
        func=get_sensor_info,
        condition=lambda x: isinstance(x, dict),
        tries=10,
        timeout=1,
    )

    print("Validate that info from Step 1 is equal to info from Step 4")
    assert sensor_info_before_reboot == sensor_info_after_reboot, ("Sensor info after reboot "
                                                                   "doesn't match sensor info before reboot")


def test_set_sensor_name(get_sensor_info, set_sensor_name):
    """
    1. Set sensor name to "new_name".
    2. Get sensor_info.
    3. Validate that current sensor name matches the name set in Step 1.
    """
    print("Step 1", 'Set sensor name to "new_name"')
    updated_sensor_name = "new_name"
    set_sensor_name(updated_sensor_name)

    print("Step 2", 'Get sensor_info')
    sensor_info_after_name_change = get_sensor_info()

    print("Step 3", 'Validate that current sensor name matches the name set in Step 1')
    assert sensor_info_after_name_change.get("name") == updated_sensor_name


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
    print("Step 1", "Set sensor reading interval to 1")
    new_sensor_reading_interval = 1
    set_sensor_reading_interval(new_sensor_reading_interval)

    print("Step 2", "Get sensor info")
    sensor_info_step2 = get_sensor_info()

    print("Step 3", "Validate that sensor reading interval is set to interval from Step 1")
    assert sensor_info_step2.get("reading_interval") == new_sensor_reading_interval

    print("Step 4", "Get sensor reading")
    sensor_reading_step4 = get_sensor_reading()

    print("Step 5", "Wait for interval specified in Step 1")
    wait(func=get_sensor_reading,
         condition=lambda x: isinstance(x, dict),
         tries=5,
         timeout=new_sensor_reading_interval)

    print("Step 6", "Get sensor reading")
    sensor_reading_step6 = get_sensor_reading()

    print("Step 7", "Validate that reading from Step 4 doesn't equal reading from Step 6")
    assert sensor_reading_step6 != sensor_reading_step4


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

    print("Step 1" "Get original sensor firmware version")
    original_sensor_fw_ver = get_sensor_info().get("firmware_version")

    print("Step 2" "Request firmware update")
    sensor_fw_upgrade_request = update_sensor_firmware()
    assert sensor_fw_upgrade_request == "updating"
    wait(func=get_sensor_info, condition=lambda x: isinstance(x, dict), tries=15, timeout=3)

    print("Step 3" "Get current sensor firmware version")
    current_sensor_fw_ver = get_sensor_info().get("firmware_version")

    print("Step 4" "Validate that current firmware version is +1 to original firmware version")
    assert current_sensor_fw_ver == (original_sensor_fw_ver + 1)

    print("Step 5" "Repeat steps 1-4 until sensor is at max_firmware_version - 1")
    while current_sensor_fw_ver < max_firmware_version - 1:
        sensor_fw_upgrade_request = update_sensor_firmware()
        assert sensor_fw_upgrade_request == "updating"
        wait(func=get_sensor_info, condition=lambda x: isinstance(x, dict), tries=15, timeout=3)

        current_sensor_fw_ver = get_sensor_info().get("firmware_version")

    print("Step 6" "Update sensor to max firmware version")
    sensor_fw_upgrade_request = update_sensor_firmware()
    assert sensor_fw_upgrade_request == "updating"
    wait(func=get_sensor_info, condition=lambda x: isinstance(x, dict), tries=15, timeout=3)

    print("Step 7" "Validate that sensor is at max firmware version")
    assert get_sensor_info().get("firmware_version") == max_firmware_version

    print("Step 8" "Request another firmware update")
    sensor_fw_upgrade_request = update_sensor_firmware()

    print("Step 9" "Validate that sensor doesn't update and responds appropriately")
    assert sensor_fw_upgrade_request != "updating"
    assert sensor_fw_upgrade_request == "already at latest firmware version"

    print("Step 10" "Validate that sensor firmware version doesn't change if it's at maximum value")
    assert get_sensor_info().get("firmware_version") == max_firmware_version
