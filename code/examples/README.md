These example programs show many of the ways of using this MQ Python library. Comments at the top of each file give more
information about what they do.

The examples mostly use `import ... as mq` to reduce typing of the full package name.

In general, these examples assume an accessible queue manager QM1 with an available listener on port 1414. The
"developer configuration" is also assumed, with DEV.QUEUE.1 etc. The `app` and `admin` userids are meant to be
available, both with `password` as the authentication.

You might need to change these assumptions in the examples for your own queue manager configurations.

* Basic operations
  * connect_simple
  * connect_client_creds
  * connect_client
  * connect_client_tls
  * checking_cc_and_rc
  * is_connected
  * get_message
  * get_wait_multiple_messages
  * get_wait_single_message
  * put1_message
  * put_get_correl_id
  * put_message
  * dynamic_queues
  * publish_message
  * subscribe

* More advanced MQI operations
  * alternate_user_id
  * async_consume
  * inq_set
  * dlq_browse
  * channel_compression
  * message_priority
  * message_properties
  * put_async_message
  * set_identity

* Admin (PCF) operations
  * def_channel
  * def_queue
  * dis_channels - Shows one way to build PCF commands
  * dis_queues - An alternative way to build PCF commands
  * dis_conns
  * set_auth_rec

* Miscellaneous
  * check_mq_version_rpm
  * check_mq_version_windows

* `runInContainer.sh` uses the `Dockerfile` to build a container, with all that's needed to build and run a Python
  application.
