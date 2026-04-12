from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestKanban(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, queue_job__no_delay=True))
        cls.stage_new = cls.env.ref("newsassistant.news_article_stage_new")
        cls.stage_relevant = cls.env.ref("newsassistant.news_article_stage_relevant")
        cls.stage_archived = cls.env.ref("newsassistant.news_article_stage_archived")
        cls.stage_discarded = cls.env.ref("newsassistant.news_article_stage_discarded")
        cls.source = cls.env["news.source"].create({
            "name": "Test Source",
            "url": "https://example.com/news",
        })

    def test_default_stages_exist(self):
        """Test that all four default stages are created."""
        stages = self.env["news.article.stage"].search([])
        stage_names = stages.mapped("name")
        self.assertIn("New", stage_names)
        self.assertIn("Relevant", stage_names)
        self.assertIn("Archived", stage_names)
        self.assertIn("Discarded", stage_names)

    def test_stage_ordering(self):
        """Test that stages are ordered by sequence."""
        stages = self.env["news.article.stage"].search([])
        sequences = stages.mapped("sequence")
        self.assertEqual(sequences, sorted(sequences))

    def test_archived_and_discarded_folded(self):
        """Test that Archived and Discarded stages are folded."""
        self.assertTrue(self.stage_archived.fold)
        self.assertTrue(self.stage_discarded.fold)
        self.assertFalse(self.stage_new.fold)
        self.assertFalse(self.stage_relevant.fold)

    def test_article_default_stage(self):
        """Test that new articles get the 'New' stage by default."""
        article = self.env["news.article"].create({
            "title": "Test Article",
            "source_id": self.source.id,
            "url": "https://example.com/test-article",
        })
        self.assertEqual(article.stage_id, self.stage_new)

    def test_article_stage_change(self):
        """Test that article stage can be changed (simulating kanban drag)."""
        article = self.env["news.article"].create({
            "title": "Test Article",
            "source_id": self.source.id,
            "url": "https://example.com/test-article-2",
        })
        self.assertEqual(article.stage_id, self.stage_new)

        article.write({"stage_id": self.stage_relevant.id})
        self.assertEqual(article.stage_id, self.stage_relevant)

        article.write({"stage_id": self.stage_archived.id})
        self.assertEqual(article.stage_id, self.stage_archived)

    def test_read_group_stage_ids_shows_all(self):
        """Test that _read_group_stage_ids returns all stages."""
        all_stages = self.env["news.article"]._read_group_stage_ids(
            self.env["news.article.stage"], []
        )
        self.assertEqual(len(all_stages), 4)

    def test_article_url_unique_constraint(self):
        """Test that duplicate URLs are rejected by the database."""
        self.env["news.article"].create({
            "title": "Article A",
            "source_id": self.source.id,
            "url": "https://example.com/unique-test",
        })
        with self.assertRaises(Exception):
            self.env["news.article"].create({
                "title": "Article B",
                "source_id": self.source.id,
                "url": "https://example.com/unique-test",
            })
