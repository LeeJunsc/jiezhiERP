from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient


class UserManagementTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username="admin", password="admin123456")
        self.user = User.objects.create_user(username="staff01", password="oldPassword123")
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def test_admin_can_reset_user_password(self):
        response = self.client.post(
            f"/api/v1/users/{self.user.id}/reset-password/",
            {"password": "newPassword123"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newPassword123"))

    def test_reset_password_requires_minimum_length(self):
        response = self.client.post(
            f"/api/v1/users/{self.user.id}/reset-password/",
            {"password": "short"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("oldPassword123"))
