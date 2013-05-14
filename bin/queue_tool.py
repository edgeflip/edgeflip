#!/usr/bin/env python
"""RabbitMQ queue utility

Usage:
    queue_tool.py (-h | --help)
    queue_tool.py [-n <name>] reset 
    queue_tool.py [-n <name>] size 
    queue_tool.py [-n <name>] load <file>
    

Options:
    -h --help  Show this screen.
    -n --name <name>  name of the queue. If not specified, use value from configuration files.

"""
import sys

from docopt import docopt

from edgeflip import stream_queue
from edgeflip.settings import config

def queueSize(name):
    qSize = stream_queue.getQueueSize(name)
    return "Queue %s has size %d" % (name, qSize)

def queueReset(name):
    stream_queue.resetQueue(name)
    return "Queue %s has been reset." % name

def queueLoad(name, path):
    count = stream_queue.loadQueueFile(name, path)
    return "Loaded %d entries into queue %s." % (count, qName)

if __name__ == '__main__':
    args = docopt(__doc__)
    
    if args['--name'] is None:
        args['--name'] = config.queue
    
    if args['reset']:
        s = queueReset(args['--name'])
    elif args['size']:
        s = queueSize(args['--name'])
    elif args['load']:
        s = queueLoad(args['--name'], args['<file>'])
    else:
        assert False, "impossible commandline args"
    
    print>>sys.stderr, s