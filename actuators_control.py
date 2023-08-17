import logging
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

class ActuatorsConfigurationException(Exception):
    pass

class ActuatorsControl():
    actuators = []

    def __init__(self, schedule):

        if not schedule.get('actuators'):
            raise ActuatorsConfigurationException("Missing actuators list in schedule")
        
        self.actuators = schedule.get('actuators')

        for sched in schedule.get('schedule'):
            self.check_actions(sched.get('actions'))


    def check_actions(self, actions):
            for action in actions:
                if action.get('id') == None or action.get('id') not in self.actuators:
                    raise ActuatorsConfigurationException(f"Missing actuators {action.get('id')} in actuators list: {self.actuators}")
    
    def execute_actions(self, actions):
        logging.info(f"Executing actions")
        for action in actions:
            self.execute_action(action)
    
    def execute_action(self, action):
            self.print_action(action)

    def print_action(self, action):
        logging.info(f'Switching actuator {action["id"]} to {action["status"]}')

    def reset(self):
        for actuator in self.actuators:
            self.execute_action({"id": actuator, "status": 0})