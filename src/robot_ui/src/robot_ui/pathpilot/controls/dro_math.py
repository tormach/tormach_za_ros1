import operator
import rospy

from PySide6.QtCore import QObject
from PySide6.QtQml import QmlElement, QmlSingleton

from ..qt_helpers import MultiSlot


####################################################################################################
# cparse - common routines for parsing DRO text
#
####################################################################################################
class CParse:
    # code for supporting math in DROs from Stackoverflow question/answer
    # http://stackoverflow.com/questions/13055884/parsing-math-expression-in-python-and-solving-to-find-an-answer
    # http://stackoverflow.com/users/748858/mgilson
    @staticmethod
    def _parse(x):
        operators = set('+-*/')
        op_out = (
            []
        )  # This holds the operators that are found in the string (left to right)
        num_out = (
            []
        )  # this holds the non-operators that are found in the string (left to right)
        buff = []
        # if first char is '+' or '-', stuff '0' into `buff`
        if len(x) > 0 and x[0] in ['+', '-']:
            buff.append('0')
        for c in x:  # examine 1 character at a time
            if c in operators:
                # found an operator.  Everything we've accumulated in `buff` is
                # a single "number". Join it together and put it in `num_out`.
                num_out.append(''.join(buff))
                buff = []
                op_out.append(c)
            else:
                # not an operator.  Just accumulate this character in buff.
                buff.append(c)
        num_out.append(''.join(buff))
        return num_out, op_out

    @staticmethod
    def _my_eval(nums, ops):
        nums = list(nums)
        ops = list(ops)
        operator_order = (
            '*/',
            '+-',
        )  # precedence from left to right.  operators at same index have same precendece.
        # map operators to functions.
        op_dict = {
            '*': operator.mul,
            '/': operator.truediv,
            '+': operator.add,
            '-': operator.sub,
        }
        for op in operator_order:  # Loop over precedence levels
            while any(
                o in ops for o in op
            ):  # Operator with this precedence level exists
                idx, oo = next(
                    (i, o) for i, o in enumerate(ops) if o in op
                )  # Next operator with this precedence
                ops.pop(idx)  # remove this operator from the operator list
                values = map(
                    float, nums[idx : idx + 2]
                )  # here I just assume float for everything
                value = op_dict[oo](*values)
                nums[idx : idx + 2] = [value]  # clear out those indices

        return nums[0]

    # return (True, float) if the passed string can be successfully cast to float
    # and False, 0.0 if not
    @staticmethod
    def is_number(s):
        try:
            val = float(CParse._my_eval(*CParse._parse(s)))
            return True, val
        except ValueError:
            return False, 0.0

    @staticmethod
    def is_number_or_expression(s, prev_val=None):
        if prev_val is not None:
            for prefix in ['/', '*', '+', '- ']:
                if s.startswith(prefix):
                    s = prev_val + s
                    break
        try:
            val = float(CParse._my_eval(*CParse._parse(s)))
            return True, val
        except ValueError:
            return False, 0.0

    @staticmethod
    def is_int(s):
        try:
            val = int(CParse._my_eval(*CParse._parse(s)))
            return True, val
        except ValueError:
            return False, 0.0

    @staticmethod
    def is_text(s):
        if s == '':
            return False, s
        else:
            return True, s


QML_IMPORT_NAME = 'pathpilot.controls'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
@QmlSingleton
class DroMath(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

    @MultiSlot(str, [None, str], result='QVariant')
    def evaluate(self, expression, previous=None):
        is_valid_number, value = CParse.is_number_or_expression(
            expression, previous
        )
        if is_valid_number:
            return value
        rospy.logdebug("Expression is not a valid number or expression.")
        return None
