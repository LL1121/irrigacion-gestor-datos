import os
import shutil
import subprocess
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
	help = "Backup database and media files"

	def add_arguments(self, parser):
		parser.add_argument(
			"--output-dir",
			type=str,
			default=str(settings.BASE_DIR / "backups"),
			help="Directory to store backups",
		)

	def handle(self, *args, **options):
		output_dir = options["output_dir"]
		os.makedirs(output_dir, exist_ok=True)

		timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
		db_engine = settings.DATABASES["default"]["ENGINE"]

		self.stdout.write(self.style.NOTICE(f"Starting backup: {timestamp}"))

		if "sqlite3" in db_engine:
			self._backup_sqlite(output_dir, timestamp)
		elif "postgresql" in db_engine:
			self._backup_postgres(output_dir, timestamp)
		else:
			self.stdout.write(self.style.WARNING("Unsupported DB engine for backup"))

		self._backup_media(output_dir, timestamp)
		self.stdout.write(self.style.SUCCESS("Backup completed"))

	def _backup_sqlite(self, output_dir, timestamp):
		source = settings.DATABASES["default"]["NAME"]
		dest = os.path.join(output_dir, f"db_backup_{timestamp}.sqlite3")
		shutil.copy2(source, dest)
		self.stdout.write(self.style.SUCCESS(f"SQLite backup saved: {dest}"))

	def _backup_postgres(self, output_dir, timestamp):
		db = settings.DATABASES["default"]
		backup_file = os.path.join(output_dir, f"db_backup_{timestamp}.sql")

		cmd = [
			"pg_dump",
			"-h", db.get("HOST", ""),
			"-p", str(db.get("PORT", 5432)),
			"-U", db.get("USER", ""),
			"-f", backup_file,
			db.get("NAME", ""),
		]

		env = os.environ.copy()
		if db.get("PASSWORD"):
			env["PGPASSWORD"] = db.get("PASSWORD")

		try:
			subprocess.run(cmd, check=True, env=env)
			self.stdout.write(self.style.SUCCESS(f"PostgreSQL backup saved: {backup_file}"))
		except Exception as exc:
			self.stdout.write(self.style.ERROR(f"PostgreSQL backup failed: {exc}"))

	def _backup_media(self, output_dir, timestamp):
		source = settings.MEDIA_ROOT
		if not source or not os.path.exists(source):
			return

		dest = os.path.join(output_dir, f"media_backup_{timestamp}")
		shutil.copytree(source, dest, dirs_exist_ok=True)
		self.stdout.write(self.style.SUCCESS(f"Media backup saved: {dest}"))
