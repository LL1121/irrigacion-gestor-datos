from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from web.models import Medicion


class ViewTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username="operario", password="test1234")

	def test_weekly_route_requires_login(self):
		response = self.client.get(reverse("weekly_route"))
		self.assertEqual(response.status_code, 302)

	def test_api_docs_requires_login(self):
		response = self.client.get(reverse("api_docs"))
		self.assertEqual(response.status_code, 302)

	def test_weekly_route_data_requires_login(self):
		response = self.client.get(reverse("weekly_route_data"))
		self.assertEqual(response.status_code, 302)

	def test_exportar_csv_requires_login(self):
		response = self.client.get(reverse("exportar_csv"))
		self.assertEqual(response.status_code, 302)

	def test_exportar_csv_as_user(self):
		self.client.login(username="operario", password="test1234")
		Medicion.objects.create(user=self.user, value=10)
		response = self.client.get(reverse("exportar_csv"))
		self.assertEqual(response.status_code, 200)
		self.assertIn("text/csv", response.get("Content-Type", ""))
