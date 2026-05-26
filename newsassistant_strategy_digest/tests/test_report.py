from datetime import date

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestStrategyDigestReport(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.digest = cls.env["strategy.digest"].create({
            "name": "Report Test Digest",
            "date_from": date(2026, 1, 1),
            "date_to": date(2026, 12, 31),
            "brief": "<h2>Executive Summary</h2><p>Test brief for PDF report.</p>",
            "state": "done",
        })

    def test_report_action_exists(self):
        """The report action for strategy.digest is registered."""
        report = self.env["ir.actions.report"].search([
            ("model", "=", "strategy.digest"),
            ("report_type", "=", "qweb-pdf"),
        ], limit=1)
        self.assertTrue(report, "No qweb-pdf report registered for strategy.digest")
        self.assertEqual(
            report.report_name,
            "newsassistant_strategy_digest.report_strategy_digest",
        )

    def test_report_no_paperformat_set(self):
        """The report does NOT have an explicit paperformat_id (inherits company default)."""
        report = self.env["ir.actions.report"].search([
            ("model", "=", "strategy.digest"),
            ("report_type", "=", "qweb-pdf"),
        ], limit=1)
        self.assertFalse(
            report.paperformat_id,
            "Report should not have explicit paperformat_id — it should inherit company settings",
        )

    def test_report_uses_company_paperformat(self):
        """get_paperformat() returns the company paperformat when none set on report."""
        report = self.env["ir.actions.report"].search([
            ("model", "=", "strategy.digest"),
            ("report_type", "=", "qweb-pdf"),
        ], limit=1)
        paperformat = report.get_paperformat()
        self.assertTrue(paperformat, "get_paperformat() must return a paperformat")
        # The fallback should equal the company's paperformat
        self.assertEqual(paperformat, self.env.company.paperformat_id)

    def test_qweb_template_exists(self):
        """QWeb template is registered for strategy.digest."""
        # Check the template view is registered
        template = self.env["ir.ui.view"].search([
            ("key", "=", "newsassistant_strategy_digest.report_strategy_digest"),
        ], limit=1)
        self.assertTrue(
            template,
            "QWeb template 'newsassistant_strategy_digest.report_strategy_digest' "
            "should be registered as an ir.ui.view",
        )
