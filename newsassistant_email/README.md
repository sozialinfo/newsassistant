# News Assistant — Email

Inbound email / newsletter capture for News Assistant.

## Overview

This addon lets News Assistant receive email newsletters directly. Configure a mail alias
(e.g. `newsassistant@yourdomain.com`) and subscribe it to mailing lists. Each incoming email is
sanitised, stored as a `news.snapshot`, and queued for AI article extraction — exactly like
website-scraped content, so articles from newsletters appear in the same kanban board alongside
website articles.

Requires `newsassistant` (base module).

## Features

- Configurable mail alias (e.g. `newsassistant@yourdomain.com`)
- Automatic `news.source` creation from the sender's domain, with AI-powered publication name lookup
- HTML sanitisation of inbound emails (removes tracking pixels, scripts, hidden elements, `display:none` content)
- One `news.snapshot` created per received email, automatically queued for extraction
- Dedicated `root.email_extraction` queue job channel for priority processing

## Pipeline

```
Inbound email → Odoo mail router
    └─▶ news.snapshot.message_new()
            ├─▶ _get_or_create_email_source()   [find or create news.source by sender domain]
            │       └─▶ _ai_get_source_name()   [AI lookup: domain → publication name]
            ├─▶ Sanitise email HTML
            ├─▶ Create news.snapshot (raw_content = sanitised HTML)
            └─▶ snapshot.with_delay()._extract_articles()   [extraction queue job]
```

The extraction job sends the sanitised email HTML to the AI and creates `news.article` records,
which appear in the kanban board under the **New** stage.

## Configuration

### Mail alias

1. Go to **News Assistant → Configuration → Settings**.
2. Set **Email Alias** to the local part of the address you want to use
   (e.g. `newsassistant` for `newsassistant@yourdomain.com`).
3. Ensure Odoo's outgoing mail server has a valid domain configured
   (**Settings → Technical → Email → Outgoing Mail Servers**).

### Verify the alias is working

Send a test newsletter:

```bash
python scripts/sendmail.py test@example.ch newsassistant
```

This injects a realistic HTML newsletter from `test@example.ch` via XMLRPC and triggers the
full inbound pipeline. Check **News Assistant → Articles** after a few seconds.

### Subscription

Subscribe the alias to any email newsletter or mailing list you want to monitor. New emails
are processed automatically — no further configuration needed per sender.

## Usage

### Monitor captured emails

Each received email becomes a `news.snapshot`. View snapshots from the source record's
**Snapshots** smart button, or browse all snapshots at
**News Assistant → Sources → [source record] → Snapshots**.

### Check for errors

If an email is not producing articles:

1. Go to **Settings → Technical → Queue → Jobs** and filter by channel `root.email_extraction`.
2. Open a failed job to see the error traceback.
3. Check **News Assistant → Logs** for the snapshot's extraction log and LLM response detail.

### New sender domains

When an email arrives from a domain not yet in the database, this addon:

1. Creates a new `news.source` of type `email` with the sender's domain.
2. Calls the AI to look up the publication name from the domain (e.g. `skos.ch` → `SKOS`).
3. Uses that name as the source's display name.

Review and rename auto-created sources at **News Assistant → Sources**.

## Error Handling

| Condition | Behaviour |
|---|---|
| Malformed email HTML | Sanitiser strips invalid markup; extraction continues on remaining content |
| Unknown sender domain | New `news.source` created automatically via AI name lookup |
| AI name lookup fails | Source created with domain as fallback name |
| Extraction job fails (transient) | `RetryableJobError` — retried with escalating delay |
| Duplicate email content | URL-based deduplication prevents duplicate articles |

## Security

| Group | Access |
|---|---|
| `newsassistant.newsassistant_group_user` | Read email-sourced snapshots and articles |
| `newsassistant.newsassistant_group_admin` | Full access |

No additional record rules beyond the base module.

## Dependencies

- `newsassistant` — base module (required)
- `mail` — Odoo mail system (required)
- `INFOMANIAK_AI_API_KEY` — environment variable (required)

## Testing

```bash
docker exec odoo-newsassistant odoo --test-tags newsassistant_email --stop-after-init -d newsassistant
```

To test the end-to-end inbound flow manually:

```bash
python scripts/sendmail.py editor@skos.ch newsassistant
```

## License

LGPL-3
