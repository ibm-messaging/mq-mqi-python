# More examples are at https://github.com/ibm-messaging/mq-dev-patterns
# and in code/examples in the source distribution.

"""
This example looks at the installed packages on an RPM-based Linux
machine and displays information about the MQ Client, if it is installed
using the default package name.
"""

import logging

import rpm

logging.basicConfig(level=logging.INFO)

package_name = 'MQSeriesClient'

ts = rpm.TransactionSet()
mi = ts.dbMatch('name', package_name)

if not mi.count():
    logging.info('Did not find package `%s` in RPM database.',package_name)
else:
    for header in mi:
        version = header['version']
        logging.info('Found package `%s`, version `%s`.',package_name, version)
