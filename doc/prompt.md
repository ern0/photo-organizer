# Photo Organizer prompt

Photo Organizer is a CLI utility written in Python,
it organizes JPG files by EXIF date into direcetories.

The utility is 99.99% made by AI.

## Claude Sonnet 4.5

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
