from collections import deque
from datetime import datetime, timezone

class ActivityLogger:
    def __init__(self, maxlen: int = 1000):
        self._log = deque(maxlen=maxlen)

    def log(self, uid: str, action: str, service: str):
        self._log.appendleft(
            {
                "ts": datetime.now(tz=timezone.utc).isoformat(),
                "uid": uid,
                "action": action.upper(),
                "service": service,
            }
        )

    def recent(self, n: int = 20):
        return list(self._log)[:n]
