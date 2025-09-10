"""QueueManager class: Implements MQI functions that do not require an hObj"""

# Copyright (c) 2025 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

from mqcommon import *
from ibmmq import CMQC, CMQXC, CNO, CSP, CTLO, SCO, PMO, STS, MD, OD, CD, MQObject, ibmmqc
from mqerrors import *

import mqcallback
import mqinq
import mqqargs

try:
    from typing import Any, Optional, Dict, Union
except ImportError:
    pass

class QueueManager(MQObject):
    """ QueueManager encapsulates the connection to the Queue Manager. By
    default, the Queue Manager is implicitly connected. If required,
    the connection may be deferred until a call to connect().
    """
    def __init__(self, name: Optional[Union[str, bytes]] ='', disconnect_on_exit: bool =True,
                 bytes_encoding: str = default.bytes_encoding,
                 default_ccsid: int = default.ccsid) -> None:
        """ Connect to the Queue Manager 'name' (default value '').
        If 'name' is None, don't connect now, but defer the connection until connect() is called.
        Input 'bytes_encoding'  and 'default_ccsid' are the encodings that will be used in PCF, MQPUT and MQPUT1 calls
        using this MQ connection in case Unicode objects should be given on input.
        """
        name = ensure_strings_are_bytes(name)

        self.__handle = None
        self.__name = name
        self.__disconnect_on_exit = disconnect_on_exit
        self.__qmobj = None
        self.bytes_encoding = bytes_encoding
        self.default_ccsid = default_ccsid

        if name is not None:
            self.connect(name)
        super().__init__(name)

    def __del__(self) -> None:
        """ Disconnect from the queue Manager, if connected. Ignore any
        errors from the MQI as there's nothing that can be done about it anyway.
        """
        if self.__handle:
            if self.__qmobj:
                try:
                    ibmmqc.MQCLOSE(self.__handle, self.__qmobj, CMQC.MQCO_NONE)
                except (PYIFError, MQMIError):
                    pass

            if self.__disconnect_on_exit:
                try:
                    self.disconnect()
                except (PYIFError, MQMIError):
                    pass

    # This is the simplest form of MQCONN and allows for no options. Not even authentication.
    def connect(self, name) -> None:
        """connect(name)

        Connect immediately to the Queue Manager 'name'."""

        rv = ibmmqc.MQCONN(name)
        if rv[1]:
            raise MQMIError(rv[1], rv[2])
        self.__handle = rv[0]
        self.__name = name

# MQCONNX code courtesy of John OSullivan (mailto:jos@onebox.com)
# SSL additions courtesy of Brian Vicente (mailto:sailbv@netscape.net)
# Connect options suggested by Jaco Smuts (mailto:JSmuts@clover.co.za)

    def connect_with_options(self, name: Union[str, bytes], *args: Any, **kwargs:Dict[str,Any]) ->None:
        """connect_with_options(name
                                [,user=user][,password=password]
                                [,opts=cnoopts][,cno=mqcno][,sco=mqsco]
                                [,csp=mqcsp] [,bno=mqbno][,cd=mqcd])

           connect_with_options(name, cd, [sco])

        Connect immediately to the Queue Manager 'name', using the
        optional MQCNO, MQCD, MQSCO, MQCSP classes.  The cnoopts
        Options field is available for backwards compatibility, but
        setting it within an MQCNO class is preferred.

        The second form is defined for backward compatibility with
        very old versions of the library. It connects immediately to
        the Queue Manager 'name', using the MQCD connection descriptor
        cd and the optional MQSCO SSL options sco.

        UserId and Password can be given explicitly (for compatibility) or
        (preferred) as fields in the MQCSP structure where they are called
        CSPUserId and CSPPassword. Other authentication mechanisms - in particular
        using Tokens - require the CSP to be supplied.
        """
        name = ensure_strings_are_bytes(name)

        # Deal with old style args
        len_args = len(args)
        if len_args:
            if len_args > 2:
                raise TypeError('Too many positional args provided')
            if len_args >= 1:
                kwargs['cd'] = args[0]
            if len_args == 2:
                kwargs['sco'] = args[1]

        restore_csp = False
        restore_cno = False
        restore_sco = False
        restore_cd = False

        csp_pack = None
        sco_pack = None
        cno_pack = None
        bno_pack = None
        cd_pack  = None

        initial_key = None
        https_keystore = None
        key_repo_password = None
        ssl_peername = None

        ccdt_url = None

        options = kwargs['opts'] if 'opts' in kwargs else CMQC.MQCNO_NONE
        bno = kwargs['bno'] if 'bno' in kwargs else None

        cno = kwargs['cno'] if 'cno' in kwargs else None
        if cno:
            if not isinstance(cno, CNO):
                raise TypeError("cno must be an instance of CNO")

            # The only field we need to work on is the CCDTUrl
            try:
                ccdt_url = cno.CCDTUrl
                cno._set_ptr_field('CCDTUrl',ccdt_url)
            except AttributeError:
                ccdt_url = None

            restore_cno = True
        else:
            cno = CNO()
            cno.Options = options
        if cno:
            # Set the most useful handle sharing option automatically
            # unless there's already an explicit value
            if (cno.Options & (CMQC.MQCNO_HANDLE_SHARE_NO_BLOCK |
                               CMQC.MQCNO_HANDLE_SHARE_BLOCK)) == 0:
                cno.Options |= CMQC.MQCNO_HANDLE_SHARE_BLOCK

            cno_pack = cno.pack()

        sco = kwargs['sco'] if 'sco' in kwargs else None
        if sco:
            if not isinstance(sco, SCO):
                raise TypeError("sco must be an instance of SCO")

            try:
                key_repo_password = sco.KeyRepoPassword
                sco._set_ptr_field('KeyRepoPassword',key_repo_password)
            except AttributeError:
                key_repo_password = None

            try:
                https_keystore = sco.HTTPSKeyStore
                sco._set_ptr_field('HTTPSKeyStore',https_keystore)
            except AttributeError:
                https_keystore = None

            restore_sco = True

            sco_pack = sco.pack()

        csp = kwargs['csp'] if 'csp' in kwargs else None
        if csp:
            if not isinstance(csp, CSP):
                raise TypeError("csp must be an instance of CSP")
            # The real names of the user/password field also start with CSP
            # but it's very easy to forget that and we don't get compile errors
            # if people just set CSP.UserId. So throw an explicit error.
            # I considered silently permitting these "bad" fields and moving them to the
            # real names under the covers, but decided that it was
            # better to encourage use of the formal MQI structure elements. Even
            # though they're not really well-named. I don't do this for other MQI
            # fields, but this pair have proven to be particularly common mistakes.
            user = csp.CSPUserId
            try:
                _ = csp.UserId
                raise PYIFError('UserId field in CSP class is called CSPUserId')
            except AttributeError:
                pass

            password = csp.CSPPassword
            try:
                _ = csp.Password
                raise PYIFError('Password field in CSP class is called CSPPassword')
            except AttributeError:
                pass

            try:
                token = csp.Token
            except AttributeError:
                token = None
            try:
                initial_key = csp.InitialKey
            except AttributeError:
                initial_key = None

            # String fields in the CSP are overwritten with a ptr
            # so we will restore them to the original values after
            # the CONNX
            restore_csp = True
        else:
            # Always use a CSP even if none of the user fields are set
            csp = CSP()
            user = kwargs.get('user')
            password = kwargs.get('password')
            token = kwargs.get('token')

        # If you give a token, the user/password are ignored
        if token:
            if not isinstance(token, (str, bytes)):
                raise TypeError('Token must be an instance of str or bytes')

            csp._set_ptr_field('Token',token)

            # We need to fix these up even if they are not going to be used
            if user:
                csp._set_ptr_field('CSPUserId',None)
            if password:
                csp._set_ptr_field('CSPPassword',None)

            csp.AuthenticationType = CMQC.MQCSP_AUTH_ID_TOKEN
            csp.Version = max(csp.Version,CMQC.MQCSP_VERSION_3)

        elif user:
            # We check for None because password can be an empty string
            if password is None:
                raise ValueError('Password must not be None if user is provided')

            if not (isinstance(user, (str, bytes)) and isinstance(password, (str, bytes))):
                raise ValueError('Both user and password must be instances of str or bytes')
            csp._set_ptr_field('CSPUserId',user)
            csp._set_ptr_field('CSPPassword',password)
            csp.AuthenticationType = CMQC.MQCSP_AUTH_USER_ID_AND_PWD

        if initial_key:
            csp._set_ptr_field('InitialKey',initial_key)
            csp.Version = max(csp.Version, CMQC.MQCSP_VERSION_2)

        if csp:
            csp_pack = csp.pack()

        if bno:
            bno_pack = bno.pack()

        cd_pack = None
        cd = kwargs['cd'] if 'cd' in kwargs else None
        if cd:

            # TLS encryption requires MQCD of version at least 7.
            # Thus, if someone uses TLS and the version is lower than that,
            # we can just increase it ourselves.
            if cd.SSLCipherSpec:
                cd.Version = max(cd.Version,CMQXC.MQCD_VERSION_7)

            ssl_peername = cd.SSLPeerNamePtr
            if ssl_peername:
                # Ideally we'd rename this field but have to keep its original
                # name for compatibility
                cd._set_ptr_field('SSLPeerNamePtr',ssl_peername)
                restore_cd = True

            cd_pack = cd.pack()

        # We are now able to call the real C function with all its parameters
        rv = ibmmqc.MQCONNX(name, cno_pack, cd_pack, csp_pack, sco_pack, bno_pack)

        # The CSP/CNO structures might have been modified so restore the original parameters from
        # pointers to the actual string
        if restore_csp:
            csp.CSPUserId = user
            csp.CSPPassword = password
            if token:
                csp.Token = token
            if initial_key:
                csp.InitialKey = initial_key

        if restore_cno:
            if ccdt_url:
                cno.CCDTUrl = ccdt_url

        if restore_cd:
            if ssl_peername:
                cd.SSLPeerNamePtr = ssl_peername

        if restore_sco:
            if https_keystore:
                sco.HTTPSKeyStore = https_keystore
            if key_repo_password:
                sco.KeyRepoPassword = key_repo_password

        if rv[1] != CMQC.MQCC_FAILED:
            self.__handle = rv[0]
            self.__name = name

        if rv[1]:
            raise MQMIError(rv[1], rv[2])

    # Backward compatibility
    connectWithOptions = connect_with_options

    # This is a basic connection for a client, where a default CD is used.
    # although it is possible to add further structures that get passed
    # down to the real CONNX operation. Many of the example programs come
    # via this method.
    def connect_tcp_client(self, name, cd, channel, conn_name,
                           user=None, password=None,
                           cno=None, csp=None,sco=None,bno=None
                           ):
        # type: (str, CD, str, str, Optional[str], Optional[str], Any, Any, Any, Any) -> None
        """ Connect immediately to the remote Queue Manager 'name', using
        a TCP Client connection, with channnel 'channel' and the
        TCP connection string 'conn_name'. Other connection
        options come from 'cd' and optionally the other connection-related
        classes.
        """

        cd.ChannelName = ensure_strings_are_bytes(channel)
        cd.ConnectionName = ensure_strings_are_bytes(conn_name)
        cd.ChannelType = CMQXC.MQCHT_CLNTCONN
        cd.TransportType = CMQXC.MQXPT_TCP

        kwargs = {
            'user': user,
            'password': password,
            'opts': CMQC.MQCNO_CLIENT_BINDING,
            'cd': cd,
        }

        if cno:
            cno.Options |= CMQC.MQCNO_CLIENT_BINDING
            kwargs['cno'] = cno
        if csp:
            kwargs['csp'] = csp
        if sco:
            kwargs['sco'] = sco
        if bno:
            kwargs['bno'] = bno

        self.connect_with_options(name, **kwargs)

    # Backward compatibility
    connectTCPClient = connect_tcp_client

    def disconnect(self) -> None:
        """ Disconnect from queue manager, if connected.
        """
        if not self.__handle:
            raise PYIFError('not connected')
        saved_handle=self.__handle

        rv = ibmmqc.MQDISC(self.__handle)
        if rv[0]:
            raise MQMIError(rv[0], rv[1])
        self.__handle = self.__qmobj = None
        mqcallback._delete_all_callbacks(saved_handle)

    def get_handle(self) -> int:
        """ Get the queue manager handle. The handle is used for most other MQI calls.
        """
        if self.__handle:
            return self.__handle
        raise PYIFError('not connected')

    def get_name(self) -> str:
        """ Get the queue manager name that was used during MQCONN(X).
        """
        if self.__name:
            return self.__name.decode(default.bytes_encoding).strip()
        raise PYIFError('not connected')

    # Backward compatibility
    getHandle = get_handle

    def begin(self) -> None:
        """ Begin a new global transaction.
        """
        rv = ibmmqc.MQBEGIN(self.__handle)
        if rv[0]:
            raise MQMIError(rv[0], rv[1])

    def commit(self) -> None:
        """ Commits any outstanding gets/puts in the current unit of work.
        """
        rv = ibmmqc.MQCMIT(self.__handle)
        if rv[0]:
            raise MQMIError(rv[0], rv[1])

    def backout(self) -> None:
        """ Backout any outstanding gets/puts in the current unit of work.
        """
        rv = ibmmqc.MQBACK(self.__handle)
        if rv[0]:
            raise MQMIError(rv[0], rv[1])

    def put1(self, q_desc: Union[str, bytes, OD], msg: Optional[bytes], *opts: Union[MD, OD]) -> None:
        """ Put the single message in string buffer 'msg' on the queue
        using the MQI PUT1 call. This encapsulates calls to MQOPEN,: Incompatible default for argumen
        MQPUT and MQCLOSE. put1 is the optimal way to put a single
        message on a queue.

        q_desc identifies the Queue either by name (if its a string),
        or by MQOD (if its a OD instance).

        mDesc is the MQMD Message Descriptor for the
        message. If it is not passed, or is None, then a default MD
        object is used.

        putOpts is the MQPMO Put Message Options structure
        for the put1 call. If it is not passed, or is None, then a
        default PMO object is used.

        If mDesc and/or putOpts arguments were supplied, they may be
        updated by the put1 operation.
        """
        m_desc, put_opts = mqqargs.common_q_args(*opts)

        if not isinstance(msg, bytes):
            if isinstance(msg, str):  # Python 3 string is unicode
                msg = msg.encode(self.bytes_encoding)
                m_desc.CodedCharSetId = self.default_ccsid
                m_desc.Format = CMQC.MQFMT_STRING
            else:
                error_message = 'Message type is {0}. Convert to bytes.'
                raise TypeError(error_message.format(type(msg)))
        if put_opts is None:
            put_opts = PMO()

        # Now send the message
        rv = ibmmqc.MQPUT1(self.__handle, mqqargs._make_q_desc(q_desc).pack(), m_desc.pack(), put_opts.pack(), msg)
        if rv[-2]:
            raise MQMIError(rv[-2], rv[-1])
        _ = m_desc.unpack(rv[0])
        _ = put_opts.unpack(rv[1])

    def inquire(self, selectors: Union[int, list[int]]) -> Union[Any, Dict[int,Any]]:
        """ Inquire on qmgr attributes. If the qmgr is not already
        open, it is opened for Inquire.

        If the selectors parameter is a single value, then that specific
        attribute's value is returned (string or int).

        If the selectors parameter is a list of values, then a dict is returned
        where all the values are stored using each element of the selectors as the keys.
        """

        if self.__qmobj is None:
            # Make an od for the queue manager, open the qmgr & cache result
            qmod = OD(ObjectType=CMQC.MQOT_Q_MGR)
            hdl = self.__handle if self.__handle else CMQC.MQHC_UNUSABLE_HCONN
            rv = ibmmqc.MQOPEN(hdl, qmod.pack(), CMQC.MQOO_INQUIRE)
            if rv[-2]:
                raise MQMIError(rv[-2], rv[-1])
            self.__qmobj = rv[0]
        # mqinq.inq will throw the exception if necessary
        rv = mqinq.common_inq(self.__handle, self.__qmobj, selectors)
        return rv

    # Create an alias that is closer to the real MQI function name
    inq = inquire

    def stat(self,status_type: int) -> STS:
        """Implementation of MQSTAT"""
        stat = STS()
        rv = ibmmqc.MQSTAT(self.__handle, status_type, stat.pack())
        if rv[1]:
            raise MQMIError(rv[-2], rv[-1])
        return stat.unpack(rv[0])

    def _is_connected(self) -> bool:
        """ Try accessing the qmgr to see whether the application
        is connected to it. Note that the method is merely a convenience wrapper around
        MQINQ(). In particular, there's still a possibility that
        the app will disconnect between checking QueueManager.is_connected
        and the next MQ call. And this operation might (silently) fail for other reasons such
        as an authorisation issue, giving the false impression that it is not connected.
        """

        # The original version of this function used the PCF PING_Q_MGR command, but
        # a) that requires more authorisations to be set
        # b) was a problem with circular imports when everything was split into multiple files
        # Using MQINQ is equally (un)reliable.
        try:
            self.inquire(CMQC.MQCA_Q_MGR_NAME)
            return True
        except MQMIError:
            return False

    is_connected = property(_is_connected)

    # Setting up a callback function
    # There is a similar method on the Queue object but they
    # both go to a common implementation
    def cb(self, **kwargs: Dict[str,Any]) -> None:
        """cb(operation=operation, md=MD,gmo=GMO,cbd=CBD)
        Register or Deregister a Callback function for asynchronous
        message consumption.

        The cbd.CallbackFunction must be defined as (Dict[str,Any]) with
        entries for queue_manager,queue(unless it's a qmgr-wide event),
        md,gmo,cbc,msg.
        """
        mqcallback.real_cb(self,kwargs)

    def ctl(self, operation: int, ctlo: CTLO) -> None:
        """Start or stop registered callbacks with the MQCTL operation.
        The connectionArea is stashed so it can be given to the callback
        function. That area is not removed until MQDISC but it might be
        overwritten by subsequent calls to this function.
        """

        if not isinstance(ctlo, CTLO):
            raise TypeError("ctlo must be an instance of CTLO")

        mqcallback._save_connection_area(self.__handle,ctlo)
        original_cna = ctlo.ConnectionArea
        # Have to set this "pointer" field to NULL for pack() to work
        ctlo.ConnectionArea = 0
        rv = ibmmqc.MQCTL(self.__handle, operation, ctlo.pack())

        # But restore it immediately so the app doesn't notice the swap
        ctlo.ConnectionArea = original_cna
        if rv[1]:
            raise MQMIError(rv[-2], rv[-1])

# ################################################################################################################################

def connect(queue_manager, channel=None, conn_info=None, user=None, password=None, disconnect_on_exit=True,
            bytes_encoding=default.bytes_encoding, default_ccsid=default.ccsid,
            cd = None, cno=None, csp=None,sco=None,bno=None
            ):
    """ A convenience wrapper for connecting to MQ queue managers without needing to explicitly create a qmgr object first.
    If given both 'channel' and 'conn_info' will connect in client mode. If neither are given
    then a default connection mode is attempted. That might be either local bindings or a client,
    depending on other environmental factors.

    A QueueManager() is returned after successfully establishing a connection.
    """
    qmgr = QueueManager(None, disconnect_on_exit, bytes_encoding=bytes_encoding, default_ccsid=default_ccsid)

    if channel and conn_info:
        qmgr.connect_tcp_client(queue_manager or '', cd or CD(), channel, conn_info, user, password, cno=cno, csp=csp,sco=sco,bno=bno)

    elif queue_manager:
        qmgr.connect_with_options(queue_manager, user=user, password=password, cno=cno, csp=csp,sco=sco,bno=bno, cd=cd)

    else:
        raise TypeError('Invalid arguments: %s' % repr([queue_manager, channel, conn_info, user, password]))

    return qmgr
