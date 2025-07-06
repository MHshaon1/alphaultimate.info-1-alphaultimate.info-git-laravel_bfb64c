import os
import logging

# Configure matplotlib to use non-GUI backend before any imports
import matplotlib
matplotlib.use('Agg')

# Reduce logging noise during startup
logging.getLogger('matplotlib').setLevel(logging.WARNING)

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')