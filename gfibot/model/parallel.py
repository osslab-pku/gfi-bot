# Run func(args) concurrently and aggregate the results
# author: @hehao98 <heh@pku.edu.cn>, @12f23eddde <12f23eddde@gmail.com>

import logging
import time
from typing import Callable, Iterable, Optional, Tuple, TypeVar, Union

import pandas as pd
from multiprocess import Pool, cpu_count
from tqdm.auto import tqdm

T = TypeVar("T")
U = TypeVar("U")
SupportedFuncType = Callable[[U], T]
AggFuncType = Callable[[Optional[T], Optional[T]], T]


def _get_default_n_workers(total: int = 512) -> int:
    return min(total, int(cpu_count() / 3 * 2))


def agg_sum(
    r: Optional[Union[int, float]], s: Optional[Union[int, float]]
) -> Union[int, float]:
    if r is None:
        return 0
    return r + s


def agg_append_df(r: Optional[pd.DataFrame], s: Optional[pd.DataFrame]) -> pd.DataFrame:
    if r is None:
        return pd.DataFrame()
    return pd.concat([r, s])


def parallel(
    func: SupportedFuncType,
    args: Iterable[U],
    agg_func: Optional[AggFuncType] = None,
    n_workers: Optional[int] = None,
    total: Optional[int] = None,
    progress_bar=tqdm,
):
    """
    Wraps multiprocessing.pool;
    :param func: function to parallel (accepts only 1 parameter)
    :param args: iterable containing function arguments
    :param agg_func: function to aggregate the results (default: returns None)
    :param n_workers: # of worker processes (default: max(4, 2/3 core count))
    :param total: # of iterations (default: len(args))
    :param progress_bar: tqdm instance (default: tqdm.auto)
    ---
    Example:
    ```python
    def func_to_parallel(a: int = 1, b: int = 2) -> pd.DataFrame:
        time.sleep(a+b)
        return pd.DataFrame([{"sum": a+b}])
    def wrapper(args: Tuple[int, int]) -> pd.DataFrame:
        return func_to_parallel(*args)
    res = parallel(wrapper, [(0, 1), (1, 2), (2, 3)], agg_func=agg_append_df)
    print(res.head())
    ```
    """
    if not total:
        total = len(args)
    if not n_workers:
        n_workers = _get_default_n_workers(total)

    logging.info("starting %d jobs on %d workers", total, n_workers)
    pool = Pool(n_workers)
    try:
        start = time.time()
        # using multiprocess.imap
        with progress_bar(total=total) as t:
            r = None
            if agg_func is not None:
                r = agg_func(None, None)
            for i in pool.imap_unordered(func, args):
                if agg_func is not None:
                    r = agg_func(r, i)
                t.set_postfix(
                    {"func": func.__name__, "time": "%.1fs" % (time.time() - start)}
                )
                t.update()
            return r
    except Exception as e:
        logging.error("error in parallel: %s", e, exc_info=True)
    finally:
        pool.close()  # close the pool to any new jobs
        pool.join()  # cleanup the closed worker processes


if __name__ == "__main__":

    def func_to_parallel(a: int = 1, b: int = 2) -> pd.DataFrame:
        time.sleep(a + b)
        return pd.DataFrame([{"sum": a + b}])

    def wrapper(args: Tuple[int, int]) -> pd.DataFrame:
        return func_to_parallel(*args)

    res = parallel(wrapper, [(0, 1), (1, 2), (2, 3)], agg_func=agg_append_df)
    print(res.head())
