import asyncio
from collections import defaultdict

class EventManager:
    def __init__(self):
        self._queues: dict[str, list[asyncio.Queue]] = defaultdict(list)

    def subscribe(self, session_id: str) -> asyncio.Queue:
        queue = asyncio.Queue()
        self._queues[session_id].append(queue)
        return queue
    
    def unsubscribe(self, session_id: str, queue: asyncio.Queue):
        self._queues[session_id].remove(queue)
        if not self._queues[session_id]:
            del self._queues[session_id]

    def publish(self, session_id: str, state: str):
        for queue in self._queues[session_id]:
            queue.put_nowait(state)

event_manager = EventManager()