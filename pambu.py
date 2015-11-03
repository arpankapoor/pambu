#!/usr/bin/env python3
import copy
import curses
import curses.ascii
from enum import Enum
import locale
import math
import sys
import signal


class Direction(Enum):
    north, east, south, west = range(4)

    def is_opp(self, other):
        return ((self == Direction.north and other == Direction.south) or
                (self == Direction.south and other == Direction.north) or
                (self == Direction.east and other == Direction.west) or
                (self == Direction.west and other == Direction.east))


class Point:
    """A point represented by a *y* and *x* coordinate"""
    def __init__(self, y, x):
        self.y = y
        self.x = x

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self.__eq__(other)

    def distance_from(self, other):
        dy = other.y - self.y
        dx = other.x - self.x
        return math.sqrt(dy**2 + dx**2)

    def has_same_y(self, other):
        return self.y == other.y

    def has_same_x(self, other):
        return self.x == other.x

    def is_to_the_left_of(self, other):
        return self.x <= other.x

    def is_to_the_right_of(self, other):
        return self.x >= other.x

    def is_above(self, other):
        return self.y <= other.y

    def is_below(self, other):
        return self.y >= other.y

    def move(self, direction):
        """Move 1 unit in given direction"""
        if direction == Direction.north:
            self.y -= 1
        elif direction == Direction.west:
            self.x -= 1
        elif direction == Direction.south:
            self.y += 1
        elif direction == Direction.east:
            self.x += 1


class LineSegment:
    """A line segment represented by a head and tail point"""
    def __init__(self, head, tail):
        self.head = head
        self.tail = tail

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self.__eq__(other)

    def length(self):
        return self.head.distance_from(self.tail)

    def is_vertical(self):
        return self.head.has_same_x(self.tail)

    def is_horizontal(self):
        return self.head.has_same_y(self.tail)

    def increment(self):
        """Increase the line segment length by 1 from the head"""
        if self.is_horizontal():
            if self.head.x < self.tail.x:
                self.head.move(Direction.west)
            else:
                self.head.move(Direction.east)
        elif self.is_vertical():
            if self.head.y < self.tail.y:
                self.head.move(Direction.north)
            else:
                self.head.move(Direction.south)

    def decrement(self):
        """Decrease the line segment length by 1 from the tail"""
        if self.is_horizontal():
            if self.head.x < self.tail.x:
                self.tail.move(Direction.west)
            else:
                self.tail.move(Direction.east)
        elif self.is_vertical():
            if self.head.y < self.tail.y:
                self.tail.move(Direction.north)
            else:
                self.tail.move(Direction.south)

    def draw(self, window):
        """Draw the line if it is horizontal or vertical"""
        length = math.floor(self.length())
        start_point = Point(min(self.head.y, self.tail.y),
                            min(self.head.x, self.tail.x))

        if self.is_vertical():
            window.vline(start_point.y, start_point.x, 0, length)
        elif self.is_horizontal():
            window.hline(start_point.y, start_point.x, 0, length)

    def lies_on(self, point):
        if self.is_horizontal():
           return point.x <= max(self.head.x, self.tail.x) and point.x >= min(self.head.x, self.tail.x) and point.y == self.head.y
        if self.is_vertical():
           return point.y <= max(self.head.y, self.tail.y) and point.y >= min(self.head.y, self.tail.y) and point.x == self.head.x

    def intersection_point(self, other):
        if isinstance(other, self.__class__):
            if self.head == other.head or self.head == other.tail:
                return self.head
            elif self.tail == other.head or self.tail == other.tail:
                return self.tail
            else:
                return None

    def join(self, other, window):
        def join_char(hline, vline):
            ch = None

            if (ipoint.is_to_the_left_of(hline.head) and
                    ipoint.is_to_the_left_of(hline.tail)):
                if (ipoint.is_above(vline.head) and
                        ipoint.is_above(vline.tail)):
                    ch = curses.ACS_ULCORNER
                elif (ipoint.is_below(vline.head) and
                        ipoint.is_below(vline.tail)):
                    ch = curses.ACS_LLCORNER
            elif (ipoint.is_to_the_right_of(hline.head) and
                    ipoint.is_to_the_right_of(hline.tail)):
                if (ipoint.is_above(vline.head) and
                        ipoint.is_above(vline.tail)):
                    ch = curses.ACS_URCORNER
                elif (ipoint.is_below(vline.head) and
                        ipoint.is_below(vline.tail)):
                    ch = curses.ACS_LRCORNER

            return ch

        if isinstance(other, self.__class__):
            hline = None
            vline = None

            if self.is_vertical():
                vline = self
            elif self.is_horizontal():
                hline = self

            if other.is_vertical():
                vline = other
            elif other.is_horizontal():
                hline = other

            if hline is not None and vline is not None and hline != vline:
                ipoint = hline.intersection_point(vline)
                if ipoint is not None:
                    ch = join_char(hline, vline)
                    if ch is not None:
                        window.addch(ipoint.y, ipoint.x, ch)


class Snake:
    def __init__(self, dimensions):
        maxy, maxx = dimensions
        self.points = [Point(math.floor(0.49 * maxy), math.floor(0.59 * maxx)),
                       Point(math.floor(0.49 * maxy), math.floor(0.40 * maxx))]
        self.direction = Direction.east

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self.__eq__(other)

    def draw(self, window):
        prev_seg = None
        for prev_point, curr_point in zip(self.points[:-1], self.points[1:]):
            curr_seg = LineSegment(prev_point, curr_point)
            curr_seg.draw(window)
            curr_seg.join(prev_seg, window)
            prev_seg = curr_seg
    def detect_collision(self):
        head = self.points[0]
        prev_seg = None
        for prev_point, curr_point in zip(self.points[1:-1], self.points[2:]):
            curr_seg = LineSegment(prev_point, curr_point)
            if curr_seg.lies_on(head):
               curses.endwin()
               print("Collision Detected!")
               sys.exit(0)

    def move(self, window, direction=None):
        """Move 1 unit in given direction"""
        first_seg = LineSegment(self.points[0], self.points[1])
        last_seg = LineSegment(self.points[-2], self.points[-1])

        if (direction is None or
                direction == self.direction or
                direction.is_opp(self.direction)):
            first_seg.increment()
        else:
            new_head = copy.deepcopy(first_seg.head)
            new_head.move(direction)
            self.points.insert(0, new_head)
            self.direction = direction
        self.detect_collision()
        last_seg.decrement()
        if last_seg.length() == 0:
            del self.points[-1]


def signal_handler(signal, frame):
    curses.endwin()
    print("Thanks for playing pambu!")
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, signal_handler)
    locale.setlocale(locale.LC_ALL, "")     # Use system's default encoding

    stdscr = curses.initscr()               # Initialize
    curses.cbreak()                         # Enter cbreak mode
    curses.noecho()                         # Don't echo any characters
    curses.curs_set(0)                      # Make cursor invisible
    stdscr.nodelay(1)                       # Make getch() non-blocking
    stdscr.keypad(1)                        # Interpret escape sequences

    snk = Snake(stdscr.getmaxyx())          # Initialize our Snake!!

    ch = None
    while ch != curses.ascii.ESC:
        stdscr.clear()
        direction = None
        if ch == curses.KEY_UP:
            direction = Direction.north
        elif ch == curses.KEY_DOWN:
            direction = Direction.south
        elif ch == curses.KEY_LEFT:
            direction = Direction.west
        elif ch == curses.KEY_RIGHT:
            direction = Direction.east

        snk.move(stdscr, direction)
        snk.draw(stdscr)
        stdscr.refresh()
        curses.napms(200)
        ch = stdscr.getch()
        curses.flushinp()

    curses.endwin()

if __name__ == "__main__":
    main()
