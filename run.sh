#!/bin/bash

toolforge-jobs run uhaibot-2 --command "$HOME/pwbvenv/bin/python3 $HOME/sdlistupdate.py" --image python3.9 --schedule "22 * * * *" --retry 1