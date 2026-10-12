"""Target display resolution used by both preparation scripts."""
WIDTH = 3440
HEIGHT = 1440

if WIDTH <= 0 or HEIGHT <= 0 or WIDTH * 9 <= HEIGHT * 16:
    raise ValueError("Set positive display dimensions wider than 16:9.")

ASPECT = WIDTH / HEIGHT
