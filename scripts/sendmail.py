#!/usr/bin/env python3
"""Inject a test newsletter email into Odoo via XMLRPC.

Usage:
    scripts/sendmail.py <from-address> [<db>]

Examples:
    scripts/sendmail.py editor@skos.ch
    scripts/sendmail.py newsletter@sozialinfo.ch newsassistant
"""
import email as emaillib
import sys
import xmlrpc.client
from datetime import datetime, timezone


def main():
    if len(sys.argv) < 2:
        print("Usage: sendmail.py <from-address> [<db>]", file=sys.stderr)
        sys.exit(1)

    sender = sys.argv[1]
    db = sys.argv[2] if len(sys.argv) > 2 else "newsassistant"
    user = "admin"
    pwd = "admin"

    domain = sender.split("@")[-1] if "@" in sender else sender
    pub_name = domain.split(".")[0].capitalize()
    alias = f"newsassistant@{db}.opencode.bruehlmeier.com"

    now = datetime.now(timezone.utc)
    ts = now.strftime("%a, %d %b %Y %H:%M:%S +0000")
    msg_id = f"<test-{now.strftime('%Y%m%d%H%M%S%f')}@{domain}>"
    date_str = now.strftime("%d.%m.%Y")
    subj_date = now.strftime("%Y-%m-%d")

    raw_email = (
        f"From: {pub_name} Newsletter <{sender}>\r\n"
        f"To: {alias}\r\n"
        f"Subject: Neue Sozialhilferichtlinien: {pub_name} veröffentlicht aktualisierte Empfehlungen\r\n"
        f"Date: {ts}\r\n"
        f"Message-ID: {msg_id}\r\n"
        f"MIME-Version: 1.0\r\n"
        f"Content-Type: text/html; charset=UTF-8\r\n"
        f"\r\n"
        f"<html><body>\r\n"
        f"<h1>Neue Sozialhilferichtlinien: {pub_name} veröffentlicht aktualisierte Empfehlungen</h1>\r\n"
        f"<p><em>Publiziert am {date_str}</em></p>\r\n"
        f"\r\n"
        f"<p>Die Schweizerische Konferenz für Sozialhilfe ({pub_name}) hat ihre Empfehlungen zur "
        f"Bemessung der Sozialhilfe grundlegend überarbeitet. Die neuen Richtlinien treten am "
        f"1. Januar 2027 in Kraft und betreffen rund 270\u202f000 Sozialhilfebeziehende in der Schweiz.</p>\r\n"
        f"\r\n"
        f"<h2>Wichtigste Änderungen im Überblick</h2>\r\n"
        f"<p>Der Grundbedarf für den Lebensunterhalt wird um 4,2 Prozent angehoben, um der "
        f"gestiegenen Inflation der letzten Jahre Rechnung zu tragen. Für Einpersonenhaushalte "
        f"steigt der monatliche Grundbedarf damit von CHF 986 auf CHF 1\u202f027.</p>\r\n"
        f"\r\n"
        f"<h2>Veranstaltungshinweis</h2>\r\n"
        f"<p>Am 15. Mai 2026 findet die jährliche Fachtagung statt. Thema dieses Jahr:\r\n"
        f"<em>Digitalisierung in der Sozialarbeit – Chancen und Risiken</em>.</p>\r\n"
        f"<p>Anmeldungen sind bis zum 1. Mai möglich unter:\r\n"
        f"<a href=\"https://{domain}/tagung\">https://{domain}/tagung</a></p>\r\n"
        f"\r\n"
        f"<p style=\"color:#999;font-size:11px;\">\r\n"
        f"Sie erhalten diesen Newsletter, weil Sie Mitglied von {pub_name} sind.<br>\r\n"
        f"<a href=\"https://{domain}/abmelden\">Abmelden</a>\r\n"
        f"</p>\r\n"
        f"<img src=\"https://track.{domain}/open.gif?id=12345\" width=\"1\" height=\"1\" />\r\n"
        f"</body></html>\r\n"
    )

    # Parse email to extract headers/body
    parsed = emaillib.message_from_bytes(raw_email.encode("utf-8"))
    body = parsed.get_payload(decode=True)
    if isinstance(body, bytes):
        body = body.decode("utf-8", errors="replace")

    msg_dict = {
        "email_from": str(parsed["From"] or ""),
        "to": str(parsed["To"] or ""),
        "subject": str(parsed["Subject"] or ""),
        "body": body,
        "message_id": str(parsed["Message-ID"] or ""),
    }

    url = f"https://{db}.opencode.bruehlmeier.com/xmlrpc/2"
    try:
        common = xmlrpc.client.ServerProxy(f"{url}/common")
        uid = common.authenticate(db, user, pwd, {})
        if not uid:
            print(f"ERROR: XMLRPC authentication failed (db={db})", file=sys.stderr)
            sys.exit(1)

        models = xmlrpc.client.ServerProxy(f"{url}/object")

        # Call message_new directly via a server action — bypasses alias domain requirement.
        code = (
            "msg = " + repr(msg_dict) + "\n"
            "env['news.snapshot'].message_new(msg)\n"
        )
        model_id = models.execute_kw(db, uid, pwd, "ir.model", "search",
            [[["model", "=", "news.snapshot"]]])[0]
        action_id = models.execute_kw(db, uid, pwd, "ir.actions.server", "create", [{
            "name": "_sendmail_tmp",
            "model_id": model_id,
            "state": "code",
            "code": code,
        }])
        try:
            models.execute_kw(db, uid, pwd, "ir.actions.server", "run", [[action_id]])
        finally:
            models.execute_kw(db, uid, pwd, "ir.actions.server", "unlink", [[action_id]])

        # Find the newly created snapshot
        new_snaps = models.execute_kw(db, uid, pwd, "news.snapshot", "search_read",
            [[["source_id.source_type", "=", "email"]]],
            {"fields": ["id", "name", "source_id"], "order": "id desc", "limit": 1})
        if new_snaps:
            s = new_snaps[0]
            print(f"OK — email from {sender} → snapshot #{s['id']} (source: {s['source_id'][1]})")
        else:
            print(f"OK — email from {sender} delivered")

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
