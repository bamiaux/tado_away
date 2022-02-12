import argparse
import getpass
import logging
import time

import PyTado.interface as tado
import rich
import rich.console
import rich.logging

console = rich.console.Console()


class Handler(rich.logging.RichHandler):
    def emit(self, record: logging.LogRecord) -> None:
        # filter oauth token refresh which are at info level
        if record.filename == "interface.py" and record.levelname == "INFO":
            return
        # rich.inspect(record)
        return super().emit(record)


FORMAT = "%(message)s"
logging.basicConfig(level="INFO", format=FORMAT, datefmt="[%X]", handlers=[Handler()])
log = logging.getLogger("rich")


class Context:
    def __init__(self, session: tado.Tado):
        self.session = session
        self.zones: dict[int, str] = {}
        self.names: dict[int, str] = {}
        self.home: str = ""
        self.time: float = 0


# login creates a tado session from input username/password
def login(args: argparse.Namespace) -> tado.Tado:
    log.info("login...")
    session = tado.Tado(args.username, args.password)
    log.info("logged")
    return session


def read_is_open(zstate: dict) -> str:
    try:
        return "close" if zstate["openWindow"] is None else "open"
    except Exception:
        return ""


def read_previous_is_open(ctx: Context, zid: int) -> str:
    try:
        return ctx.zones[zid]
    except Exception:
        return ""


def set_open_window(ctx: Context, zid: int, is_open: str):
    if is_open == "open":
        ctx.session.setOpenWindow(zid)
    else:
        ctx.session.resetOpenWindow(zid)


def cache_zone_names(ctx: Context):
    data = ctx.session.getZones()
    if not data:
        return None

    ctx.names = {}
    for zone in data:
        ctx.names[zone["id"]] = zone["name"]


def read_zone_name(ctx: Context, zid: int) -> str:
    try:
        return ctx.names[zid]
    except Exception:
        return "unknown"


# check_open_windows disables any zone
# where opened windows are detected
def check_open_windows(ctx: Context):
    # read zone states
    states = ctx.session.getZoneStates()
    if not states:
        return

    for zid, zstate in states["zoneStates"].items():
        # foreach zone check previous & current is_open state
        zid = int(zid)
        is_open = read_is_open(zstate)
        previous_is_open = read_previous_is_open(ctx, zid)
        if previous_is_open == is_open:
            continue

        # if those are different, update them
        set_open_window(ctx, zid, is_open)
        # update context with latest known state
        ctx.zones[zid] = is_open
        name = read_zone_name(ctx, zid)
        log.info(f"zone {name}: {is_open.capitalize()}")


def is_any_device_home(ctx: Context) -> str:
    # do not set away mode if no devices are found
    devices = ctx.session.getMobileDevices()
    if devices is None:
        return "home"

    for device in devices:
        # rich.inspect(device, docs=False)
        if not device["settings"]["geoTrackingEnabled"]:
            continue
        if device["location"]["atHome"]:
            return "home"

    return "away"


# check_far_from_hone checks whether any device
# is home else stops cooling until one returns
def check_far_from_home(ctx: Context):
    any_home = is_any_device_home(ctx)
    prev_home = ctx.home
    if prev_home == any_home:
        return

    # set home/away state accordingly
    state_fn = ctx.session.setHome if any_home else ctx.session.setAway
    state_fn()
    ctx.home = any_home
    log.info(f"geo: {ctx.home.capitalize()}")


def refresh_context(ctx: Context, args: argparse.Namespace):
    # rich.inspect(ctx)
    now = time.time()
    duration = int(now - ctx.time)
    if duration < args.max_cache_duration:
        return

    log.info("caching...")
    ctx.home = ""
    ctx.zones = {}
    cache_zone_names(ctx)
    ctx.time = now


def main(ctx: Context, args: argparse.Namespace):
    refresh_context(ctx, args)
    check_open_windows(ctx)
    check_far_from_home(ctx)
    return 0


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--username", type=str, default=getpass.getuser(), help="tado username"
    )
    parser.add_argument(
        "--password", type=str, default=getpass.getpass(), help="tado password"
    )
    parser.add_argument("--period", type=int, default=10, help="period in seconds")
    parser.add_argument(
        "--max-cache-duration",
        type=int,
        default=60 * 60,
        help="max cache duration in seconds",
    )
    return parser.parse_args()


def run_once(args: argparse.Namespace):
    session = login(args)
    ctx = Context(session)
    while True:
        try:
            main(ctx, args)
        except Exception:
            console.print_exception()
        time.sleep(args.period)


if __name__ == "__main__":
    args = parse_args()
    while True:
        try:
            run_once(args)
        except Exception:
            console.print_exception()
        time.sleep(args.period)
