import streamlit as st 
import numpy as np 
import pandas as pd 
import matplotlib.pyplot as plt
from PIL import Image

from utils import CohortAnalyzer#, ExcelDataReader

############################### STRICTLY CONFIDENTIAL ################################
MODULE_PATH = 'https://drive.google.com/file/d/1Ys8k21kA6AvSHEHvZnMKFCS-VTAYveAj/view?usp=sharing'
STUDENT_PATH = 'https://drive.google.com/file/d/1aoszzf2FtJD_ijv7tCmLFap0CEdaRcrL/view?usp=sharing'
MODULE_FILE_NAME = 'modules.csv'
STUDENT_FILE_NAME = 'programs.csv'
#IMAGE_PATH = 'icon.png'
######################################################################################


################################ AUXILIARY FUNCTIONS ##################################
def loadDataFromDrive(dataLink, fileName):
  '''
    dataLink: link obtained from the right button option 'get shareable link' in drive
    fileName: name of the file in frive
  '''
  # Code to read csv file into Colaboratory:
  get_ipython().system('pip install -U -q PyDrive')
  from pydrive.auth import GoogleAuth
  from pydrive.drive import GoogleDrive
  from google.colab import auth
  from oauth2client.client import GoogleCredentials
  # Authenticate and create the PyDrive client:
  auth.authenticate_user()
  gauth = GoogleAuth()
  gauth.credentials = GoogleCredentials.get_application_default()
  drive = GoogleDrive(gauth)
  # get the ID from the data link:
  fluff, id = dataLink.split('id=')
  downloaded = drive.CreateFile({'id':id}) 
  downloaded.GetContentFile(fileName+'.csv')  
    
  import pandas as pd
  data_final_obj = pd.read_csv(fileName+'.csv')
  
  return data_final_obj
######################################################################################


st.title('Cohort Analysis of Module Selection')
st.markdown('_Designed by UROP Student Han Jiatong_ | NUS WING Group')

st.sidebar.header('Dashboard Demo')
#st.sidebar.markdown('    \- progress as at June 2nd')

# image = Image.open(IMAGE_PATH)
# st.sidebar.image(image, )

with st.sidebar.beta_expander("Cautions"):
  st.markdown("""
                      1. The data is confidential; this demo version is only using some fake enrolment data for illustration purpose;
                      2. The app is updated and functional until 2nd June;
                      3. The source code is openly shared under MIT license.
                      """)
st.sidebar.markdown("""_Version 1.0.0 | June 2021_""".format(unsafe_allow_html=True))
 
  

selected_faculty = st.multiselectbox('Select one or more faculty(s) to explore',('Business School','School of Computing','Faculty of Arts and Social Sciences'),('Business School'))
st.write('You selected',selected_faculty)

module = loadDataFromDrive(MODULE_PATH, MODULE_FILE_NAME)[[x in selected_faculty for x in module.faculty]].drop(['faculty'],axis=1)
student = loadDataFromDrive(STUDENT_PATH, STUDENT_FILE_NAME)[[x in selected_faculty for x in student.faculty]].drop(['faculty'],axis=1)

col1, col2 = st.beta_columns(2)

with col1:
  cohort1 = st.number_input('Select a cohort to compare',min_value=10,max_value=18)
  st.write(cohort1,'selected')

with col2:
  cohort2 = st.number_input('Select another cohort to compare with cohort1',min_value=cohort1+1,max_value=18,help='preferably larger than'+str(cohort1))
  st.write(cohort2,'selected')

analyzer = CohortAnalyzer(module, student, cohort1, cohort2)
st.write('Cohort Analyzer installed and ready.')

with st.beta_expander("Processed Dataframe"):
  coht1_stu_count, coht2_stu_count, coht1_mod_count, coht2_mod_count = analyzer.get_student_and_module_count()
  st.write('The total students and modules of interest are',coht1_stu_count,'students for cohort',cohort1,',',coht2_stu_count,'students for cohort',cohort2,';', coht1_mod_count,'modules for cohort',cohort1,',',coht2_mod_count,'modules for cohort',cohort2,'.')
  col1, col2 = st.beta_columns(2)

  with col1:
    st.subheader("Module enrolment data")
    st.dataframe(analyzer.mod_agg.head(30))

  with col2:
    st.subheader("Module information data")
    add_info = st.checkbox("Whether to integrate module information?",help="Module information is inclusive of module faculty, module level, etc.")
    if add_info:
      analyzer.integrate_module_information()
      mod_info = analyzer.mod_info.reset_index()
      st.dataframe(mod_info.head(30))
      mod_info = None
  analyzer.integrate_module_information() # in case not called above.
  
  st.subheader('Most enroled modules in both cohorts')
  fig = analyzer.plot_topk_popular_modules()
  st.plotly_chart(fig, use_container_width=True)
  fig=None

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
  top_k = st.number_input('Top k modules',min_value=5, max_value=20, value=10, help='shown on the graph in sorted order')
  st.write(top_k,'modules are selected')
  with st.echo():
    analyzer.find_most_different_modules() # Find the differences and sort them.
    fig = analyzer.plot_topk_diff_mod_info(k=top_k)
   
  st.plotly_chart(fig, use_container_width=True)
  fig=None

  
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
  st.dataframe(mod_pc_diff.head(30))
  mod_pc_diff = None
  
  st.subheader("Plot the top "+str(n_mods)+" most different modules:")
  st.plotly_chart(fig, use_container_width=True)
  fig=None
  
  
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
  fig=None

                                            
  
