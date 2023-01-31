++++++++++++++++
pytest-testrail2
++++++++++++++++

Create and update testplans and/or testruns in TestRail based on pytest results.
Test functions marked with a TestRail case ID will have their results sent to TestRail.

This project preserves the functionality of the deprecated `pytest-testrail <https://github.com/allankp/pytest-testrail/>`_ project.

.. image:: https://img.shields.io/pypi/v/pytest-testrail2.svg
    :target: https://pypi.org/project/pytest-testrail2
    :alt: PyPI

.. image:: https://img.shields.io/pypi/pyversions/pytest-testrail2.svg
    :alt: PyPI - Python Version
    :target: https://github.com/jsfehler/pytest-testrail2

.. image:: https://img.shields.io/github/license/jsfehler/pytest-testrail2.svg
   :alt: GitHub
   :target: https://github.com/jsfehler/pytest-testrail2/blob/master/LICENSE

.. image:: https://github.com/jsfehler/pytest-testrail2/workflows/CI/badge.svg
   :target: https://github.com/jsfehler/pytest-testrail2/actions/workflows/main.yml
   :alt: Build status


Key features:

- Configurable: Handle results in whichever way makes sense for your project.
- Powerful: Handle complex use cases via a simple interface to the TestRail API.
- Flexible: Fully compatible with pytest.parametrize(), pytest-xdist, and pytest-rerunfailures.

Example
=======

.. code:: python

  import pytest

  @pytest.mark.case_id('C1950')
  def test_all_the_things():
    doit = True
    assert doit

Getting Started
===============

Installation
------------

Via pip:

.. code-block:: bash

   pip install pytest-testrail2


Plugin Configuration
--------------------

The following values are required:

- A valid TestRail instance URL.
- A valid email address for a user on the instance.
- A valid API key for the user.

They can be set on the command line via the follow flags:

.. code-block:: bash

  --tr-url=<your_url>
  --tr-email=<your_email>
  --tr-password=<your_password>

Alternatively, they can be set via a pytest configuration file:

.. code-block:: ini

  [pytest]
    tr_url=<your_url>
    tr_email=<your_email>
    tr_password=<your_password>


Marking Tests
-------------

case_id
~~~~~~~

The `case_id` marker takes a string which must match an existing TestRail testcase.
Only tests with this marker will be added to the TestRail testrun.

.. code:: python

  import pytest

  # This test's results will be uploaded.
  @pytest.mark.case_id('C1950')
  def test_all_the_things():
    ...


  # This test's results will not be uploaded.
  def test_all_the_other_things():
    ...

defect_ids
~~~~~~~~~~

The 'defect_ids' marker takes a list of strings. These will be used in the `defect`
field in TestRail. This is useful for tests with known failures.

Typically these are IDs for your bug tracking software.

.. code:: python

  import pytest

  @pytest.mark.case_id('C1950')
  @pytest.mark.defect_ids(['JS-7001', 'JS-9001'])
  def test_all_the_things():
    ...

Running Pytest
--------------

The `--testrail` command-line flag must be present to upload results:

.. code-block:: bash

  pytest --testrail


Options
=======

Setup
-----

- ``--testrail``
  Activate the TestRail plugin.

- ``--tr-url``
  Web address used to access a TestRail instance.

- ``--tr-email``
  E-mail address for an account on the TestRail instance.

- ``--tr-password``
  Password for an account on the TestRail instance.

- ``--tr-timeout``
  Timeout for connecting to a TestRail server.

- ``--tr-no-ssl-cert-check``
  Do not check for valid SSL certificate on TestRail host.

Testrun
-------

- ``--tr-run-id``
  ID of an existing testrun in TestRail.
  If specified, the testrun matching the ID will be used instead of creating a new testrun.
  If given, ``--tr-testrun-name`` will be ignored.

- ``--tr-testrun-name``
  Name used for a new testrun in TestRail.

- ``--tr-testrun-description``
  Description used for a new testrun in TestRail.

- ``--tr-testrun-assignedto-id``
  ID of the user to be assigned to the testrun.

- ``--tr-testrun-project-id``
  ID of the project the testrun will be created in.

- ``--tr-testrun-suite-id``
  ID of the suite the testrun will be created in.

- ``--tr-testrun-suite-include-all``
  Include all test cases in the specified testsuite for a new testrun.

- ``--tr-milestone-id``
  ID of milestone used in testrun creation.

- ``--tr-skip-missing``
  Skip pytest test functions with marks that are not present in a specified testrun.

Testplan
--------

- ``--tr-plan-id``
  ID of an existing testplan to use. If given, ``--tr-testrun-name`` will be ignored.

Publishing
----------

- ``--tr-version``
  Specify a version in testcase results.

- ``--tr-close-on-complete``
  On pytest completion, close the testrun.

- ``--tr-dont-publish-blocked``
  Do not publish results of "blocked" testcases (in TestRail).

- ``--tr-custom-comment``
  Custom text appended to comment for all testcase results.
