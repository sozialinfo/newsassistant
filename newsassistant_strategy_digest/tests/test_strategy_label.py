from odoo.tests.common import TransactionCase, tagged


def _make_article(env, suffix=""):
    source = env["news.source"].create({
        "name": f"LabelTest Source {suffix}",
        "source_type": "website",
        "url": f"https://labeltest{suffix}.com",
    })
    snapshot = env["news.snapshot"].with_context(skip_snapshot_extraction=True).create({
        "source_id": source.id,
        "raw_content": "<p>Test content</p>",
    })
    article = env["news.article"].create({
        "title": f"Label Test Article {suffix}",
        "snapshot_id": snapshot.id,
        "url": f"https://labeltest{suffix}.com/article",
        "state": "scraped",
    })
    return article


@tagged("post_install", "-at_install")
class TestStrategyLabel(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.StrategyLabel = cls.env["strategy.label"]

    def test_create_label(self):
        """Test creating a strategy label."""
        label = self.StrategyLabel.create({"name": "TestCreateLabel_Unique"})
        self.assertEqual(label.name, "TestCreateLabel_Unique")
        self.assertGreaterEqual(label.color, 1)
        self.assertLessEqual(label.color, 11)

    def test_unique_name_constraint(self):
        """Test that duplicate label names are rejected."""
        self.StrategyLabel.create({"name": "UniqueLabel_Constraint_Test"})
        with self.assertRaises(Exception):
            self.StrategyLabel.create({"name": "UniqueLabel_Constraint_Test"})

    def test_default_color_assigned(self):
        """Test that a default color is assigned on creation."""
        label = self.StrategyLabel.create({"name": "TestColorLabel_Unique"})
        self.assertIsNotNone(label.color)
        self.assertGreaterEqual(label.color, 1)

    def test_label_assigned_to_article(self):
        """Test that a label can be assigned to a news article via M2M."""
        label = self.StrategyLabel.create({"name": "AssignTest_Unique"})
        article = _make_article(self.env, suffix="assign")
        article.write({"strategy_label_ids": [(4, label.id)]})
        self.assertIn(label, article.strategy_label_ids)

    def test_article_can_have_multiple_labels(self):
        """Test that an article can have multiple strategy labels."""
        label1 = self.StrategyLabel.create({"name": "MultiLabel1_Unique"})
        label2 = self.StrategyLabel.create({"name": "MultiLabel2_Unique"})
        article = _make_article(self.env, suffix="multi")
        article.write({"strategy_label_ids": [(4, label1.id), (4, label2.id)]})
        self.assertIn(label1, article.strategy_label_ids)
        self.assertIn(label2, article.strategy_label_ids)
