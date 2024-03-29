import streamlit as st
import numpy as np
import pandas as pd

# import matplotlib.pyplot as plt
# from PIL import Image

from CohortAnalyzer import CohortAnalyzer  # , ExcelDataReader


############################### STRICTLY CONFIDENTIAL ################################
FACULTY_MAP = {
    "BIZ": "Business School",
    "SoC": "School of Computing",
    "FASS": "Faculty of Arts and Social Sciences",
}
# FILE_NAME_MOD = 'modules.csv'
# FILE_NAME_STU = 'programs.csv'
# IMAGE_PATH = '../assets/icon.png'
######################################################################################


st.set_page_config(layout="wide")

st.title("Cohort Analysis of Module Selection")
st.markdown("_Designed by UROP Student Han Jiatong_ | NUS WING Group")

st.sidebar.header("Dashboard Demo")
# st.sidebar.markdown('    \- progress as at June 2nd')

# image = Image.open(IMAGE_PATH)
# st.sidebar.image(image, )

with st.sidebar.expander("Notes"):
    st.markdown(
        """
                      1. The data is confidential; this demo version is only using some fake enrolment data for illustration purpose;
                      2. The app is last updated on 8th Oct, 2022;
                      3. The source code is openly shared under Apache license.
                      """
    )
st.sidebar.markdown(
    """_Version 1.4.0 | Oct 8th 2022_""".format(unsafe_allow_html=True)
)


# selected_faculty = st.multiselect('Select one or more faculty(s) to explore',('Business School','School of Computing','Faculty of Arts and Social Sciences'),('Business School'),lambda x:FACULTY_MAP[x])
selected_faculty = st.multiselect(
    "Select one or more faculty(s) to explore",
    ("BIZ", "SoC", "FASS"),
    ("BIZ"),
    lambda x: FACULTY_MAP[x],
)

# st.write('You selected',selected_faculty)
if not selected_faculty:
    st.warning("At least select one faculty!")

module = pd.read_csv(st.secrets["PATH_MOD"])
module = module[[x in selected_faculty for x in module.Faculty]]
student = pd.read_csv(st.secrets["PATH_STU"])
student = student[[x in selected_faculty for x in student.faculty_descr]]

col1, col2 = st.columns(2)

with col1:
    cohort1 = st.number_input(
        "Select a cohort to compare (10-14)", min_value=10, max_value=14
    )
    st.write(cohort1, "selected")

with col2:
    cohort2 = st.number_input(
        "Select another cohort to compare with cohort1",
        min_value=cohort1 + 1,
        max_value=15,
        help="preferably larger than" + str(cohort1),
    )
    st.write(cohort2, "selected")

# try:
#     analyzer = CohortAnalyzer(module, student, cohort1, cohort2)
# except:
#     st.error(
#         "Analyzer loading error. Please try again or select different cohorts to compare!"
#     )

analyzer = CohortAnalyzer(module, student, cohort1, cohort2)

st.write("Cohort Analyzer installed and ready.")

with st.expander("Processed Dataframe"):
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
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Module enrolment data")
        st.dataframe(analyzer.mod_agg.head(30))

    with col2:
        st.subheader("Module information data")
        # add_info = st.checkbox(
        #     "Whether to process module information?",
        #     help="Module information is inclusive of module faculty, module level, etc.",
        # )
        # if add_info:
        analyzer.process_module_information()
        mod_info = analyzer.mod_info.reset_index().copy()
        st.dataframe(mod_info.head(30))
        mod_info = None
    # analyzer.process_module_information()  # in case not called above.

    st.subheader("Most enroled modules in both cohorts")
    fig = analyzer.plot_topk_popular_modules()
    st.plotly_chart(fig, use_container_width=True)
    fig = None

with st.expander("Statistical Analysis"):
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


with st.expander("Module enrolment difference analysis"):
    st.subheader("Student level analysis")
    st.markdown(
        "Select a random student from each cohort to compare their module selection patterns"
    )
    attr_input = st.selectbox(
        "Choose which property to observe",
        ("grading_basis", "mod_faculty", "mod_activity_type", "mod_level"),
        index=1,
    )

    col1, col2, col3 = st.columns([2, 1, 1])

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

    col1, col2 = st.columns(2)

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


with st.expander("Principal component analysis"):
    st.markdown(
        "Utilize dimension reduction tool (e.g. SVD) to find the principal components."
    )
    col1, col2 = st.columns(2)
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

    mod_pc_diff, pca_fig, fig = analyzer.PCAnalysis(
        n_components=n_components, topkmods=k_mods
    )

    st.plotly_chart(pca_fig, use_container_width=True)

    st.subheader("Dataframe Results:")
    st.dataframe(mod_pc_diff.sample(30).reset_index(drop=True))
    mod_pc_diff = None

    st.subheader("Plot the top " + str(k_mods) + " most different modules:")
    st.plotly_chart(fig, use_container_width=True)
    fig = None


with st.expander("Attribute percentage analysis"):
    stu_attr_list = analyzer.academic_plans

    col1, col2 = st.columns(2)

    stu_attr = None
    with col1:
        if len(stu_attr_list) > 0:
            stu_attr = st.selectbox(
                "Select a student academic plan to explore", ['Faculty-level']+stu_attr_list, index=1
            )
            st.write("You selected", stu_attr)
            
            if stu_attr == 'Faculty-level':
                stu_attr = None

        else:
            #stu_attr = None,
            st.write("No available student academic plans to explore. Please proceed.")

    with col2:
        mod_attr = st.selectbox(
            "Select an attribute to explore",
            (
                "grading_basis",
                "mod_faculty",
                "mod_activity_type",
                "mod_level",
                "mod_department",
            ),
            index=1,
        )
        st.write("You selected", mod_attr)

    with st.echo():
        mod_attr_perc_change, ent1, ent2, fig1, fig2, fig = analyzer.attr_perc_change(
            stu_attr=stu_attr, mod_attr=mod_attr
        )

    #   st.subheader("Dataframe Results:")
    #   st.dataframe(mod_attr_perc_change)
    #   mod_attr_perc_change = None

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Cohort " + str(cohort1))
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("Cohort " + str(cohort2))
        st.plotly_chart(fig2, use_container_width=True)

    st.write("Delta Entropy:", ent2 - ent1)

    st.subheader("Plot the percentage difference for {}:".format(mod_attr))
    st.plotly_chart(fig, use_container_width=True)
    fig = None
