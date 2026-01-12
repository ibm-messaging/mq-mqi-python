"""Propagate any OpenTelemetry context between the Python environment and MQ message properties. The application
is assumed to be already instrumented, and the OTel libraries available to be called. If the OTel libraries are
not accessible, then this module does not do anything.
"""

# Copyright (c) 2025, 2026 IBM Corporation and other Contributors. All Rights Reserved.

try:
    from opentelemetry import trace as oteltrace
    otel_tracer_enabled = True
except ImportError:
    otel_tracer_enabled = False
    raise

from os import environ
from threading import Lock

import mqlog
from mqcommon import *
from mqerrors import *
from ibmmq import CMQC, MessageHandle, Queue, OD, PD, IMPO, SMPO, RFH2
# from mqqmgr import *

class PropOptions:
    """Keep track of the options used for a GET so we can preserve them across the Before/After calls.
    This class is only used in this module; more effort than it's worth to have the full setter/getter/init routines
    """
    prop_ctl = -1  # The PROPCTL attribute on the queue, or -1 if unknown
    gmo = 0  # Currently-active GMO Options value so we can reset
    managed_ho = None  # To link a managed queue with its corresponding MQSUB hObj


object_options = {}
object_handle = {}

object_options_lock = Lock()
object_handle_lock = Lock()

# The property names that we work with
traceparent = "traceparent"
tracestate = "tracestate"

# Use this as a bitmap filter to pull out relevant value from GMO.
# The AS_Q_DEF value is 0 so would not contribute.
get_props_options = CMQC.MQGMO_PROPERTIES_FORCE_MQRFH2 |\
    CMQC.MQGMO_PROPERTIES_IN_HANDLE |\
    CMQC.MQGMO_NO_PROPERTIES |\
    CMQC.MQGMO_PROPERTIES_COMPATIBILITY

# Options in an MQOPEN that mean we might do MQGET
# Do not include BROWSE variants
open_get_options = CMQC.MQOO_INPUT_AS_Q_DEF |\
    CMQC.MQOO_INPUT_SHARED |\
    CMQC.MQOO_INPUT_EXCLUSIVE


# This function can be useful to create a unique key related to the hConn and hObj values
# where the object name is not sufficiently unique
def _make_key(hc, ho) -> str:
    suffix = "*"
    if ho is not None:
        if isinstance(ho, int):
            if ho not in (CMQC.MQHO_NONE, CMQC.MQHO_UNUSABLE_HOBJ):
                suffix = str(ho)
        else:
            suffix = str(ho.get_handle())

    if isinstance(hc, int):
        prefix = str(hc)
    else:
        prefix = str(hc.get_handle())

    k = prefix + "/" + suffix
    mqlog.debug(f"make_key: {k}")
    return k

def _is_usable_handle(mh):
    """Is the message handle valid? We are given the actual integer value, not a MessageHandle object"""
    rc = False
    if mh not in (CMQC.MQHM_NONE, CMQC.MQHM_UNUSABLE_HMSG):
        rc = True

    mqlog.debug(f"is_usable_handle: {mh} {rc}")
    return rc

# Do we have a MsgHandle for this hConn? If not, create a new one
def _get_msg_handle(hc, ho) -> MessageHandle:
    key = _make_key(hc, ho)
    with object_handle_lock:
        if object_handle.get(key) is None:
            try:
                mh = MessageHandle(qmgr=hc)
                object_handle[key] = mh
            except MQMIError as e:
                mqlog.error(e)
                raise e

    o = object_handle.get(key)

    return o

# Is the GMO/PMO MsgHandle one that we allocated?
def _compare_msg_handle(hc, ho, mh_value) -> bool:
    rc = False
    key = _make_key(hc, ho)
    with object_handle_lock:
        oh = object_handle.get(key)
        if oh:
            mh_local = oh
            if mh_local.get_handle() == mh_value:
                rc = True

    return rc

def _props_contain(mh: MessageHandle, prop: str) -> bool:
    """ Is there a property of the given name?"""
    rc = False

    pd = PD()
    impo = IMPO()
    impo.Options = CMQC.MQIMPO_CONVERT_VALUE | CMQC.MQIMPO_INQ_FIRST

    # Don't care about the actual value of the property, just that it exists.
    try:
        mh.get(prop, impo=impo, pd=pd)
        rc = True
    except MQMIError:
        pass

    return rc


# Extract a substring from the RFH2 properties in a given folder
def _extract_rfh2_prop_val(props: bytes, prop: str) -> str:
    props_str = str(props, "utf-8")
    prop_xml = "<" + prop + ">"
    val = ""

    idx = props_str.find(prop_xml)
    if idx != -1:
        start = props_str[idx + len(prop_xml):]
        # Where does the next tag begin
        end = start.find("<")
        if end != -1:
            val = start[0:end]

    mqlog.debug(f"Searched for {prop} in RFH2 \"{props}\". Found: \"{val}\"")
    return val


def otel_disc(hc):
    """Get rid of entries in the hconn/hobj maps when the application calls MQDISC
     """

    mqlog.trace_entry("otel_disc")
    # Both the maps are keyed by a string which begins with
    # the hConn value. As this is MQDISC, we don't care about
    # any specific hObj
    prefix = str(hc.get_handle()) + "/"
    mqlog.debug(f"otel_disc: prefix={prefix}")
    with object_handle_lock:
        for k in object_handle.copy():  # Use copy to avoid changing dict underneath the iteration
            if k.startswith(prefix):
                mh = object_handle[k]
                try:
                    mh.dlt()
                except MQMIError as e:
                    mqlog.error(f"MessageHandle delete error: {e}")
                    # pass
                del object_handle[k]

    # And delete information about any OPENed object too
    with object_options_lock:
        for k in object_options.copy():
            if k.startswith(prefix):
                mho = object_options[k].managed_ho
                if mho:
                    otel_close_nolock(mho)
                del object_options[k]
    mqlog.trace_exit("otel_disc")

def otel_open(ho, od, open_options, managed_ho):
    """When a queue is opened for INPUT, then it will help to
    know the PROPCTL setting so we know if we can add a MsgHandle or to expect
    an RFH2 response. If the MQINQ fails, that's OK - we'll just ignore the error
    but might not be able to get any property/RFH from an inbound message

    Note that we can't (and don't need to) do the same for an MQPUT1 because the
    information we are trying to discover is only useful on MQGET/CallBack.
     """

    prop_ctl = -1

    mqlog.trace_entry("otel_open")
    mqlog.trace(f"otel_open: hobjReal={ho.get_handle()} open_options={open_options} mho={managed_ho}")

    # Do the MQINQ and stash the information
    # Only care if there's an INPUT (MQGET) option. We do the MQINQ on every relevant MQOPEN
    # because it might change between an MQCLOSE and a subsequent MQOPEN. The MQCLOSE
    # will, in any case, have discarded the entry from this map.
    # If the user opened the queue with MQOO_INQUIRE, then we can reuse the object handle.
    # Otherwise we have to do our own open/inq/close.
    # If the MQOPEN is for a topic (via MQSUB) AND there's a managed object created for the
    # target queue, then that will always have the MQOO_INQUIRE setup for us.
    if ((od and od.ObjectType == CMQC.MQOT_Q) and (open_options & open_get_options) != 0) or (managed_ho is not None):
        hc = ho.get_queue_manager()
        key = _make_key(hc, ho)
        prop_ctl = 0
        selectors = [CMQC.MQIA_PROPERTY_CONTROL]
        if managed_ho is None and (open_options & CMQC.MQOO_INQUIRE) != 0:
            mqlog.debug("open: Reusing existing hObj")
            try:
                values = ho.inquire(selectors)
                mqlog.debug(f"Inq Responses: {values}")
                prop_ctl = values[selectors[0]]
            except MQMIError as e:
                mqlog.error(f"open: Inq err {e}")
                prop_ctl = -1

        elif managed_ho is not None:
            mqlog.debug("open: Using managed hObj")
            try:
                values = managed_ho.inquire(selectors)
                mqlog.debug(f"Inq Responses: {values}")
                prop_ctl = values[selectors[0]]
            except MQMIError as e:
                mqlog.error(f"open: Inq err {e}")
                prop_ctl = -1

            # And add this to the map so it can be referenced during MQGETs
            managed_key = _make_key(hc, managed_ho)
            options = PropOptions()
            options.prop_ctl = prop_ctl
            # replace any existing value for this object handle
            with object_options_lock:
                object_options[managed_key] = options

        else:
            inq_od = OD()
            inq_od.ObjectName = od.ObjectName
            inq_od.ObjectQMgrName = od.ObjectQMgrName
            inq_od.ObjectType = CMQC.MQOT_Q
            inq_open_options = CMQC.MQOO_INQUIRE

            mqlog.debug("open: pre-Reopen")
            # This gets a little recursive as this Open will end up calling back into this function. But
            # as it's only doing MQOO_INQUIRE, then we don't nest any further
            try:
                inq_ho = Queue(hc, inq_od, inq_open_options)
                try:
                    values = inq_ho.inquire(selectors)
                    mqlog.debug(f"Inq Responses: {values}")
                    prop_ctl = values[selectors[0]]
                except MQMIError as e:
                    mqlog.error(f"open: Inq err {e}")
                    prop_ctl = -1

                try:
                    inq_ho.close()  # Ignore any error
                except MQMIError:
                    pass

            except MQMIError as e:
                mqlog.error(f"open: Reopen err {e}")
                prop_ctl = -1

        # Create an object to hold the discovered value
        options = PropOptions()
        options.prop_ctl = prop_ctl
        options.managed_ho = managed_ho
        # replace any existing value for this object handle
        with object_options_lock:
            object_options[key] = options

    else:
        mqlog.trace("open: not doing Inquire")

    mqlog.trace_exit("otel_open")

def otel_close(ho):
    """Called during the MQCLOSE"""
    mqlog.trace_entry("otel_close")
    key = _make_key(ho.get_queue_manager(), ho)
    with object_options_lock:
        if object_options.get(key):
            mho = object_options[key].managed_ho
            if mho:
                otel_close_nolock(mho)
            del object_options[key]
    mqlog.trace_exit("otel_close")

def otel_close_nolock(ho):
    """Called during the MQCLOSE of a subscription to cleanup any managed
    queues. The object lock is already held when this is called
    """
    mqlog.trace_entry("otel_close_nolock")

    key = _make_key(ho.get_queue_manager(), ho)
    if object_options.get(key):
        del object_options[key]
    mqlog.trace_exit("otel_close_nolock")

def otel_put_trace_before(hc, md, pmo, buffer):
    """Insert any span-provided properties from the environment"""

    mh = None
    mho = None

    mqlog.trace_entry("otel_put_trace_before")

    skip_parent = False
    skip_state = False

    # Is the app already using a MsgHandle for its PUT? If so, we
    # can piggy-back on that. If not, then we need to use our
    # own handle. That handle can be reused for all PUTs/GETs on this
    # hConn. This works, even when the app is primarily using an RFH2 for
    # its own properties - the RFH2 and the Handle contents are merged.

    # If there was an app-provided handle, then have they set
    # either of the key properties? If so, then we will
    # leave them alone as we are not trying to create a new span in this layer.
    if _is_usable_handle(pmo.NewMsgHandle):
        mh = pmo.NewMsgHandle
        if _props_contain(mh, traceparent):
            skip_parent = True
        if _props_contain(mh, tracestate):
            skip_state = True

    elif _is_usable_handle(pmo.OriginalMsgHandle):
        mho = pmo.OriginalMsgHandle
        if _props_contain(mho, traceparent):
            skip_parent = True

        if _props_contain(mho, tracestate):
            skip_state = True

    else:
        # The PMO uses the real integer value of the msg handle
        mh = _get_msg_handle(hc, None).msg_handle
        pmo.OriginalMsgHandle = mh

    # Make sure we've got one of the handles set
    if _is_usable_handle(mho) and not _is_usable_handle(mh):
        mh = mho

    temp_msg_handle = MessageHandle(qmgr=hc, dup_handle=mh)

    # The message MIGHT have been constructed with an explicit RFH2
    # header. Unlikely, but possible as we tend to prefer properties. If so, then we extract the properties
    # from that header (assuming there's only a single structure, and it's not
    # chained). Then very simply look for the property names in there as strings. These tests would
    # incorrectly succeed if someone had put "traceparent" into a non-"usr" folder but that would be
    # very unexpected.
    if md.Format == CMQC.MQFMT_RF_HEADER_2:
        rfh2 = RFH2()
        rfh2.unpack(buffer)
        try:
            folders = rfh2.get_folders()
            for folder in folders:
                props = rfh2[folder]
                if "<" + traceparent + ">" in props:
                    skip_parent = True
                if "<" + tracestate + ">" in props:
                    skip_state = True
        except KeyError:
            pass

    # We're now ready to extract the context information and set the MQ message property
    # We are not going to try to propagate baggage via another property
    span = oteltrace.get_current_span()
    mqlog.debug(f"Span: {span}")

    if span != oteltrace.INVALID_SPAN:
        span_context = span.get_span_context()
        mqlog.debug(f"Span/Context: {span_context}")

        if span_context.is_valid:
            smpo = SMPO()
            pd = PD()

            mqlog.debug("About to extract context from an active span")
            if not skip_parent:
                trace_id = span_context.trace_id
                span_id = span_context.span_id
                trace_flags = span_context.trace_flags
                trace_flags_string = "01"
                if trace_flags != 1:
                    trace_flags_string = "00"

                # This is the W3C-defined format for the trace property
                value = "00" + "-" + \
                    oteltrace.span.format_trace_id(trace_id) + "-" + \
                    oteltrace.span.format_span_id(span_id) + "-" + \
                    trace_flags_string

                mqlog.debug(f"Setting {traceparent} to {value}")

                try:
                    temp_msg_handle.properties.set(traceparent, value, smpo=smpo, pd=pd)
                except MQMIError:
                    # Fail silently?
                    pass

            if not skip_state:
                # Need to convert any TraceState map to a single serialised string
                ts = span_context.trace_state
                value = ts.to_header()
                if value is not None:  # and value != "":
                    mqlog.debug(f"Setting {tracestate} to \"{value}\"")
                    try:
                        temp_msg_handle.properties.set(tracestate, value, smpo=smpo, pd=pd)
                    except MQMIError:
                        # Fail silently?
                        pass

    mqlog.trace_exit("otel_put_trace_before")


def otel_put_trace_after(hc, pmo):
    """
    If we added our own MsgHandle to the PMO, then remove it
    before returning to the application. We don't need to delete
    the handle as it can be reused for subsequent PUTs on this hConn
    """
    mqlog.trace_entry("otel_put_trace_after")

    mh = pmo.OriginalMsgHandle
    if _compare_msg_handle(hc, None, mh):
        mqlog.debug("Replacing handle with default")
        pmo.OriginalMsgHandle = 0

    mqlog.trace_exit("otel_put_trace_after")

def otel_get_trace_before(hc, ho, gmo, asynchronous):
    """Decide whether or not to use a message handle when retrieving a message
    Called during MQGET and MQCB (that sets up the callback)
    """
    prop_ctl = 0

    mqlog.trace_entry("otel_get_trace_before")

    # Option combinations:
    # MQGMO_NO_PROPERTIES: Always add our own handle
    # MQGMO_PROPERTIES_IN_HANDLE: Use it
    # MQGMO_PROPERTIES_COMPAT/FORCE_RFH2: Any returned properties will be in RFH2
    # MQGMO_PROPERTIES_AS_Q_DEF:
    #      PROPCTL: NONE: same as GMO_NO_PROPERTIES
    #               ALL/COMPATV6COMPAT: Any returned properties will be either in RFH2 or Handle if supplied
    #               FORCE: Any returned properties will be in RFH2
    prop_get_options = gmo.Options & get_props_options
    mqlog.debug(f"propGetOptions: {prop_get_options}")

    if _is_usable_handle(gmo.MsgHandle):
        mqlog.debug("Using app-supplied msg handle")
    else:
        key = _make_key(hc, ho)
        prop_ctl = -1
        with object_options_lock:
            opts = object_options.get(key)
            if opts is not None:
                prop_ctl = opts.prop_ctl
                # Stash the GMO options so they can be restored afterwards
                opts.gmo = gmo.Options
                object_options[key] = opts

        # If we know that the app or queue is configured for not returning any properties, then we will override that into our handle
        if (prop_get_options == CMQC.MQGMO_NO_PROPERTIES) or (prop_get_options == CMQC.MQGMO_PROPERTIES_AS_Q_DEF and prop_ctl == CMQC.MQPROP_NONE):
            gmo.Options &= ~CMQC.MQGMO_NO_PROPERTIES
            gmo.Options |= CMQC.MQGMO_PROPERTIES_IN_HANDLE
            tmp_ho = ho
            if not asynchronous:
                tmp_ho = None

            gmo.MsgHandle = _get_msg_handle(hc, tmp_ho).get_handle()
            mqlog.debug(f"Using mqiotel msg handle. get_props_options={prop_get_options} prop_ctl={prop_ctl}")
        else:
            # Hopefully they will have set something suitable on the PROPCTL attribute
            # or are asking specifically for an RFH2-style response
            mqlog.debug(f"Not setting a message handle. prop_get_options={prop_get_options}")

    mqlog.trace_exit("otel_get_trace_before")

def _int_from_hex(s: str, default: int) -> int:
    try:
        return int(s, 16)
    except ValueError:
        return default

def otel_get_trace_after(ho, gmo, md, buffer, asynchronous):
    """ Extract the properties from the message, either with the properties API
    or from the RFH2. Construct an object with the span information.
    We do not try to extract/propagate any baggage-related fields.
    """
    mqlog.trace_entry("otel_get_trace_after")

    traceparent_val = ""
    tracestate_val = ""

    if buffer is None:
        mqlog.trace_exit("otel_get_trace_after", ep=1)
        return 0

    removed = 0
    mh = gmo.MsgHandle
    if _is_usable_handle(mh):
        temp_msg_handle = MessageHandle(qmgr=hc, dup_handle=mh)

        pd = PD()
        impo = IMPO()
        impo.Options = CMQC.MQIMPO_CONVERT_VALUE | CMQC.MQIMPO_INQ_FIRST

        try:
            val = temp_msg_handle.inq(impo, pd, traceparent)
            mqlog.debug(f"Found traceparent property: {val}")
            traceparent_val = val
        except MQMIError as e:
            if e.reason != CMQC.MQRC_PROPERTY_NOT_AVAILABLE:
                # Should not happen
                mqlog.error(e)

        try:
            val = temp_msg_handle.inq(impo, pd, tracestate)
            mqlog.debug(f"Found tracestate property: {val}")
            tracestate_val = val
        except MQMIError as e:
            if e.reason != CMQC.MQRC_PROPERTY_NOT_AVAILABLE:
                # Should not happen
                mqlog.error(e)

        # If we added our own handle in the GMO, then reset
        # but don't do it for async callbacks.
        tmp_ho = ho
        hc = ho.get_queue_manager()
        if not asynchronous:
            tmp_ho = None

        if not asynchronous and _compare_msg_handle(hc, tmp_ho, mh):
            gmo.MsgHandle = 0
            key = _make_key(hc, tmp_ho)
            with object_options_lock:
                opts = object_options.get(key)
                if opts is not None:
                    gmo.Options = opts.gmo
                else:
                    gmo.Options &= ~CMQC.MQGMO_PROPERTIES_IN_HANDLE

            mqlog.debug(f"Removing our handle: hObj={tmp_ho}")

        # Should we also remove the properties?
        # Probably not worth it, as any app dealing with
        # properties ought to be able to handle unexpected props.

    elif md.Format == CMQC.MQFMT_RF_HEADER_2:
        rfh2 = RFH2()
        rfh2.unpack(buffer)
        try:
            folders = rfh2.get_folders()
            for folder in folders:
                props = rfh2[folder]
                traceparent_val = _extract_rfh2_prop_val(props, traceparent)
                tracestate_val = _extract_rfh2_prop_val(props, tracestate)
                if traceparent_val != "" or tracestate_val != "":
                    break
        except KeyError:
            pass

        # If the only properties in the RFH2 are the OTEL ones, then perhaps
        # the application cannot process the message. But we don't know for sure,
        # and maybe the properties are useful for higher-level span generation.
        # So we should have an option to forcibly remove the RFH2. Other bindings
        # have extended the GMO to give an extra option. But that's hard to do
        # with the python way of handling MQI structures. So we disable it for now.
        # Perhaps do it via an environment variable or separate setter.
        #
        # if otelOpts.RemoveRFH2
        #    md.Format = rfh2.Format
        #    md.CodedCharSetId = rfh2.CodedCharSetId
        #    md.Encoding = rfh2.Encoding
        #    removed = rfh2.StrucLength

    # We now should have the relevant message properties to pass upwards
    trace_id = 0
    span_id = 0
    trace_flags = None
    trace_state = None

    span_context = None
    current_span = oteltrace.get_current_span()
    mqlog.debug(f"Span: {current_span}")

    if current_span != oteltrace.INVALID_SPAN:
        span_context = current_span.get_span_context()
        mqlog.debug(f"Span/Context: {span_context}")

    if span_context is not None and span_context.is_valid:

        have_new_context = False

        if traceparent_val != "":
            # Split the inbound traceparent value into its components to allow
            # construction of a new context
            elem = traceparent_val.split("-")
            if len(elem) == 4:
                # elem[0] = 0 (version indicator. Always 0 for now)

                trace_id = _int_from_hex(elem[1], oteltrace.INVALID_TRACE_ID)
                span_id = _int_from_hex(elem[2], oteltrace.INVALID_SPAN_ID)
                # Final element can only be 00 or 01 (for now)
                if elem[3] == "00":
                    trace_flags = oteltrace.TraceFlags.DEFAULT
                else:
                    trace_flags = oteltrace.TraceFlags.SAMPLED

                have_new_context = True

        if tracestate_val != "":
            # Build a TraceState structure by parsing the string
            trace_state = oteltrace.TraceState.from_header([tracestate_val])
            if trace_state is not None:
                have_new_context = True

        # If there is a current span, and we have at least one of the
        # parent/state properties, then create a link referencing these values
        if have_new_context:
            msg_context = oteltrace.SpanContext(trace_id=trace_id, span_id=span_id, is_remote=False, trace_flags=trace_flags, trace_state=trace_state)

            # mqlog.debug(f"Created new context: {msg_context}")
            if msg_context is not None:
                current_span.add_link(msg_context)
                mqlog.debug("Added link to current span")
                # mqlog.debug(f"Updated span: {currentSpan}")
            else:
                mqlog.debug("Unable to create a usable msg_context")

        else:
            mqlog.debug("No context properties found")

    else:
        # If there is no current active span, then we are not going to
        # try to create a new one, as we would have no way of knowing when it
        # ends. The properties are (probably) still available to the application if
        # it wants to work with them itself.
        mqlog.debug("No current span to update")

    mqlog.debug(f"removed:{removed}")
    mqlog.trace_exit("otel_get_trace_after")
    return removed

def init():
    """Any initialisation operations needed for the OTel interface"""

    # Set the function pointers to invoke the code in here
    OTelFunctions.disc = otel_disc
    OTelFunctions.open = otel_open
    OTelFunctions.close = otel_close
    OTelFunctions.put_trace_before = otel_put_trace_before
    OTelFunctions.put_trace_after = otel_put_trace_after
    OTelFunctions.get_trace_before = otel_get_trace_before
    OTelFunctions.get_trace_after = otel_get_trace_after

    # Set this so any underlying equivalent code in the C library (my API Exit) will not try to do its own thing
    environ["AMQ_OTEL_INSTRUMENTED"] = "true"


if environ.get("MQIPY_NOOTEL", None) is None:
    init()
