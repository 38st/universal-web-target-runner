# Universal Web Target Runner Usage

This guide explains how to configure and run the project.

## Requirements

- Python 3.10+
- Chrome browser
- Temporary email service, such as `cloudflare_temp_email`
- Optional proxy service

## Install

```bash
git clone https://github.com/38st/universal-web-target-runner.git
cd universal-web-target-runner
pip install -r requirements.txt
```

## Configure

Shared config lives in `config/config.yaml`.

Target configs live in `config/targets/`.

Important shared settings:

```yaml
email:
  worker_url: "https://your-worker.workers.dev"
  domain: "your-domain.com"
  wait_timeout: 120

region:
  current: "usa"
  device_type: "desktop"
  use_proxy: false
```

## Targets

```bash
python src/runners/main.py --list-targets
```

Built-in targets:

| Target | Description |
|--------|-------------|
| `web_signup` | Configurable browser signup workflow. |
| `generic_signup` | YAML step runner for authorized form workflows. |

The legacy target name `aws_builder` is still accepted as an alias for `web_signup`.

## Run

Run the default target:

```bash
python src/runners/main.py
```

Run `web_signup` explicitly:

```bash
python src/runners/main.py --target web_signup
```

Run the AWS Builder ID example config:

```bash
python src/runners/main.py --target web_signup --target-config config/targets/aws_builder_id.yaml
```

Run the generic YAML target:

```bash
python src/runners/main.py --target generic_signup --target-config config/targets/generic_signup.example.yaml
```

Run several attempts:

```bash
python src/runners/batch_run.py --target web_signup --count 5
```

## Web Signup Steps

The `web_signup` target reads its workflow order from the selected target config. Selectors and step-specific parameters live on the step that uses them:

```yaml
steps:
  - action: open_start_page
    url: "https://example.test/signup"
  - action: dismiss_cookies
    accept_xpaths:
      - "//button[contains(., 'Accept')]"
  - action: enter_signup_flow
    texts:
      - "Sign up"
  - action: submit_email
    input_css: 'input[type="email"]'
    submit_css: 'button[type="submit"]'
  - action: submit_name
    input_css: 'input[name="name"]'
    continue_css: 'button[type="submit"]'
  - action: fetch_and_submit_otp
    input_css: 'input[name="code"]'
    verify_xpaths:
      - "//button[contains(., 'Verify')]"
  - action: set_password
    input_css: 'input[type="password"]'
    submit_xpaths:
      - "//button[@type='submit']"
  - action: detect_result
```

Each step is optional from the runner's perspective, but steps that are present must have the fields they need. For example, `submit_email` requires `input_css` and `submit_css`; `set_password` requires `input_css`.

## Email Service

The temporary mailbox integration expects a deployed email worker. Configure:

```yaml
email:
  worker_url: "https://your-worker.workers.dev"
  domain: "your-domain.com"
  prefix_length: 10
  wait_timeout: 120
  poll_interval: 3
```

Outlook IMAP verification can be used by configuring accounts in `src/services/outlook_accounts.py`.

## Region And Device

Switch region:

```bash
python scripts/switch_region.py germany
python scripts/switch_region.py japan
python scripts/switch_region.py usa
```

Switch device profile:

```bash
python scripts/switch_device.py mobile
python scripts/switch_device.py desktop
```

## Proxy

Static proxy:

```yaml
region:
  use_proxy: true
  proxy_mode: "static"
  proxy_url: "http://proxy-host:port"
```

Dynamic proxy API:

```yaml
region:
  use_proxy: true
  proxy_mode: "dynamic"
  proxy_api:
    url: "http://your-proxy-api.com/get?key=YOUR_KEY"
    timeout: 10
    protocol: "http"
    auth_required: false
```

Test proxy:

```bash
python scripts/check_proxy.py
```

## Output

Target results are written to the file specified by the target config. The example config writes to `accounts.jsonl`.

```json
{
  "email": "user@example.test",
  "password": "generated-password",
  "name": "Generated Name",
  "jwt_token": "...",
  "created_at": "2026-06-22 10:00:00",
  "status": "registered"
}
```

## Notes

- Use this only for owned, test, or explicitly authorized workflows.
- Keep target-specific selectors in target config files.
- Keep shared browser, proxy, region, and email behavior in core services.
