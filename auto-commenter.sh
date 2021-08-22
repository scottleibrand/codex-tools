#!/usr/bin/env bash

# Check that $1 is a valid file that exists.
# If not, print out a usage string and exit.
if [ ! -f "$1" ]; then
    echo "Usage: auto-commenter.sh filename"
    exit 1
fi

# Process the filename provided in the first argument and convert it from a relative to an absolute path
file=$(realpath $1)
python3 auto-commenter.py $file
diff -U 0 $file $file.new > $file.patch
head -2 $file.patch > $file.patch.new
cat $file.patch | egrep -B1 "^\+\s+\#\s" | egrep -A1 "@@ -\d+,0 \+\d+ @@" | egrep "@@|^\+\s+\#\s" >> $file.patch.new
patch $file $file.patch.new
