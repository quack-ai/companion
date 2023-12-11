# Copyright (C) 2023, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

import multiprocessing as mp
from multiprocessing.pool import ThreadPool
from typing import Callable, Optional, Sequence, TypeVar

Inp = TypeVar("Inp")
Out = TypeVar("Out")


__all__ = ["execute_in_parallel", "run_executions_in_parallel"]


def execute_in_parallel(
    func: Callable[[Inp], Out],
    arr: Sequence[Inp],
    num_threads: Optional[int] = None,
) -> Sequence[Out]:
    """Execute a function in parallel on a sequence of inputs

    Args:
        func (callable): function to be executed on multiple workers
        arr (iterable): function argument's values
        num_threads (int, optional): number of workers to be used for multiprocessing

    Returns:
        list: list of function's results
    """
    num_threads = num_threads if isinstance(num_threads, int) else min(16, mp.cpu_count())
    if num_threads < 2:
        results = map(func, arr)
    else:
        with ThreadPool(num_threads) as tp:
            results = tp.map(func, arr)

    return results


def run_executions_in_parallel(
    funcs: Sequence[Callable[[Inp], Out]],
    arr: Sequence[Inp],
    **kwargs,
) -> Sequence[Out]:
    """Execute distinct function calls in parallel

    Args:
        funcs: function to be executed on multiple workers
        arr: function argument's values
        kwargs: keyword args for `execute_in_parallel`

    Returns:
        list: list of function's results
    """
    return execute_in_parallel(
        lambda fn_arg: fn_arg[0](fn_arg[1]),
        zip(funcs, arr),
        **kwargs,
    )
