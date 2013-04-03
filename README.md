edgeflip
========

This repo contains the code for the edgeflip Targeted Sharing application. Below are some quick notes on getting started.

AWS Set Up
----------

Set-up for an Ubuntu 12.04 EC2 instance running Python 2.7.3. Here are some basic steps to getting up and running:

1. You'll need an SSH key with access to the edgeflip github account in ~/.ssh -- contact us if you need to get one.
2. A couple of utilities: `sudo apt-get install git emacs htop`
3. Some python utilities and c++ compiler:
	sudo apt-get update
	sudo apt-get install python-pip python-dev python-mysqldb
	sudo apt-get install gcc
4. Python packages: `sudo pip install flask unidecode pika` (at some point we'll want a requirements file...)
5. Set up Apache & mod_wsgi: `sudo apt-get install apache2 libapache2-mod-wsgi`
6. Get some directories ready:
	cd /var/www
	sudo mkdir edgeflip
	sudo chmod 755 edgeflip
	sudo chown www-data edgeflip
	sudo chgrp www-data edgeflip
	cd edgeflip
	sudo emacs edgeflip.wsgi
7. Contents of edgeflip.wsgi:
	import sys
	sys.path.insert(0, '/var/www/edgeflip/gitclones/edgeflip/demo/')

	from ofa_flask import app as application
8. Set up the git clone:
	sudo chmod 755 edgeflip.wsgi
	sudo mkdir gitclones
	sudo chmod 777 gitclones
	cd gitclones
	git clone git@github.com:edgeflip/edgeflip.git
	git checkout ofa
9. Set up logging and edgeflip.config file:
	cd /var/www/edgeflip
	sudo mkdir logs
	sudo chown www-data /var/www/edgeflip/logs/
	sudo chgrp www-data /var/www/edgeflip/logs/
	cd /var/www
	sudo emacs edgeflip.config
10. Contents of edgeflip.config:
	{
	  "outdir":"edgeflip/",
	  "codedir":"/var/www/edgeflip/gitclones/edgeflip/demo/",
	  "logpath":"edgeflip/logs/demo.log",
	  "dbpath":"edgeflip/demo.sqlite",
	  "queue":"edgeflip_prod",
	  "ofa_state_config": "/var/www/edgeflip/gitclones/edgeflip/demo/config/ofa_states.json",
	  "ofa_campaign_config": "/var/www/edgeflip/gitclones/edgeflip/demo/config/ofa_campaigns.json"
	}
11. Set up Apache Virtual Host:
	cd /etc/apache2
	sudo emacs httpd.conf
12. Contents of httpd.conf:
	<VirtualHost *>
	    ServerName localhost

	    WSGIDaemonProcess edgeflip processes=2 threads=50
	    WSGIScriptAlias / /var/www/edgeflip/edgeflip.wsgi

	    LogLevel info
	    ErrorLog "/var/log/apache2/error.log"
	    CustomLog "/var/log/apache2/access.log" combined

	    <Directory /var/www/edgeflip>
	        WSGIProcessGroup edgeflip
	        WSGIApplicationGroup %{GLOBAL}
	        Order deny,allow
	        Allow from all
	    </Directory>
	</VirtualHost>
13. Finally, restart Apache and you should be up and running: `sudo /etc/init.d/apache2 restart`
