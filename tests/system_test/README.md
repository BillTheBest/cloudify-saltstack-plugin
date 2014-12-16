System test
===========

A comprehensive system test for checking saltstack plugin.

This test creates an environment consisting of two VMs: `salt-master` and `cfy-minion`.
During the test, Cloudify Manager installed on `cfy-minion` uses the salt plugin to
install and configure salt minion on itself, and then instructs salt master to manage
the minion.

`cfy-minion` has the following hosts configured in `/etc/hosts`:
* `salt-master`, pointing to salt-master VM,
* `plugin-serving-host`, pointing to the host machine on which the test is being run.


Requirements
------------

* Vagrant (tested with v1.6.5)
* VM provider (tested with VirtualBox v4.3.20)
* internet connection (the blueprint imports basic node types from getcloudify.org)
* vagrant box with appropriate version of Cloudify manager and CLI installed

Usually the vagrant box should be available for download from GigaSpaces; you can
add it with a command like this:

    vagrant box add http://gigaspaces-repository-eu.s3.amazonaws.com/org/cloudify3/3.1.0/ga-RELEASE/cloudify-virtualbox_3.1.0-ga-b85.box --name=cloudify-3.1.0-ga-b85

(adjust the URL, box name and/or the CFY_BOX variable in the Vagrantfile as necessary)


Running the test
----------------

Run

    ./run-test.sh

This will compress plugin sources into a zip, serve it over http from your machine,
setup two VMs as specified in the Vagrantfile, upload the test blueprint (to the Cloudify
Manager running on `cfy-minion` VM), deploy it and verify that the test had succeeded
(i.e. that Cloudify had successfully configured salt minion on the `cfy-minion` VM
and used salt to put the machine in a specific state).


Re-running the test
-------------------

Subsequent test runs can be done without destroying Vagrant boxes.  First,
make sure that the zip with the plugin is served from your machine by running

    ./serve_plugin_on_http.sh

Then you can log into the Cloudify VM (`vagrant ssh cfy-minion`) and run

    /vagrant/deploy_test_blueprint.sh TEST_NUMBER

to run the test.
