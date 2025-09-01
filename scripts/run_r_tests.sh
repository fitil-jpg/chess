#!/bin/bash
set -e
Rscript -e 'testthat::test_dir("tests/testthat", reporter="summary")'
