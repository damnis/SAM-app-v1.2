import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta, date, time
import matplotlib.pyplot as plt
from ta.trend import ADXIndicator
import matplotlib.dates as mdates
from yffetch import fetch_data, fetch_data_cached 
from fmpfetch import fetch_data_fmp
from sam_indicator import calculate_sam 
from sat_indicator import calculate_sat 
from adviezen import determine_advice 
from streamlit.components.v1 import html as st_html







