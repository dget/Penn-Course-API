#!/bin/sh
export DJANGO_SETTINGS_MODULE=api.settings
export PYTHONPATH=$(cd ..;pwd)

TODAY=$(date +%Y-%m-%d)
if [ ! -d $TODAY ]; then
mkdir $TODAY
python download.py
mv *.txt $TODAY/
fi

python uploadcourses.py $TODAY/*.txt
