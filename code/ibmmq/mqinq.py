"""MQINQ/MQSET implementation"""

# Copyright (c) 2025 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

from ibmmq import CMQC, MQMIError, ibmmqc, mqcommon

# This object deals with the lengths of attributes that may be processed
# by the MQSET/MQINQ calls. Only a small set of the object attributes
# are supported by MQINQ (and even fewer for MQSET) so it's reasonable
# to list them all here. But any new attributes ought to be checked to see if
# they need to be added to the list.
mqAttrLength = {
    CMQC.MQCA_ALTERATION_DATE:       CMQC.MQ_DATE_LENGTH,
    CMQC.MQCA_ALTERATION_TIME:       CMQC.MQ_TIME_LENGTH,
    CMQC.MQCA_APPL_ID:               CMQC.MQ_PROCESS_APPL_ID_LENGTH,
    CMQC.MQCA_BACKOUT_REQ_Q_NAME:    CMQC.MQ_Q_NAME_LENGTH,
    CMQC.MQCA_BASE_Q_NAME:           CMQC.MQ_Q_NAME_LENGTH,
    CMQC.MQCA_CERT_LABEL:            CMQC.MQ_CERT_LABEL_LENGTH,
    CMQC.MQCA_QSG_CERT_LABEL:        CMQC.MQ_CERT_LABEL_LENGTH,
    CMQC.MQCA_CF_STRUC_NAME:         CMQC.MQ_CF_STRUC_NAME_LENGTH,
    CMQC.MQCA_CHANNEL_AUTO_DEF_EXIT: CMQC.MQ_EXIT_NAME_LENGTH,
    CMQC.MQCA_CHINIT_SERVICE_PARM:   CMQC.MQ_CHINIT_SERVICE_PARM_LENGTH,
    CMQC.MQCA_CLUSTER_NAME:          CMQC.MQ_CLUSTER_NAME_LENGTH,
    CMQC.MQCA_CLUSTER_NAMELIST:      CMQC.MQ_NAMELIST_NAME_LENGTH,
    CMQC.MQCA_CLUSTER_WORKLOAD_DATA: CMQC.MQ_EXIT_DATA_LENGTH,
    CMQC.MQCA_CLUSTER_WORKLOAD_EXIT: CMQC.MQ_EXIT_NAME_LENGTH,
    CMQC.MQCA_CLUS_CHL_NAME:         CMQC.MQ_OBJECT_NAME_LENGTH,
    CMQC.MQCA_COMMAND_INPUT_Q_NAME:  CMQC.MQ_Q_NAME_LENGTH,
    CMQC.MQCA_COMM_INFO_NAME:        CMQC.MQ_OBJECT_NAME_LENGTH,
    CMQC.MQCA_CONN_AUTH:             CMQC.MQ_AUTH_INFO_NAME_LENGTH,
    CMQC.MQCA_CREATION_DATE:         CMQC.MQ_DATE_LENGTH,
    CMQC.MQCA_CREATION_TIME:         CMQC.MQ_TIME_LENGTH,
    CMQC.MQCA_CUSTOM:                CMQC.MQ_CUSTOM_LENGTH,
    CMQC.MQCA_DEAD_LETTER_Q_NAME:    CMQC.MQ_Q_NAME_LENGTH,
    CMQC.MQCA_DEF_XMIT_Q_NAME:       CMQC.MQ_Q_NAME_LENGTH,
    CMQC.MQCA_DNS_GROUP:             CMQC.MQ_DNS_GROUP_NAME_LENGTH,
    CMQC.MQCA_ENV_DATA:              CMQC.MQ_PROCESS_ENV_DATA_LENGTH,
    CMQC.MQCA_IGQ_USER_ID:           CMQC.MQ_USER_ID_LENGTH,
    CMQC.MQCA_INITIATION_Q_NAME:     CMQC.MQ_Q_NAME_LENGTH,
    CMQC.MQCA_INSTALLATION_DESC:     CMQC.MQ_INSTALLATION_DESC_LENGTH,
    CMQC.MQCA_INSTALLATION_NAME:     CMQC.MQ_INSTALLATION_NAME_LENGTH,
    CMQC.MQCA_INSTALLATION_PATH:     CMQC.MQ_INSTALLATION_PATH_LENGTH,
    CMQC.MQCA_LU62_ARM_SUFFIX:       CMQC.MQ_ARM_SUFFIX_LENGTH,
    CMQC.MQCA_LU_GROUP_NAME:         CMQC.MQ_LU_NAME_LENGTH,
    CMQC.MQCA_LU_NAME:               CMQC.MQ_LU_NAME_LENGTH,
    CMQC.MQCA_NAMELIST_DESC:         CMQC.MQ_NAMELIST_DESC_LENGTH,
    CMQC.MQCA_NAMELIST_NAME:         CMQC.MQ_NAMELIST_NAME_LENGTH,
    CMQC.MQCA_NAMES:                 CMQC.MQ_OBJECT_NAME_LENGTH * 256, # Maximum length to allocate
    CMQC.MQCA_PARENT:                CMQC.MQ_Q_MGR_NAME_LENGTH,
    CMQC.MQCA_PROCESS_DESC:          CMQC.MQ_PROCESS_DESC_LENGTH,
    CMQC.MQCA_PROCESS_NAME:          CMQC.MQ_PROCESS_NAME_LENGTH,
    CMQC.MQCA_Q_DESC:                CMQC.MQ_Q_DESC_LENGTH,
    CMQC.MQCA_Q_MGR_DESC:            CMQC.MQ_Q_MGR_DESC_LENGTH,
    CMQC.MQCA_Q_MGR_IDENTIFIER:      CMQC.MQ_Q_MGR_IDENTIFIER_LENGTH,
    CMQC.MQCA_Q_MGR_NAME:            CMQC.MQ_Q_MGR_NAME_LENGTH,
    CMQC.MQCA_Q_NAME:                CMQC.MQ_Q_NAME_LENGTH,
    CMQC.MQCA_QSG_NAME:              CMQC.MQ_QSG_NAME_LENGTH,
    CMQC.MQCA_REMOTE_Q_MGR_NAME:     CMQC.MQ_Q_MGR_NAME_LENGTH,
    CMQC.MQCA_REMOTE_Q_NAME:         CMQC.MQ_Q_NAME_LENGTH,
    CMQC.MQCA_REPOSITORY_NAME:       CMQC.MQ_Q_MGR_NAME_LENGTH,
    CMQC.MQCA_REPOSITORY_NAMELIST:   CMQC.MQ_NAMELIST_NAME_LENGTH,
    CMQC.MQCA_SSL_CRL_NAMELIST:      CMQC.MQ_NAMELIST_NAME_LENGTH,
    CMQC.MQCA_SSL_CRYPTO_HARDWARE:   CMQC.MQ_SSL_CRYPTO_HARDWARE_LENGTH,
    CMQC.MQCA_SSL_KEY_REPOSITORY:    CMQC.MQ_SSL_KEY_REPOSITORY_LENGTH,
    CMQC.MQCA_STORAGE_CLASS:         CMQC.MQ_STORAGE_CLASS_LENGTH,
    CMQC.MQCA_TCP_NAME:              CMQC.MQ_TCP_NAME_LENGTH,
    CMQC.MQCA_TRIGGER_DATA:          CMQC.MQ_TRIGGER_DATA_LENGTH,
    CMQC.MQCA_USER_DATA:             CMQC.MQ_PROCESS_USER_DATA_LENGTH,
    CMQC.MQCA_VERSION:               CMQC.MQ_VERSION_LENGTH,
    CMQC.MQCA_XMIT_Q_NAME:           CMQC.MQ_Q_NAME_LENGTH,
    CMQC.MQCA_STREAM_QUEUE_NAME:     CMQC.MQ_Q_NAME_LENGTH,
    CMQC.MQCA_INITIAL_KEY:           CMQC.MQ_INITIAL_KEY_LENGTH,
    CMQC.MQCA_SSL_KEY_REPO_PASSWORD: CMQC.MQ_SSL_ENCRYP_KEY_REPO_PWD_LEN,
}

def get_attr_info(attrs):
    """Return info about the list of input selectors"""
    char_attr_length = 0
    char_attr_count = 0
    int_attr_count = 0

    for attr in attrs:
        try:
            # If it's a CHAR attribute, it ought to be in this map
            v = mqAttrLength[attr]
            char_attr_count+=1
            char_attr_length += v
        except KeyError as e:
            # Only integer values in this range are valid for MQINQ/MQSET.
            # Any other attributes require PCF command processing.
            if CMQC.MQIA_FIRST <= attr <= CMQC.MQIA_LAST:
                int_attr_count+=1
            else:
                # This might happen if a new char attribute is available for MQINQ but has
                # not been added to the above list. In which case, inform the package owners.
                raise MQMIError(CMQC.MQCC_FAILED, CMQC.MQRC_SELECTOR_ERROR) from e

    return {'intAttrCount': int_attr_count, 'charAttrCount': char_attr_count, 'charAttrLen': char_attr_length}

def get_attr_length(attr):
    """What is the max length of a char attributes.
    Return 0 if unknown.
    """
    v = 0
    try:
        v= mqAttrLength[attr]
    except KeyError:
        pass
    return v

def common_inq(hconn,hobj,selectors):
    """Call MQINQ - renamed from 'inq' to match the 'common_set' function"""
    is_list = True
    single_attr = None

    # For compatibility with the original version that only
    # accepted a single attribute. Convert it to a list
    # and, at the end, return the one value.
    if not isinstance(selectors,list):
        single_attr = selectors
        is_list = False
        selectors = [selectors]

    attr_info = get_attr_info(selectors)

    # Create an empty list that will be used for the returned attributes
    int_attrs = []

    # Returns intAttrs (list), charAttr (byte string), MQCC, MQRC
    rv = ibmmqc.MQINQ(hconn,hobj,selectors,
                int_attrs,
                attr_info['intAttrCount'],
                attr_info['charAttrCount'],
                attr_info['charAttrLen'])
    if rv[-1]:
        raise MQMIError(rv[-2], rv[-1])

    #
    int_attrs = rv[0]
    char_attrs = rv[1]

    attrs = {}
    j=0
    char_offset = 0
    for s in selectors:
        if CMQC.MQIA_FIRST <= s <= CMQC.MQIA_LAST:
            attrs[s] = int_attrs[j]
            j+=1
        else:
            # If we had Namelist objects, more work would be needed to
            # deal with the lists of names returned from MQINQ
            char_length = get_attr_length(s)

            # The queue manager will not return the real key associated with this attribute,
            # but we want to make it printable.
            if s == CMQC.MQCA_INITIAL_KEY:
                v = b"********"
            else:
                v=char_attrs[char_offset:char_offset + char_length]
            char_offset += char_length

            # Turn into a string? Use default encoding?
            attrs[s] = v # .decode().strip()

    # The backwards compatibility option - return the actual value instead of a map
    if not is_list:
        return attrs[single_attr]

    return attrs

# For MQSET, the input is usually a dict of {selector:value}, similar to what's
# returned from MQINQ. But for backwards compatibility, we allow a single separate pair
# of parameters.
def common_set(hconn,hobj,*args):
    """Call MQSET - renamed from 'set' to avoid overloading language function"""
    temp=args[0][0]
    if not isinstance(temp,dict):
        # Convert an old-style k/v pair into a dict
        kv={temp:args[0][1]}
    else:
        kv=temp

    selectors=[]
    int_attrs=[]
    char_attrs=b''

    # Build the list of IntAttrs and the CharAttr byte buffer from the input dict.
    # There's actually only a single char item that can be set for a queue (none for a qmgr)
    # but this handles it in a generic fashion.
    for k,v in kv.items():
        selectors.append(k)
        if CMQC.MQIA_FIRST <= k <= CMQC.MQIA_LAST:
            int_attrs.append(v)
        else:
            ll = get_attr_length(k)
            v = mqcommon.ensure_strings_are_bytes(v)
            # Turn the input string into a byte buffer of exactly the right length
            # Throw an immediate error if it's too long
            pad_len = ll - len(v)
            if pad_len < 0:
                raise MQMIError(CMQC.MQCC_FAILED, CMQC.MQRC_CHAR_ATTR_LENGTH_ERROR)
            char_attrs += v + pad_len*b'\0'

    return ibmmqc.MQSET(hconn,hobj,selectors,int_attrs,char_attrs)
