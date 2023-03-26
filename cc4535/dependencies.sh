#!/bin/bash

sudo apt-get -y update

sudo apt-get install python3-pip 
sudo apt-get install python3.7
sudo apt-get install python3.7-venv

sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.7 1

sudo pip3 install --upgrade google-api-python-client

sudo pip3 install -U nltk