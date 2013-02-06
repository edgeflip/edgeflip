#!/usr/bin/python
import json
import logging

# read the config file and create the config dict
defaults = {}
defaults['outdir'] = ''

try: 
	config = json.load('edgeflip.config')
except AttributeError:
	config = {}
for k, v in defaults.items():
	if (k not in config):
		config[k] = v

# set up logging
logging.basicConfig(format='%(asctime)s\t%(levelname)s\t%(process)d\t%(threadName)s\t%(message)s',
					filename=config['outdir'] + 'demo.log',
					level=logging.DEBUG)
