"""Legacy orchestrator placeholder kept import-safe."""

from __future__ import annotations


class Orchestrator:
    def __init__(self):
        self.running = False

    async def start(self):
        self.running = True

    async def stop(self):
        self.running = False
