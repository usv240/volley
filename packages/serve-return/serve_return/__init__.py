"""serve-return: count adult-child conversational turns and keep no words.

The quantity is the one the developmental studies used, the
conversational turn count produced by the LENA system from daylong
recordings: an adult utterance answered by a child within five seconds,
or the reverse. This package applies that rule to any transcript that
carries speaker labels and times, from a Bee wristband, a CHILDES
corpus or a research recorder, and returns numbers only.

Everything textual is read, used for a word count and a question count,
and dropped. The output types hold integers and floats; a test in this
package serialises them from a transcript full of names and asserts that
not one name survives.
"""

from .rule import (
    WINDOW_SECONDS,
    DayCounts,
    HourCounts,
    Roles,
    Utterance,
    count_day,
    count_turns,
)

__all__ = [
    "WINDOW_SECONDS",
    "DayCounts",
    "HourCounts",
    "Roles",
    "Utterance",
    "count_day",
    "count_turns",
]
