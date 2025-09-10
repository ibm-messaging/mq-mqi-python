# More examples are at https://github.com/ibm-messaging/mq-dev-patterns
# and in code/examples in the source distribution.

"""
This example shows how to interrogate the Windows registry to determine
which version of MQ is installed
"""

import logging
import _winreg

logging.basicConfig(level=logging.INFO)

# Even though the product has changed names a few times, this key is still maintained
key_name = 'Software\\IBM\\MQSeries\\CurrentVersion'

try:
    key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, key_name)
except WindowsError:
    logging.info('Could not find IBM MQ-related information in Windows registry.')
else:
    version = _winreg.QueryValueEx(key, 'VRMF')[0]
    logging.info('IBM MQ version is `%s`.', version)
