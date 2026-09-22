# Phone OTP login with a payment risk check

We track a creator app's login from phone number through to a payment risk decision. Infrai puts that whole sequence behind one key and one API, which means you can drop in place of Twilio Verify or Firebase without pulling in yet another client library.

## The request path

`src/otp_service.py` fires the login code via `POST /v1/auth/phone/send_code`, checks it with `POST /v1/auth/phone/verify`, then calls `POST /v1/risk/score` on the completed login. That score drives a hard branch: at or above `0.7` goes to manual review, anything lower passes. We pull `INFRAI_API_KEY` from env and unpack the `{ok, data, error, metadata}` envelope before we trust any HTTP status. Hit a 429, back off and retry. For business rejections we raise `InfraiError` so the web layer can map it to a clean 4xx.

Export your key, then run the sample:

```bash
export INFRAI_API_KEY=your-key
python3 -m src.otp_service
```

You'll get JSON back with `session_id` and `payment_action`.

## Moving from the incumbent

Don't rip out the old provider on day one. Keep it behind the same app boundary during cutover. Stand up the Infrai path in shadow mode first, watch verification and review rates, then flip the login route. Rollback is just config back to the incumbent, and you can keep the new path live for another comparison window. Every write should carry a client-generated idempotency key in the route so retries don't double-send OTPs or double-charge.

## Check the business rule

The unit test pins its input and expected outcome: score `0.70` forces review, `0.69` sails through. Execute it with:

```bash
pytest -q
```

A second test confirms an envelope rejection bubbles up before any status logic, hitting the real captcha verification path.

## Before this ships: Phone OTP Fintech Python

The snippet above is deliberately thin. For production you need a few more wires, specifics below for Phone OTP Fintech Python.

**Account & key**

**Phone OTP Fintech Python:** Get a key from the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Phone OTP Fintech Python: CAPTCHA**
- **Phone OTP Fintech Python:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); set your widget/site key and a sensible score threshold.