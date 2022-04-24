from datetime import datetime


def exception_uid(exception: Exception, dt: datetime, suffix: str):
    import hashlib
    import traceback

    """Builds a unique string (exception UID) that may be exposed to the user without revealing to much.
    """
    dt_str = dt.strftime("%Y_%m_%dT%H_%M_%S")
    error_msg = str(exception)
    formatted_traceback = "\n".join(traceback.format_tb(exception.__traceback__))
    msg_hash = hashlib.sha256(error_msg.encode("utf8")).hexdigest()[:6]
    tb_hash = hashlib.sha256(formatted_traceback.encode("utf8")).hexdigest()[:6]
    return f"{dt_str}__{tb_hash}__{msg_hash}__{suffix}"
