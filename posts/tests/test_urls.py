from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse


User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='StasBasov')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.unauthorized_client = Client()

    def test_homepage(self):
        response = self.unauthorized_client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)

    def test_force_login(self):
        response = self.authorized_client.get(reverse('new_post'))
        self.assertEqual(response.status_code, 200)

    def test_unauthorized_user_newpage(self):
        """Доступность страницы /new/ для неавторизованного пользователя"""
        response = self.unauthorized_client.get(reverse('new_post'))
        self.assertRedirects(response,
                             f"{reverse('login')}?next={reverse('new_post')}",
                             status_code=302, target_status_code=200)
