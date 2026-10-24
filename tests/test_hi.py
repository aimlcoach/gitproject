import unittest

from hi import greeting


class GreetingTests(unittest.TestCase):
    def test_greeting_returns_expected_message(self) -> None:
        self.assertEqual(greeting(), "Hi There!")


if __name__ == "__main__":
    unittest.main()
