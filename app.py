import streamlit as st 
import numpy as np 
import pandas as pd 
import matplotlib.pyplot as plt
from PIL import Image

from utils import CohortAnalyzer#, ExcelDataReader

#############
DATASET_PATH = 'biz_module_selection.csv'
IMAGE_PATH = 'icon.png'
#############

st.title('Cohort Analysis of Module Selection')
st.markdown('_Designed by UROP Student Han Jiatong_ | NUS WING Group')

st.sidebar.header('Dashboard Demo')
st.sidebar.markdown('    \- progress as at June 2nd')

# image = Image.open(IMAGE_PATH)
# st.sidebar.image(image, )

with st.sidebar.beta_expander("Notes to take"):
  st.markdown("""
                      1. The data is confidential; this demo version is only using some fake enrolment data for illustration purpose;
                      2. The app is updated and functional until 2nd June;
                      3. The source code is openly shared under MIT license.
                      """)
 
  

faculty = st.selectbox('Select a faculty to explore',('Business School','School of Computing','Faculty of Arts and Social Sciences'))
st.write('You selected',faculty)

module = pd.read_csv(DATASET_PATH)

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
      mod_info = analyzer.mod_info.reset_index()
      st.dataframe(mod_info)
      mod_info = None
  fig = analyzer.plot_popular_modules()
  st.plotly_chart(fig, use_container_width=True)

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
  st.markdown('Modules are sorted based on their enrolment differences in descending order.')
  with st.echo():
    analyzer.integrate_module_information() # in case not called above.
    analyzer.get_most_different_modules()
    analyzer.plot_topk_diff_mod_info(k=10)
   
  fig = analyzer.plot_topk_diff_mod_info()
  st.plotly_chart(fig, use_container_width=True)

  
with st.beta_expander("Principal component analysis"):
  st.markdown('Utilize dimension reduction tool (e.g. SVD) to find the principal components.')
  col1, col2 = st.beta_columns(2)
  with col1:
    n_components = st.number_input("Number of components to keep: (Default 5)", min_value=2, max_value=10, value=5)
    st.write(n_components,"PCs are selected")
  with col2:
    n_mods = st.number_input("Number of modules to show in graph: (Default 10)", min_value=5, max_value=15, value=10, help="Top N most different modules")
    st.write(n_mods,"modules are selected")
  
  with st.echo():
    mod_pc_diff, fig = analyzer.PCAnalysis(n_components=n_components, topkmods=n_mods)
  
  st.subheader("Dataframe Results:")
  st.dataframe(mod_pc_diff)
  mod_pc_diff = None
  
  st.subheader("Plot the top "+str(n_mods)+" most different modules:")
  st.plotly_chart(fig, use_container_width=True)
  
  
with st.beta_expander("Attribute percentage analysis"):
  attr = st.selectbox('Select an attribute to explore',('grading_basis', 'mod_faculty', 'mod_activity_type', 'mod_level'),index=1)
  st.write('You selected',attr)
  
  with st.echo():
    mod_attr_perc_change, fig = analyzer.attr_perc_change(attr=attr)
    
#   st.subheader("Dataframe Results:")
#   st.dataframe(mod_attr_perc_change)
#   mod_attr_perc_change = None
  
  st.subheader("Plot the percentage difference for {}:".format(attr))
  st.plotly_chart(fig, use_container_width=True)  
  

                                            
  
