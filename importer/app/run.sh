#!/bin/bash
python -u get_symbols.py &
python -u get_stream.py &
python -u get_history.py