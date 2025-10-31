# Download and extract the redistributable package to support building
# the wheels on Windows and Linux.
#
# Pass the source URL as the first argument and the destination directory
# as the second argument.
#
# The source URL should end with .tar.gz or .zip
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
DESTINATION_PATH = sys.argv[2]

if SOURCE_URL.endswith('.tar.gz'):
    temp_path = DESTINATION_PATH + '-temp.tar.gz'
elif SOURCE_URL.endswith('.zip'):
    temp_path = DESTINATION_PATH + '-temp.zip'
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


print(f'Downloading "{SOURCE_URL}" to "{DESTINATION_PATH}"')
download_file(SOURCE_URL, temp_path)
extract_archive(temp_path, DESTINATION_PATH)
os.unlink(temp_path)
print(f'Done via "{temp_path}"')
