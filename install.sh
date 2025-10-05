#!/bin/bash
: '
*****************************************
AVA Single Unique Process Installer
© AVA, 2025
*****************************************
'

rm -rf ./dist
python3 -m build
pip3 uninstall suproc -y
pip3 install dist/suproc-0.10.8-py3-none-any.whl
suproc-init
