import time
from itertools import product
from functools import partial

round_up_to_two_digits = partial(round, ndigits=2)


class TimedContext:
    """
    Base for timer context. Starts a counter on enter and stores the elapsed time on exit.

    >>> from time import sleep
    >>> with TimedContext() as tc:
    ...     sleep(0.5)
    >>> round_up_to_two_digits(tc.elapsed)
    0.5
    """

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.end = time.perf_counter()
        self.elapsed = self.end - self.start


class CumulativeTimings(list, TimedContext):
    """Context manager that is meant to be used in a loop to time and accumulate both timings and relevant data.

    >>> from functools import partial
    >>> from time import sleep
    >>>
    >>> cumul_timing = CumulativeTimings()
    >>>
    >>> for i in range(4):
    ...     with cumul_timing:
    ...         sleep(i * 0.2)
    >>>
    >>>  # round_up_to_two_digits it needed here because of the variability of the system clock timing
    >>> round_up_to_two_digits(cumul_timing.elapsed) == 0.6
    True
    >>> list(map(round_up_to_two_digits, cumul_timing))
    [0.0, 0.2, 0.4, 0.6]


    You can also add some data to the accumulation by calling the instance of CumulativeTimings
    Note: Calling cumul_timing to tell it to store some data for a loop step does have an overhead, so

    >>> cumul_timing = CumulativeTimings()
    >>> for i in range(4):
    ...     with cumul_timing:
    ...         sleep(i * 0.2)
    ...     cumul_timing.append_data(f"index: {i}")
    >>>
    >>> list(zip(map(round_up_to_two_digits, cumul_timing), cumul_timing.data_store))
    [(0.0, 'index: 0'), (0.2, 'index: 1'), (0.4, 'index: 2'), (0.6, 'index: 3')]

    """
    no_data = type('NoData', (), {})

    def __init__(self, datas=None):
        super().__init__()
        if datas is not None:
            assert hasattr(datas, 'append') and hasattr(datas, 'len'), \
                "data_store needs to have methods: append and __len__"
            self.datas = datas
        else:
            self.datas = list()

    def append_data(self, data):
        """Append data to the data_store.

        The purpose of this function is to be able to save the context (usually the inputs) the function call that is
        being timed.

        Will raise an assertion error if length of datas (+1) doesn't equal the current length of the CumulativeTimings
        list. This is so as to avoid misalignments between timing and data
        """
        assert (len(self.datas) + 1) == len(self), \
            f"append_data can only be called if your data_store has exactly one less item than your timings list. " \
            f"What you have is len(self.data_store)={len(self.datas)} " \
            f"and len(self)={len(self)}"
        self.datas.append(data)

    def __exit__(self, *args):
        super().__exit__(*args)
        self.append(self.elapsed)


def time_multiple_calls(func, arguments, return_func_args=True, include_func_output=True):
    """
    Feed collections of arguments to a function, measure how much time it takes to run,
    and output the timings (and possible function inputs and outputs).

    :param func: Function that will be called on all argument combinations
    :param arguments: an iterable of (position) arguments to feed to func
    :param return_func_args: Whether to return the arguments
    :param include_func_output: Whether to include the output of the function in the
    :return:

    >>> from time import sleep
    >>> def func(i, j):
    ...     t = i * j
    ...     sleep(t)
    ...     return t
    >>> timings, args = time_multiple_calls(func, [(0.2, 0.3), (0.5, 0.8), (0.5, 2)])
    >>>
    >>> list(map(round_up_to_two_digits, timings))
    [0.06, 0.4, 1.0]
    >>> args
    [(0.2, 0.3, 0.06), (0.5, 0.8, 0.4), (0.5, 2, 1.0)]

    """
    if return_func_args or include_func_output:
        if return_func_args:
            if include_func_output:
                output_kind = 'func_args_and_output'
            else:
                output_kind = 'func_output'
        else:
            output_kind = 'func_args'
    else:
        output_kind = 'only_timings'

    cumul_timing = CumulativeTimings()
    for func_args in arguments:
        with cumul_timing:
            func_output = func(*func_args)
        if output_kind != 'only_timings':
            data = None
            if output_kind == 'func_args_and_output':
                data = (*func_args, func_output)
            elif output_kind == 'func_output':
                data = func_output
            elif output_kind == 'func_args':
                data = func_args
            cumul_timing.append_data(data)

    if output_kind != 'only_timings':
        return cumul_timing, cumul_timing.datas
    else:
        return cumul_timing


def time_arg_combinations(func, args_base, return_func_args=True, include_func_output=True):
    """
    Feed combinations of arguments to a function, measure how much time it takes to run,
    and output the timings (and possible function inputs and outputs.

    :param func: Function that will be called on all argument combinations
    :param args_base: a collection of iterables of arguments from which to create the combinatorial mesh
    :param include_func_output: Whether to include the output of the function in the
    :return:

    >>> from time import sleep
    >>> def func(i, j):
    ...     t = i * j
    ...     sleep(t)
    ...     return t
    >>> timings, args = time_arg_combinations(func, args_base=([0.1, 0.2], [2, 5]))
    >>>
    >>> list(map(round_up_to_two_digits, timings))
    [0.2, 0.5, 0.4, 1.0]
    >>> args
    [(0.1, 2, 0.2), (0.1, 5, 0.5), (0.2, 2, 0.4), (0.2, 5, 1.0)]
    """
    return time_multiple_calls(func, product(*args_base), return_func_args, include_func_output)


class TimerAndFeedback(TimedContext):
    """Context manager that will serve as a timer, with custom feedback prints (or logging, or any callback)
    >>> with TimerAndFeedback():
    ...     time.sleep(0.5)
    Took 0.5 seconds
    >>> with TimerAndFeedback("doing something...", "... finished doing that thing"):
    ...     time.sleep(0.5)
    doing something...
    ... finished doing that thing
    Took 0.5 seconds
    >>> with TimerAndFeedback(verbose=False) as feedback:
    ...     time.sleep(1)
    >>> # but you still have access to some stats through feedback object (like elapsed, started, etc.)
    """

    def __init__(self, start_msg="", end_msg="", verbose=True, print_func=print):
        self.start_msg = start_msg
        if end_msg:
            end_msg += '\n'
        self.end_msg = end_msg
        self.verbose = verbose
        self.print_func = print_func  # change print_func if you want to log, etc. instead

    def print_if_verbose(self, *args, **kwargs):
        if self.verbose:
            if len(args) > 0 and len(args[0]) > 0:
                return self.print_func(*args, **kwargs)

    def __enter__(self):
        self.print_if_verbose(self.start_msg)
        return super().__enter__()

    def __exit__(self, *args):
        super().__exit__()
        self.print_if_verbose(self.end_msg + f"Took {self.elapsed:0.1f} seconds")

    def __repr__(self):
        return f"elapsed={self.elapsed} (start={self.start}, end={self.end})"


class TimerAndCallback(TimedContext):
    """Context manager that will serve as a timer, with a custom callback called on exit

    The callback is usually meant to have some side effect like logging or storing information.

    >>> # run some loop, accumulating timing
    >>> from time import sleep
    >>> cumul = list()
    >>> for i in range(4):
    ...    with TimerAndCallback(cumul.append) as t:
    ...        sleep(i * 0.2)
    >>> # since system timing is not precise, we'll need to round our numbers to assert them, so:
    >>> # See that you can always see what the timing was in the elapsed attribute
    >>> assert round_up_to_two_digits(t.elapsed) == 0.6
    >>> # but the point of this demo is to show that cumul now holds all the timings
    >>> assert list(map(round_up_to_two_digits, cumul)) == [0.0, 0.2, 0.4, 0.6]

    """

    def __init__(self, callback=lambda x: x):
        self.callback = callback
        self.extra_callback_data = None

    def __exit__(self, *args):
        super().__exit__()

        if self.extra_callback_data is not None:
            self.callback((self.elapsed, self.extra_callback_data))
        else:
            self.callback(self.elapsed)
