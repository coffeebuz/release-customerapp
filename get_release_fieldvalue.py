#!/usr/bin/python

import sys
import yaml

release = yaml.safe_load(open('Release.yml'))
sys.stdout.writelines(release[sys.argv[1]])