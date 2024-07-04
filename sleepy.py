#!/usr/bin/python3

from __future__ import print_function

import time

if hasattr(time, 'perf_counter'):
    perf_counter = time.perf_counter
else:
    perf_counter = time.time

# if run as an executable, this is the start time used for start-up time corrections
__starttime = perf_counter()

import sys

try:
    from argparse import ArgumentParser, REMAINDER
    using_optparse = False
except ImportError:
    from optparse import OptionParser as ArgumentParser
    using_optparse = True


def DEBUG(level, *msg, **args):
    if not hasattr(DEBUG, 'debuglevel'):
        DEBUG.debuglevel = 0
    end = args.get('end', '\n')
    if level<=DEBUG.debuglevel:
        print(*msg, file=sys.stderr, end=end)
        sys.stderr.flush()

def get_duration(arg):
    "convert duration - a number with 's', 'm', 'h', 'd' or 'S' suffix to seconds"
    if not arg: # None or empty string
        return arg
    suffix = 's'
    conv = { 's': 1,
             'm': 60,
             'h': 3600,
             'd': 24*3600+0.002,
             'S': 24*3600+39*60+35.24409
            }
    if arg[-1] in conv:
        suffix = arg[-1]
        x = arg[:-1]
    else:
        x = arg

    value_ok = False
    try:
        d = float(x)
        value_ok = d>=0
    except ValueError:
        value_ok = False

    if not value_ok:
        print(sys.argv[0]+": invalid time interval: '%s'" % arg, file=sys.stderr)
        print("Try '%s --help' for more information." % sys.argv[0], file=sys.stderr)
        sys.exit(1)

    d = conv[suffix] * d
    return d

def format_time(t):
    "human readable time (duration)"
    subseconds = t-int(t)
    #t = int(t)
    minutes, seconds = divmod(t, 60)
    minutes = int(round(minutes))
    seconds = int(round(seconds))
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    weeks, days = divmod(days, 7)
    r = []
    if weeks:
        r.append(str(weeks)+'w')
    if r or days:
        r.append(str(days)+'d')
    if r or hours:
        r.append('{:2}h'.format(hours))
    if r or minutes:
        r.append('{:2}m'.format(minutes))
    fmt_sec = '{:02}s'.format(seconds)
#    if subseconds > 0.1:
#        fmt_sec += '{:.1f}'.format(subseconds)[1:]
#    fmt_sec += 's'

    r.append(fmt_sec)

    r = ''.join(r)

    return r

def format_output(start, stop, sleeptime, now, symbol, formatstring='{symbol} {sleeptime} - {passed} = {remaining}'):
    remaining = format_time(stop - now)
    passed = format_time(now - start)
    sleeptime = format_time(sleeptime)
    f = formatstring.format(passed=passed, remaining=remaining, sleeptime=sleeptime, symbol=symbol)
    return f

def sleep(seconds, interval=1, debuglevel=0, starttime=None):
    if starttime is None:
        starttime = perf_counter()
    DEBUG.debuglevel = debuglevel
    DEBUG(3, 'starttime', starttime)

    now = perf_counter()
    correction = now - starttime
    startsleep = now

    DEBUG(3, 'Correction', correction)
    if correction < 0:
        DEBUG(0, 'Negative time lapse detected, ignoring')
    elif correction > 10:
        DEBUG(0, 'Took too long to start the program')
    sleeptime_corr = seconds - correction
    if sleeptime_corr < 0:
        DEBUG(1, 'Took too long to start the program, missed', sleeptime_corr, 'seconds')

    stopsleep = sleeptime_corr+startsleep
    pause = interval

    rotating_slash = '|/-\\'
    rotating_slash_index = 0

    while True:

        now = perf_counter()
        if now >= stopsleep:
            break
        elif stopsleep - now > 0.9*interval:
            rot = rotating_slash[rotating_slash_index]
            out = format_output(startsleep, stopsleep, seconds, now, rot)
            print (out, end='    \r', file=sys.stderr); sys.stderr.flush()
        elif stopsleep - now < 1.5*interval:
            pause = min(pause/2, (stopsleep-now))
        time.sleep(pause)
        rotating_slash_index = (rotating_slash_index+1) % len(rotating_slash)

if __name__ == '__main__':

    VERSION='0.2'

    parser = ArgumentParser(prog='sleepy',
            description='Delay for a specified amount of time, with a countdown.')
    if using_optparse:
        DEBUG(3, 'using optparse')
        parser.add_argument = parser.add_option
        parser.parse_known_args = parser.parse_args
        parser.disable_interspersed_args()

    parser.add_argument('-v', dest='debuglevel', action='count',
                       default = 0,
                       help='Be verbose (repeat for more)')

    parser.add_argument('--interval', dest='interval', action='store',
                       default = '1',
                       help='Print countdown in these intervals (default 1)')


    if not using_optparse:
        parser.add_argument('--version', action='version',
                       version='%(prog)s '+VERSION)

    args, rest = parser.parse_known_args()

    DEBUG.debuglevel = args.debuglevel

    DEBUG(3, 'args:', str(args))
    DEBUG(3, 'optparse:', using_optparse)
    DEBUG(3, 'rest:', repr(rest))

    sleeptime = sum(get_duration(x) for x in rest)
    DEBUG(3, 'sleep time', sleeptime)

    interval = get_duration(args.interval)
    sleep(sleeptime, interval=interval, debuglevel=args.debuglevel, starttime=__starttime)

