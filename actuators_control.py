import logging

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)


class ActuatorsConfigurationException(Exception):
    pass

class ActuatorsTriggerException(Exception):
    pass

class ActuatorsControl:
    actuators = []

    def _actuators_ids(self):
        return [actuator["id"] for actuator in self.actuators]

    def _actuator_by_id(self, actuator_id):
        actuator = next(
            (actuator for actuator in self.actuators if actuator["id"] == actuator_id),
            None,
        )
        if not actuator:
            raise ActuatorsTriggerException(f"Actuator {actuator_id} not found")
        return actuator

    def _actuator_name(self, actuator_id):
        actuator = self._actuator_by_id(actuator_id)
        return actuator["label"] if actuator["label"] else actuator["id"]

    def __init__(self, schedule):
        if not schedule.get("actuators"):
            raise ActuatorsConfigurationException("Missing actuators list in schedule")

        self.actuators = schedule.get("actuators")

        for sched in schedule.get("schedule"):
            self.check_actions(sched.get("actions"))

    def check_actions(self, actions):
        for action in actions:
            if (
                action.get("id") == None
                or action.get("id") not in self._actuators_ids()
            ):
                raise ActuatorsConfigurationException(
                    f"Missing actuator {action.get('id')} in actuators list: {self.actuators}"
                )

    def execute_actions(self, actions):
        logging.info(f"Executing actions")
        for action in actions:
            self.execute_action(action)

    def execute_action(self, action):
        self.print_action(action)

    def print_action(self, action):
        logging.info(
            f'Switching actuator {self._actuator_name(action["id"])} to {action["status"]}'
        )

    def reset(self):
        for actuator in self.actuators:
            self.execute_action({"id": actuator['id'], "status": 0})
