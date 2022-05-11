import sys
from pathlib import Path

from pettingzoo.test import api_test, parallel_api_test

from docs._includes.code import aec_rps
from docs._includes.code import parallel_rps


def test_rps_aec_example():
    api_test(aec_rps.raw_env(), 100)
    api_test(aec_rps.env(), 100)


def test_rps_parallel_example():
    print(type(parallel_rps.raw_env()))
    print(type(parallel_rps.raw_env().env))
    parallel_api_test(parallel_rps.parallel_env(), 100)
    api_test(parallel_rps.raw_env(), 100)
    api_test(parallel_rps.env(), 100)
