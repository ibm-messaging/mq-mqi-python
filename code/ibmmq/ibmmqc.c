/***********************************************************
Copyright 1991-1995 by Stichting Mathematisch Centrum, Amsterdam,
The Netherlands.

                        All Rights Reserved

Permission to use, copy, modify, and distribute this software and its
documentation for any purpose and without fee is hereby granted,
provided that the above copyright notice appear in all copies and that
both that copyright notice and this permission notice appear in
supporting documentation, and that the names of Stichting Mathematisch
Centrum or CWI or Corporation for National Research Initiatives or
CNRI not be used in advertising or publicity pertaining to
distribution of the software without specific, written prior
permission.

While CWI is the initial source for this software, a modified version
is made available by the Corporation for National Research Initiatives
(CNRI) at the Internet address ftp://ftp.python.org.

STICHTING MATHEMATISCH CENTRUM AND CNRI DISCLAIM ALL WARRANTIES WITH
REGARD TO THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS, IN NO EVENT SHALL STICHTING MATHEMATISCH
CENTRUM OR CNRI BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL
DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR
PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER
TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.

******************************************************************/

/*
 * Python Extension for IBM MQ.
 * This provides the direct interface to the MQI 'C' library.
 *
 * Author: L. Smithson (lsmithson@open-networks.co.uk)
 * Author: Dariusz Suchojad (dsuch at zato.io)
 * Author: Mark Taylor (ibmmqmet on GitHub)
 *
 * Copyright (c) 2025, 2026 IBM Corporation and other Contributors. All Rights Reserved.
 * Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.
 */

 /*
 * 64bit suppport courtesy of Brent S. Elmer, Ph.D. (mailto:webe3vt@aim.com)
 *
 * On 64 bit machines when MQ is compiled 64bit, MQLONG is an int defined
 * in /opt/mqm/inc/cmqc.h or wherever your MQ installs to.
 *
 * On 32 bit machines, MQLONG is a long and many other MQ data types are
 * set to MQLONG.
 */

/* This version is normally provided by the setup.py build process */
#if defined PYVERSION
static char __version__[] = PYVERSION;
#else
static char __version__[] = "Unknown";
#endif

static char ibmmqc_doc[] = " \
ibmmqc - A Python Extension for IBM MQ.  This presents a direct Python \
interface to the MQI 'C' library. Its usage and conventions are more \
or less the same as the MQI 'C' language API. \
 \
MQI Connection & Object handles are passed around as Python \
longs. These get converted to the 4-byte values used by the MQI in this layer.\
 \
Structure parameters (such as MQGMO) are passed as Python \
byte arrays. These buffers should be aligned & byte-ordered the \
same way the native 'C' compiler does. \
 \
All calls return the MQI completion code & reason as the last two\
elements of a tuple. Any other returned elements precede those in the tuple.\
 \
";

/* This include should come before any standard system headers */
#define PY_SSIZE_T_CLEAN 1
#include "Python.h"

// For Windows, we won't want warnings about functions like ctime that we know are OK in the way we use them
#define _CRT_SECURE_NO_WARNINGS

#include <time.h>

#include <cmqc.h>
#include <cmqcfc.h>
#include <cmqxc.h>

#if MQCMDL_CURRENT_LEVEL < 910
#error Need to build/install against MQ 9.1 or later
#endif

#if !defined(TRUE)
#define TRUE (1)
#endif
#if !defined(FALSE)
#define FALSE (0)
#endif

/* Platform-specific mutex includes */
#ifdef _WIN32
#include <windows.h>
typedef CRITICAL_SECTION map_mutex_t;
#else
#include <pthread.h>
typedef pthread_mutex_t map_mutex_t;
#endif

#include "ibmmqc.h"

/* Structures used by the Map functions */

/* Generic entry */
typedef struct MapEntry {
    char *key;
    void *value;
    struct MapEntry *next;
} MapEntry;

/* Map structure */
typedef struct Map {
    MapEntry **buckets;
    size_t capacity;
    size_t size;
    map_mutex_t mutex;
} Map;

/* The real structure that is added as the value */
typedef struct GetBuffer {
    size_t size;
    char * buf;
} GetBuffer;

#define MAP_INITIAL_CAPACITY 16
#define MAP_LOAD_FACTOR 0.75
#define KEY_SIZE 24 /* Big enough for 2 32-bit ints + '/' */

/* Required map function declarations */
static Map* map_create(void);
static int map_put(Map *map, const char *key, void *value);
static void* map_get(Map *map, const char *key); // Returns the value or NULL
static int map_remove(Map *map, const char *key);

static int map_lock(Map *map);
static int map_unlock(Map *map);

/* Other functions we want to pre-declare */
static void debug_fn(int level, const char *fmt, ...);
#if 1
#define debug(...)  debug_fn(__VA_ARGS__)
#else
#define debug(...)
#endif
/* Where do we put any errors */
static PyObject *ErrorObj;

/* To control any trace logging */
static FILE *fp = NULL;
static int fpOpened = 0;
static long debugOpts = 0; /* Not a BOOL so we can use bitmask to control what's logged */
static int shortTrace = FALSE;

/* The Map of message buffers for MQGET calls. It is not needed for any other MQ verb
 * including MQCB/CallBacks (where the buffer is owned by the qmgr).
 */
static Map *getBufferMap = NULL;

/*
 * MQI Structure sizes for the current supported MQ version are
 * defined here for convenience. This allows older versions of the
 * module to work with newer versions of MQI.
 * Some structures may have sizeof() not the same as CURRENT_LENGTH because
 * of implied padding. Need to check that.
 */

#define PY_IBMMQ_CD_SIZEOF MQCD_CURRENT_LENGTH
#define PY_IBMMQ_OD_SIZEOF MQOD_CURRENT_LENGTH
#define PY_IBMMQ_MD_SIZEOF sizeof(MQMD)
#define PY_IBMMQ_PMO_SIZEOF MQPMO_CURRENT_LENGTH
#define PY_IBMMQ_GMO_SIZEOF sizeof(MQGMO)
#define PY_IBMMQ_SCO_SIZEOF sizeof(MQSCO)
#define PY_IBMMQ_CNO_SIZEOF sizeof(MQCNO)

#define PY_IBMMQ_SD_SIZEOF sizeof(MQSD)
#define PY_IBMMQ_SRO_SIZEOF sizeof(MQSRO)
#define PY_IBMMQ_STS_SIZEOF sizeof(MQSTS)

#define PY_IBMMQ_CBD_SIZEOF sizeof(MQCBD)
#define PY_IBMMQ_CBC_SIZEOF sizeof(MQCBC)
#define PY_IBMMQ_CTLO_SIZEOF sizeof(MQCTLO)

#define PY_IBMMQ_CMHO_SIZEOF sizeof(MQCMHO)
#define PY_IBMMQ_DMHO_SIZEOF sizeof(MQDMHO)
#define PY_IBMMQ_SMPO_SIZEOF sizeof(MQSMPO)
#define PY_IBMMQ_IMPO_SIZEOF sizeof(MQIMPO)
#define PY_IBMMQ_PD_SIZEOF sizeof(MQPD)

/*
 * Convert an object that might be either a Python string or a byte array to a C NULL-terminated string
 */
static char* PyBytesOrText_AsStringAndSize(PyObject *txtObj, MQLONG *outLen) {
  if(PyBytes_Check(txtObj)) {
    // bytes
    if (outLen != NULL) {
      (*outLen) = (MQLONG)PyBytes_Size(txtObj);
    }
    return PyBytes_AsString(txtObj);
  } else if (PyUnicode_Check(txtObj)) {
    PyObject *bytesObj;
    // Using the generic codec so it conforms to the "Limited API" available at Python 3.9
    bytesObj = PyUnicode_AsEncodedString(txtObj,"utf-8","ignore");  // PyUnicode_As[UTF8] returns NULL on binary data! Text only.
    if (bytesObj != NULL) {
      if (outLen != NULL) {
        (*outLen) = (MQLONG)PyBytes_Size(bytesObj);
      }
      Py_DECREF(bytesObj);
      return PyBytes_AsString(bytesObj);
    } else {
      return NULL;
    }
  } else {
    return NULL;
  }
}

static char* PyBytesOrText_AsString(PyObject *txtObj) {
  return PyBytesOrText_AsStringAndSize(txtObj, NULL);
}

/* For the simplest case, where we only need to return MQCC/MQRC values */
#define MQRETURN(cc,rc)  Py_BuildValue("(ll)", (long)cc, (long)rc);

/*
 * This is a static buffer, so multi-threads might try to update it at once.
 * But by now, we're likely in a really bad situation anyway. Don't want to
 * have to malloc space for the error message.
 */
#define ERRORBUF 256
static char errorBuf[ERRORBUF] = {0};
static void *myAlloc(size_t s,const char *cause) {
  void *p = malloc(s);
  if (!p) {
    snprintf(errorBuf,ERRORBUF-1,"Cannot allocate memory buffer: %d bytes. Caller: %s",(int)s,cause);
    PyErr_SetString(ErrorObj, errorBuf);
  }

  // debug(1,"myAlloc: \"%s\" asked for %d bytes. p=%p",cause,s,p);
  return p;
}

static void *myRealloc(char *oldBuf, size_t s, const char *cause) {
  void *p = realloc(oldBuf, s );
  if (!p) {
    snprintf(errorBuf,ERRORBUF-1,"Cannot reallocate memory buffer:%d bytes. Caller: %s",(int)s,cause);
    PyErr_SetString(ErrorObj, errorBuf);
  }

  // debug(1,"myRealloc: \"%s\" asked for %d bytes p=%p",cause,s,p);
  return p;
}

static void myFree(void *p) {
  // debug(1,"myFree: %p",p);
  if (p) {
    free(p);
  }
}

/* ----------------------------------------------------- */

static int checkArgSize(Py_ssize_t given, Py_ssize_t expected, const char *name) {
  if (given != expected) {
    PyErr_Format(ErrorObj, "%s wrong size. Given: %lu, expected %lu", name, (unsigned long)given, (unsigned long)expected);
    return 1;
  }
  return 0;
}

/* Print the debug info to the log file. Note that that boilerplate prefix   */
/* is designed to match the Formatter object in mqlog.py associated with     */
/* a configured filename. The default (stderr) formatter is a bit different. */
static void debug_fn(int level, const char *fmt, ...) {
    va_list vaArgs;

    /* Not filtering any output based on logLevel for now. Just on/off */
    if (debugOpts == 0) {
        return;
    }

    va_start(vaArgs,fmt);
    if (fp) {
        if (shortTrace) {
          fprintf(fp,"%s:%s:","DEBUG","ibmmqc");
        } else {
          time_t t = time(NULL);
          char *now = ctime(&t);
          fprintf(fp,"%-8.8s %-8s %-8s ",&now[11],"DEBUG","ibmmqc");
        }
         vfprintf(fp,fmt,vaArgs);
        if (fmt[strlen(fmt) -1] != '\n')
          fprintf(fp,"\n");
        fflush(fp);
    }
    va_end(vaArgs);
}

/* Some failures in an MQI verb can still mean a resource should be deleted from
   internal maps as we don't know the real outcome.
 */
static int cleanupOK(MQLONG mqrc) {
    int rc = FALSE;

    switch (mqrc) {
    case MQRC_NONE:
    case MQRC_Q_MGR_STOPPING:
    case MQRC_Q_MGR_QUIESCING:
    case MQRC_CONNECTION_BROKEN:
    case MQRC_CONNECTION_STOPPING:
    case MQRC_CONNECTION_QUIESCING:
      rc = TRUE;
      break;
    default:
      rc = FALSE;
      break;
    }
    return rc;
}

/* Allocate a message buffer ready for MQGET. Stash the buffer */
/* in a map entry so it can be used on the next MQGET for this */
/* queue. If there is already an assigned buffer but it's too  */
/* small, reallocate it and update the map entry.              */
static char *updateQ(MQHCONN hConn, MQHOBJ hObj, size_t size) {
  char *buf = NULL;

  GetBuffer *bd;
  char key[KEY_SIZE] = {0};

  snprintf(key,sizeof(key)-1,"%d/%d",hConn,hObj);

  map_lock(getBufferMap);

  /* The map_get function returns the stored value or NULL if not found */
  bd = map_get(getBufferMap,key);
  if (!bd) {
    bd = (GetBuffer *)myAlloc(sizeof(GetBuffer),"buffer descriptor");
    if (bd) {
      buf = (char *)myAlloc(size,"message buffer");
      if (buf) {
        bd->buf = buf;
        bd->size = size;

        debug(1,"UpdateQ: Adding entry for %s",key);

        /* Insert into the map. If it fails, free our allocated buffers and return NULL */
        int rc = map_put(getBufferMap, key, bd);
        if (rc != 0) {
          myFree(buf);
          myFree(bd);
          buf = NULL;
        }
      }
    }
  } else if (bd->size < size) {
    /* Update the map entry in place */
    debug(1,"UpdateQ: Reallocating new buffer from size %d to %d for %s",bd->size, size, key);
    buf = (char *)myRealloc(bd->buf,size, "message buffer");
    if (buf) {
      bd->size = size;
      bd->buf = buf;
    }
  } else {
    debug(1,"UpdateQ: Reusing buffer of size %d for %s",size, key);
    buf = bd->buf;
  }

  map_unlock(getBufferMap);

  return buf;
}

/* Called when a queue is closed, so we can free the associated message buffer */
static void deleteQ(MQHCONN hConn, MQHOBJ hObj) {
  char key[KEY_SIZE] = {0};
  GetBuffer *bd;

  snprintf(key,sizeof(key)-1,"%d/%d",hConn,hObj);

  map_lock(getBufferMap);

  /* Removing the entry will free() the value as well as control structures. But it does
     not free the allocated message buffer. So we have to do that here first.
   */
  bd = map_get(getBufferMap, key);
  if (bd) {
    debug(1,"DeleteQ: deleting entry for %s",key);
    myFree(bd->buf);
    /* Not a lot can be done if the removal fails */
    map_remove(getBufferMap, key);
  } else {
    debug(1,"DeleteQ: no entry for %s",key);
  }

  map_unlock(getBufferMap);
}

/* Called during MQDISC to free message buffers for all associated queues */
static void deleteAll(MQHCONN hConn) {

  char key[KEY_SIZE] = {0};
  // Just put the hConn and separator in the key as we will then
  // match on any real keys that start with that string
  snprintf(key,sizeof(key)-1,"%d/",hConn);

  debug(1,"DeleteAll: removing all entries for %d",hConn);

  map_lock(getBufferMap);

  /* Iterate through all entries in the bucket chains */
  for (size_t i = 0; i < getBufferMap->capacity; i++) {
    MapEntry *entry = getBufferMap->buckets[i];

    while (entry) {
      MapEntry *next = entry->next;
      if (!strncmp(entry->key,key,strlen(key))) {
        debug(1,"           removing entry for %s in bucket %d",entry->key,i);
        GetBuffer *bd = entry->value;
        myFree(bd->buf);

        map_remove(getBufferMap,entry->key);
      }
      entry = next;
    }
  }

  map_unlock(getBufferMap);
}

/*
TODO: Actually add debug statements that make use of this!
TODO: Define granularity masks or loglevel distinctions to opts.
*/
static char ibmmqc_MQLOGCF__doc__[] =
"MQLOGCF(opts, filename) \
An internal call to configure any debug logging from this module. \
If opts is non-zero, debug info gets reported to filename. Or stderr if \
that is empty/not supplied.\
";

static PyObject * ibmmqc_MQLOGCF(PyObject *self, PyObject *args) {
  char *filename = NULL;
  long lOpts;

  if (!PyArg_ParseTuple(args, "l|s", &lOpts,&filename)) {
    return NULL;
  }

  if (lOpts != 0) {
    /* Might be resetting to a different output file */
    if (fpOpened && fp) {
        fclose(fp);
        fp = NULL;
        fpOpened = 0;
    }

    if ((filename != NULL) && (strncmp(filename,"stderr",6) != 0)) {
      fp = fopen(filename,"a");
      if (fp) {
        fpOpened = 1;
      } else {
        snprintf(errorBuf,ERRORBUF-1,"Cannot open log file. Errno: %d ",(int)errno);
        PyErr_SetString(ErrorObj, errorBuf);
      }
    } else {
      /* Don't set fpOpened, as we don't want to try to close stderr later */
      fp = stderr;
      //shortTrace=TRUE;
    }
    setbuf(fp,NULL); /* Force the log file to be flushed immediately */
  }

  /* Debug is being turned off. So close the log file */
  if (lOpts == 0 && fpOpened) {
    if (fp) {
        fflush(fp);
        fclose(fp);

        fp = NULL;
        fpOpened = 0;
    }
  }

  debugOpts = lOpts;

  debug(1,"MQLOGCF Opts: %ld File: %s",lOpts,filename?filename:"N/A");
  // fprintf(stderr,"MQLOGCF Opts: %ld File: %s\n",lOpts,filename?filename:"N/A");

  return Py_BuildValue("(l)", (long) 0L);
}

static char ibmmqc_MQCONN__doc__[] =
"MQCONN(mgrName) \
 \
Calls the MQI MQCONN(mgrName) function to connect the Queue Manager \
specified by the string mgrName. The tuple (handle, comp, reason) is \
returned. Handle should be passed to subsequent calls to MQOPEN, etc.\
";

static PyObject * ibmmqc_MQCONN(PyObject *self, PyObject *args) {
  char *name;
  MQHCONN hConn;
  MQLONG compCode, reasonCode;
  PyObject *nameObj;

  if (!PyArg_ParseTuple(args, "O|", &nameObj)) {
    return NULL;
  }
  name = PyBytesOrText_AsString(nameObj);
  Py_BEGIN_ALLOW_THREADS
  MQCONN(name, &hConn, &compCode, &reasonCode);
  Py_END_ALLOW_THREADS

  return Py_BuildValue("(lll)", (long) hConn, (long) compCode, (long) reasonCode);
}

/*
 * MQCONNX code courtesy of John OSullivan (mailto:jos@onebox.com)
 * SSL additions courtesy of Brian Vicente (mailto:sailbv@netscape.net)
 * Connect options suggested by Jaco Smuts (mailto:JSmuts@clover.co.za)
 */

static char ibmmqc_MQCONNX__doc__[] =
"MQCONNX(mgrName, options, mqcno, mqcd, mqcsp, mqsco, mqbno) \
 \
Calls the MQI MQCONNX function to connect the Queue \
Manager specified by the string mgrName using options with the channel descriptor \
mqcd. The optional mqsco specifies SSL information. \
The tuple (handle, comp, reason) is returned. Handle should be \
passed to subsequent calls to MQOPEN, etc.\
";

static PyObject * ibmmqc_MQCONNX(PyObject *self, PyObject *args) {
  char* name = NULL;

  MQHCONN hConn = MQHC_UNUSABLE_HCONN;
  MQLONG compCode, reasonCode;

  PMQCNO cno = NULL;
  PMQCD mqcd = NULL;
  PMQSCO sco = NULL;
  PMQCSP csp = NULL;

  /* The MQBNO structure was introduced after the oldest version of MQ (9.1) stated as
   * supported by this package. So we have to use ifdefs to not refer to it if
   * that's where we are building.
   */
#if defined MQBNO_CURRENT_VERSION
  PMQBNO bno = NULL;
#else
  void *bno = NULL;
#endif

  Py_ssize_t mqcd_len = 0;
  Py_ssize_t sco_len = 0;
  Py_ssize_t cno_len = 0;
  Py_ssize_t csp_len = 0;
  Py_ssize_t bno_len = 0;

  /* There are no optional parameters here. But some can be None/NULL */
  /* Order of parameters from Python is important and must match      */
  if (!PyArg_ParseTuple(args, "yz#z#z#z#z#", &name, &cno, &cno_len, &mqcd, &mqcd_len, &csp, &csp_len, &sco, &sco_len, &bno,&bno_len)) {
    return NULL;
  }

  /*
   * Setup client connection fields appropriate to the version of MQ
   * we've been built with.
   *
   * We assume a basis of CNO_VERSION_6 will work. Higher levels can be
   * set explicitly based on the level of MQ client we are built against.
   *
   * We do NOT automatically set MQCNO_CLIENT_BINDING, even if a CD is given.
   * Rely on the application setting it, or it being derived from the external
   * environment somehow.
   */
  if (cno->Version < MQCNO_VERSION_6) {
    cno->Version = MQCNO_VERSION_6;
  }

  /* These fields can be assumed to always be available */
  if(mqcd) {
    cno->ClientConnPtr = (MQCD *)mqcd;

  /* SPLProtection is not used by clients, but was a convenient way of  */
  /* testing the version management before V10                          */
#if defined(MQCD_VERSION_12)
    if (mqcd->SPLProtection != 0) {
      if (mqcd->Version < MQCD_VERSION_12) {
        mqcd->Version = MQCD_VERSION_12;
      }
    }
#endif

  /* The Post-Quantum features came in MQ 10, with a new MQCD version */
#if defined(MQCD_VERSION_13)
    if ((mqcd->QuantumSafeAlgorithm > 0) || (mqcd->QuantumSafeRequired > 0)) {

      if (mqcd->Version < MQCD_VERSION_13) {
        mqcd->Version = MQCD_VERSION_13;
      }
    }
#endif
  }

  if (sco) {
    cno->SSLConfigPtr = sco;
  }

#if defined(MQCNO_VERSION_7)
  if (cno->ApplName[0] != 0 || cno->ApplName[0] != ' ') {
    if (cno->Version < MQCNO_VERSION_7) {
      cno->Version = MQCNO_VERSION_7;
    }
  }
#endif

  if (sco != NULL) {

#if defined(MQSCO_VERSION_6)
    if (sco->KeyRepoPasswordPtr) {
      if (sco->Version < MQSCO_VERSION_6) {
        sco->Version = MQSCO_VERSION_6;
      }
    }
#endif

    /* Defaults for the flags are 0. We only need to use these fields in the SCO if non-zero. So
     * it's easy to deal with backlevel version structures
     */
#if defined(MQSCO_VERSION_7)
    if(sco->HTTPSCertValidation != 0 || sco->HTTPSCertRevocation != 0 || sco->HTTPSKeyStorePtr != NULL) {
      if (sco->Version < MQSCO_VERSION_7) {
        sco->Version = MQSCO_VERSION_7;
      }
    }
#endif
  }

  /* The bno variable is always available even for older levels of MQ. But it is not USABLE without the
   * MQBNO structure and the CNO versions being suitable.
   */
  if (bno != NULL) {
#if defined(MQCNO_VERSION_8)
    if (cno->Version < MQCNO_VERSION_8) {
      cno->Version = MQCNO_VERSION_8;
      cno->BalanceParmsPtr = bno;
    }
#else
    return Py_BuildValue("(lll)", (long)-1, (long)MQCC_FAILED, (long)MQRC_WRONG_VERSION);
#endif
  }

  if (csp != NULL) {
    cno->SecurityParmsPtr = csp;
  }

  Py_BEGIN_ALLOW_THREADS
  MQCONNX(name, cno, &hConn, &compCode, &reasonCode);
  Py_END_ALLOW_THREADS

  return Py_BuildValue("(lll)", (long) hConn, (long) compCode, (long) reasonCode);
}

static char ibmmqc_MQDISC__doc__[] =
"MQDISC(handle) \
 \
Calls the MQI MQDISC(handle) function to disconnect the Queue \
Manager. The tuple (comp, reason) is returned. \
";

static PyObject * ibmmqc_MQDISC(PyObject *self, PyObject *args) {
  MQLONG compCode, reasonCode;

  long lQmgrHandle;
  MQHCONN qmgrHandle;
  MQHCONN savedQmgrHandle; // Need to keep track as successful MQDISC resets value to -1

  if (!PyArg_ParseTuple(args, "l", &lQmgrHandle)) {
    return NULL;
  }

  qmgrHandle = (MQHCONN)lQmgrHandle;
  savedQmgrHandle = qmgrHandle;

  Py_BEGIN_ALLOW_THREADS
  MQDISC((PMQHCONN)&qmgrHandle, &compCode, &reasonCode);
  Py_END_ALLOW_THREADS

  if (cleanupOK(reasonCode)) {
    deleteAll(savedQmgrHandle);
  }

  return MQRETURN(compCode, reasonCode);
}

static char ibmmqc_MQOPEN__doc__[] =
"MQOPEN(qMgr, qDesc, options) \
\
Calls the MQI MQOPEN(qMgr, qDesc, options) function to open the queue \
specified by the MQOD structure in the string buffer qDesc. QMgr is \
the Queue Manager handled returned by an earlier call to \
MQCONN. Options are the options for opening the Queue. \
 \
The tuple (qHandle, qDesc, comp, reason) is returned, where qHandle is \
the Queue Handle for the open queue and qDesc is the (possibly) \
updated copy of the Queue MQOD structure. \
 \
If qDesc is not the size expected for an MQOD structure, an exception \
is raised. \
" ;

static PyObject *ibmmqc_MQOPEN(PyObject *self, PyObject *args) {

  MQOD *qDescP;
  char *qDescBuffer;
  Py_ssize_t qDescBufferLength = 0;
  MQHOBJ qHandle;
  MQLONG compCode, reasonCode;

  long lOptions, lQmgrHandle;

  if (!PyArg_ParseTuple(args, "ly#l", &lQmgrHandle, &qDescBuffer,
            &qDescBufferLength, &lOptions)) {
    return NULL;
  }

  qDescP = (MQOD *)qDescBuffer;
  if (checkArgSize(qDescBufferLength, PY_IBMMQ_OD_SIZEOF, "MQOD")) {
    return NULL;
  }

  Py_BEGIN_ALLOW_THREADS
    MQOPEN((MQHCONN)lQmgrHandle, qDescP, (MQLONG) lOptions, &qHandle, &compCode, &reasonCode);
  Py_END_ALLOW_THREADS

  return Py_BuildValue("(ly#ll)", (long) qHandle, qDescP, PY_IBMMQ_OD_SIZEOF, (long) compCode, (long) reasonCode);
}

static char ibmmqc_MQCLOSE__doc__[] =
"MQCLOSE(qMgr, qHandle, options) \
 \
Calls the MQI MQCLOSE(qMgr, qHandle, options) function to close the \
queue referenced by qMgr & qHandle. The tuple (comp, reason), is \
returned. \
";

static PyObject * ibmmqc_MQCLOSE(PyObject *self, PyObject *args) {
  MQHOBJ qHandle;
  MQHOBJ savedQHandle;
  MQLONG compCode, reasonCode;

  /* Note: MQLONG is an int on 64 bit platforms and MQHCONN and MQHOBJ are MQLONG */
  long lOptions, lQmgrHandle, lqHandle;

  if (!PyArg_ParseTuple(args, "lll", &lQmgrHandle, &lqHandle, &lOptions)) {
    return NULL;
  }
  qHandle = (MQHOBJ) lqHandle;
  savedQHandle = qHandle;


  Py_BEGIN_ALLOW_THREADS
  MQCLOSE((MQHCONN) lQmgrHandle, &qHandle, (MQLONG) lOptions, &compCode, &reasonCode);
  Py_END_ALLOW_THREADS

  if (cleanupOK(reasonCode)) {
    deleteQ((MQHCONN)lQmgrHandle,savedQHandle);
  }

  return MQRETURN(compCode, reasonCode);
}

/*
 * Internal function that calls either PUT or PUT1 according to the
 * put1Flag arg
 */
static PyObject *mqputN(int put1Flag, PyObject *self, PyObject *args) {
  MQLONG compCode, reasonCode;
  char *mDescBuffer;
  Py_ssize_t mDescBufferLength = 0;
  MQMD *mDescP;
  char *putOptsBuffer;
  Py_ssize_t putOptsBufferLength = 0;
  MQPMO *pmoP;
  char *msgBuffer;
  Py_ssize_t msgBufferLength = 0;
  char *qDescBuffer;
  Py_ssize_t qDescBufferLength = 0;
  MQOD *qDescP = NULL;

  PyObject *rv;

  long lQmgrHandle, lqHandle;

  if (!put1Flag) {
    /* PUT call, expects qHandle for an open q */

    if (!PyArg_ParseTuple(args, "lly#y#y#", &lQmgrHandle, &lqHandle,
              &mDescBuffer, &mDescBufferLength,
              &putOptsBuffer, &putOptsBufferLength,
              &msgBuffer, &msgBufferLength)) {
      return NULL;
    }
  } else {
    /* PUT1 call, expects od for a queue to be opened */
    if (!PyArg_ParseTuple(args, "ly#y#y#y#", &lQmgrHandle,
              &qDescBuffer, &qDescBufferLength,
              &mDescBuffer, &mDescBufferLength,
              &putOptsBuffer, &putOptsBufferLength,
              &msgBuffer, &msgBufferLength)) {
      return NULL;

    }
    if (checkArgSize(qDescBufferLength, PY_IBMMQ_OD_SIZEOF, "MQOD")) {
      return NULL;
    }
    qDescP = (MQOD *)qDescBuffer;
  }

  if (checkArgSize(mDescBufferLength, PY_IBMMQ_MD_SIZEOF, "MQMD")) {
    return NULL;
  }
  mDescP = (MQMD *)mDescBuffer;

  if (checkArgSize(putOptsBufferLength, PY_IBMMQ_PMO_SIZEOF, "MQPMO")) {
    return NULL;
  }
  pmoP = (MQPMO *)putOptsBuffer;
  if (!put1Flag) {
    Py_BEGIN_ALLOW_THREADS
    MQPUT((MQHCONN) lQmgrHandle, (MQHOBJ) lqHandle, mDescP, pmoP, (MQLONG) msgBufferLength, msgBuffer,
      &compCode, &reasonCode);
    Py_END_ALLOW_THREADS
  } else {
    Py_BEGIN_ALLOW_THREADS
    MQPUT1((MQHCONN) lQmgrHandle, qDescP, mDescP, pmoP, (MQLONG) msgBufferLength, msgBuffer,
       &compCode, &reasonCode);
    Py_END_ALLOW_THREADS
  }

  rv = Py_BuildValue("(y#y#ll)",
              mDescP, (Py_ssize_t)PY_IBMMQ_MD_SIZEOF,
              pmoP, (Py_ssize_t)PY_IBMMQ_PMO_SIZEOF,
              (long) compCode, (long) reasonCode);
  return rv;
}


static char ibmmqc_MQPUT__doc__[] =
"MQPUT(qMgr, qHandle, mDesc, options, msg) \
 \
Calls the MQI MQPUT(qMgr, qHandle, mDesc, putOpts, msg) function to \
put msg on the queue referenced by qMgr & qHandle. The message msg may \
contain embedded nulls. mDesc & putOpts are string buffers containing \
a MQMD Message Descriptor structure and a MQPMO Put Message Option \
structure. \
 \
The tuple (mDesc, putOpts, comp, reason) is returned, where mDesc & \
putOpts are the (possibly) updated copies of the MQMD & MQPMO \
structures. \
 \
If either mDesc or putOpts are the wrong size, an exception is raised. \
";

static PyObject *ibmmqc_MQPUT(PyObject *self, PyObject *args) {
  return mqputN(0, self, args);
}


static char ibmmqc_MQPUT1__doc__[] =
"MQPUT1(qMgr, qDesc, mDesc, options, msg) \
 \
Calls the MQI MQPUT1(qMgr, qDesc, mDesc, putOpts, msg) function to put \
the message msg on the queue referenced by qMgr & qDesc. The message \
msg may contain embedded nulls. mDesc & putOpts are string buffers \
containing a MQMD Message Descriptor structure and a MQPMO Put Message \
Option structure. \
 \
The tuple (mDesc, putOpts, comp, reason) is returned, where mDesc & \
putOpts are the (possibly) updated copies of the MQMD & MQPMO \
structures. \
 \
MQPUT1 is the optimal way to put a single message on a queue. It is \
equivalent to calling MQOPEN, MQPUT and MQCLOSE. \
 \
If any of qDesc, mDesc or putOpts are the wrong size, an exception is \
raised. \
";

static PyObject *ibmmqc_MQPUT1(PyObject *self, PyObject *args) {
  return mqputN(1, self, args);
}


static char ibmmqc_MQGET__doc__[] =
"MQGET(qMgr, qHandle, mDesc, getOpts, maxlen) \
 \
Calls the MQI MQGET(qMgr, qHandle, mDesc, getOpts, maxlen) function to \
get a message from the queue referred to by qMgr & qHandle.  mDesc & \
getOpts are string buffers containing a MQMD Message Descriptor and a \
MQGMO Get Message Options structure. maxlen specified the maximum \
length of messsage to read from the queue. If the message length \
exceeds maxlen, the the behaviour is as defined by MQI. \
 \
The tuple (msg, mDesc, getOpts, actualLen, comp, reason) is returned, \
where msg is a string containing the message read from the queue and \
mDesc & getOpts are copies of the (possibly) updated MQMD & MQGMO \
structures. actualLen is the actual length of the message in the \
Queue. If this is bigger than maxlen, then as much data as possible is \
copied into the return buffer. In this case, the message may or may \
not be removed from the queue, depending on the MQGMO options. See the \
MQI APG/APR for more details. \
 \
If mDesc or getOpts are the wrong size, an exception is raised. \
";

static PyObject *ibmmqc_MQGET(PyObject *self, PyObject *args) {
  MQLONG compCode, reasonCode;
  char *mDescBuffer;
  Py_ssize_t mDescBufferLength = 0;
  MQMD *mDescP;
  char *getOptsBuffer;
  Py_ssize_t getOptsBufferLength = 0;
  MQGMO *gmoP;
  long maxLength, returnLength;
  MQLONG actualLength;
  char *msgBuffer;
  PyObject *rv;

  long lQmgrHandle, lqHandle;
  if (!PyArg_ParseTuple(args, "lly#y#l", &lQmgrHandle, &lqHandle,
            &mDescBuffer, &mDescBufferLength,
            &getOptsBuffer, &getOptsBufferLength, &maxLength)) {
    return NULL;
  }
  if (checkArgSize(mDescBufferLength, PY_IBMMQ_MD_SIZEOF, "MQMD")) {
    return NULL;
  }

  mDescP = (MQMD *)mDescBuffer;

  if (checkArgSize(getOptsBufferLength, PY_IBMMQ_GMO_SIZEOF, "MQGMO")) {
    return NULL;
  }
  gmoP = (MQGMO *)getOptsBuffer;

  /* Allocate or find storage for message */
  if (!(msgBuffer = updateQ((MQHCONN) lQmgrHandle, (MQHOBJ) lqHandle, maxLength))) {
    return NULL;
  }

  actualLength = 0;
  Py_BEGIN_ALLOW_THREADS
  MQGET((MQHCONN) lQmgrHandle, (MQHOBJ) lqHandle, mDescP, gmoP, (MQLONG) maxLength, msgBuffer, &actualLength,
    &compCode, &reasonCode);
  Py_END_ALLOW_THREADS

  /*
   * Message may be too big for caller's buffer, so only copy in as
   * much data as will fit, but return the actual length of the
   * message. Thanks to Maas-Maarten Zeeman for this fix.
   */
  if(actualLength >= maxLength) {
    returnLength = maxLength;
  } else {
    returnLength = actualLength;
  }

  rv = Py_BuildValue("(y#y#y#lll)", msgBuffer, (int) returnLength,
             mDescP, PY_IBMMQ_MD_SIZEOF, gmoP, PY_IBMMQ_GMO_SIZEOF,
             (long) actualLength, (long) compCode, (long) reasonCode);

  return rv;
}


static char ibmmqc_MQBEGIN__doc__[] =
"MQBEGIN(handle)  \
\
Calls the MQI MQBEGIN(handle) function to begin a new global \
transaction. This is used in conjunction with MQ coodinated \
Distributed Transactions and XA resources. \
 \
The tuple (comp, reason) is returned.\
";

static PyObject * ibmmqc_MQBEGIN(PyObject *self, PyObject *args) {
  MQLONG compCode, reasonCode;
  MQBO beginOpts = {MQBO_DEFAULT};

  long lHandle;

  if (!PyArg_ParseTuple(args, "l", &lHandle)) {
    return NULL;
  }
  Py_BEGIN_ALLOW_THREADS
  MQBEGIN((MQHCONN) lHandle, &beginOpts, &compCode, &reasonCode);
  Py_END_ALLOW_THREADS
  return MQRETURN(compCode, reasonCode);
}


static char ibmmqc_MQCMIT__doc__[] =
"MQCMIT(handle) \
 \
Calls the MQI MQCMIT(handle) function to commit any pending gets or \
puts in the current unit of work. The tuple (comp, reason) is \
returned. \
";

static PyObject * ibmmqc_MQCMIT(PyObject *self, PyObject *args) {
  MQLONG compCode, reasonCode;

  long lHandle;

  if (!PyArg_ParseTuple(args, "l", &lHandle)) {
    return NULL;
  }
  Py_BEGIN_ALLOW_THREADS
  MQCMIT((MQHCONN) lHandle, &compCode, &reasonCode);
  Py_END_ALLOW_THREADS
  return MQRETURN(compCode, reasonCode);
}

static char ibmmqc_MQBACK__doc__[] =
"MQBACK(handle) \
 \
Calls the MQI MQBACK(handle) function to backout any pending gets or \
puts in the current unit of work. The tuple (comp, reason) is \
returned. \
";

static PyObject * ibmmqc_MQBACK(PyObject *self, PyObject *args) {
  MQLONG compCode, reasonCode;

  long lHandle;

  if (!PyArg_ParseTuple(args, "l", &lHandle)) {
    return NULL;
  }
  Py_BEGIN_ALLOW_THREADS
  MQBACK((MQHCONN) lHandle, &compCode, &reasonCode);
  Py_END_ALLOW_THREADS
  return MQRETURN(compCode, reasonCode);
}


/*
 * MQINQ Interface.
 */
static char ibmmqc_MQINQ__doc__[] =
"MQINQ(qMgr, handle, selectors, intAttrList, intAttrCount, charAttrCount, charAttrLength ) \
\
Calls MQINQ with a list of attributes. Returns the values of those \
attributes as a tuple of (intAttrs,charAttr,CC,RC). It is the caller's \
responsibility to split the charAttr byte string into its component pieces.\
";

static PyObject *ibmmqc_MQINQ(PyObject *self, PyObject *args) {
  MQLONG compCode, reasonCode;
  MQLONG selectorCount;
  MQLONG *selectors = NULL;

  long intAttrCount = 0;
  MQLONG *intAttrs = NULL;

  long charAttrCount = 0;
  Py_ssize_t charAttrLength = 0;
  char *charAttrs = NULL;


  PyObject *rv = NULL;
  PyObject *lSelectors;
  PyObject *lIntAttrs;

  long lQmgrHandle, lObjHandle;

  if (!PyArg_ParseTuple(args, "llOOlll", &lQmgrHandle, &lObjHandle,
      &lSelectors,
      &lIntAttrs,
      &intAttrCount,
      &charAttrCount,
      &charAttrLength)) {
    return NULL;
  }

  if (!PyList_Check(lSelectors)) {
    PyErr_SetString(ErrorObj, "Arg is not a list");
    return NULL;
  }

  selectorCount = (MQLONG)PyList_Size(lSelectors);

  selectors = (MQLONG *)myAlloc(sizeof(MQLONG) * selectorCount, "MQINQ");
  if (!selectors) {
    return NULL;
  }

  if (selectors) {
    Py_ssize_t i;
    for (i=0;i<selectorCount;i++) {
      PyObject *s = PyList_GetItem(lSelectors,i);
      selectors[i] = (int)PyLong_AsLong(s); // _AsInt was not added until 3.13
    }
  }

  // This is passed as an empty list; we add the returned attribute values
  // after the MQINQ
  if (!PyList_Check(lIntAttrs)) {
    PyErr_SetString(ErrorObj, "Arg is not a list");
    return NULL;
  }

  if (intAttrCount > 0) {
    intAttrs = (MQLONG *)myAlloc(sizeof(MQLONG) * intAttrCount, "MQINQ");
    if (!intAttrs) {
        return NULL;
    }
  }

  if (charAttrLength > 0) {
     charAttrs = (char *)myAlloc(charAttrLength, "MQINQ");
     if (!charAttrs) {
        return NULL;
     }
  }

  Py_BEGIN_ALLOW_THREADS
  MQINQ((MQHCONN) lQmgrHandle, (MQHOBJ) lObjHandle, selectorCount, selectors,
        (MQLONG)intAttrCount, intAttrs, (MQLONG)charAttrLength, charAttrs, &compCode, &reasonCode);
  Py_END_ALLOW_THREADS

  if (compCode == MQCC_OK) {
    Py_ssize_t i;
    for (i=0;i<intAttrCount;i++) {
      PyObject *item = PyLong_FromLong((long)intAttrs[i]);
      if (PyList_Append(lIntAttrs,item)<0) {
        Py_DECREF(item);
      }
    }
  }

  rv = Py_BuildValue("(Oy#ll)", lIntAttrs, charAttrs, charAttrLength, (long) compCode, (long) reasonCode);

  if (intAttrs) {
    myFree(intAttrs);
  }
  if (charAttrs) {
    myFree(charAttrs);
  }

  if (selectors) {
    myFree(selectors);
  }
  return rv;
}

/*
 * MQSET Interface.
 */
static char ibmmqc_MQSET__doc__[] =
"MQSET(qMgr, handle, selectors, intAttrs, charAttrs ) \
\
Calls MQSET with lists of the attribute selectors and the values split into an int array and a byte string,\
following the real MQSET function style.\
";

static PyObject *ibmmqc_MQSET(PyObject *self, PyObject *args) {
  MQLONG compCode, reasonCode;

  long lQmgrHandle, lObjHandle;
  PyObject *lSelectors;
  PyObject *lIntAttrs;
  MQCHAR   *charAttrs;

  Py_ssize_t charAttrLength;

  MQLONG selectorCount;
  MQLONG *selectors = NULL;
  MQLONG intAttrCount;
  MQLONG *intAttrs = NULL;

  if (!PyArg_ParseTuple(args, "llOOy#", &lQmgrHandle, &lObjHandle, &lSelectors, &lIntAttrs, &charAttrs,&charAttrLength)) {
    return NULL;
  }

  if (!PyList_Check(lSelectors)) {
    PyErr_SetString(ErrorObj, "Selectors arg is not a list");
    return NULL;
  }

  if (!PyList_Check(lIntAttrs)) {
    PyErr_SetString(ErrorObj, "IntAttrs arg is not a list");
    return NULL;
  }

  selectorCount = (MQLONG) PyList_Size(lSelectors);
  selectors = (MQLONG *)myAlloc(sizeof(MQLONG) * selectorCount, "MQSET");
  if (selectors) {
    Py_ssize_t i;
    for (i=0;i<selectorCount;i++) {
      PyObject *s = PyList_GetItem(lSelectors,i);
      selectors[i] = (int)PyLong_AsLong(s); // _AsInt was not added until 3.13
    }
  }

  intAttrCount = (MQLONG) PyList_Size(lIntAttrs);
  if (intAttrCount > 0) {
  intAttrs = (MQLONG *)myAlloc(sizeof(MQLONG) * intAttrCount, "MQSET");
    if (intAttrs) {
      Py_ssize_t i;
      for (i=0;i<intAttrCount;i++) {
        PyObject *s = PyList_GetItem(lIntAttrs,i);
        intAttrs[i] = (int)PyLong_AsLong(s); // _AsInt was not added until 3.13
      }
    }
  }

  Py_BEGIN_ALLOW_THREADS
  MQSET((MQHCONN) lQmgrHandle, (MQHOBJ) lObjHandle, selectorCount, selectors,
        intAttrCount, intAttrs, (MQLONG)charAttrLength, charAttrs, &compCode, &reasonCode);
  Py_END_ALLOW_THREADS

  if (intAttrs) {
    myFree(intAttrs);

  }

  if (selectors) {
    myFree(selectors);
  }
  return MQRETURN(compCode, reasonCode);
}

/* Publish/subscribe - Hannes Wagener 2011 */
static char ibmmqc_MQSUB__doc__[] =
"MQSUB(connectionHandle, sd, objectHandle) \
 \
Calls the MQI MQSUB(connectionHandle, subDesc, objectHandle) \
";

static PyObject * ibmmqc_MQSUB(PyObject *self, PyObject *args) {
  MQSD *subDescP;
  MQHOBJ subHandle;
  MQHOBJ objectHandle;
  MQLONG compCode, reasonCode;
  PyObject *rv;

  char *subDescBuffer;
  Py_ssize_t subDescBufferLength = 0;


  long lQmgrHandle;

  if (!PyArg_ParseTuple(args, "ly#l", &lQmgrHandle,
            &subDescBuffer, &subDescBufferLength,
            &objectHandle)) {
    return NULL;
  }
  if (checkArgSize(subDescBufferLength, PY_IBMMQ_SD_SIZEOF, "MQSD")) {
    return NULL;
  }

  subDescP = (MQSD *)subDescBuffer;

  Py_BEGIN_ALLOW_THREADS
  MQSUB((MQHCONN) lQmgrHandle, subDescP, &objectHandle, &subHandle,
    &compCode, &reasonCode);
  Py_END_ALLOW_THREADS

  rv = Py_BuildValue("(y#llll)", subDescP, PY_IBMMQ_SD_SIZEOF, objectHandle, subHandle,
             (long) compCode, (long) reasonCode);
  return rv;

}

static char ibmmqc_MQSUBRQ__doc__[] =
"MQSUBRQ(connectionHandle, subHandle, subAction, subRequestOptions) \
 \
Calls the MQI MQSUBRQ(connectionHandle, subHandle, subAction, subRequestOptions) \
";

static PyObject * ibmmqc_MQSUBRQ(PyObject *self, PyObject *args) {

  MQLONG compCode, reasonCode;
  MQSRO *sro;
  Py_ssize_t sroLength = 0;

  PyObject *rv;

  long lQmgrHandle;
  long lSubHandle;
  long subAction;

  if (!PyArg_ParseTuple(args, "llly#", &lQmgrHandle,&lSubHandle,&subAction,
            &sro,&sroLength)) {
    return NULL;
  }
  if (checkArgSize(sroLength, PY_IBMMQ_SRO_SIZEOF, "MQSRO")) {
    return NULL;
  }

  Py_BEGIN_ALLOW_THREADS
  MQSUBRQ((MQHCONN) lQmgrHandle, (MQHOBJ)lSubHandle, (MQLONG)subAction, sro, &compCode, &reasonCode);
  Py_END_ALLOW_THREADS

  rv = Py_BuildValue("(y#ll)", sro, PY_IBMMQ_SRO_SIZEOF, (long) compCode, (long) reasonCode);
  return rv;

}

static char ibmmqc_MQSTAT__doc__[] =
"MQSTAT(connectionHandle, statusType) \
 \
Calls the MQI MQSTAT(connectionHandle, statusType) \
";

static PyObject * ibmmqc_MQSTAT(PyObject *self, PyObject *args) {
  MQSTS *sts;
  Py_ssize_t stsLength = 0;
  MQLONG compCode, reasonCode;
  PyObject *rv;

  long lQmgrHandle;
  long lStatusType;

  if (!PyArg_ParseTuple(args, "lly#", &lQmgrHandle, &lStatusType, &sts,&stsLength)) {
    return NULL;
  }

  if (checkArgSize(stsLength, PY_IBMMQ_STS_SIZEOF, "MQSTS")) {
    return NULL;
  }

  Py_BEGIN_ALLOW_THREADS
  MQSTAT((MQHCONN) lQmgrHandle, (MQLONG)lStatusType, sts, &compCode, &reasonCode);
  Py_END_ALLOW_THREADS

  rv = Py_BuildValue("(y#ll)", sts, PY_IBMMQ_STS_SIZEOF, (long) compCode, (long) reasonCode);
  return rv;

}

/****************************************************************************************/
/* Asynchronous callback - MQCTL, MQCB                                                  */
/* Callback processing and registration always uses cbFunc_C as the known function given*/
/* to MQCB (ie called directly by the qmgr). This C function then always calls a known  */
/* Python function (cbFunc_Py) whose address is given via the CBINIT initialisation call*/
/* That Python function will then reformat the C parameters into Python classes and     */
/* finally invoke the real user-designated callback. And then it all unwinds.           */
/****************************************************************************************/
static PyObject *cbFunc_Py = NULL;
static void cbFunc_C(MQHCONN hc,MQMD *md,MQGMO *gmo,unsigned char *buf,MQCBC *cbc) {
    PyObject *result = NULL;
    PyObject *arglist = NULL;
    MQHOBJ realHObj;

    // Unstash the hObj from the CBC.ConnectionArea and pass it explicitly
    // to cope with the pre-943 issue where some callbacks are not
    // always given the right hObj
    if (cbc->Hobj < 1) {
      memcpy(&realHObj,&cbc->CallbackArea,sizeof(MQHOBJ));
      cbc->Hobj = realHObj;
    }

    PyGILState_STATE state = PyGILState_Ensure();

    if (cbFunc_Py) {
      arglist = Py_BuildValue("(ly#y#y#y#)",
                   (long)hc,
                   md,PY_IBMMQ_MD_SIZEOF,
                   gmo,PY_IBMMQ_GMO_SIZEOF,
                   (cbc->BufferLength>0)?buf:NULL,(int)cbc->BufferLength,
                   cbc, PY_IBMMQ_CBC_SIZEOF);

      result = PyObject_CallObject(cbFunc_Py,arglist);
      if (!result) {
        if (PyErr_Occurred()) {
          PyErr_PrintEx(0);
          PyErr_Clear();
        }
      }
    }

    if (arglist) {
      Py_DECREF(arglist);
    }

    PyGILState_Release(state);

    return;
}

static char ibmmqc_MQCBINIT__doc__[] =
"MQCBINIT(CBFunc) \
 \
An internal non-MQI call to setup how MQCB will work by passing a reference \
to the fixed Python proxy callback function. \
";

static PyObject * ibmmqc_MQCBINIT(PyObject *self, PyObject *args) {

  if (!PyArg_ParseTuple(args, "O",&cbFunc_Py)) {
    return NULL;
  }

  if (!PyCallable_Check(cbFunc_Py)) {
    PyErr_Format(ErrorObj,"Need a callable object.");
    return NULL;
  }

  return Py_None;
}

static char ibmmqc_MQCB__doc__[] =
"MQCB(connectionHandle, Operation, CallbackDesc, Hobj, MsgDesc, GetMsgOpts) \
 \
Calls the MQI MQCB(connectionHandle, Operation, CallbackDesc, Hobj, MsgDesc, GetMsgOpts) \
";

static PyObject * ibmmqc_MQCB(PyObject *self, PyObject *args) {

  MQLONG compCode, reasonCode;
  PyObject *rv;

  long lQmgrHandle;
  long lOperation;
  long lObjectHandle;

  MQHOBJ hObj;
  MQCBD *cbd;
  MQMD *md;
  MQGMO *gmo;
  Py_ssize_t cbdLength;
  Py_ssize_t mdLength;
  Py_ssize_t gmoLength;


  if (!PyArg_ParseTuple(args, "lly#ly#y#", &lQmgrHandle, &lOperation,
                                           &cbd,&cbdLength,
                                           &lObjectHandle,
                                           &md,&mdLength,
                                           &gmo,&gmoLength)
                                        ) {
    return NULL;
  }

  if (checkArgSize(gmoLength, PY_IBMMQ_GMO_SIZEOF, "MQGMO")) {
    return NULL;
  }

  if (checkArgSize(mdLength, PY_IBMMQ_MD_SIZEOF, "MQMD")) {
    return NULL;
  }

  if (checkArgSize(cbdLength, PY_IBMMQ_CBD_SIZEOF, "MQCBD")) {
    return NULL;
  }

  cbd->CallbackFunction = cbFunc_C;

  // Stash the hObj in the CBD so it is always available on the
  // callback - pre-943 client libraries had a bug that didn't
  // always get it right.
  hObj = (MQHOBJ)lObjectHandle;
  memcpy(&cbd->CallbackArea,&hObj,sizeof(MQHOBJ));

  Py_BEGIN_ALLOW_THREADS
  MQCB((MQHCONN) lQmgrHandle, (MQLONG)lOperation, cbd, (MQHOBJ)lObjectHandle, md, gmo, &compCode, &reasonCode);
  Py_END_ALLOW_THREADS

  rv = Py_BuildValue("(ll)", (long) compCode, (long) reasonCode);
  return rv;

}

static char ibmmqc_MQCTL__doc__[] =
"MQCTL(connectionHandle, operation, controlOptions) \
 \
Calls the MQI MQCTL(connectionHandle, operation, controlOptions) \
";

static PyObject * ibmmqc_MQCTL(PyObject *self, PyObject *args) {
  MQCTLO *ctlo;
  Py_ssize_t ctloLength = 0;

  MQLONG compCode, reasonCode;
  PyObject *rv;

  long lQmgrHandle;
  long lOperation;

  if (!PyArg_ParseTuple(args, "lly#", &lQmgrHandle, &lOperation, &ctlo,&ctloLength)) {
    return NULL;
  }

  if (checkArgSize(ctloLength, PY_IBMMQ_CTLO_SIZEOF, "MQCTLO")) {
    return NULL;
  }

  Py_BEGIN_ALLOW_THREADS
  MQCTL((MQHCONN) lQmgrHandle, (MQLONG)lOperation, ctlo, &compCode, &reasonCode);
  Py_END_ALLOW_THREADS

  rv = Py_BuildValue("(ll)", (long) compCode, (long) reasonCode);
  return rv;

}

/****************************************************************************************/
/* MQI calls that deal with message properties                                          */
/****************************************************************************************/
static char ibmmqc_MQCRTMH__doc__[] =
"MQCRTMH(conn_handle, cmho) \
 \
Calls the MQI's MQCRTMH function \
";

static PyObject* ibmmqc_MQCRTMH(PyObject *self, PyObject *args) {

  long lQmgrHandle;

  char *cmho_buffer;
  Py_ssize_t cmho_buffer_length = 0;

  MQCMHO *cmho;
  MQHMSG msg_handle = MQHM_UNUSABLE_HMSG;
  MQLONG compCode = MQCC_UNKNOWN, reasonCode = MQRC_NONE;

  PyObject *rv;

  if (!PyArg_ParseTuple(args, "ly#", &lQmgrHandle, &cmho_buffer, &cmho_buffer_length)) {
    return NULL;
  }

  if (checkArgSize(cmho_buffer_length, PY_IBMMQ_CMHO_SIZEOF, "MQCMHO")) {
    return NULL;
  }

  cmho = (MQCMHO *)cmho_buffer;

  Py_BEGIN_ALLOW_THREADS
  MQCRTMH((MQHCONN)lQmgrHandle, cmho, &msg_handle, &compCode, &reasonCode);
  Py_END_ALLOW_THREADS

  rv = Py_BuildValue("(Lll)", msg_handle, (long)compCode, (long)reasonCode);

  return rv;
}

static char ibmmqc_MQDLTMH__doc__[] =
"MQDLTMH(conn_handle, dmho) \
 \
Calls the MQI's MQDLTMH function \
";

static PyObject* ibmmqc_MQDLTMH(PyObject *self, PyObject *args) {

  long lQmgrHandle;

  PMQDMHO dmho;
  Py_ssize_t dmho_length = 0;

  MQHMSG msg_handle = MQHM_UNUSABLE_HMSG;
  MQLONG compCode = MQCC_UNKNOWN, reasonCode = MQRC_NONE;

  if (!PyArg_ParseTuple(args, "lLy#", &lQmgrHandle, &msg_handle,&dmho, &dmho_length)) {
    return NULL;
  }

  if (checkArgSize(dmho_length, PY_IBMMQ_DMHO_SIZEOF, "MQDMHO")) {
    return NULL;
  }

  Py_BEGIN_ALLOW_THREADS
  MQDLTMH((MQHCONN)lQmgrHandle, &msg_handle, dmho, &compCode, &reasonCode);
  Py_END_ALLOW_THREADS

  return MQRETURN(compCode, reasonCode);

}

static char ibmmqc_MQSETMP__doc__[] =
"MQSETMP(conn_handle, msg_handle, smpo, name, pd, type, value, value_length) \
 \
Calls the MQI's MQSETMP function \
";

static PyObject* ibmmqc_MQSETMP(PyObject *self, PyObject *args) {

  long lQmgrHandle = MQHC_UNUSABLE_HCONN;
  MQHMSG msg_handle = MQHM_UNUSABLE_HMSG;

  MQSMPO *smpo;
  char *smpo_buffer;
  Py_ssize_t smpo_buffer_length = 0;

  MQPD *pd;
  char *pd_buffer;
  Py_ssize_t pd_buffer_length = 0;

  MQCHARV name = {MQCHARV_DEFAULT};
  char *property_name;
  Py_ssize_t property_name_length = 0;

  long lPropertyType;
  MQLONG property_type;

  MQLONG compCode = MQCC_UNKNOWN;
  MQLONG reasonCode = MQRC_NONE;

  void *value = NULL;
  Py_ssize_t value_length = 0;

  PyObject *property_value_object;
  PyObject *v = NULL;

  if (!PyArg_ParseTuple(args, "lLy#y#y#lOl",
                              &lQmgrHandle, &msg_handle,
                              &smpo_buffer, &smpo_buffer_length,
                              &property_name, &property_name_length,
                              &pd_buffer, &pd_buffer_length,
                              &lPropertyType, &property_value_object, &value_length)) {
    return NULL;
  }

  property_type = (MQLONG)lPropertyType;

  if (property_name_length <= 0) {
    property_name_length = strlen(property_name);
  }

  Py_ssize_t property_value_free = 0;

  switch(property_type){
    /* Boolean value */
    case MQTYPE_BOOLEAN:
      value = myAlloc(sizeof(MQBOOL),"property value");
      if (!value) {
        return NULL;
      }
      value_length = sizeof(MQBOOL);

      property_value_free = 1;
      *(PMQBOOL)value = (MQBOOL)PyFloat_AsDouble(property_value_object);
      break;

    /* Byte-string value */
    case MQTYPE_BYTE_STRING:
      value = PyBytes_AsString(property_value_object);
      break;

    /* 8-bit integer value */
    case MQTYPE_INT8:
      value = myAlloc(sizeof(MQINT8),"property value");
      if (!value) {
        return NULL;
      }
      value_length = sizeof(MQINT8);
      property_value_free = 1;
      *(PMQINT8)value = (MQINT8)PyLong_AsLong(property_value_object);
      break;

    /* 16-bit integer value */
    case MQTYPE_INT16:
      value = myAlloc(sizeof(MQINT16),"property value");
      if (!value) {
        return NULL;
      }
      value_length = sizeof(MQINT16);
      property_value_free = 1;
      *(PMQINT16)value = (MQINT16)PyLong_AsLong(property_value_object);
      break;

    /* 32-bit integer value */
    case MQTYPE_INT32:{
      value = myAlloc(sizeof(MQINT32),"property value");
      if (!value) {
        return NULL;
      }
      value_length = sizeof(MQINT32);
      property_value_free = 1;
      *(PMQINT32)value = (MQINT32)PyLong_AsLongLong(property_value_object);
      break;
    }

    /* 64-bit integer value */
    case MQTYPE_INT64:
      value = myAlloc(sizeof(MQINT64),"property value");
      if (!value) {
        return NULL;
      }
      value_length = sizeof(MQINT64);
      property_value_free = 1;
      *(PMQINT64)value = (MQINT64)PyLong_AsLongLong(property_value_object);
      break;


    /* String value */
    case MQTYPE_STRING:
      v = PyUnicode_AsEncodedString(property_value_object,"utf-8","ignore");
      value = PyBytes_AsString(v);
      break;

    /* 32-bit floating-point number value */
    case MQTYPE_FLOAT32:
      value = myAlloc(sizeof(MQFLOAT32),"property value");
      if (!value) {
        return NULL;
      }
      value_length = sizeof(MQFLOAT32);
      property_value_free = 1;
      *(PMQFLOAT32)value = (MQFLOAT32)PyFloat_AsDouble(property_value_object);
      break;

    /* 64-bit floating-point number value */
    case MQTYPE_FLOAT64:
      value = myAlloc(sizeof(MQFLOAT64),"property value");
      if (!value) {
        return NULL;
      }
      value_length = sizeof(MQFLOAT64);
      property_value_free = 1;
      *(PMQFLOAT64)value = (MQFLOAT64)PyFloat_AsDouble(property_value_object);
      break;

    /* without value */
    case MQTYPE_NULL:
      value = NULL;
      value_length = 0;
      break;
  }

  if (checkArgSize(smpo_buffer_length, PY_IBMMQ_SMPO_SIZEOF, "MQSMPO")) {
    return NULL;
  }
  smpo = (MQSMPO *)smpo_buffer;

  if (checkArgSize(pd_buffer_length, PY_IBMMQ_PD_SIZEOF, "MQPD")) {
    return NULL;
  }
  pd = (MQPD *)pd_buffer;

  name.VSPtr = property_name;
  name.VSLength = (MQLONG)property_name_length;

  Py_BEGIN_ALLOW_THREADS
  MQSETMP((MQHCONN)lQmgrHandle, msg_handle, smpo, &name, pd, property_type, (MQLONG)value_length,
            value, &compCode, &reasonCode);
  Py_END_ALLOW_THREADS

  if (v) {
    Py_DECREF(v);
  }

  if (property_value_free){
    myFree(value);
  }

  return MQRETURN(compCode,reasonCode);

}


static char ibmmqc_MQINQMP__doc__[] =
"MQINQMP(conn_handle, msg_handle, smpo, name, pd, type, value_length) \
 \
Calls the MQI's MQINQMP function \
";

static PyObject* ibmmqc_MQINQMP(PyObject *self, PyObject *args) {

  MQLONG compCode = MQCC_UNKNOWN, reasonCode = MQRC_NONE;

  long lQmgrHandle = MQHC_UNUSABLE_HCONN;
  MQHMSG msg_handle = MQHM_UNUSABLE_HMSG;

  MQCHARV name = {MQCHARV_DEFAULT};
  size_t vsbufsize = 10240; // The longest property name could be 10K

  char *property_name = NULL;
  Py_ssize_t property_name_length = 0;

  MQPD *pd;
  long pd_length;

  long lPropertyType;
  MQLONG property_type;
  MQLONG data_length;
  long value_length;

  MQIMPO *impo;
  long impo_length;

  PyObject *rv;

  if (!PyArg_ParseTuple(args, "lLy#y#y#ll",
                        &lQmgrHandle, &msg_handle,
                        &impo, &impo_length,
                        &property_name, &property_name_length,
                        &pd, &pd_length,
                        &lPropertyType, &value_length)) {
    return NULL;
  }

  property_type = (MQLONG)lPropertyType;
  name.VSPtr = property_name;
  name.VSLength = (MQLONG)property_name_length;

  // We know that the property_name is null-terminated because of
  // how Python passes the value. Only ask for the name if a wildcard
  // is in play.
  if (strchr(property_name,'%')) {
    impo->ReturnedName.VSPtr = myAlloc(vsbufsize,"property name");
    if (!impo->ReturnedName.VSPtr) {
      return NULL;
    }
    impo->ReturnedName.VSCCSID = MQCCSI_APPL;
    impo->ReturnedName.VSLength = 0;
    impo->ReturnedName.VSBufSize = (MQLONG)vsbufsize;
  }

  void *value = NULL;
  value = (PMQBYTE)myAlloc(value_length,"property value");
  if (!value) {
      return NULL;
  }

  MQINQMP((MQHCONN)lQmgrHandle, msg_handle, impo, &name, pd, &property_type, value_length,
    value, &data_length, &compCode, &reasonCode);

  MQLONG return_length;
  if (value_length > data_length)
    return_length = data_length;
  else
    return_length = value_length;

  switch(property_type){
    /* Boolean value */
    case MQTYPE_BOOLEAN:
      rv = Py_BuildValue("(ils#ll)",
            *(MQBOOL*)value,
            (long)data_length,
                        impo->ReturnedName.VSPtr,(Py_ssize_t)impo->ReturnedName.VSLength,

            (long)compCode, (long)reasonCode);
      break;

    /* Byte-string value */
    case MQTYPE_BYTE_STRING:
      rv = Py_BuildValue("(y#ls#ll)",
            (PMQBYTE)value, (Py_ssize_t)return_length,
            (long)data_length,
                        impo->ReturnedName.VSPtr,(Py_ssize_t)impo->ReturnedName.VSLength,

            (long)compCode, (long)reasonCode);
       break;

    /* 8-bit integer value */
    case MQTYPE_INT8:
      rv = Py_BuildValue("(bls#ll)",
            *(PMQINT8)value,
            (long)data_length,
                        impo->ReturnedName.VSPtr,(Py_ssize_t)impo->ReturnedName.VSLength,

            (long)compCode, (long)reasonCode
          );
      break;

    /* 16-bit integer value */
    case MQTYPE_INT16:
      rv = Py_BuildValue("(hls#ll)",
            *(PMQINT16)value,
            (long)data_length,
            impo->ReturnedName.VSPtr,(Py_ssize_t)impo->ReturnedName.VSLength,
            (long)compCode, (long)reasonCode
          );
      break;

    /* 32-bit integer value */
    case MQTYPE_INT32:
      rv = Py_BuildValue("(ils#ll)",
            *(PMQINT32)value,
            (long)data_length,
                        impo->ReturnedName.VSPtr,(Py_ssize_t)impo->ReturnedName.VSLength,

            (long)compCode, (long)reasonCode
          );
      break;

    /* 64-bit integer value */
    case MQTYPE_INT64:
      rv = Py_BuildValue("(Lls#ll)",
            *(PMQINT64)value,
            (long)data_length,
                        impo->ReturnedName.VSPtr,(Py_ssize_t)impo->ReturnedName.VSLength,

            (long)compCode, (long)reasonCode
          );
      break;

    /* 32-bit floating-point number value */
    case MQTYPE_FLOAT32:
      rv = Py_BuildValue("(fls#ll)",
            *(PMQFLOAT32)value,
            (long)data_length,
                        impo->ReturnedName.VSPtr,(Py_ssize_t)impo->ReturnedName.VSLength,

            (long)compCode, (long)reasonCode);
      break;

    /* 64-bit floating-point number value */
    case MQTYPE_FLOAT64:
      rv = Py_BuildValue("(dls#ll)",
            *(PMQFLOAT64)value,
            (long)data_length,
            impo->ReturnedName.VSPtr,(Py_ssize_t)impo->ReturnedName.VSLength,

            (long)compCode, (long)reasonCode);
      break;

    /* String value */
    case MQTYPE_STRING:
      rv = Py_BuildValue("(s#ls#ll)",
            (PMQCHAR)value, (Py_ssize_t)return_length,
            (long)data_length,
            impo->ReturnedName.VSPtr,(Py_ssize_t)impo->ReturnedName.VSLength,
            (long)compCode, (long)reasonCode);
      break;

    /* NULL value */
    case MQTYPE_NULL:
      rv = Py_BuildValue("(sls#ll)",
            NULL,
            (long)data_length,
            impo->ReturnedName.VSPtr,(Py_ssize_t)impo->ReturnedName.VSLength,
            (long)compCode, (long)reasonCode);
      break;

    default:
      rv = Py_BuildValue("(sls#ll)",
            NULL,
            (long)data_length,
            impo->ReturnedName.VSPtr,(Py_ssize_t)impo->ReturnedName.VSLength,
            (long)compCode, (long)reasonCode);
      break;
  }

  if (impo->ReturnedName.VSPtr) {
    myFree(impo->ReturnedName.VSPtr);
  }
  myFree(value);

  return rv;
}

static char ibmmqc_MQDLTMP__doc__[] =
"MQDLTMP(conn_handle, msg_handle, dmpo, name) \
 \
Calls the MQI's MQDLTMP function \
";

static PyObject* ibmmqc_MQDLTMP(PyObject *self, PyObject *args) {

  MQLONG compCode = MQCC_UNKNOWN, reasonCode = MQRC_NONE;

  long lQmgrHandle = MQHC_UNUSABLE_HCONN;
  MQHMSG msg_handle = MQHM_UNUSABLE_HMSG;
  MQDMPO *dmpo = NULL;
  Py_ssize_t dmpo_length = 0;

  MQCHARV name = {MQCHARV_DEFAULT};

  char *property_name;
  Py_ssize_t property_name_length = 0;

  if (!PyArg_ParseTuple(args, "lLy#y#",
                        &lQmgrHandle, &msg_handle,
                        &dmpo, &dmpo_length,
                        &property_name, &property_name_length)) {
    return NULL;
  }

  name.VSPtr = property_name;
  name.VSLength = (MQLONG)property_name_length;

  MQDLTMP((MQHCONN)lQmgrHandle, msg_handle, dmpo, &name, &compCode, &reasonCode);

  return MQRETURN(compCode,reasonCode);
}

/* List of methods defined and exported in the module */
static struct PyMethodDef ibmmqc_methods[] = {
  {"MQLOGCF", (PyCFunction)ibmmqc_MQLOGCF,    METH_VARARGS, ibmmqc_MQLOGCF__doc__},

  {"MQCONN", (PyCFunction)ibmmqc_MQCONN,    METH_VARARGS, ibmmqc_MQCONN__doc__},
  {"MQCONNX", (PyCFunction)ibmmqc_MQCONNX, METH_VARARGS, ibmmqc_MQCONNX__doc__},
  {"MQDISC", (PyCFunction)ibmmqc_MQDISC,    METH_VARARGS, ibmmqc_MQDISC__doc__},
  {"MQOPEN", (PyCFunction)ibmmqc_MQOPEN,    METH_VARARGS, ibmmqc_MQOPEN__doc__},
  {"MQCLOSE", (PyCFunction)ibmmqc_MQCLOSE, METH_VARARGS, ibmmqc_MQCLOSE__doc__},
  {"MQPUT", (PyCFunction)ibmmqc_MQPUT, METH_VARARGS, ibmmqc_MQPUT__doc__},
  {"MQPUT1", (PyCFunction)ibmmqc_MQPUT1, METH_VARARGS, ibmmqc_MQPUT1__doc__},
  {"MQGET", (PyCFunction)ibmmqc_MQGET, METH_VARARGS, ibmmqc_MQGET__doc__},

  {"MQBEGIN", (PyCFunction)ibmmqc_MQBEGIN, METH_VARARGS, ibmmqc_MQBEGIN__doc__},
  {"MQCMIT", (PyCFunction)ibmmqc_MQCMIT, METH_VARARGS, ibmmqc_MQCMIT__doc__},
  {"MQBACK", (PyCFunction)ibmmqc_MQBACK, METH_VARARGS, ibmmqc_MQBACK__doc__},

  {"MQINQ", (PyCFunction)ibmmqc_MQINQ, METH_VARARGS, ibmmqc_MQINQ__doc__},
  {"MQSET", (PyCFunction)ibmmqc_MQSET, METH_VARARGS, ibmmqc_MQSET__doc__},

  {"MQSUB", (PyCFunction)ibmmqc_MQSUB, METH_VARARGS, ibmmqc_MQSUB__doc__},
  {"MQSUBRQ", (PyCFunction)ibmmqc_MQSUBRQ, METH_VARARGS, ibmmqc_MQSUBRQ__doc__},
  {"MQSTAT", (PyCFunction)ibmmqc_MQSTAT, METH_VARARGS, ibmmqc_MQSTAT__doc__},

  {"MQCB", (PyCFunction)ibmmqc_MQCB, METH_VARARGS, ibmmqc_MQCB__doc__},
  {"MQCTL", (PyCFunction)ibmmqc_MQCTL, METH_VARARGS, ibmmqc_MQCTL__doc__},
  {"MQCBINIT", (PyCFunction)ibmmqc_MQCBINIT, METH_VARARGS, ibmmqc_MQCBINIT__doc__},

  {"MQCRTMH", (PyCFunction)ibmmqc_MQCRTMH, METH_VARARGS, ibmmqc_MQCRTMH__doc__},
  {"MQDLTMH", (PyCFunction)ibmmqc_MQDLTMH, METH_VARARGS, ibmmqc_MQDLTMH__doc__},
  {"MQSETMP", (PyCFunction)ibmmqc_MQSETMP, METH_VARARGS, ibmmqc_MQSETMP__doc__},
  {"MQINQMP", (PyCFunction)ibmmqc_MQINQMP, METH_VARARGS, ibmmqc_MQINQMP__doc__},
  {"MQDLTMP", (PyCFunction)ibmmqc_MQDLTMP, METH_VARARGS, ibmmqc_MQDLTMP__doc__},

  {NULL, (PyCFunction)NULL, 0, NULL}        /* sentinel */
};

static char ibmmqc_module_documentation[] = "";

/* Module description                    */
static struct PyModuleDef ibmmqc_module = {
    PyModuleDef_HEAD_INIT,
    "ibmmqc",
    ibmmqc_module_documentation,
    -1,
    ibmmqc_methods
};

/* Initialization function for the module */
/* Everything else should be 'static'     */
PyMODINIT_FUNC PyInit_ibmmqc(void) {
  int localError = FALSE;
  PyObject *m, *d, *v;

  /* Create the module and add the functions */
  m = PyModule_Create(&ibmmqc_module);

  /* Add some symbolic constants to the module */
  d = PyModule_GetDict(m);
  ErrorObj = PyErr_NewException("ibmmqc.error", NULL, NULL);
  PyDict_SetItemString(d, "ibmmqc.error", ErrorObj);

  /*
   * Setup features. The version is added to the ibmmqc dict so
   * that the Python module can check consistency.
   */
  PyDict_SetItemString(d, "__doc__", PyUnicode_FromString(ibmmqc_doc));
  PyDict_SetItemString(d,"__version__", PyUnicode_FromString(__version__));
  PyDict_SetItemString(d,"__cmdlevel__", PyLong_FromLong((long)MQCMDL_CURRENT_LEVEL));

  /* Create a dict for structure versions that we're built against.
   * Not all MQI structures have versions. On the other hand, some of
   * the structures are ones we might not care about for applications. But since this list
   * is auto-generated, it's not going to do any harm to have extras here. The ifdefs are needed
   * to protect against new structures that are not known at all in older versions of MQ.
   */
  v = PyModule_GetDict(m);
#if defined(MQBNO_CURRENT_VERSION)
  PyDict_SetItemString(v,"bno", PyLong_FromLong((long)MQBNO_CURRENT_VERSION));
#endif
#if defined(MQCD_CURRENT_VERSION)
  PyDict_SetItemString(v,"cd", PyLong_FromLong((long)MQCD_CURRENT_VERSION));
#endif
#if defined(MQCFH_CURRENT_VERSION)
  PyDict_SetItemString(v,"cfh", PyLong_FromLong((long)MQCFH_CURRENT_VERSION));
#endif
#if defined(MQCMHO_CURRENT_VERSION)
  PyDict_SetItemString(v,"cmho", PyLong_FromLong((long)MQCMHO_CURRENT_VERSION));
#endif
#if defined(MQCNO_CURRENT_VERSION)
  PyDict_SetItemString(v,"cno", PyLong_FromLong((long)MQCNO_CURRENT_VERSION));
#endif
#if defined(MQCSP_CURRENT_VERSION)
  PyDict_SetItemString(v,"csp", PyLong_FromLong((long)MQCSP_CURRENT_VERSION));
#endif
#if defined(MQCBC_CURRENT_VERSION)
  PyDict_SetItemString(v,"cbc", PyLong_FromLong((long)MQCBC_CURRENT_VERSION));
#endif
#if defined(MQCBD_CURRENT_VERSION)
  PyDict_SetItemString(v,"cbd", PyLong_FromLong((long)MQCBD_CURRENT_VERSION));
#endif
#if defined(MQCIH_CURRENT_VERSION)
  PyDict_SetItemString(v,"cih", PyLong_FromLong((long)MQCIH_CURRENT_VERSION));
#endif
#if defined(MQCTLO_CURRENT_VERSION)
  PyDict_SetItemString(v,"ctlo", PyLong_FromLong((long)MQCTLO_CURRENT_VERSION));
#endif
#if defined(MQDLH_CURRENT_VERSION)
  PyDict_SetItemString(v,"dlh", PyLong_FromLong((long)MQDLH_CURRENT_VERSION));
#endif
#if defined(MQGMO_CURRENT_VERSION)
  PyDict_SetItemString(v,"gmo", PyLong_FromLong((long)MQGMO_CURRENT_VERSION));
#endif
#if defined(MQIIH_CURRENT_VERSION)
  PyDict_SetItemString(v,"iih", PyLong_FromLong((long)MQIIH_CURRENT_VERSION));
#endif
#if defined(MQIMPO_CURRENT_VERSION)
  PyDict_SetItemString(v,"impo", PyLong_FromLong((long)MQIMPO_CURRENT_VERSION));
#endif
#if defined(MQMD_CURRENT_VERSION)
  PyDict_SetItemString(v,"md", PyLong_FromLong((long)MQMD_CURRENT_VERSION));
#endif
#if defined(MQMDE_CURRENT_VERSION)
  PyDict_SetItemString(v,"mde", PyLong_FromLong((long)MQMDE_CURRENT_VERSION));
#endif
#if defined(MQOD_CURRENT_VERSION)
  PyDict_SetItemString(v,"od", PyLong_FromLong((long)MQOD_CURRENT_VERSION));
#endif
#if defined(MQPD_CURRENT_VERSION)
  PyDict_SetItemString(v,"pd", PyLong_FromLong((long)MQPD_CURRENT_VERSION));
#endif
#if defined(MQPMO_CURRENT_VERSION)
  PyDict_SetItemString(v,"pmo", PyLong_FromLong((long)MQPMO_CURRENT_VERSION));
#endif
#if defined(MQSCO_CURRENT_VERSION)
  PyDict_SetItemString(v,"sco", PyLong_FromLong((long)MQSCO_CURRENT_VERSION));
#endif
#if defined(MQSD_CURRENT_VERSION)
  PyDict_SetItemString(v,"sd", PyLong_FromLong((long)MQSD_CURRENT_VERSION));
#endif
#if defined(MQSMPO_CURRENT_VERSION)
  PyDict_SetItemString(v,"smpo", PyLong_FromLong((long)MQSMPO_CURRENT_VERSION));
#endif
#if defined(MQDMPO_CURRENT_VERSION)
  PyDict_SetItemString(v,"dmpo", PyLong_FromLong((long)MQDMPO_CURRENT_VERSION));
#endif
#if defined(MQDMHO_CURRENT_VERSION)
  PyDict_SetItemString(v,"dmho", PyLong_FromLong((long)MQDMHO_CURRENT_VERSION));
#endif
#if defined(MQSRO_CURRENT_VERSION)
  PyDict_SetItemString(v,"sro", PyLong_FromLong((long)MQSRO_CURRENT_VERSION));
#endif
#if defined(MQSTS_CURRENT_VERSION)
  PyDict_SetItemString(v,"sts", PyLong_FromLong((long)MQSTS_CURRENT_VERSION));
#endif
#if defined(MQTMC_CURRENT_VERSION)
  // This constant is defined as a string in the MQI headers. So we hardcode the equivalent int, as it's
  // unlikely to change.
  PyDict_SetItemString(v,"tmc", PyLong_FromLong((long)2));
#endif
#if defined(MQTM_CURRENT_VERSION)
  PyDict_SetItemString(v,"tm", PyLong_FromLong((long)MQTM_CURRENT_VERSION));
#endif
#if defined(MQXQH_CURRENT_VERSION)
  PyDict_SetItemString(v,"xqh", PyLong_FromLong((long)MQXQH_CURRENT_VERSION));
#endif

  // And now add this map to the parent object
  PyDict_SetItemString(d,"__strucversions__", v);
  // Py_XDECREF(v);

  /*
   * Set the client/server build flag - always "common" now as there is no
   * distinction in the build mode. But there might be code that tries to
   * look at this reserved field.
   */
  PyDict_SetItemString(d,"__mqbuild__", PyUnicode_FromString("common"));

  /* Create the Map where we will store information about message buffers
   * for MQGETs. The map is never explicitly destroyed as there's no suitable
   * "terminate" call to this layer.
   */
  if (!getBufferMap) {
    getBufferMap = map_create();
  }

  if (!getBufferMap) {
    localError = TRUE;
  }

  /* Check for errors */
  if (PyErr_Occurred() || localError)
    Py_FatalError("can't initialize module ibmmqc");

  return m;

}

/*********************************************************/
/* Implementation of a Map collection. Only a subset     */
/* of operations is required (eg no "destroy")           */
/*********************************************************/

/*Hash function for string keys (djb2 algorithm) */
static unsigned long map_hash(const char *str) {
  unsigned long hash = 5381;
  int c;
  while ((c = *str++)) {
    hash = ((hash << 5) + hash) + c; /* hash * 33 + c */
  }
  return hash;
}

/* Resize the map when load factor is exceeded */
static int map_resize(Map *map) {
  size_t old_capacity = map->capacity;
  MapEntry **old_buckets = map->buckets;

  map->capacity *= 2;
  map->buckets = (MapEntry **)myAlloc(sizeof(MapEntry *) * map->capacity, "map buckets");

  if (!map->buckets) {
    map->buckets = old_buckets;
    map->capacity = old_capacity;
    return -1;
  }

  for (size_t i = 0; i < map->capacity; i++) {
    map->buckets[i] = NULL;
  }

  /* Rehash all entries */
  for (size_t i = 0; i < old_capacity; i++) {
    MapEntry *entry = old_buckets[i];
    while (entry) {
      MapEntry *next = entry->next;
      unsigned long hash = map_hash(entry->key);
      size_t index = hash % map->capacity;

      entry->next = map->buckets[index];
      map->buckets[index] = entry;

      entry = next;
    }
  }

  myFree(old_buckets);
  return 0;
}

/* Create a new map with initial capacity. This has to be called in an environment
 * where we don't need the map's own lock, but can ensure it's only called once.
 */
static Map* map_create(void) {
  Map *map = (Map *)myAlloc(sizeof(Map), "map structure");
  if (!map) {
    return NULL;
  }

  map->capacity = MAP_INITIAL_CAPACITY;
  map->size = 0;
  map->buckets = (MapEntry **)myAlloc(sizeof(MapEntry *) * map->capacity, "map buckets");

  if (!map->buckets) {
    myFree(map);
    return NULL;
  }

  for (size_t i = 0; i < map->capacity; i++) {
    map->buckets[i] = NULL;
  }

  /* Initialize mutex */
#ifdef _WIN32
  InitializeCriticalSection(&map->mutex);
#else
   if (pthread_mutex_init(&map->mutex, NULL) != 0) {
    myFree(map->buckets);
    myFree(map);
    return NULL;
  }
#endif

  return map;
}

/*
 * Insert or update a key-value pair in the map
 * Returns 0 on success, -1 on failure
 */
static int map_put(Map *map, const char *key, void *value) {

  debug(1, "map_put for %s value %p",key,value);
  if (!map || !key) {
    return -1;
  }

  /* Check if we need to resize */
  if ((double)map->size / map->capacity > MAP_LOAD_FACTOR) {
    if (map_resize(map) != 0) {
        return -1;
    }
  }

  unsigned long hash = map_hash(key);
  size_t index = hash % map->capacity;

  /* Check if key already exists */
  MapEntry *entry = map->buckets[index];
  while (entry) {
    if (strcmp(entry->key, key) == 0) {
      /* Update existing value */
      entry->value = value;
      return 0;
    }
    entry = entry->next;
  }

  /* Create new entry */
  MapEntry *new_entry = (MapEntry *)myAlloc(sizeof(MapEntry), "map entry");
  if (!new_entry) {
    return -1;
  }

  new_entry->key = (char *)myAlloc(strlen(key) + 1, "map key");
  if (!new_entry->key) {
    myFree(new_entry);
    return -1;
  }

  strcpy(new_entry->key, key);
  new_entry->value = value;
  new_entry->next = map->buckets[index];
  map->buckets[index] = new_entry;
  map->size++;

  return 0;
}

/*
 * Get a value from the map by key. Returns the value or NULL if not found
 */
static void* map_get(Map *map, const char *key) {
  if (!map || !key) {
    return NULL;
  }

  unsigned long hash = map_hash(key);
  size_t index = hash % map->capacity;

  MapEntry *entry = map->buckets[index];
  while (entry) {
    if (strcmp(entry->key, key) == 0) {
        return entry->value;
    }
    entry = entry->next;
  }

  return NULL;
}


/*
 * Remove a key-value pair from the map
 * Returns 0 on success, -1 if key not found
 */
static int map_remove(Map *map, const char *key) {

  if (!map || !key) {
    return -1;
  }

  unsigned long hash = map_hash(key);
  size_t index = hash % map->capacity;

  MapEntry *entry = map->buckets[index];
  MapEntry *prev = NULL;

  while (entry) {
    if (strncmp(entry->key, key, strlen(key)) == 0) {
      if (prev) {
        prev->next = entry->next;
      } else {
        map->buckets[index] = entry->next;
      }

      myFree(entry->key);
      if (entry->value) {
        /* We know the "value" was a malloced block, so can be freed here */
        myFree(entry->value);
      }
      myFree(entry);

      map->size--;
      return 0;
    }
    prev = entry;
    entry = entry->next;
  }

  return -1;

}

/* Lock the map mutex. Returns 0 on success, -1 on failure */
static int map_lock(Map *map) {
  if (!map) {
    return -1;
  }

#ifdef _WIN32
  EnterCriticalSection(&map->mutex);
  return 0;
#else
  if (pthread_mutex_lock(&map->mutex) == 0) {
    return 0;
  }
  return -1;
#endif
}

/* Unlock the map mutex. Returns 0 on success, -1 on failure  */
static int map_unlock(Map *map) {
  if (!map) {
    return -1;
  }

#ifdef _WIN32
  LeaveCriticalSection(&map->mutex);
  return 0;
#else
  if (pthread_mutex_unlock(&map->mutex) == 0) {
    return 0;
  }
  return -1;
#endif
}
