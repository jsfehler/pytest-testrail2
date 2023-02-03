=========
Changelog
=========
All notable changes to this project will be documented in this file.

[1.0.2] - 2023-02-03
=====================

Changed
-------

- If a URL, email address, or API key are not found then pytest will exit immediately.

[1.0.1] - 2023-02-01
=====================

Fixed
-----

- If the plugin throws an unexpected error and temporary files were not created,
  an error will no longer be raised when the temporary files cannot be removed.
