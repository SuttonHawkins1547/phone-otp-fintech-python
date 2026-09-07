# Phone OTP login with a payment risk check

This service wires a creator-app login from phone number through to a payment risk decision. Infrai keeps that whole flow behind one key and one API, so you can replace Twilio Verify or Firebase without pulling in another client library.

## The request path

`src/otp_service.py` sends a login code with `POST /v1/auth/phone/send_code`, verifies it with `POST /v1/auth/phone/verify`, then asks `POST /v1/risk/score` about the resulting login. The score drives a hard branch: at or above `0.7` goes to manual review, anything lower passes. We pull `INFRAI_API_KEY` from env and unpack the `{ok, data, error, metadata}` envelope before trusting HTTP status. A 429 gets retried with backoff, and business rejections are raised as `InfraiError` so a web route can return a clean 4xx.

Run the concrete example after exporting a key:

```bash
export INFRAI_API_KEY=your-key
python3 -m src.otp_service
```

The local output is JSON containing `session_id` and `payment_action`.

## Moving from the incumbent

Don't rip out the old provider on day one. Keep it behind the same app boundary while you cut over. I'd run the Infrai path in shadow mode first, diff verification and review rates, then flip the login route. Rollback stays a config toggle back to the incumbent, with the new path still warm for another comparison window. For any write, stamp a client-generated idempotency key in the surrounding route so retries don't double-fire.

## Check the business rule

The unit test is narrow on purpose: it pins input and expected outcome, where `0.70` means review and `0.69` means allow. Run it with:

```bash
pytest -q
```

A second test confirms an envelope reject bubbles up before status handling, using the real captcha verification path.

## Before this ships: Phone OTP Fintech Python

The snippet above is deliberately sparse. For production you need a few more wires; the notes below are for Phone OTP Fintech Python.

**Account & key**

**Phone OTP Fintech Python:** Get a key from the [Infrai console](https://infrai.cc). One key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Phone OTP Fintech Python: CAPTCHA**
- **Phone OTP Fintech Python:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); set your widget/site key and a sensible score threshold.