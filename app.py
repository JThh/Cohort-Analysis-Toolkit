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

faculty = st.selectbox('Select a faculty to explore',('Business School','School of Computing','Faculty of Arts and Social Sciences'))
st.write('You selected',faculty)

module = pd.read_csv(PATH)

col1, col2 = st.beta_columns(2)

with col1:
  cohort1 = st.number_input('Select a cohort to compare',min_value=10,max_value=18)
  st.write(cohort1,'selected')

with col2:
  cohort2 = st.number_input('Select another cohort to compare with cohort1',min_value=cohort1+1,max_value=18,help='preferably larger than'+str(cohort1))
  st.write(cohort2,'selected')

analyzer = CohortAnalyzer(module, cohort1, cohort2)
st.write('Cohort Analyzer installed and ready.')

with st.beta_expander("Processed Dataframe"):
  col1, col2 = st.beta_columns(2)

  with col1:
    st.subheader("Module enrolment data")
    st.dataframe(analyzer.mod_agg)

  with col2:
    st.subheader("Module information data")
    add_info = st.checkbox("Whether to add module information?",help="Module information is inclusive of module faculty, module level, etc.")
    if add_info:
      analyzer.integrate_module_information()
      st.dataframe(analyzer.mod_info)

with st.beta_expander("Statistical Analysis"):
  st.markdown('Conduct statistical tests to check whether there are significant differences betweent the cohorts.')
  with st.echo():
    analyzer.stata_analysis()
  t_sta_ttest, p_val_ttest, t_sta_oneway, p_val_oneway = analyzer.stata_analysis()
  
  st.write("Results from t test: t-statistics:",t_sta_ttest,'p value:',p_val_ttest)
  if p_val_ttest < 0.05:
    st.write("Thus, their means are significantly different.")
  else:
    st.write("Thus, there is no significant difference between their means")
    
  st.write("Results from ANOVA test: t-statistics:",t_sta_oneway,'p value:',p_val_oneway)
  
  if p_val_oneway < 0.05:
    st.write("Thus, their variances are significantly different.")
  else:
    st.write("Thus, there is no significant difference between their variances")
    
  

with st.beta_expander("Module enrolment difference analysis"):
  st.markdown('Modules are sorted based on their enrolment differences between cohorts in descending order.')
  with st.echo():
    analyzer.get_most_different_modules()
    analyzer.plot_topk_diff_mod_info(k=10)
   
  

                                            
  
