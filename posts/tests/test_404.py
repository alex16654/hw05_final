from django.test import TestCase


class Sample404TestCase(TestCase):
    def test_wrong_url_returns_404(self):
        response = self.client.get('bla/bla/bla')
        self.assertEqual(response.status_code, 404)