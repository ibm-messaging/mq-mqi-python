# Extended PCF response model

This document describes extensions to the original PCF admin interface to allow applications to deal with a partial error
response. The original model throws an exception and does not provide any extra information on the failure.

For example, consider a qmgr with queues X0, X1 and X2 The qfile for X0 has been overwritten with some garbage, and
the qmgr restarted. We expect to see "Object Damaged" errors with some admin commands.

## MQSC examples

Note that MQSC may not actually tell you WHICH queue is damaged. It depends on the command, as these MQSC examples show.

```
    1 : dis q(X*)
AMQ8149S: IBM MQ object damaged.
AMQ8409I: Display Queue details.
   QUEUE(X1)                               TYPE(QLOCAL)
AMQ8409I: Display Queue details.
   QUEUE(X2)                               TYPE(QLOCAL)


dis ql(x*)
     2 : dis ql(X*)
AMQ8409I: Display Queue details.
   QUEUE(X0)                               TYPE(QLOCAL)
AMQ8409I: Display Queue details.
   QUEUE(X1)                               TYPE(QLOCAL)
AMQ8409I: Display Queue details.
   QUEUE(X2)                               TYPE(QLOCAL)

dis qs(x*)
     3 : dis qs(X*)
AMQ8450I: Display queue status details.
   QUEUE(X2)                               TYPE(QUEUE)
   CURDEPTH(0)
AMQ8450I: Display queue status details.
   QUEUE(X1)                               TYPE(QUEUE)
   CURDEPTH(0)

dis qs(x0)
     4 : dis qs(X0)
AMQ8149S: IBM MQ object damaged.


```

## Python original behaviour
The original behaviour of the Python PCF classes throws an exception instead of returning any values:

```
  try:
    responses=pcf.MQCMD_INQUIRE_Q(attrs)
  except mq.MQMIError as e:
    print(f"Caught error {e}")
  else:
    # There's only something useful when there's no exception
    for q in responses:
      print(f"QName: {q[mq.CMQC.MQCA_Q_NAME]}")
```

## Python extended responses

To replicate the MQSC behaviour in the Python code, the caller of the operation has to provide somewhere for the partial
responses to be stashed rather than having them simply returned. This is done via the `responses` list parameter passed
via a keyword.

Because there is an error, we still should throw an exception. Apart from anything else, this is needed to maintain
compatibility.

But we also return the corresponding CFH structures in the same list element so you can dive deeper into which response
had the particular error. Each element in this format is a tuple of (index 0) the "normal" PCF response and (index 1)
the corresponding CFH.

```
  resp_list=[]
  try:
    pcf.MQCMD_INQUIRE_Q(attrs, responses=resp_list)
  except mq.MQMIError as e:
    print(f"Caught error {e}")

  # Even though there's been an exception, we might have some returned data.
  for q in resp_list:
    print(f"QName: {q[0][mq.CMQC.MQCA_Q_NAME]} rc:{q[1].Reason}")
```

Note that other MQ errors (eg 2033) will take precedence over specific CFH-returned errors.


