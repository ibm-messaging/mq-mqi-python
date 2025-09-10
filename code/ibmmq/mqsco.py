"""MQSCO: SSL/TLS Control Options"""

# Copyright (c) 2025 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

from mqcommon import *
from mqopts import MQOpts
from ibmmq import CMQC, ibmmqc

# SCO Class for SSL Support courtesy of Brian Vicente (mailto:sailbv@netscape.net)
class SCO(MQOpts):
    """ Construct an MQSCO Structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    The default structure is chosen to be VERSION_5, which was MQ 8.0
    """
    def __init__(self, **kw):
        sco_current_version = ibmmqc.__strucversions__.get("sco",1)

        opts = [['_StrucId', CMQC.MQSCO_STRUC_ID, '4s'],
            ['Version', CMQC.MQSCO_VERSION_5, MQLONG_TYPE],
            ['KeyRepository', b'', '256s'],
            ['CryptoHardware', b'', '256s'],
            ['AuthInfoRecCount', (0), MQLONG_TYPE],
            ['AuthInfoRecOffset', (0), MQLONG_TYPE],
            ['AuthInfoRecPtr', 0, 'P'],
            ['KeyResetCount', (0), MQLONG_TYPE],
            ['FipsRequired', (0), MQLONG_TYPE],
            ['EncryptionPolicySuiteB', [1, 0, 0, 0], '4' + MQLONG_TYPE],
            ['CertificateValPolicy', (0), MQLONG_TYPE],
            ['CertificateLabel', b'', '64s']]

        if sco_current_version >= CMQC.MQSCO_VERSION_6:
            opts += [['KeyRepoPassword',0,'P'],
                     ['_KeyRepoPasswordOffset',0,MQLONG_TYPE],
                     ['_KeyRepoPasswordLength',0,MQLONG_TYPE]]

        if sco_current_version >= CMQC.MQSCO_VERSION_7:
            opts += [['HTTPSCertValidation',0,MQLONG_TYPE],
                     ['HTTPSCertRevocation',0,MQLONG_TYPE],
                     ['HTTPSKeyStore',0,'P'],
                     ['_HTTPSKeyStoreOffset',0,MQLONG_TYPE],
                     ['_HTTPSKeyStoreLength',0,MQLONG_TYPE]]

        super().__init__(tuple(opts), **kw)

# Backward compatibility
sco = SCO
