# Proxy Guide

The runner supports static proxies and dynamic proxy APIs.

## Static Proxy

```yaml
region:
  use_proxy: true
  proxy_mode: "static"
  proxy_url: "http://proxy-host:port"
```

Supported URL forms include:

- `http://host:port`
- `https://host:port`
- `socks5://host:port`
- `http://username:password@host:port`

## Dynamic Proxy API

```yaml
region:
  use_proxy: true
  proxy_mode: "dynamic"
  proxy_api:
    url: "http://your-proxy-api.com/get?key=YOUR_KEY"
    timeout: 10
    protocol: "http"
    auth_required: false
    username: ""
    password: ""
```

The API should return `ip:port`. When authentication is enabled, the runner builds a proxy URL using `username` and `password`.

## Test Proxy

```bash
python scripts/check_proxy.py
```

## Disable Proxy

```bash
python scripts/disable_proxy.py
```

Or edit config:

```yaml
region:
  use_proxy: false
```

## HTTP 407

HTTP 407 means the proxy requires authentication. Fix it by:

1. Adding username and password to the proxy config.
2. Asking the provider to whitelist your public IP.
3. Using an API endpoint that returns authenticated proxy URLs.

## Region Alignment

For best consistency, choose a proxy region that matches `region.current`.

```yaml
region:
  current: "germany"
  use_proxy: true
  proxy_mode: "dynamic"
  proxy_api:
    url: "http://your-proxy-api.com/get?cty=de&key=YOUR_KEY"
```
