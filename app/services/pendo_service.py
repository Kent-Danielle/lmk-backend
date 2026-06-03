import json
import logging
import time
import urllib.request
import urllib.error
from threading import Thread

logger = logging.getLogger(__name__)

PENDO_TRACK_URL = "https://data.pendo.io/data/track"
PENDO_INTEGRATION_KEY = "1e1ed19e-e0a1-4b68-a7fa-a57ac59601a4"


def pendo_track(
    event: str,
    visitor_id: str = "system",
    account_id: str = "system",
    properties: dict | None = None,
) -> None:
    """Send a track event to Pendo asynchronously. Failures are logged but never raised."""

    payload = {
        "type": "track",
        "event": event,
        "visitorId": visitor_id,
        "accountId": account_id,
        "timestamp": int(time.time() * 1000),
    }
    if properties:
        payload["properties"] = properties

    def _send():
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                PENDO_TRACK_URL,
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "x-pendo-integration-key": PENDO_INTEGRATION_KEY,
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                resp.read()
        except Exception:
            logger.warning("Failed to send Pendo track event '%s'", event, exc_info=True)

    Thread(target=_send, daemon=True).start()
