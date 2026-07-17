from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    cron = env.ref("newsassistant_website.ir_cron_scrape_news_website", False)
    if cron and not cron.active:
        cron.write({"active": True})