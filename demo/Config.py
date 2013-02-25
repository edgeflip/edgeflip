#!/usr/bin/python
import json
import logging
import logging.handlers



CONFIG_PATH = './edgeflip.config'

# read the config file and create the config dict
defaults = {}
defaults['outdir'] = '.'
defaults['codedir'] = '.'
defaults['queue'] = 'edgeflip_demo'
defaults['logpath'] = './demo.log'
defaults['dbpath'] = './demo.sqlite'
defaults['stream_days'] = 120
defaults['stream_days_chunk'] = 2
defaults['stream_threadcount'] = 60
defaults['stream_read_timeout'] = 10 # seconds
defaults['stream_read_sleep'] = 0.1 # seconds




# the config dict will be imported from other modules
try: 
	config = json.load(open(CONFIG_PATH, 'r'))
except IOError:
	config = {}

# set up logging
logger = logging.getLogger()
logpath = config.get('logpath', defaults['logpath'])
loghand = logging.handlers.TimedRotatingFileHandler(logpath, when='d', interval=1, backupCount=0, encoding=None, delay=False, utc=False)
logformat = logging.Formatter(fmt='%(asctime)s\t%(levelname)s\t%(process)d\t%(threadName)s\t%(message)s', datefmt=None)
loghand.setFormatter(logformat)
logger.addHandler(loghand)
logger.setLevel(logging.DEBUG)

for k, v in config.items():
	logging.debug("config %s: %s" % (k, str(v)))

for k, v in defaults.items():
	if (k not in config):
		logging.debug("config default %s: %s" % (k, str(v)))
		config[k] = v

