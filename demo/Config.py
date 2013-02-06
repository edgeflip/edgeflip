#!/usr/bin/python
import json
import logging

# read the config file and create the config dict
defaults = {}
defaults['outdir'] = ''

try: 
	config = json.load(open('edgeflip.config', 'r'))
except AttributeError:
	config = {}

# set up logging
logging.basicConfig(format='%(asctime)s\t%(levelname)s\t%(process)d\t%(threadName)s\t%(message)s',
					filename=config.get('outdir', defaults['outdir']) + 'demo.log',
					level=logging.DEBUG)


for k, v in config.items():
	logging.debug("config %s: %s" % (k, str(v)))

for k, v in defaults.items():
	if (k not in config):
		logging.debug("config default %s: %s" % (k, str(v)))
		config[k] = v

