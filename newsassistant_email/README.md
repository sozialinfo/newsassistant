# News Assistant — Email

Inbound email capture for News Assistant. Converts received newsletters into snapshots for AI extraction.

## Features

- Configurable mail alias (e.g. `newsassistant@yourdomain.com`)
- Automatic news source creation from sender domain with AI-powered name lookup
- HTML sanitization of inbound emails (removes tracking pixels, scripts, hidden elements)
- Snapshot creation per received email, auto-triggering article extraction on a dedicated channel
- Separate `root.email_extraction` queue job channel for priority processing

## Models

### news.snapshot (extended)

Inherits `mail.thread` and `mail.alias.mixin` to enable email routing.

| Method | Description |
|--------|-------------|
| `message_new()` | Handles inbound email: creates snapshot, auto-creates source if needed |
| `_get_or_create_email_source()` | Finds or creates email source by sender domain |
| `_ai_get_source_name()` | Uses AI to determine publication name from domain |

## Security

| Group | Access |
|-------|--------|
| `newsassistant.newsassistant_group_user` | Read access to email-sourced snapshots |
| `base.group_system` | Full system access |

No additional access rules beyond base module.

## Configuration

After installation, configure in **News Assistant → Configuration → Settings**:

| Parameter | Description |
|-----------|-------------|
| Email Alias | Alias name for the inbound email address (e.g. `newsassistant`) |

The alias must be set up in Odoo's mail configuration with a valid domain. Send a test email to verify.

## Dependencies

- `newsassistant` — base module
- `mail` — Odoo mail system

## License

LGPL-3
