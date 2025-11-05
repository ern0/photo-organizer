#!/usr/bin/env python3

"""
Photo Organizer - Organizes JPG files by EXIF date
Renames images to img-yyyymmdd-hhmmss format and moves them to yyyymmdd directories
99% AI generated code - Claude Sonnet 4.5

Features:
- Recursively processes source directory
- Reads EXIF data from JPG files
- Renames files to img-yyyymmdd-hhmmss.jpg format
- Creates date-based directories (yyyymmdd format)
- Moves renamed images into corresponding directories
- Skips photos before specified date
- Skips duplicates if file size matches
- Handles files without EXIF by using directory name with year
- Deletes empty directories after moving files
- Creates detailed log file
- Supports dry-run mode

Usage:
    python photo_organizer.py -s /source -t /target
    python photo_organizer.py -s /source -t /target -f 2024-01-01
    python photo_organizer.py -s /source -t /target -d
    python photo_organizer.py -s /source -t /target -f 2024-01-01 -d
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS


def setup_logging(dry_run=False):
    """
    Setup logging configuration with file and console handlers.
    Returns the log filename.
    """
    log_filename = f"photo_organizer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler()
        ]
    )

    if dry_run:
        logging.info("DRY RUN MODE - No files will be moved")

    return log_filename


def get_exif_date(image_path):
    """
    Extract the date taken from EXIF data.
    Returns datetime object or None if not found.
    """
    try:
        image = Image.open(image_path)
        exif_data = image._getexif()

        if exif_data is None:
            return None

        # Look for DateTimeOriginal (36867) or DateTime (306)
        for tag_id, value in exif_data.items():
            tag_name = TAGS.get(tag_id, tag_id)
            if tag_name in ['DateTimeOriginal', 'DateTime']:
                # EXIF date format: "YYYY:MM:DD HH:MM:SS"
                return datetime.strptime(value, '%Y:%m:%d %H:%M:%S')

        return None
    except Exception as e:
        logging.debug(f"Error reading EXIF from {image_path}: {e}")
        return None


def extract_year_from_directory(directory_name):
    """
    Try to extract a 4-digit year from directory name.
    Returns year string or None if not found.
    """
    for i in range(len(directory_name) - 3):
        if directory_name[i:i+4].isdigit():
            return directory_name[i:i+4]
    return None


def get_target_info(jpg_file, exif_date, min_date):
    """
    Determine target directory and filename for a photo.
    Returns tuple of (date_dir, new_filename, should_skip, skip_reason)
    """
    if exif_date is None:
        # No EXIF data - use directory name with year as first 4 digits
        parent_dir = jpg_file.parent.name
        year_match = extract_year_from_directory(parent_dir)

        if year_match:
            date_dir = parent_dir
            new_filename = jpg_file.name
            logging.info(f"No EXIF for {jpg_file.name}: Using directory '{date_dir}' (found year {year_match})")
            return date_dir, new_filename, False, None
        else:
            return None, None, True, f"No EXIF date and no year in directory name '{parent_dir}'"

    # Has EXIF date - check minimum date filter
    if min_date and exif_date < min_date:
        return None, None, True, f"Date {exif_date.strftime('%Y-%m-%d')} is before minimum date"

    # Format date components
    date_dir = exif_date.strftime('%Y%m%d')
    new_filename = exif_date.strftime('img-%Y%m%d-%H%M%S.jpg')

    return date_dir, new_filename, False, None


def check_duplicate(source_file, target_file):
    """
    Check if target file exists and has the same size as source.
    Returns True if it's a duplicate, False otherwise.
    """
    if not target_file.exists():
        return False

    source_size = source_file.stat().st_size
    target_size = target_file.stat().st_size

    return source_size == target_size


def find_available_filename(target_subdir, new_filename, source_file, exif_date):
    """
    Find an available filename by adding counter if needed.
    Returns tuple of (final_path, final_filename, is_duplicate)
    """
    final_path = target_subdir / new_filename
    counter = 1

    # Check if file already exists with same name and size
    if check_duplicate(source_file, final_path):
        return final_path, new_filename, True

    # File exists but different size, find new name
    while final_path.exists():
        if exif_date:
            new_filename = exif_date.strftime(f'img-%Y%m%d-%H%M%S_{counter}.jpg')
        else:
            # For files without EXIF, add counter before extension
            name_parts = source_file.stem, source_file.suffix
            new_filename = f"{name_parts[0]}_{counter}{name_parts[1]}"
        final_path = target_subdir / new_filename

        # Check size of this potential duplicate too
        if check_duplicate(source_file, final_path):
            return final_path, new_filename, True

        counter += 1

    return final_path, new_filename, False


def process_single_file(jpg_file, target_path, min_date, dry_run, stats):
    """
    Process a single JPG file.
    Updates stats dictionary with results.
    Returns the source directory if file was moved, None otherwise.
    """
    # Get EXIF date
    exif_date = get_exif_date(jpg_file)

    # Determine target directory and filename
    date_dir, new_filename, should_skip, skip_reason = get_target_info(jpg_file, exif_date, min_date)

    if should_skip:
        logging.warning(f"Skipping {jpg_file.name}: {skip_reason}")
        if "year in directory" in skip_reason:
            stats['skipped'] += 1
        else:
            stats['skipped_date'] += 1
        return None

    # Create target subdirectory
    target_subdir = target_path / date_dir
    if not dry_run:
        target_subdir.mkdir(exist_ok=True)

    # Find available filename
    final_path, final_filename, is_duplicate = find_available_filename(
        target_subdir, new_filename, jpg_file, exif_date
    )

    if is_duplicate:
        logging.info(f"Skipping {jpg_file.name}: Duplicate found with same size")
        stats['skipped_duplicate'] += 1
        return None

    # Move and rename file
    try:
        if not dry_run:
            jpg_file.rename(final_path)
            logging.info(f"✓ {jpg_file.name} → {date_dir}/{final_filename}")
        else:
            logging.info(f"[DRY RUN] Would move: {jpg_file.name} → {date_dir}/{final_filename}")
        stats['processed'] += 1
        return jpg_file.parent
    except Exception as e:
        logging.error(f"Error moving {jpg_file.name}: {e}")
        stats['skipped'] += 1
        return None


def find_jpg_files(source_path):
    """
    Find all JPG files recursively in source path.
    Returns list of Path objects.
    """
    jpg_files = list(source_path.rglob('*.jpg')) + list(source_path.rglob('*.JPG'))
    return jpg_files


def delete_empty_directory(dir_path):
    """
    Delete directory if it's empty.
    Returns True if deleted, False otherwise.
    """
    try:
        if dir_path.exists() and dir_path.is_dir():
            if not any(dir_path.iterdir()):
                dir_path.rmdir()
                logging.info(f"Deleted empty directory: {dir_path}")
                return True
    except Exception as e:
        logging.warning(f"Could not delete directory {dir_path}: {e}")
    return False


def cleanup_empty_directories(moved_from_dirs, source_path):
    """
    Delete empty directories after moving files.
    Returns count of deleted directories.
    """
    logging.info(f"{'='*50}")
    logging.info("Checking for empty directories...")

    deleted_dirs = 0

    # Sort directories by depth (deepest first) to handle nested empties
    sorted_dirs = sorted(moved_from_dirs, key=lambda p: len(p.parts), reverse=True)

    for dir_path in sorted_dirs:
        if delete_empty_directory(dir_path):
            deleted_dirs += 1

            # Also check and delete parent directories if they become empty
            parent = dir_path.parent
            while parent.exists():
                if delete_empty_directory(parent):
                    deleted_dirs += 1
                    parent = parent.parent
                else:
                    break

    # Finally, check if source directory itself is empty
    if delete_empty_directory(source_path):
        deleted_dirs += 1

    if deleted_dirs > 0:
        logging.info(f"Total empty directories deleted: {deleted_dirs}")
    else:
        logging.info("No empty directories to delete")

    return deleted_dirs


def print_summary(stats, deleted_dirs, log_filename):
    """
    Print final summary of all operations.
    """
    logging.info(f"{'='*50}")
    logging.info("SUMMARY:")
    logging.info(f"  Processed: {stats['processed']}")
    logging.info(f"  Skipped (no EXIF/year): {stats['skipped']}")
    if stats['skipped_date'] > 0:
        logging.info(f"  Skipped (before min date): {stats['skipped_date']}")
    if stats['skipped_duplicate'] > 0:
        logging.info(f"  Skipped (duplicates): {stats['skipped_duplicate']}")
    if deleted_dirs > 0:
        logging.info(f"  Empty directories deleted: {deleted_dirs}")
    logging.info(f"Log saved to: {log_filename}")
    logging.info('='*50)


def validate_directories(source_path, target_path, dry_run):
    """
    Validate and prepare source and target directories.
    Returns True if valid, False otherwise.
    """
    if not source_path.exists():
        logging.error(f"Directory '{source_path}' does not exist")
        return False

    # Create target directory if it doesn't exist
    if not target_path.exists():
        if not dry_run:
            try:
                target_path.mkdir(parents=True, exist_ok=True)
                logging.info(f"Created target directory: {target_path}")
            except Exception as e:
                logging.error(f"Could not create target directory '{target_path}': {e}")
                return False
        else:
            logging.info(f"Would create target directory: {target_path}")

    return True


def organize_photos(source_dir, target_dir=None, min_date=None, dry_run=False):
    """
    Process all JPG files in the source directory.
    Moves organized files to target_dir if specified, otherwise organizes in source_dir.

    Args:
        source_dir: Source directory containing JPG files
        target_dir: Target directory for organized files (None = use source_dir)
        min_date: Skip photos before this date (datetime object or None)
        dry_run: If True, don't actually move files, just log what would happen
    """
    source_path = Path(source_dir)
    target_path = Path(target_dir) if target_dir else source_path

    # Setup logging
    log_filename = setup_logging(dry_run)

    logging.info(f"Source directory: {source_path.absolute()}")
    logging.info(f"Target directory: {target_path.absolute()}")

    # Validate directories
    if not validate_directories(source_path, target_path, dry_run):
        return

    # Find all JPG files
    jpg_files = find_jpg_files(source_path)

    if not jpg_files:
        logging.warning(f"No JPG files found in '{source_dir}' (searched recursively)")
        return

    logging.info(f"Found {len(jpg_files)} JPG file(s) (searched recursively)")

    # Initialize statistics
    stats = {
        'processed': 0,
        'skipped': 0,
        'skipped_date': 0,
        'skipped_duplicate': 0
    }
    moved_from_dirs = set()

    # Process each file
    for jpg_file in jpg_files:
        source_dir_result = process_single_file(jpg_file, target_path, min_date, dry_run, stats)
        if source_dir_result:
            moved_from_dirs.add(source_dir_result)

    # Clean up empty directories
    deleted_dirs = 0
    if not dry_run and moved_from_dirs:
        deleted_dirs = cleanup_empty_directories(moved_from_dirs, source_path)

    # Print summary
    print_summary(stats, deleted_dirs, log_filename)


def parse_arguments():
    """
    Parse command line arguments.
    Returns parsed arguments.
    """
    parser = argparse.ArgumentParser(
        color=False,
        description='Organize JPG files by EXIF date into dated directories',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s -s /photos -t /organized
  %(prog)s -s /photos -t /organized -f 2024-01-01
  %(prog)s -s /photos -t /organized -d
  %(prog)s -s /photos -t /organized -f 2024-01-01 -d
        '''
    )

    parser.add_argument('-s', '--source',
                        help='Source directory containing JPG files (default: current directory)',
                        default='.')
    parser.add_argument('-t', '--target',
                        help='Target directory for organized files (default: same as source)',
                        default=None)
    parser.add_argument('-f', '--filter',
                        help='Minimum date filter in YYYY-MM-DD format (skip photos before this date)',
                        default=None)
    parser.add_argument('-d', '--dry-run',
                        action='store_true',
                        help='Dry run mode - show what would be done without moving files')

    return parser.parse_args()


def parse_date_filter(date_string):
    """
    Parse date string in YYYY-MM-DD format.
    Returns datetime object or exits on error.
    """
    if not date_string:
        return None

    try:
        min_date = datetime.strptime(date_string, '%Y-%m-%d')
        print(f"Processing photos from {min_date.strftime('%Y-%m-%d')} onwards")
        return min_date
    except ValueError:
        print(f"Invalid date format: {date_string}. Expected YYYY-MM-DD")
        sys.exit(1)


def main():
    """
    Main entry point of the program.
    """
    args = parse_arguments()
    min_date = parse_date_filter(args.filter)
    organize_photos(args.source, args.target, min_date, args.dry_run)


if __name__ == "__main__":
    main()
