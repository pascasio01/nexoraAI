# Core Orchestrator
from nexoraAI.stress_simulator import StressSimulator


class Orchestrator:
    def __init__(self):
        self.stress_simulator = StressSimulator()

    def start(self):
        return "orchestrator_started"

    def stop(self):
        return "orchestrator_stopped"

    def stress_simulator_blueprint(self):
        return self.stress_simulator.blueprint()

    def run_stress_simulator(self, simulation_request):
        return self.stress_simulator.run(simulation_request)
