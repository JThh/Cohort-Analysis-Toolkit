import streamlit as st 
import numpy as np 
import pandas as pd 
import matplotlib.pyplot as plt

from utils import CohortAnalyzer#, ExcelDataReader

#############
PATH = 'biz_module_selection.csv'
#############

st.title('Cohort Analysis of Module Selection Pattern')

st.sidebar.title('Dashboard for illustration (not yet finished)')

faculty = st.selectbox('Select a faculty to explore',('Business','Soc','FASS'))
st.write('You selected',faculty)

module = pd.read_csv(PATH)

cohort1 = st.number_input('Select a cohort to compare',min_value=10,max_value=18)
st.write(cohort1,'selected')

cohort2 = st.number_input('Select another cohort to compare with the previous one'+cohort1,min_value=cohort1,max_value=18,help='preferably larger than'+cohort1)
st.write(cohort2,'selected')

analyzer = CohortAnalyzer(module, cohort1, cohort2)


                                            
  
