from time import sleep
import pytest
from enum import Enum
import requests
from typing import Callable
import logging
from dataclasses import dataclass


log = logging.getLogger(__name__)


@dataclass
class SensorInfo:
    name: str
    hid: str
    model: str
    firmware_version: int
    reading_interval: int

    def __post_init__(self):
        if not isinstance(self.name, str):
            raise TypeError("'name' should be a string")
        if self.name == "":
            raise ValueError("'name' should not be empty")

        if not isinstance(self.hid, str):
            raise TypeError("'hid' should be a string")
        if self.hid == "":
            raise ValueError("'hid' should not be empty")

        if not isinstance(self.model, str):
            raise TypeError("'model' should be a string")
        if self.model == "":
            raise ValueError("'model' should not be empty")

        if not isinstance(self.firmware_version, int):
            raise TypeError("'firmware_version' should be an int")
        if not 10 <= self.firmware_version <= 15:
            raise ValueError("'firmware_version' should be between 10 and 15")

        if not isinstance(self.reading_interval, int):
            raise TypeError("'reading_interval' should be an int")
        if self.reading_interval < 1:
            raise ValueError("'reading_interval' should be equal or more than 1")


class SensorMethod(Enum):
    GET_INFO = "get_info"
    GET_READING = "get_reading"
    SET_NAME = "set_name"
    GET_METHODS = "get_methods"
    SET_READING_INTERVAL = "set_reading_interval"
    RESET_TO_FACTORY = "reset_to_factory"
    UPDATE_FIRMWARE = "update_firmware"
    REBOOT = "reboot"


def make_valid_payload(
    method: SensorMethod, params: dict | None = None
) -> dict:
    payload = {"method": method, "jsonrpc": "2.0", "id": 1}

    if params:
        payload["params"] = params

    return payload


def wait(
    func: Callable, condition: Callable, tries: int, timeout: int, **kwargs
):
    for i in range(tries):
        try:
            log.debug(
                f"Calling function {func.__name__} with args {kwargs} - attempt {i + 1}"
            )
            result = func(**kwargs)

            log.debug(
                f"Evaluating result of the call with function {condition.__name__}"
            )
            if condition(result):
                return result
        except Exception as e:
            log.debug(f"Function call raised exception {e}, ignoring it")

        log.debug(f"Sleeping for {timeout} seconds")
        sleep(timeout)

    log.debug(
        "Exhausted all tries, condition evaluates to False, returning None"
    )
    return


def pytest_addoption(parser):
    parser.addoption(
        "--sensor-host",
        action="store",
        default="http://127.0.0.1",
        help="Sensor host",
    )
    parser.addoption(
        "--sensor-port", action="store", default="9898", help="Sensor port"
    )
    parser.addoption(
        "--sensor-pin", action="store", default="0000", help="Sensor pin"
    )


@pytest.fixture(scope="session")
def sensor_host(request):
    return request.config.getoption("--sensor-host")


@pytest.fixture(scope="session")
def sensor_port(request):
    return request.config.getoption("--sensor-port")


@pytest.fixture(scope="session")
def sensor_pin(request):
    return request.config.getoption("--sensor-pin")


@pytest.fixture(scope="session")
def send_post(sensor_host, sensor_port, sensor_pin):
    def _send_post(
        method: SensorMethod | None = None,
        params: dict | None = None,
        jsonrpc: str | None = None,
        id: int | None = None,
    ):
        request_body = {}

        if method:
            request_body["method"] = method.value

        if params:
            request_body["params"] = params

        if jsonrpc:
            request_body["jsonrpc"] = jsonrpc

        if id:
            request_body["id"] = id

        request_headers = {"Authorization": sensor_pin}
        res = requests.post(
            f"{sensor_host}:{sensor_port}/rpc",
            json=request_body,
            headers=request_headers,
        )

        return res.json()

    return _send_post


@pytest.fixture(scope="session")
def make_valid_request(send_post):
    def _make_valid_request(
        method: SensorMethod, params: dict | None = None
    ) -> dict:
        payload = make_valid_payload(method=method, params=params)
        sensor_response = send_post(**payload)
        return sensor_response

    return _make_valid_request


@pytest.fixture(scope="session")
def get_sensor_info(make_valid_request):
    def _get_sensor_info():
        log.info("Get sensor info")
        sensor_response = make_valid_request(SensorMethod.GET_INFO)
        result = None

        if "result" in sensor_response:
            result = SensorInfo(**sensor_response["result"])

        if "error" in sensor_response:
            result = sensor_response["error"]

        return result

    return _get_sensor_info


@pytest.fixture(scope="session")
def get_sensor_reading(make_valid_request):
    def _get_sensor_reading():
        log.info("Get sensor reading")
        sensor_response = make_valid_request(SensorMethod.GET_READING)
        return sensor_response["result"]

    return _get_sensor_reading


@pytest.fixture(scope="session")
def set_sensor_name(make_valid_request):
    def _set_sensor_name(name: str):
        log.info("Set sensor name to %s", name)
        sensor_response = make_valid_request(SensorMethod.SET_NAME, {"name": name})
        result = None

        if "result" in sensor_response:
            result = SensorInfo(**sensor_response["result"])

        if "error" in sensor_response:
            result = sensor_response["error"]

        return result

    return _set_sensor_name


@pytest.fixture(scope="session")
def get_sensor_methods(make_valid_request):
    def _get_sensor_methods():
        log.info("Get sensor methods")
        return make_valid_request(SensorMethod.GET_METHODS)

    return _get_sensor_methods


@pytest.fixture(scope="session")
def set_sensor_reading_interval(make_valid_request):
    def _set_sensor_reading_interval(interval: int):
        log.info("Set sensor reading interval to %d seconds", interval)
        sensor_response = make_valid_request(SensorMethod.SET_READING_INTERVAL, {"interval": interval})
        result = None

        if "result" in sensor_response:
            result = SensorInfo(**sensor_response["result"])

        if "error" in sensor_response:
            result = sensor_response["error"]

        return result

    return _set_sensor_reading_interval


@pytest.fixture(scope="session")
def reset_sensor_to_factory(make_valid_request, get_sensor_info):
    def _reset_sensor_to_factory():
        log.info("Send reset firmware request to sensor")
        sensor_response = make_valid_request(SensorMethod.RESET_TO_FACTORY)
        if "result" in sensor_response:
            if sensor_response["result"] != "resetting":
                raise RuntimeError("Sensor didn't respond to factory reset properly")

            sensor_info = wait(get_sensor_info,
                               lambda x: isinstance(x, SensorInfo),
                               tries=15,
                               timeout=1)
            if not sensor_info:
                raise RuntimeError("Sensor didn't reset to factory property")

            return sensor_info

        if "error" in sensor_response:
            return sensor_response["error"]

    return _reset_sensor_to_factory


@pytest.fixture(scope="session")
def update_sensor_firmware(make_valid_request):
    def _update_sensor_firmware():
        log.info("Send firmware update request to sensor")
        sensor_response = make_valid_request(SensorMethod.UPDATE_FIRMWARE)
        return sensor_response["result"]
    return _update_sensor_firmware


@pytest.fixture(scope="session")
def reboot_sensor(make_valid_request):
    def _reboot_sensor():
        log.info("Send reboot request to sensor")
        sensor_response = make_valid_request(SensorMethod.REBOOT)
        return sensor_response["result"]

    return _reboot_sensor


@pytest.fixture(scope="session")
def factory_sensor_settings(reset_sensor_to_factory):
    log.info("Reset sensor to factory defaults")
    yield reset_sensor_to_factory()


@pytest.fixture(autouse=True)
def ensure_sensor_factory_settings(
    factory_sensor_settings, reset_sensor_to_factory, get_sensor_info
):
    current_sensor_settings = get_sensor_info()
    log.info("Ensure sensor has factory settings before starting test")
    if current_sensor_settings != factory_sensor_settings:
        log.info("Detected non-factory settings, resetting sensor")
        reset_sensor_to_factory()
