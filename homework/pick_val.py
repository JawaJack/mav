# .. -*- coding: utf-8 -*-
#
# *********************************************************
# pick_val.py -- Introductory Python programming assignment
# *********************************************************
# This file must be named ``pick_val.py``; none of the function names below are
# allowed to change.
#
# Code skeleton
# =============
# Pick a value from a sequence of items.
def pick_val(
  # The sequence to pick from.
  seq,
  #
  # The index of the element to select, measured from the end of the list. That
  # is, 1 refers to the last item in seq, 2 to the second item from the end,
  # etc. This parameter defaults to the 4th from the end.
  #
  # * If the sequence is shorter than 4 elements, select the third, second,
  #   first, or raise an IndexError exception if the sequence is empty.
  # * If the index is negative, select from the beginning of the list:
  #   index == -2 returns seq[2]. Again, if the list is less than index in
  #   length, return an earlier value.
  index=4):

    # Convert the index (which counts from the end of the list) to the standard
    # Python index, which counts from the beginning of the list.
    py_index = -index

    # Keep the index within the range of the list, which is [-n, n - 1] where
    # n == len(seq).
    py_index = min(py_index, len(seq) - 1)
    py_index = max(py_index, -len(seq))

    return seq[py_index]
#
# Tests
# =====
class TestPickVal(object):
    # Test picking from a list with > 4 elements.
    def test_1(self):
        assert pick_val(range(10)) == 6

    # Test picking from a list with exactly 4 elements.
    def test_2(self):
        assert pick_val(range(4)) == 0

    # Test picking from a list with < 4 elements.
    def test_3(self):
        assert pick_val(range(3)) == 0
        assert pick_val(range(2)) == 0
        assert pick_val(range(1)) == 0

    # Test picking from an empty list.
    def test_4(self):
        try:
            pick_val([])
            assert False
        except IndexError:
            pass

    # Test passing a non-integral type for the index.
    def test_5(self):
        try:
            pick_val(range(10), 1.5)
            assert False
        except TypeError:
            pass

    # Test picking values outside the range.
    def test_6(self):
        assert pick_val(range(10), 11) == 0

    # Test picking values from other types (string, tuple).
    def test_7(self):
        assert pick_val('hello') == 'e'
        assert pick_val('hello', 10) == 'h'
        assert pick_val('hello', 1) == 'o'

        assert pick_val(tuple(range(10))) == 6
        assert pick_val(tuple(range(10)), 3) == 7
        assert pick_val(tuple(range(10)), 11) == 0

    # Test passing a very large index
    def test_8(self):
        assert pick_val(range(10), 100000000) == 0
#
# Test driver code
# ================
def run_tests():
    tpv = TestPickVal()
    tpv.test_1()
    tpv.test_2()
    tpv.test_3()
    tpv.test_4()
    tpv.test_5()
    tpv.test_6()
    tpv.test_7()
    tpv.test_8()
    print('All tests passed.')

if __name__ == '__main__':
    run_tests()
