"""Message Handles and Message Properties"""

# Copyright (c) 2025 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

from mqcommon import *
from mqerrors import *
from ibmmq import CMQC, ibmmqc
from mqsub import *
from mqprops import *

from mqqmgr import *

class MessageHandle:
    """ A higher-level wrapper around the MQI's native Message Handle and
    Property processing.
    """

    class _Properties:
        """ Encapsulates access to message properties.
        """

        def __init__(self, conn_handle, msg_handle):
            self.conn_handle = conn_handle
            self.msg_handle = msg_handle

            # When accessing message properties, this will be the maximum number
            # of characters a value will be able to hold. If it's not enough
            # an exception will be raised and its 'actual_value_length' will be
            # filled in with the information of how many characters there are actually
            # so that an application may re-issue the call.
            self.default_value_length = 64

        def __getitem__(self, name):
            """ Allows for a dict-like access to properties,
            handle.properties[name]
            """
            value = self.get(name)
            if not value:
                raise KeyError('No such property [%s]' % name)

            return value

        def __setitem__(self, name, value):
            """ Implements 'handle.properties[name] = value'.
            """
            return self.set(name, value)

        def get(self, name, default=None, max_value_length=None,
                impo_options=CMQC.MQIMPO_INQ_FIRST, impo = None, pd=None,
                property_type=CMQC.MQTYPE_AS_SET):
            """ Returns the value of message property 'name'. If a wildcard
            is used in the property name, then the real name is also returned.

            'max_value_length' is the maximum number of characters the underlying
            C function is allowed to allocate for fetching the value
            (defaults to default_value_length).

            Either 'impo_options' or 'impo' can be given. If the full IMPO
            object is used, then its options take preference.

            The 'pd' can be either the options value or the PD class. (The original parameter name
            did not include "options" so it's easier to repurpose it to take either type of
            value than it is wth the impo for compatibility.)

            'property_type' points to the expected data type of the property.

            The name can be '%' for a wildcard, and can be preceded by a
            folder. For example, 'usr.%'. But you cannot use, say, 'ABC%'. The
            wildcard means all properties within a single folder.
            """

            if impo:
                if not isinstance(impo,IMPO):
                    raise TypeError("impo must be an instance of IMPO")
            else:
                impo = IMPO()
                impo.Options = impo_options | CMQC.MQIMPO_CONVERT_VALUE

            if pd:
                pd_val = pd
                if isinstance(pd_val,int):
                    pd = PD()
                    pd.Options = pd
                if not isinstance(pd,PD):
                    raise TypeError("pd must be an instance of PD")
            else:
                pd = PD()

            name = ensure_strings_are_bytes(name)

            if not max_value_length:
                max_value_length = self.default_value_length

            value, data_length, returned_name, comp_code, comp_reason  = ibmmqc.MQINQMP(
                self.conn_handle, self.msg_handle, impo.pack(), name, pd.pack(), property_type, max_value_length)

            if comp_code != CMQC.MQCC_OK:
                raise MQMIError(comp_code, comp_reason, value=default, data_length=data_length)

            if returned_name:
                return value, returned_name
            return value

        def set(self, name, value, property_type=CMQC.MQTYPE_STRING,
                value_length=CMQC.MQVL_NULL_TERMINATED, pd=None, smpo=None):
            """ Allows for setting arbitrary properties of a message. 'name'
            and 'value' are mandatory. All other parameters are OK to use as-is
            if 'value' is a string. If it isn't a string, the 'property_type'
            and 'value_length' should be set accordingly. For further
            customization, you can also use 'pd' and 'smpo' parameters for
            passing in MQPD and MQSMPO structures.
            """

            name = ensure_strings_are_bytes(name)

            # If the VALUE is of MQTYPE_STRING, then the input is expected to be a real string
            # (Unicode allowed) and it's converted in the C layer. Unlike the name, we do not convert
            # it here.

            pd = pd if pd else PD()
            smpo = smpo if smpo else SMPO()

            comp_code, comp_reason = ibmmqc.MQSETMP(
                self.conn_handle, self.msg_handle, smpo.pack(), name, pd.pack(), property_type, value, value_length)

            if comp_code != CMQC.MQCC_OK:
                raise MQMIError(comp_code, comp_reason)

        def dlt(self, name, dmpo=None):
            """ Deletes a message property. Only the name is required. For further
            customization, you can also use the 'dmpo' parameters for
            passing in the MQDMPO structure.
            """

            name = ensure_strings_are_bytes(name)

            dmpo = dmpo if dmpo else DMPO()

            comp_code, comp_reason = ibmmqc.MQDLTMP(
                self.conn_handle, self.msg_handle, dmpo.pack(), name)

            if comp_code != CMQC.MQCC_OK:
                raise MQMIError(comp_code, comp_reason)

    def __init__(self, qmgr=None, cmho=None):
        self.conn_handle = qmgr.get_handle() if qmgr else CMQC.MQHO_NONE
        cmho = cmho if cmho else CMHO()

        self.msg_handle, comp_code, comp_reason = ibmmqc.MQCRTMH(self.conn_handle, cmho.pack())

        if comp_code != CMQC.MQCC_OK:
            raise MQMIError(comp_code, comp_reason)

        self.properties = self._Properties(self.conn_handle, self.msg_handle)

    # Note that this deletes a MsgHandle at the MQI level and is not __del__ (the object destructor)
    def dlt(self, dmho=None):
        """Delete a message handle"""
        dmho = dmho if dmho else DMHO()

        comp_code, comp_reason = ibmmqc.MQDLTMH(self.conn_handle, self.msg_handle, dmho.pack())

        if comp_code != CMQC.MQCC_OK:
            raise MQMIError(comp_code, comp_reason)

        self.properties = self._Properties(CMQC.MQHC_UNUSABLE_HCONN,CMQC.MQHM_NONE)
