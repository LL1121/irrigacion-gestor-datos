from io import BytesIO

from django.test import TestCase
from PIL import Image

from web.utils import compress_and_resize_image, generate_unique_filename


class UtilsTests(TestCase):
	def test_generate_unique_filename(self):
		name = generate_unique_filename(1, "foto.png")
		self.assertTrue(name.endswith(".png"))
		self.assertIn("user_1", name)

	def test_compress_and_resize_image(self):
		img = Image.new("RGB", (2000, 1500), color=(255, 0, 0))
		buffer = BytesIO()
		img.save(buffer, format="JPEG")
		buffer.seek(0)

		compressed = compress_and_resize_image(buffer, max_size=1280, quality=70)
		self.assertIsNotNone(compressed)

		compressed_img = Image.open(compressed)
		width, height = compressed_img.size
		self.assertTrue(max(width, height) <= 1280)
