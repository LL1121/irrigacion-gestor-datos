from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from web.models import Medicion


class MedicionModelTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username="operario", password="test1234")

	def test_negative_value_validation(self):
		medicion = Medicion(user=self.user, value=-1)
		with self.assertRaises(ValidationError):
			medicion.full_clean()

	def test_null_island_validation(self):
		medicion = Medicion(user=self.user, value=10, captured_latitude=0, captured_longitude=0)
		with self.assertRaises(ValidationError):
			medicion.full_clean()

	def test_maps_url_property(self):
		medicion = Medicion(user=self.user, value=10, captured_latitude=-35.4, captured_longitude=-69.5)
		self.assertIn("maps/search", medicion.maps_url)

	def test_has_location_property(self):
		medicion = Medicion(user=self.user, value=10)
		self.assertFalse(medicion.has_location)
		medicion.captured_latitude = -35.4
		medicion.captured_longitude = -69.5
		self.assertTrue(medicion.has_location)
