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
    

AWS
---
Cross-service configuration for AWS/boto. Currently this is just access & secret keys. If these are unset, fall back to standard `boto configuration <http://boto.readthedocs.org/en/latest/boto_config_tut.html>`

.. envvar:: aws.AWS_ACCESS_KEY_ID

    AWS access key

.. envvar:: aws.AWS_SECRET_ACCESS_KEY

    AWS secret key
