# lag
Performance gauging tools.

Light weight, pure-python and only builtins (no further dependencies than python itself).


To install:	```pip install lag```

# Examples

`TimedContext` is the base context manager of other context manager timers 
that add some functionality to it: `CumulativeTimings, TimerAndFeedback, TimerAndCallback`.


## TimedContext

Starts a counter on enter and stores the elapsed time on exit.
 
```pydocstring
>>> from lag import TimedContext, round_up_to_two_digits
>>> from time import sleep
>>> with TimedContext() as tc:
...     sleep(0.5)
>>> round_up_to_two_digits(tc.elapsed)
```

## `CumulativeTimings`

Context manager that is meant to be used in a loop to time and accumulate both timings and relevant data.

It's a context manager, 
but also a list (which will contain the an accumulation of the timings the instance encountered).

```pydocstring
>>> from lag import CumulativeTimings
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
```

You can also add some data to the accumulation by calling the instance of CumulativeTimings
Note: Calling cumul_timing to tell it to store some data for a loop step does have an overhead, so

```pydocstring
>>> from lag import CumulativeTimings
>>> from time import sleep
>>> cumul_timing = CumulativeTimings()
>>> for i in range(4):
...     with cumul_timing:
...         sleep(i * 0.2)
...     cumul_timing.append_data(f"index: {i}")
>>>
>>> list(zip(map(round_up_to_two_digits, cumul_timing), cumul_timing.data_store))
[(0.0, 'index: 0'), (0.2, 'index: 1'), (0.4, 'index: 2'), (0.6, 'index: 3')]
```

## `time_multiple_calls` and `time_arg_combinations`

These functions use `CumulativeTimings` to time a function call repeatedly with different inputs.

`time_multiple_calls` feeds collections of arguments to a function, 
measures how much time it takes to run, and output the timings (and possible function inputs and outputs).

```pydocstring
>>> from lag import time_multiple_calls
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
```

`time_arg_combinations' uses the above to feed combinations of arguments to a function.
    
```pydocstring
>>> from lag import time_arg_combinations
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
```

## TimerAndFeedback

Context manager that will serve as a timer, with custom feedback prints (or logging, etc.)

```pydocstring
>>> from lag import TimerAndFeedback
>>> from time import sleep
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
```


## TimerAndCallback

Context manager that will serve as a timer, with a custom callback called on exit

The callback is usually meant to have some side effect like logging or storing information.

```pydocstring
>>> # run some loop, accumulating timing
>>> from lag import TimerAndCallback
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
```



