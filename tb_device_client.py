import logging.handlers
import os
import shutil
from tb_gateway_mqtt import TBDeviceMqttClient
import time
import adafruit_dht
from board import D5, D6, D13, D19

from dotenv import load_dotenv

load_dotenv()

THINGSBOARD_SERVER = os.getenv("THINGSBOARD_SERVER")
THINGSBOARD_PORT = int(os.getenv("THINGSBOARD_PORT"))

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)


class ThingsBoardDevice:
    """
    This class is a wrapper for the ThingsBoardClient class.
    It allows you to create a device with states and RPC callbacks.

    "states" format: { "state_name": { "value": "state_value" } }
    "rpc_callbacks" format: { "rpc_method_name": "callback_function or string representing class method" }

    """

    client: TBDeviceMqttClient = None
    states: dict = {}
    rpc_callbacks: dict = {}

    def __init__(
        self, ACCESS_TOKEN, states: dict = {}, rpc_callbacks: dict = {}
    ) -> None:
        logging.info(f"Initializing ThingsBoardDevice {self.__class__.__name__}")
        self.client = TBDeviceMqttClient(
            THINGSBOARD_SERVER, THINGSBOARD_PORT, ACCESS_TOKEN
        )
        self.connect()

        if states:
            if type(states) is not dict:
                raise TypeError("States must be a dictionary")
            self.states = states

            for key, value in states.items():
                # Initiate states
                setattr(self, key, value)

            self.client.subscribe_to_all_attributes(self.attribute_callback)
            # Get all states from server
            self.client.request_attributes(
                shared_keys=list(self.states.keys()), callback=self.sync_state
            )

        if rpc_callbacks:
            if type(rpc_callbacks) is not dict:
                raise TypeError(
                    f"RPC callbacks must be a dictionary, receive {type(rpc_callbacks)}"
                )
            self.rpc_callbacks = rpc_callbacks
            self.client.set_server_side_rpc_request_handler(self.register_rpc_callbacks)

    # request attribute callback
    def sync_state(self, result, exception=None):
        logging.info(f"Synchronizing ThingsBoardDevice {self.__class__.__name__}")
        global period
        if exception is not None:
            logging.warning("Exception: " + str(exception), exc_info=exception)
        else:
            shared_attributes = result.get("shared", {})
            logging.info("Synchronizing status with server")
            for key, value in shared_attributes.items():
                logging.info(f"Setting {key} to {value}")
                setattr(self, key, value)

    # callback function that will call when we will change value of our Shared Attribute
    def attribute_callback(self, results, _):
        logging.info("Received new shared attribute values from ThingsBoard")
        for key, value in results.items():
            logging.info(f"Setting {key} to {value}")
            setattr(self, key, value)

    # callback function that will call when we will send RPC
    def register_rpc_callbacks(self, id, request_body):
        # request body contains method and other parameters
        logging.info(f"Received rpc callback with body: {request_body}")
        method_key = request_body.get("method")
        if method_key in self.rpc_callbacks.keys():
            cb = None
            if callable(self.rpc_callbacks[method_key]):
                cb = self.rpc_callbacks[method_key]
            elif (
                type(self.rpc_callbacks[method_key]) is str
                and hasattr(self, self.rpc_callbacks[method_key])
                and callable(getattr(self, self.rpc_callbacks[method_key]))
            ):
                cb = getattr(self, self.rpc_callbacks[method_key])
            if not cb:
                logging.warning(f"Invalid callback for method '{method_key}'")
            else:
                logging.info(f"Executing RPC callback {cb}")
                cb()
        else:
            logging.info(
                f"Unknown method '{method_key}'. Available methods are: {self.rpc_callbacks.keys().join(', ')}"
            )

    def get_data(self) -> tuple[dict, dict]:
        raise NotImplementedError()

    def connect(self):
        logging.info(f"Connecting ThingsBoardDevice {self.__class__.__name__}")
        if not self.client.is_connected():
            self.client.connect()

    def publish(self):
        logging.info(f"Publishing data for ThingsBoardDevice {self.__class__.__name__}")
        self.connect()
        attributes, telemetry = self.get_data()
        if attributes:
            logging.info(f"Sending attributes: {attributes}")
            self.client.send_attributes(attributes)
        if telemetry:
            logging.info(f"Sending telemetry: {telemetry}")
            self.client.send_telemetry(telemetry)

    def disconnect(self):
        self.client.disconnect()


class TempHumDevice(ThingsBoardDevice):
    devices = []

    def __init__(
        self,
        ACCESS_TOKEN,
        states: dict = {},
        rpc_callbacks: dict = {},
        sensors_config=[
            {"pin": D5, "label": "Top"},
            {"pin": D6, "label": "Top-middle"},
            {"pin": D13, "label": "Bottom-middle"},
            {"pin": D19, "label": "Bottom"},
        ],
    ) -> None:
        rpc_callbacks.update({"getTelemetry": "publish"})
        # states.update({"blinkingPeriod": 1.0})
        super().__init__(ACCESS_TOKEN, states, rpc_callbacks)

        for sensor_config in sensors_config:
            self.devices.append(
                {
                    "sensor": adafruit_dht.DHT22(sensor_config["pin"], use_pulseio=False),
                    "label": sensor_config["label"],
                }
            )

    def get_data(self):
        logging.info("Getting temp humidity telemetry")
        telemetry = []
        # import pdb; pdb.set_trace()
        for device in self.devices:
            try:
                logging.info(f"Reading sensor {device['label']}")

                temperature = device["sensor"].temperature
                humidity = device["sensor"].humidity

                if humidity is not None and temperature is not None:
                    logging.info(
                        "Temp={0:0.1f}C  Humidity={1:0.1f}%".format(temperature, humidity)
                    )
                else:
                    logging.info("Failed to retrieve data from humidity sensor")

                telemetry.append(
                    {
                        f"temperature_{device['label']}": temperature,
                        f"humidity_{device['label']}": humidity,
                    }
                )
            except RuntimeError as error:
                # Errors happen fairly often, DHT's are hard to read, just keep going
                logging.error(f"Failed reading sensor {device['label']}", exc_info=True)
            except:
                logging.error(f"Failed reading sensor {device['label']}. Deactivating", exc_info=True)
                # try:
                #     device["sensor"].exit()
                # except:
                #     logging.error(f"Failed deactivating sensor {device['label']}", exc_info=True)

            finally:
                # ✅
                logging.info("Exiting sensor")
                time.sleep(2.0)
                try:
                    device["sensor"].exit()
                except:
                    logging.error(f"Failed deactivating sensor {device['label']}", exc_info=True)

        logging.info(f"Telemetry for temhumidity: {telemetry}")
        return {}, telemetry


class RPIDevice(ThingsBoardDevice):
    def __init__(
        self, ACCESS_TOKEN, states: dict = {}, rpc_callbacks: dict = {}
    ) -> None:
        rpc_callbacks.update({"getTelemetry": "publish"})
        states.update({"blinkingPeriod": 1.0})
        super().__init__(ACCESS_TOKEN, states, rpc_callbacks)

    def get_data(self):
        cpu_usage = round(
            float(
                os.popen(
                    """grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$4+$5)} END {print usage }' """
                )
                .readline()
                .replace("\n", "")
                .replace(",", ".")
            ),
            2,
        )
        ip_address = (
            os.popen("""hostname -I""")
            .readline()
            .replace("\n", "")
            .replace(",", ".")[:-1]
        )
        mac_address = (
            os.popen("""cat /sys/class/net/*/address""")
            .readline()
            .replace("\n", "")
            .replace(",", ".")
        )
        processes_count = (
            os.popen("""ps -Al | grep -c bash""")
            .readline()
            .replace("\n", "")
            .replace(",", ".")
        )
        swap_memory_usage = (
            os.popen("free -m | grep Swap | awk '{print ($3/$2)*100}'")
            .readline()
            .replace("\n", "")
            .replace(",", ".")
        )
        ram_usage = float(
            os.popen("free -m | grep Mem | awk '{print ($3/$2) * 100}'")
            .readline()
            .replace("\n", "")
            .replace(",", ".")[:-1]
        )

        disk_available = shutil.disk_usage("/").free / 1024 / 1024 / 1024
        disk_used = shutil.disk_usage("/").used / 1024 / 1024 / 1024
        boot_time = os.popen("uptime -p").read()[:-1]
        avg_load = (cpu_usage + ram_usage) / 2
        cpu_temp = float(
            os.popen(
                "cat /sys/class/thermal/thermal_zone0/temp | awk '{print $1/1000}'"
            )
            .readline()
            .replace("\n", "")
            .replace(",", ".")
        )

        gpu_temp = float(
            os.popen("vcgencmd measure_temp | grep  -o -E '[[:digit:]].*'")
            .readline()
            .replace("\n", "")
            .replace("'C", "")
            .replace(",", ".")
        )

        attributes = {"ip_address": ip_address, "macaddress": mac_address}
        telemetry = {
            "cpu_usage": cpu_usage,
            "processes_count": processes_count,
            "disk_usage": disk_used,
            "disk_available": disk_available,
            "RAM_usage": ram_usage,
            "swap_memory_usage": swap_memory_usage,
            "boot_time": boot_time,
            "avg_load": avg_load,
            "cpu_temp": cpu_temp,
            "gpu_temp": gpu_temp,
        }
        return attributes, telemetry
