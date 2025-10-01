#!/bin/bash
: '
*****************************************
AVA Single Unique Process
© AVA, 2025
*****************************************
'

rm -rf ./dist
python3 -m build
pip3 uninstall suproc -y
pip3 install dist/suproc-0.9.6-py3-none-any.whl
