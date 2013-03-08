#!/usr/bin/python
import json
import logging
import logging.handlers



CONFIG_PATH = './edgeflip.config'

# read the config file and create the config dict
defaults = {}

# locations of logs, code, and other important files
defaults['outdir'] = '.'
defaults['codedir'] = '.'
defaults['queue'] = 'edgeflip_demo'
defaults['logpath'] = './logs/demo.log'
# defaults['dbpath'] = './demo.sqlite'
defaults['dbhost'] = 'edgeflipdev.cwvoczji8mgi.us-east-1.rds.amazonaws.com'
defaults['dbuser'] = 'edgeflip'
defaults['dbpass'] = 'B0redsickdog'
defaults['dbname'] = 'edgeflipdev'
# defaults['dburi'] = 'mysql://edgeflip:B0redsickdog@edgeflipdev.cwvoczji8mgi.us-east-1.rds.amazonaws.com:3306/edgeflipdev'

# parameters for initial incoming stream reading ("px4")
defaults['stream_days_in'] = 120
defaults['stream_days_chunk_in'] = 2
defaults['stream_threadcount_in'] = 60
defaults['stream_read_timeout_in'] = 10 # seconds
defaults['stream_read_sleep_in'] = 0.1 # seconds

# parameters for outgoing stream reading ("px5")
defaults['stream_days_out'] = 120
defaults['stream_days_chunk_out'] = 10
defaults['stream_threadcount_out'] = 12
defaults['stream_read_timeout_out'] = 20 # seconds
defaults['stream_read_sleep_out'] = 0.2 # seconds

# general parameters for crawling and results
defaults['stream_read_trycount'] = 3 # ...strikes and you're out
defaults['bad_chunk_thresh'] = 0.25 # abort crawl if too many chunks fail 
defaults['freshness'] = 1

# FB app parameters
defaults['app_id'] = 471727162864364
defaults['app_secret'] = '120fe5e6d5bffa6a9aa3bf075bd3076a'



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

