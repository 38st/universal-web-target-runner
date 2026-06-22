# Region Configuration Guide

The runner supports region profiles for browser locale, timezone, Accept-Language, geolocation, and User-Agent selection.

## Supported Regions

| Region | Code | Locale | Timezone |
|--------|------|--------|----------|
| Germany | `germany` | de-DE | Europe/Berlin |
| Japan | `japan` | ja-JP | Asia/Tokyo |
| United States | `usa` | en-US | America/New_York |

## Switch Region

Use the helper script:

```bash
python scripts/switch_region.py show
python scripts/switch_region.py germany
python scripts/switch_region.py japan
python scripts/switch_region.py usa
```

Or edit `config/config.yaml`:

```yaml
region:
  current: "germany"
```

## What Region Profiles Affect

- Browser locale
- Timezone override
- Accept-Language header
- Approximate geolocation
- Desktop and mobile User-Agent pools

## Proxy Alignment

For stronger environment consistency, use a proxy from the same region as the configured profile.

```yaml
region:
  current: "germany"
  use_proxy: true
  proxy_mode: "static"
  proxy_url: "socks5://de-proxy.example.com:1080"
```

## Troubleshooting

If a target still detects mismatched environment signals:

1. Confirm the proxy region matches `region.current`.
2. Confirm locale, timezone, and Accept-Language values in `config/config.yaml`.
3. Clear temporary browser profile data.
4. Update Chrome and `undetected-chromedriver`.
