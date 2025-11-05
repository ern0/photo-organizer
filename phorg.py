#!/usr/bin/env python3

import argparse
import datetime
import logging
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Optional, Tuple, List

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
except ImportError:
    print("Pillow library is required. Install it with: pip install Pillow", file=sys.stderr)
    sys.exit(1)


class PhotoOrganizer:
    def __init__(self):
        self.args = None
        self.logger = None
        self.stats = {
            'files_processed': 0,
            'files_moved': 0,
            'files_skipped': 0,
            'dirs_created': 0,
            'dirs_deleted': 0,
        }

    def setup_logging(self):
        """Setup logging to file or console."""
        if self.args.log_file:
            # Delete old log file if it exists
            if os.path.exists(self.args.log_file):
                os.remove(self.args.log_file)
            logging.basicConfig(
                filename=self.args.log_file,
                level=logging.INFO,
                format='%(message)s'
            )
        else:
            logging.basicConfig(
                level=logging.INFO,
                format='%(message)s',
                stream=sys.stdout
            )

        self.logger = logging.getLogger()

    def log(self, message: str):
        """Log a message without extra formatting."""
        self.logger.info(message)

    def parse_args(self):
        """Parse command line arguments."""
        parser = argparse.ArgumentParser(description='Organize photos by date')
        parser.add_argument('-s', '--source', required=True, help='Root source directory')
        parser.add_argument('-t', '--target', required=True, help='Root target directory')
        parser.add_argument('-f', '--filter-date', help='Date filter (YYYY-MM-DD)')
        parser.add_argument('-d', '--dry-run', action='store_true', help='Dry run (no actual operations)')
        parser.add_argument('-l', '--log-file', help='Log file name')

        self.args = parser.parse_args()

        # Validate source directory
        if not os.path.exists(self.args.source):
            print(f"Source directory does not exist: {self.args.source}", file=sys.stderr)
            sys.exit(1)

        # Parse filter date if provided
        if self.args.filter_date:
            try:
                self.args.filter_date_parsed = datetime.datetime.strptime(
                    self.args.filter_date, '%Y-%m-%d'
                ).date()
            except ValueError:
                print(f"Invalid date format for filter: {self.args.filter_date}. Use YYYY-MM-DD", file=sys.stderr)
                sys.exit(1)
        else:
            self.args.filter_date_parsed = None

    def extract_date_from_path(self, path: Path) -> Optional[datetime.date]:
        """Extract date from directory path if it contains YYYYMMDD or YYYY-MM-DD."""
        # Check the directory name and its parent
        parts_to_check = [path.name, path.parent.name]

        for part in parts_to_check:
            # Remove leading DCIM- if present
            clean_part = re.sub(r'^DCIM-', '', part)

            # Try YYYYMMDD format (optionally followed by a letter)
            match = re.search(r'(\d{8})([A-Za-z]?)', clean_part)
            if match:
                date_str = match.group(1)
                try:
                    return datetime.datetime.strptime(date_str, '%Y%m%d').date()
                except ValueError:
                    pass

            # Try YYYY-MM-DD format
            match = re.search(r'(\d{4}-\d{2}-\d{2})', clean_part)
            if match:
                try:
                    return datetime.datetime.strptime(match.group(1), '%Y-%m-%d').date()
                except ValueError:
                    pass

        return None

    def get_exif_date(self, image_path: Path) -> Optional[datetime.datetime]:
        """Extract date from EXIF data."""
        try:
            with Image.open(image_path) as img:
                exif_data = img._getexif()
                if exif_data is not None:
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        if tag == 'DateTimeOriginal':
                            try:
                                return datetime.datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                            except (ValueError, TypeError):
                                pass
        except Exception:
            pass
        return None

    def get_file_creation_date(self, file_path: Path) -> datetime.datetime:
        """Get file creation date (or modification date on Unix)."""
        stat = file_path.stat()
        try:
            # Try to get creation time (Windows)
            return datetime.datetime.fromtimestamp(stat.st_ctime)
        except AttributeError:
            # Fall back to modification time (Unix)
            return datetime.datetime.fromtimestamp(stat.st_mtime)

    def should_process_file(self, file_date: datetime.date) -> bool:
        """Check if file should be processed based on date filter."""
        if self.args.filter_date_parsed is None:
            return True
        return file_date >= self.args.filter_date_parsed

    def get_target_directory(self, source_file: Path, source_dir: Path) -> Tuple[str, Path]:
        """Determine target directory and name for the file."""
        # First, try to extract date from source directory path
        date_from_path = self.extract_date_from_path(source_dir)

        if date_from_path:
            # Use the date from path and keep the original directory name (stripping DCIM-)
            dir_name = re.sub(r'^DCIM-', '', source_dir.name)
            target_dir = Path(self.args.target) / str(date_from_path.year) / dir_name
            return dir_name, target_dir
        else:
            # Try EXIF date
            exif_date = self.get_exif_date(source_file)
            if exif_date:
                date_str = exif_date.strftime('%Y-%m-%d')
                target_dir = Path(self.args.target) / str(exif_date.year) / date_str
                return date_str, target_dir
            else:
                # Use file creation date
                creation_date = self.get_file_creation_date(source_file)
                date_str = creation_date.strftime('%Y-%m-%d')
                target_dir = Path(self.args.target) / str(creation_date.year) / date_str
                return date_str, target_dir

    def get_target_filename(self, source_file: Path, source_dir: Path) -> str:
        """Determine target filename."""
        if source_file.name.startswith('-'):
            # Get timestamp for renaming
            exif_date = self.get_exif_date(source_file)
            if exif_date:
                timestamp = exif_date.strftime('%Y%m%d-%H%M%S')
            else:
                creation_date = self.get_file_creation_date(source_file)
                timestamp = creation_date.strftime('%Y%m%d-%H%M%S')
            return f"img-{timestamp}{source_file.suffix.lower()}"
        else:
            return source_file.name.lower()

    def create_directory(self, dir_path: Path):
        """Create directory if it doesn't exist."""
        if not dir_path.exists():
            if not self.args.dry_run:
                dir_path.mkdir(parents=True, exist_ok=True)
            self.log(f"CREATE DIR: {dir_path}")
            self.stats['dirs_created'] += 1

    def move_file(self, source_file: Path, target_file: Path):
        """Move file to target location."""
        if not self.args.dry_run:
            shutil.move(str(source_file), str(target_file))
        self.log(f"MOVE FILE: {source_file} -> {target_file}")
        self.stats['files_moved'] += 1

    def delete_directory_if_empty(self, dir_path: Path):
        """Delete directory if it's empty."""
        if dir_path.exists() and not any(dir_path.iterdir()):
            if not self.args.dry_run:
                dir_path.rmdir()
            self.log(f"DELETE DIR: {dir_path}")
            self.stats['dirs_deleted'] += 1

    def process_file(self, source_file: Path):
        """Process a single photo file."""
        self.stats['files_processed'] += 1

        source_dir = source_file.parent

        # Get target directory and name
        dir_name, target_dir = self.get_target_directory(source_file, source_dir)

        # Get the date for filtering
        if self.extract_date_from_path(source_dir):
            file_date = self.extract_date_from_path(source_dir)
        else:
            exif_date = self.get_exif_date(source_file)
            if exif_date:
                file_date = exif_date.date()
            else:
                file_date = self.get_file_creation_date(source_file).date()

        # Check date filter
        if not self.should_process_file(file_date):
            self.log(f"SKIP FILE (date filter): {source_file}")
            self.stats['files_skipped'] += 1
            return

        # Get target filename
        target_filename = self.get_target_filename(source_file, source_dir)
        target_file = target_dir / target_filename

        # Create target directory
        self.create_directory(target_dir)

        # Handle filename conflicts
        counter = 1
        original_target_file = target_file
        while target_file.exists():
            name, ext = os.path.splitext(original_target_file.name)
            target_file = target_dir / f"{name}_{counter}{ext}"
            counter += 1

        # Move the file
        self.move_file(source_file, target_file)

        # Mark source directory for potential deletion
        self.directories_to_check.add(source_dir)

    def run(self):
        """Main execution method."""
        self.parse_args()
        self.setup_logging()

        source_path = Path(self.args.source)
        target_path = Path(self.args.target)

        # Create target root directory if it doesn't exist
        if not target_path.exists():
            if not self.args.dry_run:
                target_path.mkdir(parents=True, exist_ok=True)
            self.log(f"CREATE DIR: {target_path}")
            self.stats['dirs_created'] += 1

        # Set to keep track of directories that might need deletion
        self.directories_to_check = set()

        # Process all JPG files recursively
        jpg_files = list(source_path.rglob("*.jpg")) + list(source_path.rglob("*.JPG"))

        for jpg_file in sorted(jpg_files):
            try:
                self.process_file(jpg_file)
            except Exception as e:
                self.log(f"ERROR processing {jpg_file}: {str(e)}")
                self.stats['files_skipped'] += 1

        # Check directories for deletion (in reverse order to handle nested dirs)
        dirs_to_check = sorted(self.directories_to_check, key=lambda x: len(str(x)), reverse=True)
        for dir_path in dirs_to_check:
            self.delete_directory_if_empty(dir_path)

        # Check if root source directory is empty and should be deleted
        if source_path.exists() and not any(source_path.iterdir()):
            if not self.args.dry_run:
                source_path.rmdir()
            self.log(f"DELETE DIR: {source_path}")
            self.stats['dirs_deleted'] += 1

        # Log statistics
        self.log(f"STATISTICS:")
        self.log(f"  Files processed: {self.stats['files_processed']}")
        self.log(f"  Files moved: {self.stats['files_moved']}")
        self.log(f"  Files skipped: {self.stats['files_skipped']}")
        self.log(f"  Directories created: {self.stats['dirs_created']}")
        self.log(f"  Directories deleted: {self.stats['dirs_deleted']}")

def main():
    organizer = PhotoOrganizer()
    organizer.run()

if __name__ == "__main__":
    main()
