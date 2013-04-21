edgeflip
========

This repo contains the code for the edgeflip Targeted Sharing application. Below are some quick notes on getting started.

Basic Installation
------------------

Set-up for an Ubuntu 12.04 EC2 instance running Python 2.7.3. Here are some basic steps to getting up and running:

1. You'll need an SSH key with access to the edgeflip github account in ~/.ssh -- contact us if you need to get one.
2. Install minimal developer tools `sudo apt-get install git`
3. Check out the repo `git clone https://github.com/edgeflip/edgeflip.git` *All following commands are run in checkout directory.*
4. Install system dependencies: `./scripts/install-dependencies.txt`
5. Create a virtualenv (you will need to open a new terminal/shell first): `mkvirtualenv edgeflip`
6. Add your checkout to the virtualenv `add2virtualenv .`
7. Upgrade distribute: `pip install -U distribute`
8. Install python packages: `pip install -r requirements.txt`
9. If using Apache or uWSGI, create a `edgeflip.wsgi`. Copy `templates/edgeflip.wsgi` to your deployment root (usually `/var/www/edgeflip`). Edit, replacing `$VIRTUALENV_PATH` with the full path to your virtualenv. *This is not needed if using the debug or devel server.*

Configuring Apache
------------------
**XXX this needs a little attention***

5. Set up Apache & mod_wsgi: `sudo apt-get install apache2 libapache2-mod-wsgi`
6. Get some directories ready:
<pre><code>cd /var/www
	sudo mkdir edgeflip
	sudo chmod 755 edgeflip
	sudo chown www-data edgeflip
	sudo chgrp www-data edgeflip
	cd edgeflip
	sudo emacs edgeflip.wsgi</code></pre>

8. Set up the git clone:
<pre><code>sudo chmod 755 edgeflip.wsgi
	sudo mkdir gitclones
	sudo chmod 777 gitclones
	cd gitclones
	git clone git@github.com:edgeflip/edgeflip.git</code></pre>
9. Set up logging and edgeflip.config file:
<pre><code>cd /var/www/edgeflip
	sudo mkdir logs
	sudo chown www-data /var/www/edgeflip/logs/
	sudo chgrp www-data /var/www/edgeflip/logs/
	cd /var/www
	sudo emacs edgeflip.config</code></pre>
10. Set up your configuation, as specified in the [docs](http://edgeflip.github.io/edgeflip/index.html)
11. Set up Apache Virtual Host:
<pre><code>cd /etc/apache2
	sudo emacs httpd.conf</code></pre>
12. Contents of httpd.conf:
<pre><code>&lt;VirtualHost *&gt;
	    ServerName localhost

	    WSGIDaemonProcess edgeflip processes=2 threads=50
	    WSGIScriptAlias / /var/www/edgeflip/edgeflip.wsgi

	    LogLevel info
	    ErrorLog "/var/log/apache2/error.log"
	    CustomLog "/var/log/apache2/access.log" combined

	    &lt;Directory /var/www/edgeflip&gt;
	        WSGIProcessGroup edgeflip
	        WSGIApplicationGroup %{GLOBAL}
	        Order deny,allow
	        Allow from all
	    &lt;/Directory&gt;
	&lt;/VirtualHost&gt;</code></pre>
13. Finally, restart Apache and you should be up and running: `sudo /etc/init.d/apache2 restart`
