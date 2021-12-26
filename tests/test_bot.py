"""
Unit tests. Right now use only to test github actions.
"""

import sys
import unittest
import logging

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


class TestEchoBot(unittest.TestCase):
    """Tests for echo bot."""

    def test_nothing(self):
        """Log message."""
        log = logging.getLogger("TestEchoBot.test_nothing")
        log.info(" Has nothing to test but github actions")
        self.assertEqual(1, 1)
