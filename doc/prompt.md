# Photo Organizer prompt

Photo Organizer is a CLI utility written in Python,
it organizes JPG files into directories by EXIF stamp.

The utility is 100% made by AI.

> There are more versions.

## V2: DeepSeek

Second version with single prompt.

New features:
- keep description elements in directory name,
- move non-image files,
- sophisticated date detection,
- delete of trash, thumbnail etc. images,
- ignore list arg,
- rename wrong filenames,
- skip empty dirs,
- fix my personal quirky naming conventions.

### Prompt

```
Create photo organizer program in Python3.

Command line args:
 -s, --source: root source path,
 -t, --target: root target path,
 -f, --filter: date filter,
 -d, --dry-run: dry run
 -l, --log: log file name
 -i, --ignore-list: ignored directory list

Process root source path recursively and
process directories which have subdirectories or contains least one
JPG or GIF or PNG or BMP or PDF or WAV or MP3 or AVI or MOV or MPG or 3GP or M4V or MP4 file.

If the directory is in the ignore list, ignore it.
Ignore list is specified by command line arg -i.

Process each file.
If the photo date is older than specified date filter, skip it.
If filename is "Thumbs.db" or ".DS_Store", skip it and delete source file.
If filename begins with ".trashed" or "._", skip it and delete source file.
If filename extension is ".EXE" or ".DLL", skip it and delete source file.

Use get_official_dir_name() method to get target directory.
Target path is YYYY/ and target directory name.

If the root target path not exists, create it.
If the photo target path not exists, create it.

If the photo name starts with '-'
or contains only more than 15 numbers,
rename it to "img-YYYYMMDD-hhmmss" using EXIF timestamp.
Move JPG file to the photo target directory.
Move all other files from source directory to the target path.
If the file exist with same name and same size, overwrite it,
else rename to a unique name.

If the photo source directory is empty after file move,
delete the photo source directory.
If the root source directory is empty after file move,
delete the root source directory.

If the dry run arg is specified, do not perform, only log.

Use log file to log all
skip, directory creation, file move, rename, directory delete.
Include source and target path in log messages.
Delete old log file, if any.
If no log file specified print on console.
Do not add loglevel and timestamp to log messages, only raw lines.
Do not use logger library.

At the end of program, create a statistics.
Count
source directories processed,
source directories skipped,
source directories deleted,
files moved with name unchanged,
files moved with changed name,
source files skipped,
source files deleted.

Use argparse with no color.
Organize the program in a class.
Split the program to methods.
Add shebang.
Use PIL for exif reading.

Write get_official_dir_name() method.
Parameter is full path to filename.
Split it by '/', remove last piece.
Strip leading "DCIM-" from all pieces.
Take all pieces.
If piece starts with YYYYMMDD,
return with the piece.
If piece starts with YYYY-MM-DD,
replace YYYY-MM-DD with YYYYMMDD and return with the piece.
If piece starts with YYYY-nodate,
return with the piece.
If no piece match,
return exif date of parameter filename in YYYYMMDD format.
```

### Handmade changes

No handmade changes made.

The prompt is more verbose:

- Without `get_official_dir_name()` specified separately,
  the LLM was ubable to create proper handling of dates.
- Had to force to use PIL for EXIF parsing, sometimes
  used other libs not installed on my system.
- Listed extensions to include, and patterns to exclude.

## V1: Claude Sonnet 4.5

First version with incremental prompt.

### Initial prompt

- Start with basic description, suggesting timestamp format,
  exif reading and directory creation.

```
write python program
takes *.jpg files from a directory
reads exif data
renames image to img-yyyymmdd-hhmmss
creates if not exists directory yyyymmdd
moves image to created directory
```

### More features

- Specify what to do with existing and duplicate items.
- Add feature to process only new items, filter for date.

```
skip photos before a specified date
skip photos if they exists
skip duplicated files if their sizes are equal
```

### Debug features

- Dry mode would be nice for testing the program
  without destroying data.
- Add some logging.
- Suggest timestamp fallback if EXIF not present.

```
add dry mode, not performing the move
create log
if no exif present, keep directory name, use year as first 4 digits
```

### Arg handling cleanup

- Different purpose positional arguments are uncomfortable, fix it.

```
add switch to all arg: -s source -t target -d dry -f date filter
```

### Delete empty dirs

- Once all files moved, source directories should be deleted.

```
after move check source directory and delete if it contains no files
```

- Even empty source root directory should be deleted.

```
also delete source directory if it's empty
```

### Minor UI fix

- Move deletion summary after processing summary.

```
print summary at the end, not before deleting
```

### Refactor

- The whole program is  single function,
  which looks awkward.

```
refactor, split program into functions
```

### Handmade changes

Removed line break from separator logging.

Before:
```
  logging.info(f"\n{'='*50}")
```

After:
```
  logging.info(f"{'='*50}")
```
