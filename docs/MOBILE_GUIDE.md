# Mobile Device Mode Guide

Mobile mode switches the browser profile to a mobile User-Agent and mobile-sized viewport. It can be useful for targets that expose a simpler mobile flow.

## Enable Mobile Mode

Use the helper script:

```bash
python scripts/switch_device.py mobile
```

Switch back to desktop:

```bash
python scripts/switch_device.py desktop
```

Or edit `config/config.yaml`:

```yaml
region:
  device_type: "mobile"
```

## Check Current Device Mode

```bash
python scripts/switch_device.py show
```

## Customize User-Agents

Edit the region profile in `config/config.yaml`:

```yaml
region:
  profiles:
    usa:
      mobile_user_agents:
        - "Mozilla/5.0 (...) Mobile Safari/537.36"
```

## Notes

- Mobile mode may require different selectors on some sites.
- Some pages hide desktop-only elements in mobile mode.
- Keep proxy region, locale, timezone, and User-Agent consistent.
