# Core Orchestrator

from nexoraAI.pre_action_safety_layer import PreActionSafetyLayer


class Orchestrator:
    STATUS_STARTED = "orchestrator_started"
    STATUS_STOPPED = "orchestrator_stopped"

    def __init__(self):
        self._started = False
        self.pre_action_safety_layer = PreActionSafetyLayer()

    def start(self):
        self._started = True
        return self.STATUS_STARTED

    def stop(self):
        self._started = False
        return self.STATUS_STOPPED

    def review_before_action(self, user_input, available_context=None, action_metadata=None):
        return self.pre_action_safety_layer.analyze_action(
            user_input=user_input,
            available_context=available_context,
            action_metadata=action_metadata,
        )

    def get_pre_action_architecture(self):
        return self.pre_action_safety_layer.get_architecture_blueprint()
