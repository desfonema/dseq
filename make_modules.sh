#!bin/sh
rm -r build
python setup.py build
find build/ -name alsamidi.so -exec cp {} . \;
find build/ -name nanosleep.so -exec cp {} . \;
rm -r build
