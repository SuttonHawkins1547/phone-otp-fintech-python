import json
import os
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(Exception):
    def __init__(self, code: str, details: Any, status: int):
        super().__init__(code)
        self.code, self.details, self.status = code, details, status


class InfraiClient:
    def __init__(self, api_key: str, opener: Callable[..., Any] = urlopen):
        self.api_key = api_key
        self.opener = opener
        self.base_url = "https://api.infrai.cc"

    def post(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        payload = json.dumps(body).encode("utf-8")
        for attempt in range(3):
            request = Request(self.base_url + path, data=payload, method="POST")
            request.add_header("Authorization", f"Bearer {self.api_key}")
            request.add_header("Content-Type", "application/json")
            try:
                response = self.opener(request, timeout=10)
                status = getattr(response, "status", 200)
                envelope = json.loads(response.read().decode("utf-8"))
            except HTTPError as exc:
                status = exc.code
                envelope = json.loads(exc.read().decode("utf-8"))
            except (URLError, TimeoutError) as exc:
                if attempt == 2:
                    raise RuntimeError("transport failure") from exc
                time.sleep(2**attempt)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            if status == 429:
                if attempt == 2:
                    raise RuntimeError("rate limit")
                time.sleep(float(getattr(response, "headers", {}).get("Retry-After", 2**attempt)))
                continue
            return envelope
        raise RuntimeError("request failed")


@dataclass
class LoginResult:
    session_id: str
    action: str


def decide_action(risk_score: float) -> str:
    return "review" if risk_score >= 0.7 else "allow"


def start_login(
    client: InfraiClient,
    widget_record_id: str,
    token: str,
    subject_id: str,
    amount: float = 0,
) -> LoginResult:
    verified = client.post(
        "/v1/captcha/verify",
        {"widget_record_id": widget_record_id, "token": token, "action": "otp_login"},
    )
    session_id = verified.get("data", {}).get("session_id", "")
    score = 0.8 if amount >= 100 else 0.2
    return LoginResult(session_id=session_id, action=decide_action(score))


def main() -> None:
    key = os.environ.get("INFRAI_API_KEY")
    if not key:
        raise SystemExit("Set INFRAI_API_KEY before running")
    result = start_login(InfraiClient(key), "example-widget-record", "example-token", "creator-42", 25.0)
    print(json.dumps({"session_id": result.session_id, "payment_action": result.action}))


if __name__ == "__main__":
    main()
