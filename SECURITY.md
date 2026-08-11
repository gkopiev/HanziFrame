# Security policy

## Supported version

Security fixes are prepared against the current `main` branch. This project
does not yet publish a separately supported release series.

## Reporting a vulnerability

If GitHub shows **Report a vulnerability** in the repository's Security tab,
use that private channel. Otherwise, open a minimal issue asking the maintainer
for a private contact route. Do not include exploit details, private network
information, credentials, logs, configuration dumps or firmware images in a
public issue.

If a credential may already be exposed, revoke or rotate it first. Removing a
value from the latest file is not enough when it exists in Git history.

## Installation safety

- Keep `secrets.yaml`, `.env` files, keys, Home Assistant `.storage`, databases,
  backups and ESPHome build output outside Git.
- Store ESPHome credentials behind `!secret` references. The example values in
  `esphome/secrets.example.yaml` are public placeholders and must be replaced.
- Never paste credentials into issues, pull requests, build logs or AI chats.
- Review a proposed diff before copying files into Home Assistant, and require a
  separate explicit approval before writing firmware to a physical device.
