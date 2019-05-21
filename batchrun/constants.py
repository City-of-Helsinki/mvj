from datetime import timedelta

#: Grace period length.
#:
#: If the starting time of a scheduled job was missed, it will still be
#: started until the grace period has elapsed too.  After the grace
#: period has passed, the missed scheduling will be discarded.
GRACE_PERIOD_LENGTH = timedelta(minutes=5)
