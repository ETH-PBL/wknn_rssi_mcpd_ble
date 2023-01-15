#!/usr/bin/python
import subprocess
import threading
import time
import psutil
import curses
import sys
from configs import room

class color:
   BOLD = '\033[1m'
   END = '\033[0m'

def kill(proc_pid):
    process = psutil.Process(proc_pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()


def get_string_repetition(searchstr, file):
    p1 = subprocess.Popen(["rg", searchstr, file], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["wc", "-l"], stdin=p1.stdout, stdout=subprocess.PIPE)
    out, err = p2.communicate()
    return int(out.strip().decode("ascii"))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("No file given")
        exit()

    stdscr = curses.initscr()
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(6, curses.COLOR_BLUE, curses.COLOR_BLACK)
    try:
        curses.noecho()
        curses.cbreak()
        stdscr.keypad(True)
        
        filename = "../raw_data/" + sys.argv[1]
        p = subprocess.Popen(["./screen_read.sh", filename])
        stdscr.clear()
        stdscr.addstr(3, 3, "Writing to file '" + filename + "'")
        while True:
            for beacon in room.beacons:
                stdscr.move(beacon.n+4, 5)
                stdscr.addstr(str(beacon.uuid) + " (" + str(beacon.n) + ")", curses.color_pair(beacon.n) | curses.A_BOLD)
                stdscr.addstr(" has got ")
                stdscr.addstr(str(get_string_repetition(beacon.uuid, filename)), curses.color_pair(beacon.n) | curses.A_BOLD)

            stdscr.move(len(room.beacons)+5, 5)
            stdscr.refresh()
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        kill(p.pid)
        curses.nocbreak()
        stdscr.keypad(False)
        curses.echo()
        curses.endwin()
        print("Quitting the application")
        
