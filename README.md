edgeflip
========

This repo contains the code for the edgeflip Targeted Sharing application. Below are some quick notes on getting started.

Basic Installation
------------------

Set-up for an Ubuntu 12.04 EC2 instance running Python 2.7.3. Here are some basic steps to getting up and running:

1. You'll need an SSH key with access to the edgeflip github account in ~/.ssh -- contact us if you need to get one.
2. Install minimal developer tools `sudo apt-get install git`
3. Check out the repo `git clone https://github.com/edgeflip/edgeflip.git` *All following commands are run in checkout directory.*
4. Install system dependencies: `./scripts/install-dependencies.sh`
5. Create a virtualenv (you will need to open a new terminal/shell first): `mkvirtualenv edgeflip`
6. Add your checkout to the virtualenv `add2virtualenv .`
7. Upgrade distribute: `pip install -U distribute`
8. Install python packages: `pip install -r requirements.txt`
9. If using Apache or uWSGI, create a `edgeflip.wsgi`. Copy `templates/edgeflip.wsgi` to your deployment root (usually `/var/www/edgeflip`). Edit, replacing `$VIRTUALENV_PATH` with the full path to your virtualenv. *This is not needed if using the debug or devel server.*
10. Configure your system, as specified in the [docs](https://github.com/edgeflip/edgeflip/blob/master/doc/edgeflip.rst)
 
Local Database
--------------
To set up a local mysql database:

1. *Once only*, run `scripts/initial_db_setup.sh`. This creates an `edgeflip` database & user with a insecure default password.
2. To reset the database, use `bin/reset_db.py`. This will use your configuration values.
3. To seed the database with values for the mockclient, use `bin/mockclient_campaigns.py`. This uses the edgeflip and mockclient host data in your configuration.

Hostname Alias
--------------
Facebook requires a URL to use as a callback after auth. To point this to your local development server, add the following entry to `/etc/hosts`

```
127.0.0.1   local.edgeflip.com
```

If you are using a local virtual machine, you will need an entry in the *host* machine's `/etc/hosts` as well. Use the same line, but replace with the IP address of the VM.

Devel Server
------------
To run the server use `bin/devel_server.py`. If you need a barebones server (for use with a debugger, for example), use `bin/debug_server.py`.

Mock Client
-----------
The default configuration is written against a mock client site. You'll need to run this server as well; see the instructions in the [mockclient repo](https://github.com/edgeflip/mockclient)

Load Testing
------------
For the purposes of load testing, a POST request can be made against the /faces endpoing in a "mock mode" that will do everything but talk to facebook, instead returning a set of randomly-generated fake friend records. The following is an example of such a mock request against the local development server:

```
curl -X POST --data '{"mockmode" : "true", "fbid" : 100011235813, "token" : "IamAfakeTOKEN", "num" : 6, "sessionid" : "i-am-a-fake-session", "campaignid" : 1, "contentid" : 1}' http://local.edgeflip.com:8080/faces --header "Content-Type:application/json"
```

Facebook Canvas App
-------------------

1. Make sure you have the following line in /etc/hosts:
	127.0.0.1	app.edgeflip.com


2. Now, you need to patch werkzeug (or install a version > 0.8.3).  For me, I edited the file:
	/Users/matthew/.virtualenvs/edgeflip/lib/python2.7/site-packages/werkzeug/serving.py

Add the following function to the _SSLConnectionFix class (line 302):
	def shutdown(self, args=None):
	    return self._con.shutdown()

	For more info, see: https://github.com/mitsuhiko/werkzeug/issues/249

	Note that this will get blown away if you reset your virtual environment, so we should figure out the grownup way to handle this.


3. [OPTIONAL] generate a self-signed key/certificate using a terminal, and stick them somewhere
	$ openssl genrsa 1024 > ssl.key
	$ openssl req -new -x509 -nodes -sha1 -days 365 -key ssl.key > ssl.cert

	For more info, see: http://werkzeug.pocoo.org/docs/serving/#generating-certificates

	If you skip this step, you will be limited to "ad hoc mode" as described below


4. If it's not there already, install SSL for python:
	$ pip install pyOpenSSL

5.  When you start the devel server, pass it the --canvas or --canvas-adhoc flag.  This will start the server on port 443 and configure it to use SSL.  If you use the former, you can specify the name/location of the key and cert files you made in step 3 (run devel_server.py -h for details).  Alternatively, using "ad hoc mode" will generate one on the fly; if you do this, you must hit the server directly (via https://app.edgeflip.com/canvas/) and accept the cert before loading it up in canvas (https://apps.facebook.com/sharing-social-good/).  Also, I had to use sudo to get things to work on port 443.

	$ sudo bin/devel_server.py --canvas --cert-dir ~/edgeflip/gits/shaycrk/ssl/


