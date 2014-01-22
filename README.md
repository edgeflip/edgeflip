edgeflip
========

This repo contains the code for the edgeflip Targeted Sharing application. Below are some quick notes on getting started.

Basic Installation
------------------

Set-up for an Ubuntu 12.04 EC2 instance running Python 2.7.3. Here are some basic steps to getting up and running:

1. You'll need an SSH key with access to the edgeflip github account in ~/.ssh -- contact us if you need to get one.
2. Install minimal developer tools, git and Fabric:

    $ `sudo apt-get install git python-pip`  
    $ `sudo pip install Fabric>=1.6`

3. Check out the repo: `git clone https://github.com/edgeflip/edgeflip.git`
4. From within the checkout hierarchy, build (and test) the application:

    $ `fab build test`

    (To see all tasks and options, run `fab -l`.)

5. If using Apache or uWSGI, create a `edgeflip.wsgi`. Copy `templates/edgeflip.wsgi` to your deployment root (usually `/var/www/edgeflip`). Edit, replacing `$VIRTUALENV_PATH` with the full path to your virtualenv. *This is not needed if using the debug or devel server.*
6. Configure your system, as specified in the [docs](https://github.com/edgeflip/edgeflip/blob/master/doc/edgeflip.rst)

Local Database
--------------

A local mysql database is automatically set up by the build task; (see `fab -d build.db`). This creates an `edgeflip` database & user with an insecure default password.

* To set up the database ad-hoc, run `fab build.db`.
* To force the database schema to reinitialize, provide the "force" option: `fab build.db:force=1`.
* To seed the database with values for the mockclient, you have two options:
    * If you're resetting or starting a new database just pass "testdata=1" to the build.db command. e.g: `fab build.db:force=1,testdata=1`
    * If you have an existing database, you can run the following command from the root of the `edgeflip` repo: `python manage.py loaddata targetshare/fixtures/test_data.yaml`


Dynamo
------
The config option `dynamo.engine` may be set to either `mock` (default) or `aws`. The latter requires AWS keys to be set up. *If you are testing against AWS*, set the `dynamo.prefix` to a unique value to avoid stepping on existing tables!

To run a local mock dynamo server, [FakeDynamo](https://github.com/ananthakumaran/fake_dynamo) must be installed; (note, this is handled automatically by the build task in development mode &mdash; see `fab -d build.dependencies`).

1. With FakeDynamo installed, the server may be invoked and managed via `fab serve.dynamo`; (see `fab -d serve.dynamo`).
2. Set up and create tables &mdash; (note, this can be quite slow on live AWS):
    * If necessary, drop tables with `python manage.py dynamo destroy`
    * Create tables with `python manage.py dynamo create`


RabbitMQ
--------------
To set up your RabbitMQ instance:

1. Start by installing RabbitMQ from the [Debian PPA](http://rabbitmq.com/install-debian.html#apt) 
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

1. Make sure you have the Celery packages installed: `fab build.requirements`
2. Then run the celery fab command: `fab serve.celery`

*Production*:

1. Make sure you have the Celery packages installed: `fab build.requirements`
2. Symlink `scripts/celery/celeryd` to `/etc/init.d/celeryd`
3. Copy `scripts/celery/celeryd.conf` to `/etc/default/celeryd`
4. Set CELERY_CHDIR to the proper virtualenv path in `/etc/default/celeryd`
5. Create celery user/group: `sudo adduser --system celery` and `sudo addgroup --system celery`
6. Chown log/pid dirs: `sudo chown -R celery:celery /var/run/celery /var/log/celery`
7. Start the daemon: `/etc/init.d/celeryd start`

Hostname Alias
--------------
Facebook requires a URL to use as a callback after auth. To point this to your local development server, add the following entry to `/etc/hosts`

```
127.0.0.1   local.edgeflip.com
```

If you are using a local virtual machine, you will need an entry in the *host* machine's `/etc/hosts` as well. Use the same line, but replace with the IP address of the VM.

Devel Server
------------
To run the server use `fab serve.server`. This command also has options for `host` and `port`:

* `fab serve.server:host=0.0.0.0,port=1234`

Mock Client
-----------
This should no longer be necessary as this aspect of the stack has been brought into the `targetmock` Django app.
However, with this change, instead of using a url such as "http://mockclient.edgeflip.com:5000/guncontrol_share" you will
now use "http://local.edgeflip.com/mocks/guncontrol_share". This saves us from having to run
two web instances locally in order to test the app.

User Testing
------------
You can view the results for a given authed user by hitting the /frame_faces endpoint with GET parameters for `test_mode`, `fbid`, and `token`. For instance, to view results for our test user in your local environment, you could go to:

```
http://local.edgeflip.com:8080/frame_faces/1/1?test_mode&fbid=100005022126470&token=CAAGtCIn5MuwBAJ1oSTKUT47Cat0uxmQ1Ixj2LAqCOGzVxCRnkESooyHttCwBH9v5z45GfTjAIZBfLkxt0Uy6yjPB714ZCQV4riYhFE0nfub6JRY8ofIruYTVOpO72wVZAN4jxYOkYMJ4ErCEr81DfYrZCqku9EQZD
```
The front-end will still require you to be logged into Facebook & authorized, but will display results for the specified user instead. **Note: posting to Facebook is disabled in test mode!**

Load Testing
------------
For the purposes of load testing, a POST request can be made against the /faces endpoint in a "mock mode" that will do everything but talk to facebook, instead returning a set of randomly-generated fake friend records. The following is an example of such a mock request against the local development server:

```
curl -X POST --data '{"mockmode" : "true", "fbid" : 100011235813, "token" : "IamAfakeTOKEN", "num" : 6, "sessionid" : "i-am-a-fake-session", "campaignid" : 1, "contentid" : 1}' http://local.edgeflip.com:8080/faces --header "Content-Type:application/json"
```

Note that although you supply a fbid in the request, what will actually be used is a randomly-generated fbid (to avoid all your requests stacking up in the DB trying to update the same records). The set of fbid's used by the load test were chosen to fall into what appears to be a gap in actual id's assigned by Facebook.


Running Tests With Nose
------------
New tests and the start of a test framework have been added to edgeflip/tests. 
These tests can be run with `fab test`; (see `fab -d test`). These tests also include
building an HTML summary of test coverage which can be found at `cover/index.html`
