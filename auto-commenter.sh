#!/usr/bin/env bash
python3 auto-commenter.py
diff -U 0 $1 $1.new > $1.patch
cat $1.patch | egrep -B1 "^\+\s+\#\s" | egrep "@@|^\+\s+\#\s" > $1.patch.new
patch $1 $1.patch.new

