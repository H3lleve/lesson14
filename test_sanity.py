import requests
from requests.exceptions import JSONDecodeError


def make_valid_payload(method: str, params: dict | None = None) -> dict:
    payload = {"method": method, "jsonrpc": "2.0", "id": 1}

    if params:
        payload["params"] = params

    return payload


def send_post(method: str | None = None, params: dict | None = None,
              jsonrpc: str | None = None, id: int | None = None):
    request_body = {}

    if method:
        request_body["method"] = method

    if params:
        request_body["params"] = params

    if jsonrpc:
        request_body["jsonrpc"] = jsonrpc

    if id:
        request_body["id"] = id

    request_headers = {"Authorization": "0000"}
    res = requests.post("http://localhost:9898/rpc", json=request_body, headers=request_headers)

    try:
        return res.json()
    except JSONDecodeError:
        return {}


def get_sensor_info():
    payload = make_valid_payload(method="get_info")
    sensor_response = send_post(**payload)
    sensor_info = sensor_response.get("result", {})
    return sensor_info


def get_sensor_reading():
    payload = make_valid_payload(method="get_reading")
    sensor_response = send_post(**payload)
    sensor_reading = sensor_response.get("result", {})
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
    assert isinstance(sensor_fw_ver, int), "firmware_version is not an int"

    reading_reading_interval = sensor_info.get("reading_interval")
    assert isinstance(reading_reading_interval, int), "reading_reading_interval is not an int"

    sensor_reading = get_sensor_reading()
    assert isinstance(sensor_reading, float), "Sensor doesn't seem to register temperature"

    print("Sanity test passed")
