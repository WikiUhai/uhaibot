#!/bin/bash

toolforge-jobs flush

rm -fdr pwbvenv

python3 -m venv pwbvenv

source pwbvenv/bin/activate

pip install --upgrade pip setuptools wheel
pip install pywikibot
pip install mwoauth
pip install pymysql