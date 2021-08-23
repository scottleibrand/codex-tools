#!/usr/bin/env bash

# Auto-commenter script to add OpenAI Codex generated comments to source code, explaining what the code is doing.

# This shell script first runs auto-commenter.py to prompt OpenAI Codex add comments to $file.
# It then diffs the generated function against the original, identifies all the added comments, and injects
# them into the original code.
# In most cases auto-commenter.py will produce a commented function identical to the generated one, but often
# it will decide the most likely completion is different from what was in the prompt in some way.
# This script programmatically parses the resulting changes to keep only the added comments, to avoid
# introducing any other changes to the original function.


# Check that $1 is a valid file that exists.
# If not, print out a usage string and exit.
if [ ! -f "$1" ]; then
    echo "Usage: auto-commenter.sh filename"
    exit 1
fi

# Process the filename provided in the first argument and convert it from a relative to an absolute path
#file=$(realpath $1)
# realpath doesn't exist on linux. Do it cross-platform.
file=$(cd "$(dirname "$1")"; pwd)/$(basename "$1")

# Run auto-commenter.py to prompt OpenAI Codex add comments to $file
python3 auto-commenter.py $file
# Write out a patch file containing all the changes Codex suggested
diff -U 0 $file $file.new > $file.patch
# Keep the patch file header
head -2 $file.patch > $file.patch.new
# Process the patch file to keep only added comments starting with whitespace and #.
# Patch syntax like @@ -112,0 +127 @@ is what we want (the ,0 represents 0 lines removed/replaced).
# Keep only the first line after each such patch header that matches the comment regex.
cat $file.patch | egrep -B1 "^\+\s+\#\s" | egrep -A1 "@@ -\d+,0 \+\d+ @@" | egrep "@@|^\+\s+\#\s" >> $file.patch.new
# Apply the trimmed down patch to the original $file, to generate a $file.new containing only the added comments.
patch $file $file.patch.new
