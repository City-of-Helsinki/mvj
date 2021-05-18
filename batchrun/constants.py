from datetime import timedelta

#: Grace period length.
#:
#: If the starting time of a scheduled job was missed, it will still be
#: started until the grace period has elapsed too.  After the grace
#: period has passed, the missed scheduling will be discarded.
GRACE_PERIOD_LENGTH = timedelta(minutes=5)

#: Line end characters to determine log entry boundaries
LINE_END_CHARACTERS = (  # Note: Must be tuple for str.endswith
    "\n",  # Line Feed
    "\r",  # Carriage Return
    "\v",  # Line Tabulation
    "\f",  # Form Feed
    "\x1c",  # File Separator
    "\x1d",  # Group Separator
    "\x1e",  # Record Separator
    "\x85",  # Next Line (C1 Control Code)
    "\u2028",  # Line Separator
    "\u2029",  # Paragraph Separator
)
