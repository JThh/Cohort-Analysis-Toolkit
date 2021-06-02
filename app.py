import streamlit as st 
import numpy as np 
import pandas as pd 
import matplotlib.pyplot as plt

from utils import CohortAnalyzer, ExcelDataReader

########
##Not revealed: temporary parameters
PATH = 'biz.xlsx'
SHEET_NAME = 'module_enrolment'
RANGE_FROM = 'B1'
RANGE_TO = 'P30065'
########


st.title('Cohort Analysis of Module Selection Pattern')

st.sidebar('Dashboard for illustration (not yet finished)')

faculty = st.selectbox('Select a faculty to explore',('Business','Soc','FASS'))
st.write('You selected',faculty)

module = ExcelDataReader(PATH, SHEET_NAME, RANGE_FROM, RANGE_TO).dataframe

cohort1 = st.number_input('Select a cohort to compare')
st.write(cohort1,'selected')

cohort2 = st.number_input('Select another cohort to compare with the previous one (preferably larger than'+cohort1)
st.write(cohort2,'selected')

analyzer = CohortAnalyzer(module, cohort1, cohort2)


                                            
  
