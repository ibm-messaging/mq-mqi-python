"""MQCB/MQCTL implementation, including the proxy Python callback"""

# Copyright (c) 2025 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

from threading import Lock

from mqcommon import *
from mqerrors import *
from ibmmq import CMQC, GMO, MD, CBC, CBD, ibmmqc


_callback_lock = Lock()

# A couple of classes hold data that's given to the callback function
# _cbCBD has a per-callback block; _cbCTLO has a per-connection block
class _cbCBD:
    def __init__(self, obj, cbd):
        self.callback_function = cbd.CallbackFunction
        self.callback_area = cbd.CallbackArea
        self.object = obj

class _cbCTLO:
    def __init__(self,ctlo):
        self.connection_area = ctlo.ConnectionArea

_stashedCBD: dict[str, _cbCBD] = {}
_stashedCTLO: dict[int,_cbCTLO] = {}

# Create the key that's going to give us stashed info for a queue or qmgr
def _make_key(hc,ho):
    s = str(hc) + "/" + str(ho)
    return s

# Create a key to cover all stashed info for a qmgr connection
def _make_partial_key(hc):
    s = str(hc) + "/"
    return s

# The hConn and hObj are the actual numbers, while we also stash the object (Queue or QueueManager) and other fields
# from the CBD structure
def _save_callback(obj,qmgr,queue,cbd):
    key = _make_key(qmgr,queue)
    with _callback_lock:
        _stashedCBD[key] = _cbCBD(obj,cbd)

def _delete_callback(hconn,hobj):
    key = _make_key(hconn,hobj)
    try:
        with _callback_lock:
            del _stashedCBD[key]
    except KeyError:
        pass

def _delete_all_callbacks(hconn):
    pk = _make_partial_key(hconn)
    with _callback_lock:
        for key in list(_stashedCBD.keys()):
            if key.startswith(pk):
                try:
                    del _stashedCBD[key]
                except KeyError:
                    pass
        key = str(hconn)
        try:
            del _stashedCTLO[key]
        except KeyError:
            pass

def _save_connection_area(hconn,ctlo):
    with _callback_lock:
        _stashedCTLO[hconn] = _cbCTLO(ctlo)

# This is the Python "proxy" callback invoked from the C proxy.
# Most of the parameters to this function are byte buffers.
#
# It locates the real user-specified callback function, using
# the hConn and hObj. It then calls the user function
# with suitably-reformatted parameters.
def _internal_cb(hc,md,gmo,buf,cbc):
    key=_make_key(hc,CBC().unpack(cbc).Hobj)
    try:
        cb = _stashedCBD[key]
    except KeyError as exc:
        # Should not happen as we've got control of the map. But just in case ...
        raise KeyError(f'Cannot find key {key} in callback map') from exc

    try:
        qmgr = cb.object.get_queue_manager()
        queue = cb.object
    except AttributeError:
        qmgr = cb.object
        queue = None

    cbc_up = CBC().unpack(cbc)
    cbc_up.CallbackArea = cb.callback_area
    cbc_up.CallbackFunction = cb.callback_function
    cbc_up.ConnectionArea = 0
    try:
        ca = _stashedCTLO[hc]
        cbc_up.ConnectionArea = ca.connection_area
    except KeyError:
        pass

    # There's a difference between local and client connections
    # when CallbackType=EVENT_CALL: in clients, the MD may be None. Whereas
    # local bindings always gives an MD.
    # So we fake a dummy MD (and similar for GMO) even if it's not going to be used, so
    # both modes look the same.
    if md:
        md_up = MD().unpack(md)
    else:
        md_up = MD()

    if gmo:
        gmo_up = GMO().unpack(gmo)
    else:
        gmo_up = GMO()

    # Call the real user function with the unpacked forms of the structures
    cb.callback_function(queue_manager=qmgr, queue=queue, md=md_up, gmo=gmo_up, msg=buf, cbc=cbc_up)

def real_cb(obj, kwargs):
    """
    Register or deregister a user function to be called when a message arrives or an event occurs.
    The function and relevant correlator blocks are stashed locally, so they can be restored
    in the proxy callback function.
    The related MQCTL is called as a method on the QMgr object
    """
    operation = kwargs['operation'] if 'operation' in kwargs else CMQC.MQOP_REGISTER
    md        = kwargs['md'] if 'md' in kwargs else MD()
    cbd       = kwargs['cbd'] if 'cbd' in kwargs else CBD()
    gmo       = kwargs['gmo'] if 'gmo' in kwargs else GMO()

    if not isinstance(cbd, CBD):
        raise TypeError("cbd must be an instance of CBD")
    if not isinstance(md, MD):
        raise TypeError("md must be an instance of MD")
    if not isinstance(gmo, GMO):
        raise TypeError("gmo must be an instance of GMO")

    # The object must be either a queue or qmgr class.
    # But we can't use isinstance here because of circular
    # import nesting. So try to treat it as a Queue and if
    # that fails, treat it as a QMgr (without a 'cast')
    try:
        hconn = obj.get_queue_manager().get_handle()
        hobj = obj.get_handle()
    except AttributeError:
        hconn = obj.get_handle()
        hobj = CMQC.MQHO_NONE

    # These fields do not need to be passed to the
    # C layer as they point at Python objects and get stashed locally. Instead,
    # set them to 0 so as to allow pack() to work. Then restore them after
    # the MQCB call, to allow the stashing and so the app doesn't
    # see the change.
    original_cbf = cbd.CallbackFunction
    original_cba = cbd.CallbackArea
    cbd.CallbackFunction = 0
    cbd.CallbackArea = 0

    rv = ibmmqc.MQCB(hconn, operation, cbd.pack(), hobj, md.pack(), gmo.pack())

    # Restore the fields so they can be stashed in the _save_callback function
    cbd.CallbackFunction = original_cbf
    cbd.CallbackArea = original_cba

    if rv[0]:
        raise MQMIError(rv[-2], rv[-1])

    if operation == CMQC.MQOP_REGISTER:
        _save_callback(obj,hconn,hobj, cbd)
    elif operation == CMQC.MQOP_DEREGISTER:
        _delete_callback(hconn,hobj)

# Initialise the C layer with the address of this module's proxy callback function.
ibmmqc.MQCBINIT(_internal_cb)
