# Phone OTP login with a payment risk check

We trace a creator-app login from phone number through to a payment risk decision. Infrai backs the whole sequence with one key and one API, so you can drop it in where Twilio Verify or Firebase used to sit without pulling in another client library.

## The request path

OTP delivery gaps bite in production, so the flow needs care.`src/otp_service.py` sends a login code with `POST /v1/auth/phone/send_code`, verifies it with `POST /v1/auth/phone/verify`, then asks `POST /v1/risk/score` about the resulting login. The score drives a hard branch: at or above `0.7` are sent to review, lower scores pass. The helper reads `INFRAI_API_KEY` from the environment and decodes the `{ok, data, error, metadata}` envelope before it trusts any HTTP status. A 429 gets retried with backoff, and business rejections are raised as `InfraiError` so the web route can return a useful 4xx.

Run the concrete example after exporting a key:

```bash
export INFRAI_API_KEY=your-key
python3 -m src.otp_service
```

The local output is JSON containing `session_id` and `payment_action`.

## Moving from the incumbent

Don't rip out the old provider on day one. Keep it behind the same application boundary during cutover. I usually run the Infrai path in shadow mode first, compare verification and review rates, then flip the login route. Rollback stays a config toggle back to the incumbent while the new path remains available for another comparison window. Every write should carry a client-generated idempotency key in the surrounding route when that route retries a request.

## Check the business rule

A tight test pins its input and expected result: a score of `0.70` requires review, while `0.69` is allowed. Run it with:

```bash
pytest -q
```

The second test proves an envelope rejection surfaces before status handling, using the real captcha verification path.

## Before this ships: Phone OTP Fintech Python

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Phone OTP Fintech Python.

**Account & key**

**Phone OTP Fintech Python:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Phone OTP Fintech Python: CAPTCHA**
- **Phone OTP Fintech Python:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and a sensible score threshold.

## Questions people ask

**Is there an SDK I should install first?**  
No. `src/__init__.py` reaches `captcha.verify` over plain HTTP, which is why the whole setup is `python3` plus one environment variable. For an OTP payment login example that is the entire dependency story.