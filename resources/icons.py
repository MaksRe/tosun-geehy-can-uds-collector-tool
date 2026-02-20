from dataclasses import dataclass
from typing import Optional


@dataclass
class Icons:

    main_path: Optional[str] = ":/icons/feather/"

    edit: Optional[str] = main_path + "edit.svg"
    send: Optional[str] = main_path + "play.svg"

    connect_on: Optional[str] = main_path + "arrow-right-circle.svg"
    connect_off: Optional[str] = main_path + "x-circle.svg"

    trace_on: Optional[str] = main_path + "zap.svg"
    trace_off: Optional[str] = main_path + "zap-off.svg"

    stop: Optional[str] = main_path + "square.svg"
    play: Optional[str] = main_path + "play.svg"
