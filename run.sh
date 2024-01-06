#!/bin/bash

toolforge-jobs flush

toolforge-jobs run sdlistadd --command "$HOME/pythonenv/bin/python3 $HOME/sdlistadd.py" --image python3.11 --mem 4Gi --cpu 1 --schedule "8 3 1 * *"
toolforge-jobs run sdlistupdate --command "$HOME/pythonenv/bin/python3 $HOME/sdlistupdate.py" --image python3.11 --schedule "@hourly"