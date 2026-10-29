import random
import unittest
from algorithm import max_profit, brute_force


class AlgorithmTests(unittest.TestCase):
    def test_sample(self):
        result = max_profit([100, 113, 110, 85, 105, 102, 86, 63, 81, 101, 94, 106, 101, 79, 94, 90, 97])
        self.assertEqual((result.buy_day, result.sell_day, result.profit), (8, 12, 43))

    def test_declining_prices_have_no_trade(self):
        result = max_profit([9, 7, 5, 2])
        self.assertIsNone(result.buy_day)
        self.assertEqual(result.profit, 0)

    def test_matches_brute_force(self):
        random.seed(42)
        for _ in range(300):
            prices = [random.randint(1, 200) for _ in range(random.randint(2, 25))]
            result = max_profit(prices)
            expected_profit, expected_pair = brute_force(prices)
            self.assertAlmostEqual(result.profit, expected_profit)
            if expected_pair == (None, None):
                self.assertIsNone(result.buy_day)
            else:
                self.assertEqual((result.buy_day, result.sell_day), expected_pair)


if __name__ == "__main__":
    unittest.main()
