import json

from src.otp_service import InfraiClient, decide_action


def test_high_risk_login_requires_review():
    assert decide_action(0.7) == "review"
    assert decide_action(0.69) == "allow"


def test_client_decodes_business_rejection_before_status():
    class Response:
        status = 422
        def read(self):
            return json.dumps({"ok": False, "error": {"code": "CAPTCHA_SCORE_TOO_LOW"}}).encode()

    try:
        InfraiClient("test-key", lambda *args, **kwargs: Response()).post("/v1/captcha/verify", {"token": "x"})
    except Exception as exc:
        assert exc.code == "CAPTCHA_SCORE_TOO_LOW"
        assert exc.status == 422
    else:
        raise AssertionError("business rejection was not surfaced")
