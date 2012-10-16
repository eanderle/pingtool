# Pingtool

This is a dirt-simple tool for pinging hosts and dumping ping results
to a CSV file for later analysis.

## Installation

Just run:

    ./install.sh

## Running it

Just do:

    sudo ./venv/bin/pingtool.py

If you don't want to ping the default hosts (10.11.0.1 and google.com),
you can specify your own list like so:

    sudo ./venv/bin/pingtool.py 10.0.0.1 google.com

## Retrieving the data

Data is written both to the terminal and to ``/tmp/pingtool.csv``.
