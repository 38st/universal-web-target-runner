# Fingerprint Guide

The project includes basic browser-signal controls for authorized testing workflows.

## Implemented Controls

- Temporary Chrome user data directory per run
- Region-based User-Agent selection
- Locale and Accept-Language settings
- Timezone override through Chrome DevTools Protocol
- Approximate geolocation override
- Hardware signal variation for CPU core count and memory
- WebGL renderer override
- WebRTC IP handling flags

## Test Fingerprint Behavior

```bash
python scripts/check_fingerprint.py
```

The script opens public fingerprint test pages so you can inspect the browser signals manually.

## Operational Notes

- Avoid unrealistic combinations, such as a mobile profile with impossible desktop hardware signals.
- Keep User-Agent, locale, timezone, geolocation, and proxy region aligned.
- Update User-Agent examples as Chrome versions change.
- Treat this as a testing aid, not a guarantee of undetectability.

## Relevant Files

- `src/core/browser.py`
- `src/helpers/fingerprint.py`
- `config/config.yaml`
