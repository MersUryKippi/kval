from django.test import TestCase


class HealthEndpointTests(TestCase):
    def test_ping_ok(self):
        self.assertEqual(self.client.get("/ping/").status_code, 200)

    def test_list_opens(self):
        self.assertEqual(self.client.get("/").status_code, 200)

    def test_add_page_opens(self):
        self.assertEqual(self.client.get("/add/").status_code, 200)

    def test_missing_edit_returns_404(self):
        self.assertEqual(self.client.get("/123456/edit/").status_code, 404)
