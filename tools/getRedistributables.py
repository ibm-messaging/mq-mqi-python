# Download and extract the MQ packages that support building
# wheels on MacOS, Windows and Linux.
#
# Pass the source URL as the first argument and the destination directory
# as the second argument.
#
# The source URL should end with .tar.gz (Linux) or .zip (Windows) or .pkg (MacOS)
#
import os
import sys
import tarfile
import zipfile

import requests

if len(sys.argv) != 3:
    print("Usage: this_script.py <source_url> <destination_path>")
    sys.exit(1)

SOURCE_URL = sys.argv[1]
# This is a directory
DESTINATION_PATH = sys.argv[2]

# And we actually download to a file whose name starts with the destination directory
if SOURCE_URL.endswith('.tar.gz'):
    temp_path = DESTINATION_PATH + '-temp.tar.gz'
elif SOURCE_URL.endswith('.zip'):
    temp_path = DESTINATION_PATH + '-temp.zip'
elif SOURCE_URL.endswith('.pkg'):
    temp_path = DESTINATION_PATH + '-temp.pkg'
else:
    print("Unsupported archive format")
    sys.exit(1)

if os.path.exists(DESTINATION_PATH):
    print(
        f"Destination path {DESTINATION_PATH} already exists. "
        "Remove it to use this script.")
    sys.exit(1)

_CHUNK_SIZE = 64 * 1024


def download_file(source_url, destination_path):
    with requests.get(source_url, stream=True) as r:
        r.raise_for_status()
        with open(destination_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=_CHUNK_SIZE):
                f.write(chunk)

def extract_archive(archive_path, extract_to):
    if archive_path.endswith('.tar.gz'):
        with tarfile.open(archive_path, 'r:gz') as tar:
            tar.extractall(path=extract_to)
    elif archive_path.endswith('.zip'):
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
    else:
        raise ValueError("Unsupported archive format")


# If it's a .pkg file, that's for MacOS which we do not unpack here.
# Instead, it'll be installed properly by the calling environment.
print(f'Downloading "{SOURCE_URL}" to {temp_path}' )
download_file(SOURCE_URL, temp_path)
if not SOURCE_URL.endswith('.pkg'):
    print(f'Extracting files from {temp_path} to {DESTINATION_PATH}')
    extract_archive(temp_path, DESTINATION_PATH)
    os.unlink(temp_path)
print(f'Done via "{temp_path}"')
