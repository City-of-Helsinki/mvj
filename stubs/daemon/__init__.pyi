from typing import Any, Dict, Optional


class DaemonContext:
    def __init__(
            self,
            chroot_directory: Optional[str] = ...,
            working_directory: str = ...,
            umask: int = ...,
            uid: Optional[int] = ...,
            gid: Optional[int] = ...,
            initgroups: bool = ...,
            prevent_core: bool = ...,
            detach_process: Optional[bool] = ...,
            files_preserve: Optional[bool] = ...,
            pidfile: Optional[str] = ...,
            stdin: Optional[Any] = ...,
            stdout: Optional[Any] = ...,
            stderr: Optional[Any] = ...,
            signal_map: Optional[Dict[int, Optional[str]]] = ...,
    ):
        ...

    def __enter__(self) -> 'DaemonContext':
        ...

    def __exit__(
            self,
            exc_type: Any,
            exc_value: Any,
            traceback: Any,
    ) -> None:
        ...
