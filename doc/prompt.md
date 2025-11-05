# Photo Organizer prompt

Photo Organizer is a CLI utility written in Python,
it organizes JPG files into directories by EXIF stamp.

The utility is 99.99% made by AI.

> There are more versions.

## V2: DeepSeek

Second version with single prompt.

New feature: keep description elements in directory name.

### Prompt

```
Create photo organizer program in Python3.

Command line args:
 -s: root source directory,
 -t: root target directory,
 -f: date filter,
 -d: dry run
 -l: log file name.
 Add long arg versions.

Take recursively all *.jpg files from the specified source directory,
and move it to the photo target directory.
If the photo target directory does not exists, create it.
If the root target directory does not exists, create it.

Strip leading "DCIM-" from source directory name.
If the photo source directory or its parent directory contains a date YYYYMMDD or YYYY-MM-DD, or followed by a letter, use it unchanged,
create target directory under YYYY/ with same name.
Else if the photo has EXIF data, crate target under YYYY/ directory named YYYY-MM-DD.
Else use photo creation date YYYY-MM-DD, use as target directory name and put under YYYY/
Strip leading "DCIM-" from target directory name.

If the photo name starts with '-' rename it to "img-YYYYMMDD-hhmmss"
using EXIF timestamp.

If the photo source directory is empty after file move,
delete the photo source directory.
If the root source directory is empty after file move,
delete the root source directory.

If the photo date is older than specified date filter, skip it.

If the dry run arg is specified, do not perform, only log.

Use log file to log all directory creation, file move, directory delete.
Delete old log file, if any.
If no log file specified print on console.
Do not add "\n" to log messages.
Do not add loglevel and timestamp to log messages, only raw lines.

At the end of program, create a statistics about operations.

Use argparse with no color.
Organize the program in a class.
Split the program to methods.
Add shebang.
```

### Handmade changes

TODO

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
