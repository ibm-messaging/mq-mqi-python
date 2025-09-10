""""MQCD: Channel Descriptor"""

# Copyright (c) 2025 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

from mqcommon import *
from mqopts import MQOpts
from ibmmq import CMQC, CMQXC, ibmmqc

# MQCONNX code courtesy of John OSullivan (mailto:jos@onebox.com)
# SSL additions courtesy of Brian Vicente (mailto:sailbv@netscape.net)

class CD(MQOpts):
    """ Construct an MQCD Structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    The VERSION_11 structure was current from at least MQ 8.0 and does not need to flow
    to other systems, so we take that as the default version.
    """
    def __init__(self, **kw):
        """__init__(**kw)"""
        opts = []
        opts += [
            ['ChannelName', b'', '20s'],
            ['Version', CMQXC.MQCD_VERSION_11, MQLONG_TYPE],
            ['ChannelType', CMQXC.MQCHT_CLNTCONN, MQLONG_TYPE],
            ['TransportType', CMQXC.MQXPT_TCP, MQLONG_TYPE],
            ['Desc', b'', '64s'],
            ['QMgrName', b'', '48s'],
            ['XmitQName', b'', '48s'],
            ['ShortConnectionName', b'', '20s'],
            ['MCAName', b'', '20s'],
            ['ModeName', b'', '8s'],
            ['TpName', b'', '64s'],
            ['BatchSize', (50), MQLONG_TYPE],
            ['DiscInterval', (6000), MQLONG_TYPE],
            ['ShortRetryCount', (10), MQLONG_TYPE],
            ['ShortRetryInterval', (60), MQLONG_TYPE],
            ['LongRetryCount', (999999999), MQLONG_TYPE],
            ['LongRetryInterval', (1200), MQLONG_TYPE],
            ['SecurityExit', b'', '128s'],
            ['MsgExit', b'', '128s'],
            ['SendExit', b'', '128s'],
            ['ReceiveExit', b'', '128s'],
            ['SeqNumberWrap', (999999999), MQLONG_TYPE],
            ['MaxMsgLength', (4194304), MQLONG_TYPE],
            ['PutAuthority', CMQXC.MQPA_DEFAULT, MQLONG_TYPE],
            ['DataConversion', CMQXC.MQCDC_NO_SENDER_CONVERSION, MQLONG_TYPE],
            ['SecurityUserData', b'', '32s'],
            ['MsgUserData', b'', '32s'],
            ['SendUserData', b'', '32s'],
            ['ReceiveUserData', b'', '32s'],
            # Version 1
            ['UserIdentifier', b'', '12s'],
            ['Password', b'', '12s'],
            ['MCAUserIdentifier', b'', '12s'],
            ['MCAType', CMQXC.MQMCAT_PROCESS, MQLONG_TYPE],
            ['ConnectionName', b'', '264s'],
            ['RemoteUserIdentifier', b'', '12s'],
            ['RemotePassword', b'', '12s'],
            # Version 2
            ['MsgRetryExit', b'', '128s'],
            ['MsgRetryUserData', b'', '32s'],
            ['MsgRetryCount', (10), MQLONG_TYPE],
            ['MsgRetryInterval', (1000), MQLONG_TYPE],
            # Version 3
            ['HeartbeatInterval', (300), MQLONG_TYPE],
            ['BatchInterval', (0), MQLONG_TYPE],
            ['NonPersistentMsgSpeed', CMQXC.MQNPMS_FAST, MQLONG_TYPE],
            ['StrucLength', CMQXC.MQCD_CURRENT_LENGTH, MQLONG_TYPE],
            ['ExitNameLength', CMQC.MQ_EXIT_NAME_LENGTH, MQLONG_TYPE],
            ['ExitDataLength', CMQC.MQ_EXIT_DATA_LENGTH, MQLONG_TYPE],
            ['MsgExitsDefined', (0), MQLONG_TYPE],
            ['SendExitsDefined', (0), MQLONG_TYPE],
            ['ReceiveExitsDefined', (0), MQLONG_TYPE],
            ['MsgExitPtr', 0, 'P'],
            ['MsgUserDataPtr', 0, 'P'],
            ['SendExitPtr', 0, 'P'],
            ['SendUserDataPtr', 0, 'P'],
            ['ReceiveExitPtr', 0, 'P'],
            ['ReceiveUserDataPtr', 0, 'P'],
            # Version 4
            ['ClusterPtr', 0, 'P'],
            ['ClustersDefined', (0), MQLONG_TYPE],
            ['NetworkPriority', (0), MQLONG_TYPE],
            ['LongMCAUserIdLength', (0), MQLONG_TYPE],
            ['LongRemoteUserIdLength', (0), MQLONG_TYPE],
            # Version 5
            ['LongMCAUserIdPtr', 0, 'P'],
            ['LongRemoteUserIdPtr', 0, 'P'],
            ['MCASecurityId', b'', '40s'],
            ['RemoteSecurityId', b'', '40s'],
            # Version 6
            ['SSLCipherSpec', b'', '32s'],
            ['SSLPeerNamePtr', 0, 'P'],
            ['SSLPeerNameLength', (0), MQLONG_TYPE],
            ['SSLClientAuth', (0), MQLONG_TYPE],
            ['KeepAliveInterval', -1, MQLONG_TYPE],
            ['LocalAddress', b'', '48s'],
            ['BatchHeartbeat', (0), MQLONG_TYPE],
            # Version 7
            ['HdrCompList', [(0), (-1)], '2' + MQLONG_TYPE],
            ['MsgCompList', [0] + 15 * [(-1)], '16' + MQLONG_TYPE],
            ['CLWLChannelRank', (0), MQLONG_TYPE],
            ['CLWLChannelPriority', (0), MQLONG_TYPE],
            ['CLWLChannelWeight', (50), MQLONG_TYPE],
            ['ChannelMonitoring', (0), MQLONG_TYPE],
            ['ChannelStatistics', (0), MQLONG_TYPE],
            # Version 8
            ['SharingConversations', 10, MQLONG_TYPE],
            ['PropertyControl', 0, MQLONG_TYPE],      # 0 = MQPROP_COMPATIBILITY
            ['MaxInstances', 999999999, MQLONG_TYPE],
            ['MaxInstancesPerClient', 999999999, MQLONG_TYPE],
            ['ClientChannelWeight', 0, MQLONG_TYPE],
            ['ConnectionAffinity', 1, MQLONG_TYPE],  # 1 = MQCAFTY_PREFERRED
            # Version 9
            ['BatchDataLimit', 5000, MQLONG_TYPE],
            ['UseDLQ', 2, MQLONG_TYPE],
            ['DefReconnect', 0, MQLONG_TYPE],
            # Version 10
            ['CertificateLabel', b'', '64s'],
            # Version 11 # This is in 9.1 - can use as base
        ]

        # The MQ 12 additional field is not relevant for client connections
        # but we'll put it here for completeness.
        cd_current_version = ibmmqc.__strucversions__.get("cd",1)
        if cd_current_version >= CMQXC.MQCD_VERSION_12:
            opts += [['SPLProtection', 0, MQLONG_TYPE]]
            if MQLONG_TYPE == 'i':
                opts += [['__pad', b'', '4s']]

        # In theory, the pad should've been placed right before the 'MsgExitPtr'
        # attribute, however setting it there makes no effect and that's why
        # it's being set here, as a last element in the list.

        super().__init__(tuple(opts), **kw)

# Backward compatibility
cd = CD
