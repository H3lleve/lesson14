import requests


def send_post(method: str):
    request_body = {"method": method, "jsonrpc": "2.0", "id": 1}
    res = requests.post("http://localhost:9898/rpc", json=request_body)
    return res.json()


def get_sensor_info():
    sensor_response = send_post(method="get_info")
    sensor_info = sensor_response["result"]
    return sensor_info


def get_sensor_reading():
    sensor_response = send_post(method="get_reading")
    sensor_reading = sensor_response["result"]
    return sensor_reading


def test_sanity():
    sensor_info = get_sensor_info()

    sensor_name = sensor_info.get("name")
    assert isinstance(sensor_name, str), "sensor_name is not a string"

    sensor_hid = sensor_info.get("hid")
    assert isinstance(sensor_hid, str), "sensor_hid is not a string"

    sensor_model = sensor_info.get("model")
    assert isinstance(sensor_model, str), "sensor_model is not a string"

    sensor_fw_ver = sensor_info.get("firmware_version")
    assert isinstance(sensor_fw_ver, float), "firmware_version is not a float"

    reading_reading_interval = sensor_info.get("reading_interval")
    assert isinstance(reading_reading_interval, int), "reading_reading_interval is not an int"

    sensor_reading = get_sensor_reading()
    assert isinstance(sensor_reading, float), "Sensor doesn't seem to register temperature"

    print("Sanity test passed")


test_sanity()
