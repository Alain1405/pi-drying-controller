import logging

from abc import ABC
from time import sleep
import RPi.GPIO as GPIO
from picamera import PiCamera
from datetime import datetime
from settings import IMAGES_FOLDER

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)


class ActuatorsConfigurationException(Exception):
    pass


class ActuatorsTriggerException(Exception):
    pass


class Actuator(ABC):
    status = None
    # id = None
    label = None

    def __init__(self, label, status=0):
        # self.id = id
        self.label = label
        self.status = status

    def __str__(self):
        return f"Actuator {self.label} is {self.status}"

    def __repr__(self):
        return str(self)

    def trigger(self, value):
        self.execute_action(value)
        self.status = value

    def execute_action(self, value):
        raise NotImplementedError()

    def reset(self):
        self.trigger(0)


class ActuatorsControl:
    actuators = []
    actuators_map: dict[str, Actuator] = {}

    def __init__(self):
        pass

    def from_actions(self, actions):
        for action in actions:
            actuator = action["actuator"]
            actuator_id = id(actuator)
            if actuator_id not in self.actuators_map.keys():
                self.actuators_map[actuator_id] = actuator

    # def execute_actions(self, actions):
    #     logging.info(f"Executing actions")
    #     for action in actions:
    #         self.execute_action(action)

    # def execute_action(self, action):
    #     self.print_action(action)

    # def print_action(self, action):
    #     logging.info(
    #         f'Switching actuator {self._actuator_name(action["id"])} to {action["status"]}'
    #     )

    def trigger_actuators(self, actions):
        for action in actions:
            actuator_id = action["actuator_id"]
            value = action["status"]
            actuator = self.actuators_map.get(actuator_id)
            if not actuator:
                raise ActuatorsTriggerException(
                    f"Actuator with id {actuator_id} not found. Available actuators: {self.actuators_map.keys()}"
                )
            actuator.trigger(value)

    def reset_actuators(self):
        for _, actuator in self.actuators_map.items():
            actuator.trigger(value=0)


class DummyActuator(Actuator):
    def __init__(self, label, status=0):
        super().__init__(label, status)

    def execute_action(self, value):
        logging.info(f"Switching actuator {self.label} to {value}")


class CameraActuator(Actuator):
    flash_pin = None

    def __init__(self, label, status=0, flash_pin=None):
        super().__init__(label, status)

        if flash_pin:
            self.flash_pin = flash_pin
            GPIO.setmode(GPIO.BCM)
            # removing the warings
            GPIO.setwarnings(False)
            # setting the mode for all pins so all will be switched on
            GPIO.setup(self.flash_pin, GPIO.OUT)
            self.flash_off()

    def flash_off(self):
        if self.flash_pin:
            logging.info("De-activating flash")
            GPIO.output(self.flash_pin, GPIO.HIGH)

    def flash_on(self):
        if self.flash_pin:
            logging.info("Activating flash")
            GPIO.output(self.flash_pin, GPIO.LOW)

    def take_picture(self):
        try:
            with PiCamera() as camera:
                if self.flash_pin:
                    self.flash_on()
                    sleep(2)
                current_td = datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")
                # Set ISO to the desired value
                camera.iso = 600
                # Wait for the automatic gain control to settle
                sleep(2)
                # Now fix the values
                camera.shutter_speed = camera.exposure_speed
                camera.exposure_mode = "off"
                g = camera.awb_gains
                camera.awb_mode = "off"
                camera.awb_gains = g
                # Finally, take a photo with the fixed settings
                image_name = f"{IMAGES_FOLDER}/image_{current_td}.jpg"
                camera.capture(image_name)

        finally:
            logging.info("Deactivating the flash")
            if self.flash_pin:
                self.flash_off()

    def execute_action(self, value):
        if value == 1:
            self.take_picture()
        else:
            logging.info("Camera is off")
