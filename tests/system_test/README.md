Manual system test
==================

A manual system test for checking saltstack plugin.


Requirements
------------

- Vagrant (tested with v1.6.5)
- VM provider (tested with VirtualBox v4.3.20)


Running & verifying the test
----------------------------

- "Up" vagrant boxes.
- On host machine run `serve_plugin_on_http.sh`.
- SSH to the Cloudify box (`vagrant ssh cfy-minion`).
- On CFY box run `/vagrant/cloudify-test-run.sh <a_unique_string>`.
- If there are no Cloudify errors, the CFY box has a file `~/testfile`
        and `tree` program has been installed, the test has succeeded.
