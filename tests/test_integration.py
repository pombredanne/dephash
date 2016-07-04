#!/usr/bin/env python
"""Integration tests for dephash
"""
import logging
import os
import pytest
import random
import dephash
import shutil
import string
import sys
import tempfile

from . import DATA_DIR, read_file

SKIP_REASON = "NO_TESTS_OVER_WIRE: skipping integration test"

# params {{{1
# Run integration 'dephash gen' tests against the already pinned+hashed
# requirements files, so we know what versions + hashes to expect.
GEN_PARAMS = [
    os.path.join(DATA_DIR, "prod1.txt"),
]
if sys.version_info >= (3, 5):
    GEN_PARAMS.append(os.path.join(DATA_DIR, "prod2.txt"))
PROD_REQ_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'requirements-prod.txt')


# gen tests against test prod.txt reqfiles {{{1
@pytest.mark.skipif(os.environ.get("NO_TESTS_OVER_WIRE"), reason=SKIP_REASON)
@pytest.mark.parametrize("req_path", GEN_PARAMS)
def test_gen(req_path, mocker):
    try:
        _, tmppath = tempfile.mkstemp()
        mocker.patch.object(sys, 'argv', new=["dephash", "gen", "-o", tmppath, req_path])
        with pytest.raises(SystemExit):
            dephash.cli()
        output = read_file(tmppath)
        assert output == read_file(req_path)
    finally:
        os.remove(tmppath)


@pytest.mark.skipif(os.environ.get("NO_TESTS_OVER_WIRE"), reason=SKIP_REASON)
@pytest.mark.parametrize("req_path", GEN_PARAMS)
def test_gen_cmdln(req_path, mocker):
    logger = logging.getLogger(
        ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits)
                for _ in range(6))
    )
    mocker.patch.object(dephash, 'log', new=logger)
    try:
        _, logfile = tempfile.mkstemp()
        _, output_file = tempfile.mkstemp()
        mocker.patch.object(sys, 'argv', new=["dephash", "-v", "-l", logfile, "gen", req_path])
        with open(output_file, "w") as fh:
            mocker.patch.object(sys, 'stdout', new=fh)
            with pytest.raises(SystemExit):
                dephash.main()
        output = read_file(output_file)
        assert output == read_file(req_path)
    finally:
        os.remove(output_file)
        os.remove(logfile)


# outdated tests against PROD_REQ_PATH {{{1
@pytest.mark.skipif(os.environ.get("NO_TESTS_OVER_WIRE"), reason=SKIP_REASON)
def test_outdated_req(mocker):
    try:
        _, tmppath = tempfile.mkstemp()
        mocker.patch.object(sys, 'argv', new=["dephash", "-v", "-l", tmppath,
                                              "outdated", PROD_REQ_PATH])
        try:
            dephash.cli()
        except SystemExit as e:
            with open(tmppath, "r") as fh:
                print(fh.read())
            assert e.code == 0, "This test may fail if there are new dependencies on pypi"
    finally:
        os.remove(tmppath)


@pytest.mark.skipif(os.environ.get("NO_TESTS_OVER_WIRE"), reason=SKIP_REASON)
def test_outdated_venv(mocker):
    # create venv
    try:
        venv_path = tempfile.mkdtemp()
        dephash.create_virtualenv('virtualenv', venv_path, PROD_REQ_PATH)
        mocker.patch.object(sys, 'argv', new=["dephash", "-v", "outdated", venv_path])
        try:
            dephash.main()
        except SystemExit as e:
            assert e.code == 0, "This test may fail if there are new dependencies on pypi"
    finally:
        shutil.rmtree(venv_path)
