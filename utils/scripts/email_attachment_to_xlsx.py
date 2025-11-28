"""
Converts email attachments from base64 encoded plaintext files to binary xlsx
file.

MVJ saves emails in plaintext format in a temporary directory, if a file-based
email backend is configured. You can find the email directory e.g. from Django's
settings.EMAIL_FILE_PATH
"""

import base64
import logging
import os
import re
import sys

logger = logging.getLogger(__name__)
stdout_handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(stdout_handler)
logger.setLevel(logging.INFO)

# Get filename from command line argument
if len(sys.argv) < 2:
    logger.info(f"Usage: python {os.path.relpath(__file__)}  <log_filepath>")
    sys.exit(1)

EMAIL_FILEPATH = sys.argv[1]

# Read file
with open(EMAIL_FILEPATH, "r") as input_file:
    email_file = input_file.read()

logger.info(f"Processing email file: {EMAIL_FILEPATH}")

# Get filename
match = re.search(r'filename="(.+)"', email_file)
if match:
    attachment_filename = match.group(1)
    logger.info(f"Found attachment filename: {attachment_filename}")
else:
    logger.warning("Didn't find a filename from the log, exiting")
    sys.exit()

# Get attachment base64
match = re.search(r"filename=.*\n\n([A-Za-z0-9\n\/\+\=\-]*)\n\n", email_file)
if match:
    attachment_base64 = match.group(1)
    logger.info("Found attachment base64 data")
else:
    logger.warning("Didn't find an attachment blob from the log, exiting")
    sys.exit()

# Decode the attachment
attachment_bytes = base64.b64decode(attachment_base64)

# Write to xlsx
output_path = f"./{attachment_filename}"
with open(output_path, "wb") as output_file:
    output_file.write(attachment_bytes)

logger.info(f"Successfully saved email attachment to {output_path}")
