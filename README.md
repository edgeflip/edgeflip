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

RabbitMQ
--------------
To set up your RabbitMQ instance:

1. Start by installing RabbitMQ: `sudo apt-get install rabbitmq-server` (If this is your first setup, `install-dependencies.sh` will have done this for you)
2. Create a user: `sudo rabbitmqctl add_user edgeflip edgeflip`
3. Create a vhost: `sudo rabbitmqctl add_vhost edgehost`
4. Set permissions for this user on that new vhost: `sudo rabbitmqctl set_permissions -p edgehost edgeflip ".*" ".*" ".*"`

Celery
--------------
Starting Celery:

Setup and operation of Celery differs a bit between your local environments and production.
This is mainly due to the fact that init scripts are excessive for local development, and tend to
be far too specific for a particular environment. 

*Locally*:

1. Make sure you have the Celery packages installed: `pip install -r requirements.txt`
2. Run the celery startup script (with your virtualenv active): `./scripts/celery/local_celery.sh`

*Production*:

1. Make sure you have the Celery packages installed: `pip install -r requirements.txt`
2. Symlink `scripts/celery/celeryd` to `/etc/init.d/celeryd`
3. Copy `scripts/celery/celeryd.conf` to `/etc/default/celeryd`
4. Set CELERY_CHDIR to the proper virtualenv path in `/etc/default/celeryd`
4. Create celery user/group: `sudo adduser --system celery` and `sudo addgroup --system celery` 
5. Chown log/pid dirs: `sudo chown -R celery:celery /var/run/celery /var/log/celery`
4. Start the daemon: `/etc/init.d/celeryd start`

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

Note that although you supply a fbid in the request, what will actually be used is a randomly-generated fbid (to avoid all your requests stacking up in the DB trying to update the same records). The set of fbid's used by the load test were chosen to fall into what appears to be a gap in actual id's assigned by Facebook.

### Using Siege ###
Load tests can be performed using the [Siege utility](http://www.joedog.org/siege-home/), however [some modification](http://www.skybert.net/bytes/2011/05/16/using-siege-to-test-the-write-performance-of-couchdb/) is required to send JSON requests. To so:

1. Remove siege if it's already installed: `sudo apt-get remove siege`
2. Install siege source: `sudo apt-src install siege` (may need to run `apt-get install apt-src` first)
3. Locate and edit (as root) the file `load.c` (likely in `/usr/src/siege-2.70/src/`) by adding a line `{"json", TRUE, "application/json"},` (being sure to include the final comma) immediately following the line `{"js", FALSE, "application/x-javascript"},`. *This defines the headers that Siege will send with different types of requests.*
4. Package up your edited code: `sudo dpkg-buildpackage -rfakeroot -uc -b`
5. And install the package: `sudo dpkg -i ../siege*.deb`

Once you've patched and installed Siege, you can run load tests by creating a few files and telling Siege to use them at the command line:

1. A JSON file with the request parameters, such as:
```
    {
        "mockmode" : "true", 
        "fbid" : 100011235813, 
        "token" : "IamAfakeTOKEN", 
        "num" : 9, 
        "sessionid" : "i-am-a-fake-session", 
        "campaignid" : 2, 
        "contentid" : 2
     }
```

2. A one-line siege file that specifies the request itself, such as:
```
http://local.edgeflip.com:8080/faces POST < test_data.json
```
3. Finally, at the command line, invoke Siege:
```
sudo siege -c 5 -d 1 -r 20 -f test_data.json.siege
```
(Here, with 20 repeats of 5 concurrent requests with a maximum (random) delay of 1 sec. between repeats. More on parameters can be found on the [Siege homepage](http://www.joedog.org/siege-home/).)

Running Tests With Nose
------------
New tests and the start of a test framework have been added to edgeflip/tests. 
This tests can be ran with `nosetests edgeflip/tests/ --config=nose.cfg`. 

They build up a new test database and destroy it upon completion, so you shouldn't
have to worry about them trampling your current database. This does require a minor
bit of setup on your machine however. You'll need to create a file at ~/.my.cnf. 
The contents of that file should look like so:

    [client]
    user=ROOT_USER
    password=ROOT_PASSWORD
