import argparse
import getpass
import sys

import PyTado.interface as tado
import rich
import rich.console

console = rich.console.Console()


# login creates a tado session from input username/password
def login(args) -> tado.Tado:
    rich.print("* login...")
    session = tado.Tado(args.username, args.password)
    rich.print("* logged")
    return session


# is_zone_open returns whether input zone have opened windows
def is_zone_open(session: tado.Tado, zone: dict) -> bool:
    zid = zone["id"]
    data = session.getOpenWindowDetected(zid)
    try:
        return data["openWindowDetected"]
    except:
        return False


# check_open_windows disables any zone
# where opened windows are detected
def check_open_windows(session: tado.Tado):
    for zone in session.getZones():
        name = zone["name"]
        is_open = is_zone_open(session, zone)
        zstate = "stopped" if is_open else "running"
        rich.print(f"* zone {name}: {zstate}")
        session.setOpenWindow(is_open)


# check_far_from_hone checks whether any device
# is home else stops cooling until one returns
def check_far_from_home(session: tado.Tado):
    any_home = False
    for device in session.getMobileDevices():
        # rich.inspect(device, docs=False)
        if not device["settings"]["geoTrackingEnabled"]:
            continue
        any_home = any_home or device["location"]["atHome"]

    # set home/away state accordingly
    state = "home" if any_home else "away"
    state_fn = session.setHome if any_home else session.setAway
    rich.print(f"+ devices: {state}")
    state_fn()


def main(args):
    session = login(args)
    check_open_windows(session)
    check_far_from_home(session)
    rich.print("* exit")
    return 0


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--username", type=str, default=getpass.getuser(), help="tado username"
    )
    parser.add_argument(
        "--password", type=str, default=getpass.getpass(), help="tado password"
    )
    return parser.parse_args()


if __name__ == "__main__":
    try:
        args = parse_args()
        ret = main(args)
    except Exception:
        console.print_exception()
        ret = -1
    sys.exit(ret)