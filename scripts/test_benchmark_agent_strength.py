#!/usr/bin/env python3
"""No-engine regression tests for competitive agent benchmark."""
import pathlib
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from benchmark_agent_strength import (
    game_schedule, parse_result, play_once, stable_seed, wilson_interval
)


class BenchmarkTests(unittest.TestCase):
    def test_exact_mirrored_schedule(self):
        paths = [pathlib.Path("z.txt"), pathlib.Path("a.txt")]
        rows = list(game_schedule(paths, 3, 42))
        self.assertEqual(len(rows), 12)
        self.assertEqual([r[0].name for r in rows[:6]], ["a.txt"] * 6)
        for i in range(0, len(rows), 2):
            deck1, repeat1, seed1, first1 = rows[i]
            deck2, repeat2, seed2, first2 = rows[i + 1]
            self.assertEqual((deck1, repeat1, seed1), (deck2, repeat2, seed2))
            self.assertEqual((first1, first2), (True, False))
        self.assertNotEqual(stable_seed(42, "a.txt", 0), stable_seed(42, "a.txt", 1))

    def test_extract_winner_only_after_success(self):
        self.assertEqual(parse_result(0, "Game over: winner = 1", "")["winner_seat"], 1)
        self.assertEqual(parse_result(0, "Game over: winner = 2", "")["winner_seat"], 2)
        self.assertEqual(parse_result(0, "Game over: winner = 0", "")["status"], "error")
        self.assertEqual(parse_result(1, "Game over: winner = 1", "")["status"], "error")
        self.assertEqual(parse_result(0, "no winner in stdout", "")["status"], "error")

    def test_win_condition_mirrors_agents_correctly(self):
        with patch("benchmark_agent_strength.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="Game over: winner = 1", stderr=""
            )
            engine, deck = pathlib.Path("riftbound"), pathlib.Path("deck.txt")
            first = play_once(engine, deck, "ismcts:sims=24", "ismcts:sims=128",
                              True, 11, 15)
            self.assertTrue(first["challenger_win"])
            first_command = mock_run.call_args.args[0]
            self.assertEqual(first_command[first_command.index("--agent1") + 1],
                             "ismcts:sims=128")
            second = play_once(engine, deck, "ismcts:sims=24", "ismcts:sims=128",
                               False, 11, 15)
            self.assertFalse(second["challenger_win"])
            second_command = mock_run.call_args.args[0]
            self.assertEqual(second_command[second_command.index("--agent1") + 1],
                             "ismcts:sims=24")
            self.assertEqual(first["seed"], second["seed"])

    def test_timeout_never_counts_as_a_loss(self):
        with patch("benchmark_agent_strength.subprocess.run",
                   side_effect=subprocess.TimeoutExpired(cmd="test", timeout=2)):
            row = play_once(pathlib.Path("engine"), pathlib.Path("deck"),
                            "random", "ismcts:sims=128", True, 123, 2)
            self.assertEqual(row["status"], "timeout")
            self.assertIsNone(row["challenger_win"])

    def test_wilson(self):
        self.assertEqual(wilson_interval(1, 0), (None, None))
        self.assertAlmostEqual(wilson_interval(5, 10)[0], 0.2366, places=3)
        self.assertAlmostEqual(wilson_interval(5, 10)[1], 0.7634, places=3)


if __name__ == "__main__":
    unittest.main()
