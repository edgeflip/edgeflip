Configuration
=============

.. automodule:: edgeflip.settings
    :members:
    :undoc-members:
    :show-inheritance:

New Relic
---------
`New Relic <https://newrelic.com>`__ is used for performance monitoring. There is a default `newrelic.ini` file in the repo root. This needs to be populated with the appropriate API key before use.

.. envvar:: newrelic.enabled

    should New Relic support be turned on
    
.. envvar:: newrelic.inifile

    a fully qualified path to the `newrelic.ini` file.
    
.. envvar:: newrelic.environment
    
    a New Relic environment, as defined in `newrelic.ini`. Defaults to `development`.
    

S3
--
`Flask-S3 <http://flask-s3.readthedocs.org/en/latest/>`__ is used to manage static assets on S3. The underlying library requires the AWS access & secret keys; refer to `Boto's configuration <http://boto.readthedocs.org/en/latest/boto_config_tut.html>`__. These keys can be specified in a `~/.boto` config file, as environment variables or in `conf.d` files.

.. envvar:: S3_BUCKET_NAME
   
    the name of the s3 bucket. Defaults to `local-edgeflip`.

.. envvar:: USE_S3
   
    should S3 be enabled? Defaults to False.
