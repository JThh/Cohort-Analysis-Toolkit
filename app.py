import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image

from utils import CohortAnalyzer  # , ExcelDataReader

############################### STRICTLY CONFIDENTIAL ################################
DRIVE_URL_MOD = (
    "https://drive.google.com/file/d/1--KTK4vU5cA1akMGcIsHBmfo3FVfJSdp/view?usp=sharing"
)
DRIVE_URL_STU = (
    "https://drive.google.com/file/d/1aoszzf2FtJD_ijv7tCmLFap0CEdaRcrL/view?usp=sharing"
)
PATH_MOD = (
    "https://drive.google.com/uc?export=download&id=" + DRIVE_URL_MOD.split("/")[-2]
)
PATH_STU = (
    "https://drive.google.com/uc?export=download&id=" + DRIVE_URL_STU.split("/")[-2]
)
FACULTY_MAP = {
    "BIZ": "Business School",
    "SoC": "School of Computing",
    "FASS": "Faculty of Arts and Social Sciences",
}
# FILE_NAME_MOD = 'modules.csv'
# FILE_NAME_STU = 'programs.csv'
# IMAGE_PATH = 'icon.png'
######################################################################################

st.set_page_config(layout="wide")

st.title("Cohort Analysis of Module Selection")
st.markdown("_Designed by UROP Student Han Jiatong_ | NUS WING Group")

st.sidebar.header("Dashboard Demo")
# st.sidebar.markdown('    \- progress as at June 2nd')

# image = Image.open(IMAGE_PATH)
# st.sidebar.image(image, )

with st.sidebar.beta_expander("Notes"):
    st.markdown(
        """
                      1. The data is confidential; this demo version is only using some fake enrolment data for illustration purpose;
                      2. The app is updated and functional until 2nd June;
                      3. The source code is openly shared under MIT license.
                      """
    )
st.sidebar.markdown(
    """_Version 1.1.0 | June 4th 2021_""".format(unsafe_allow_html=True)
)


# selected_faculty = st.multiselect('Select one or more faculty(s) to explore',('Business School','School of Computing','Faculty of Arts and Social Sciences'),('Business School'),lambda x:FACULTY_MAP[x])
selected_faculty = st.multiselect(
    "Select one or more faculty(s) to explore",
    ("BIZ", "SoC", "FASS"),
    ("BIZ"),
    lambda x: FACULTY_MAP[x],
)

# st.write('You selected',selected_faculty)


module = pd.read_csv(PATH_MOD)
module = module[[x in selected_faculty for x in module.Faculty]]
student = pd.read_csv(PATH_STU)
student = student[[x in selected_faculty for x in student.faculty_descr]]

col1, col2 = st.beta_columns(2)

with col1:
    cohort1 = st.number_input("Select a cohort to compare", min_value=10, max_value=18)
    st.write(cohort1, "selected")

with col2:
    cohort2 = st.number_input(
        "Select another cohort to compare with cohort1",
        min_value=cohort1 + 1,
        max_value=18,
        help="preferably larger than" + str(cohort1),
    )
    st.write(cohort2, "selected")

analyzer = CohortAnalyzer(module, student, cohort1, cohort2)
st.write("Cohort Analyzer installed and ready.")

with st.beta_expander("Processed Dataframe"):
    (
        coht1_stu_count,
        coht2_stu_count,
        coht1_mod_count,
        coht2_mod_count,
    ) = analyzer.get_student_and_module_count()
    st.write(
        "The total students and modules of interest are",
        coht1_stu_count,
        "students for cohort",
        cohort1,
        ",",
        coht2_stu_count,
        "students for cohort",
        cohort2,
        ";",
        coht1_mod_count,
        "modules for cohort",
        cohort1,
        ",",
        coht2_mod_count,
        "modules for cohort",
        cohort2,
        ".",
    )
    col1, col2 = st.beta_columns(2)

    with col1:
        st.subheader("Module enrolment data")
        st.dataframe(analyzer.mod_agg.head(30))

    with col2:
        st.subheader("Module information data")
        # add_info = st.checkbox(
        #     "Whether to integrate module information?",
        #     help="Module information is inclusive of module faculty, module level, etc.",
        # )
        # if add_info:
        analyzer.integrate_module_information()
        mod_info = analyzer.mod_info.reset_index().copy()
        st.dataframe(mod_info.head(30))
        mod_info = None
    # analyzer.integrate_module_information()  # in case not called above.

    st.subheader("Most enroled modules in both cohorts")
    fig = analyzer.plot_topk_popular_modules()
    st.plotly_chart(fig, use_container_width=True)
    fig = None

with st.beta_expander("Statistical Analysis"):
    st.markdown(
        "Conduct statistical tests to check whether there are significant differences betweent the cohorts."
    )
    with st.echo():
        analyzer.stata_analysis()
    t_sta_ttest, p_val_ttest, t_sta_oneway, p_val_oneway = analyzer.stata_analysis()

    st.write("Results from t test: t-statistics:", t_sta_ttest, "p value:", p_val_ttest)
    if p_val_ttest < 0.05:
        st.write("Thus, their means are significantly different.")
    else:
        st.write("Thus, there is no significant difference between their means")

    st.write(
        "Results from ANOVA test: t-statistics:", t_sta_oneway, "p value:", p_val_oneway
    )

    if p_val_oneway < 0.05:
        st.write("Thus, their variances are significantly different.")
    else:
        st.write("Thus, there is no significant difference between their variances")


with st.beta_expander("Module enrolment difference analysis"):
    st.subheader("Student level analysis")
    st.markdown(
        "Select a random student from each cohort to compare their module selection patterns"
    )
    attr_input = st.selectbox(
        "Choose which property to observe",
        ("grading_basis", "mod_faculty", "mod_activity_type", "mod_level"),
        index=1,
    )

    col1, col2, col3 = st.beta_columns([2, 1, 1])

    with col1:
        min_num_mods = st.slider(
            "Minimum number of modules taken", min_value=0, max_value=16, value=10
        )
        st.write(min_num_mods, "selected")

    with col2:
        num_students = st.number_input(
            "Number of students",
            min_value=1,
            max_value=10,
            value=1,
            help="How many students to sample from each cohort; default 1",
        )
        st.write(num_students, "selected")

    with col3:
        seed = st.number_input(
            "Choose a random state",
            value=167,
            help="Choose a random state to sample students; default 167",
        )
        st.write(seed, "selected")

    (
        rand_stu_num_of_mod1,
        rand_stu_num_of_mod2,
        fig1,
        fig2,
    ) = analyzer.plot_random_student_selection_info(
        attr=attr_input,
        at_least_selecting=min_num_mods,
        random_state=seed,
        num_students=num_students,
    )
    st.write("Analyzer is ready.")

    st.write(
        num_students,
        "random student(s) from cohort",
        cohort1,
        "selected",
        rand_stu_num_of_mod1,
        "distinct modules in that academic year;",
        num_students,
        "random student(s) from cohort",
        cohort2,
        "selected",
        rand_stu_num_of_mod2,
        "distinct modules in that academic year",
    )

    col1, col2 = st.beta_columns(2)

    with col1:
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Module level analysis")
    st.markdown(
        "Modules are sorted based on their enrolment differences in descending order."
    )
    top_k = st.number_input(
        "Top k modules",
        min_value=5,
        max_value=20,
        value=10,
        help="shown on the graph in sorted order",
    )
    st.write(top_k, "modules are selected")
    with st.echo():
        analyzer.find_most_different_modules()  # Find the differences and sort them.
        fig = analyzer.plot_topk_diff_mod_info(k=top_k)

    st.plotly_chart(fig, use_container_width=True)
    fig = None


with st.beta_expander("Principal component analysis"):
    st.markdown(
        "Utilize dimension reduction tool (e.g. SVD) to find the principal components."
    )
    col1, col2 = st.beta_columns(2)
    with col1:
        n_components = st.number_input(
            "Number of components to keep: (Default 4)",
            min_value=2,
            max_value=10,
            value=4,
        )
        st.write(n_components, "PCs are selected")
    with col2:
        k_mods = st.number_input(
            "Number of modules to show in graph: (Default 10)",
            min_value=5,
            max_value=15,
            value=10,
            help="Top K most different modules",
        )
        st.write(k_mods, "modules are selected")

    # with st.echo():
    #     mod_pc_diff, fig = analyzer.PCAnalysis(
    #         n_components=n_components, topkmods=k_mods
    #     )

    mod_pc_diff, pca_fig, fig = analyzer.PCAnalysis(n_components=n_components, topkmods=k_mods)

    st.plotly_chart(pca_fig, use_container_width=True)
        
    st.subheader("Dataframe Results:")
    st.dataframe(mod_pc_diff.sample(30).reset_index(drop=True))
    mod_pc_diff = None

    st.subheader("Plot the top " + str(k_mods) + " most different modules:")
    st.plotly_chart(fig, use_container_width=True)
    fig = None


with st.beta_expander("Attribute percentage analysis"):
    attr = st.selectbox(
        "Select an attribute to explore",
        ("grading_basis", "mod_faculty", "mod_activity_type", "mod_level"),
        index=1,
    )
    st.write("You selected", attr)

    with st.echo():
        mod_attr_perc_change, fig = analyzer.attr_perc_change(attr=attr)

    #   st.subheader("Dataframe Results:")
    #   st.dataframe(mod_attr_perc_change)
    #   mod_attr_perc_change = None

    st.subheader("Plot the percentage difference for {}:".format(attr))
    st.plotly_chart(fig, use_container_width=True)
    fig = None
