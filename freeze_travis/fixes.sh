#!/bin/bash

# matplotlib backend workaround
mkdir $HOME/.matplotlib
echo "backend: TkAgg" >> $HOME/.matplotlib/matplotlibrc
