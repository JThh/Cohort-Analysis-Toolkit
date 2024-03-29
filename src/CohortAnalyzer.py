import numpy as np
import pandas as pd

# import matplotlib.pyplot as plt
# import seaborn as sns

# import xlwings as xw

################   GLOBAL VARIABLES   ################
ACADEMIC_YEARS = [10 + x for x in range(9)]
EMROLMENT_ATTRIBUTES = [
    "student_token",
    "term",
    "academic_career",
    "mod_code",
    "mod_name",
    "grading_basis",
    "mod_faculty",
    "mod_department",
    "mod_activity_type",
    "mod_level",
]
STUDENT_ATTRIBUTES = [
    "student_token",
    "term",
    "academic_career",
    "admit_term",
    "academic_plan_descr",
]
######################################################


class CohortAnalyzer:
    def __init__(self, mod_enrol, student_program, coht1, coht2):
        self.coht1 = "Cohort " + str(coht1)
        self.coht2 = "Cohort " + str(coht2)
        assert coht1 in ACADEMIC_YEARS and coht2 in ACADEMIC_YEARS

        for attr in EMROLMENT_ATTRIBUTES:
            assert attr in mod_enrol.columns

        for attr in STUDENT_ATTRIBUTES:
            assert attr in student_program.columns

        self.mod_enrol = mod_enrol
        mod_stu_cross = mod_enrol.merge(
            student_program.drop(["term", "academic_career"], axis=1).drop_duplicates(
                subset=["student_token"]
            ),
            on="student_token",
            how="left",
        )

        self.ds_coht1 = mod_stu_cross[
            [
                int(row.term / 100) == int(row.admit_term / 100) == coht1
                and row.academic_career == "UGRD"
                for row in mod_stu_cross.itertuples()
            ]
        ]
        self.ds_coht2 = mod_stu_cross[
            [
                int(row.term / 100) == int(row.admit_term / 100) == coht2
                and row.academic_career == "UGRD"
                for row in mod_stu_cross.itertuples()
            ]
        ]

        self.ds_coht1["count"] = 1
        self.ds_coht2["count"] = 1

        ds_coht_agg1 = (
            self.ds_coht1[["count", "mod_code"]]
            .groupby(["mod_code"])
            .sum()
            .reset_index()
        )
        ds_coht_agg2 = (
            self.ds_coht2[["count", "mod_code"]]
            .groupby(["mod_code"])
            .sum()
            .reset_index()
        )

        mod_agg = (
            ds_coht_agg1.merge(ds_coht_agg2, on="mod_code")
            .fillna(0)
            .rename({"count_x": self.coht1, "count_y": self.coht2}, axis=1)
        )

        self.mod_agg = mod_agg.fillna(0)
        self.mod_agg["mod_code_hash"] = list(range(mod_agg.shape[0]))

        self.stu_attr_of_interest = "academic_plan_descr"

        academic_plan_list = sorted(
            set(self.ds_coht1.academic_plan_descr.values).intersection(
                set(self.ds_coht2.academic_plan_descr.values)
            ),
            reverse=True,
            key=lambda x: pd.concat(
                [self.ds_coht1, self.ds_coht2]
            ).academic_plan_descr.value_counts()[x],
        )

        # academic_plan_perc = (
        #     mod_stu_cross.academic_plan_descr.value_counts() / mod_stu_cross.shape[0]
        # )

        # Threshold value for selecting student academic plan list
        self.acad_plan_thres = 6
        self.academic_plans = academic_plan_list[: self.acad_plan_thres]

    @property
    def _mod_agg(self):
        return self.mod_agg

    @property
    def _academic_plans(self):
        return self.academic_plans

    def get_student_and_module_count(self):
        return (
            self.ds_coht1.student_token.nunique(),
            self.ds_coht2.student_token.nunique(),
            self.ds_coht1.mod_code.nunique(),
            self.ds_coht2.mod_code.nunique(),
        )

    def process_module_information(self):
        self.kept_attr = [
            "mod_code",
            "grading_basis",
            "mod_faculty",
            "mod_activity_type",
            "mod_level",
            "mod_department",
        ]
        for attr in self.kept_attr:
            assert attr in self.mod_enrol.columns
        mod_info = self.mod_enrol[self.kept_attr].drop_duplicates()

        mod_info_agg = mod_info.groupby(["mod_code"]).agg(
            {
                "grading_basis": " ".join,
                "mod_faculty": min,
                "mod_activity_type": set,
                "mod_level": max,
                "mod_department": max,  # Assume no module belongs to multiple departments
            }
        )

        mod_info = None  # Release the memory.

        # mod_info_agg['mod_faculty'] = mod_info_agg['mod_faculty'].apply(lambda x:x)

        def filter_out_empty(lst):
            try:
                lst.remove(" ")
            except ValueError:
                pass  # do nothing!
            return lst

        mod_info_agg.mod_activity_type = (
            mod_info_agg.mod_activity_type.apply(list)
            .apply(filter_out_empty)
            .apply(sorted)
            .apply(",".join)
        )

        # Rules of cleaning grading basis.
        def clean_grading_basis(string):
            if "CSU" in string:
                return "CSU"
            elif "SNU" in string:
                return "SNU"
            elif "GRD" in string:
                return "GRD"
            else:
                return "NON"

        mod_info_agg.loc[:, "grading_basis"] = mod_info_agg.loc[
            :, "grading_basis"
        ].apply(clean_grading_basis)

        # Rehash department names
        faculty_x_department = (
            mod_info_agg[["mod_department", "mod_faculty"]]
            .groupby(["mod_faculty"])
            .agg({"mod_department": set})
            .reset_index()
        )

        faculty_short_names_mapping = {
            'ARTS & SOCIAL SCIENCES': 'FASS',
            'SCHOOL OF BUSINESS': 'BIZ',
            'ENGINEERING': 'ENG',
            'NON-FACULTY-BASED DEPARTMENTS': 'NON_FAC',
            'SCIENCE': 'FoS',
            'SCHOOL OF COMPUTING': 'SoC',
            'UNIVERSITY SCHOLARS PROGRAMME': 'USP',
            'SCHOOL OF DESIGN AND ENVIRONMENT': 'SDE',
            'SAW SWEE HOCK SCHOOL OF PUBLIC HEALTH': 'SSHSPH',
            'YONG LOO LIN SCHOOL OF MEDICINE': 'YLLSM',
            'LEE KUAN YEW SCHOOL OF PUBLIC POLICY': 'LKYSPP',
            'YONG SIEW TOH CONSERVATORY OF MUSIC': 'YSTCM',
            'NUS ENTERPRISE':'ENT',
            'SPECIALITY RESEARCH INSTITUTES/CENTRES': 'SRI/C',
            'LAW': 'LAW',
            'UNIVERSITY ADMINISTRATION': 'UniAdmin',
            'JOINT MULTI-DISCIPLINARY PROGRAMMES': 'JMDP',
            'SCHOOL OF CONTINUING & LIFELONG EDN': 'SCLE',
            'NUS GRAD SCH FOR INTEGRATIVE SCI & ENGG': 'NGSFISE',
            'n.a.': 'N.A.'
        }


        faculty_x_department["mod_dep_rehash"] = [
            list(
                map(
                    lambda n: faculty_short_names_mapping[row.mod_faculty] + "-dep" + str(n),
                    list(range(1, len(row.mod_department) + 1)),
                )
            )
            for row in faculty_x_department.itertuples()
        ]

        faculty_x_department["mod_dep_mapping"] = [
            dict(zip(list(row.mod_department), row.mod_dep_rehash))
            for row in faculty_x_department.itertuples()
        ]

        departments_map = dict()

        for mapping in faculty_x_department.mod_dep_mapping:
            departments_map.update(mapping)

        faculty_x_department = None  # Recycle the memory

        mod_info_agg.loc[:, "mod_department"] = mod_info_agg.loc[
            :, "mod_department"
        ].apply(lambda x: departments_map[x])

        self.mod_info = mod_info_agg.reset_index()
        print("Module information successfully processed.")

    @property
    def _mod_info(self):
        return self.mod_info

    def stata_analysis(self):
        from scipy.stats import ttest_ind, f_oneway

        # print('Running t-test')
        t_sta_ttest, p_value_ttest = ttest_ind(
            self.mod_agg[self.coht1], self.mod_agg[self.coht2]
        )
        # print('t test result: t-statistics:',t-sta,',p value:'p_value)
        # if p_value < 0.05:
        #     print("There is significant difference in the mean student enrolments between two cohorts. And the p-value for t test is",p_value)
        # else:
        #     print("There isn't significant difference in the mean student enrolments between two cohorts.")

        # print('Running one-way anova test')
        t_sta_oneway, p_value_oneway = f_oneway(
            self.mod_agg[self.coht1], self.mod_agg[self.coht2]
        )
        # print('ANOVA test result: t-statistics:',t-sta,',p value:'p_value)
        # if p_value < 0.05:
        #     print("There is significant difference in the selection variances between two cohorts. And the p-value for anova test is",p_value)
        # else:
        #     print("There isn't significant difference in the selection variances between two cohorts.")

        return map(
            lambda x: float("{:.3f}".format(x)),
            (t_sta_ttest, p_value_ttest, t_sta_oneway, p_value_oneway),
        )

    def plot_topk_popular_modules(self, k=10):
        """
        Plot the module enrolment sorted by module popularity.
        Note that process_module_information() needs to be run first.
        :param thres: Filter only modules with at least thres amount of students enrolled.
        """
        # Sort the modules by the sum of enrolled students in the two academic years.
        mod_agg_sorted = self.mod_agg.iloc[
            (self.mod_agg[self.coht1] + self.mod_agg[self.coht2])
            .sort_values(ascending=False)
            .index,
            :,
        ].reset_index(drop=True)

        # Filter modules with total enrolment > thres
        # mod_agg_sorted_filter = mod_agg_sorted[[x > thres for x in (mod_agg_sorted[self.coht1] + mod_agg_sorted[self.coht2]).values]]

        mod_melted = pd.melt(
            mod_agg_sorted.iloc[:k, :].drop(["mod_code"], axis=1),
            id_vars="mod_code_hash",
        )

        mod_agg_sorted_info = mod_agg_sorted.merge(self.mod_info, on="mod_code")

        for attr in self.kept_attr:
            mod_melted[attr] = mod_agg_sorted_info.loc[: k - 1, attr].tolist() * 2

        import plotly.express as px

        fig = px.bar(
            mod_melted,
            x="mod_code_hash",
            y="value",
            color="variable",
            barmode="group",
            hover_data=self.kept_attr,
        )
        fig.update_xaxes(type="category")
        return fig
        # print("It is advised to clear the cache each time after running a graphing function!")

    def find_most_different_modules(self, verbose=1):
        """
        Obtain the module list sorted by normalized enrolment difference between the two academic years.
        :param n: Keep top n most different modules.
        """
        # Modules with the largest differences
        mod_agg = self.mod_agg.copy()

        mod_agg["diff_"] = abs(mod_agg[self.coht1] - mod_agg[self.coht2])
        mod_agg["normalized_diff"] = abs(
            mod_agg[self.coht1] - mod_agg[self.coht2]
        ) / mod_agg[[self.coht1, self.coht2]].max(axis=1)

        mod_code_sorted_by_diff = (
            mod_agg[["mod_code", self.coht1, self.coht2]]
            .iloc[
                (mod_agg.diff_ * mod_agg.normalized_diff)
                .sort_values(ascending=False)
                .index,
                :,
            ]
            .reset_index(drop=True)
        )

        mod_code_sorted_by_diff.reset_index(inplace=True)

        self.mod_code_sorted_by_diff = mod_code_sorted_by_diff
        # mod_diff_melted = pd.melt(mod_code_sorted_by_diff.iloc[:n,:].drop(['mod_code'],axis=1),id_vars='index')

        # sns.factorplot(x='index',y='value',hue='variable',data=mod_diff_melted,kind='bar')
        # plt.show()
        if verbose == 1:
            print("Most different module list obtained.")

    def plot_random_student_selection_info(
        self,
        attr="mod_faculty",
        at_least_selecting=10,
        random_state=167,
        num_students=1,
    ):
        assert attr in self.kept_attr

        def sample_student(ds_coht):
            ds_of_interest = ds_coht[["student_token", "mod_code"]].drop_duplicates()
            agg_stu = (
                ds_of_interest.groupby(["student_token"])
                .size()
                .reset_index(name="counts")
            )
            filtered_stu = agg_stu[agg_stu.counts >= at_least_selecting]

            if filtered_stu.shape[0] == 0:
                raise ValueError("The threshold is set too high.")

            selected_stu_token = filtered_stu.sample(
                num_students, random_state=random_state
            ).student_token.values
            filtered_stu = agg_stu = ds_coht = None  # clear the cache
            selected_stu = ds_of_interest[
                [x in selected_stu_token for x in ds_of_interest.student_token]
            ]["mod_code"].reset_index()
            return selected_stu

        sample_coht1_stu_mods = sample_student(self.ds_coht1)
        sample_coht2_stu_mods = sample_student(self.ds_coht2)

        stu_mod_cross1 = (
            sample_coht1_stu_mods.merge(
                self.mod_info[["mod_code", attr]], on="mod_code", how="left"
            )
            .drop(["index"], axis=1)
            .groupby([attr])
            .size()
            .reset_index(name="counts")
        )
        stu_mod_cross2 = (
            sample_coht2_stu_mods.merge(
                self.mod_info[["mod_code", attr]], on="mod_code", how="left"
            )
            .drop(["index"], axis=1)
            .groupby([attr])
            .size()
            .reset_index(name="counts")
        )

        import plotly.express as px

        fig1 = px.pie(stu_mod_cross1, values="counts", names=attr)
        fig2 = px.pie(stu_mod_cross2, values="counts", names=attr)

        custom_legend = dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=12, color="black"),
        )

        custom_title1 = {
            "text": self.coht1,
            "x": 0.5,
            "y": 0.1,
            "xanchor": "center",
            "yanchor": "bottom",
        }

        custom_title2 = {
            "text": self.coht2,
            "x": 0.5,
            "y": 0.1,
            "xanchor": "center",
            "yanchor": "bottom",
        }

        fig1.update_layout(legend=custom_legend, title=custom_title1)
        fig2.update_layout(legend=custom_legend, title=custom_title2)

        return (
            sample_coht1_stu_mods.mod_code.nunique(),
            sample_coht2_stu_mods.mod_code.nunique(),
            fig1,
            fig2,
        )

    def plot_topk_diff_mod_info(self, k=10):
        """
        Note that get_most_different_modules() method needs to be run first.
        """
        mod_diff = self.mod_code_sorted_by_diff.copy()

        mod_diff_melted = pd.melt(
            mod_diff.iloc[:k, :].drop(["mod_code"], axis=1), id_vars="index"
        )

        mod_diff_info = mod_diff.merge(self.mod_info, on="mod_code")

        for attr in self.kept_attr:
            mod_diff_melted[attr] = mod_diff_info.loc[: k - 1, attr].tolist() * 2

        import plotly.express as px

        fig = px.bar(
            mod_diff_melted,
            x="index",
            y="value",
            color="variable",
            barmode="group",
            hover_data=self.kept_attr,
        )
        return fig
        # print("It is advised to clear the cache each time after running a graphing function!")

    def PCAnalysis(self, n_components=5, n_iters=7, random_state=47, topkmods=10):
        stu_mod_1 = (
            self.ds_coht1[["student_token", "mod_code"]]
            .drop_duplicates()
            .groupby(["student_token"])
            .agg(list)
            .reset_index()
        )
        stu_mod_2 = (
            self.ds_coht2[["student_token", "mod_code"]]
            .drop_duplicates()
            .groupby(["student_token"])
            .agg(list)
            .reset_index()
        )
        # student_set = set(stu_mod_1.student_token).intersection(set(stu_mod_2.student_token))
        module_set = list(
            set(self.ds_coht1.mod_code).union(set(self.ds_coht2.mod_code))
        )

        stu_mod_vec_1 = list()
        stu_mod_vec_2 = list()

        n_mod_list = len(module_set)

        for row in stu_mod_1.iterrows():
            vec = [0] * n_mod_list
            for mod in row[1].mod_code:
                vec[module_set.index(mod)] = 1
            stu_mod_vec_1.append(vec)

        for row in stu_mod_2.iterrows():
            vec = [0] * n_mod_list
            for mod in row[1].mod_code:
                vec[module_set.index(mod)] = 1
            stu_mod_vec_2.append(vec)

        stu_mod_1 = stu_mod_2 = None  # Clear the cache

        from sklearn.decomposition import TruncatedSVD

        svd = TruncatedSVD(
            n_components=n_components, n_iter=n_iters, random_state=random_state
        )

        stacked_cohort_vec = pd.concat(
            [pd.DataFrame(stu_mod_vec_1), pd.DataFrame(stu_mod_vec_2)],
            ignore_index=True,
        )
        stacked_cohort_vec["cohort"] = [self.coht1] * len(stu_mod_vec_1) + [
            self.coht2
        ] * len(stu_mod_vec_2)

        embeddings = svd.fit_transform(stacked_cohort_vec.iloc[:, :-1])

        label = {
            str(i): "PC {} ({:.1f}%)".format(
                i + 1, svd.explained_variance_ratio_[i] * 100
            )
            for i in range(n_components)
        }

        import plotly.express as px

        pca_fig = px.scatter_matrix(
            embeddings,
            labels=label,
            dimensions=range(n_components),
            color=stacked_cohort_vec.cohort,
        )
        pca_fig.update_traces(diagonal_visible=False)

        svd = embeddings = None  # Clear the cache

        svd1 = TruncatedSVD(
            n_components=n_components, n_iter=n_iters, random_state=random_state
        )
        svd1.fit(stu_mod_vec_1)

        svd2 = TruncatedSVD(
            n_components=n_components, n_iter=n_iters, random_state=random_state
        )
        svd2.fit(stu_mod_vec_2)

        # print("SVD Model successfully trained.")

        components_1 = svd1.components_
        components_2 = svd2.components_

        pc_diff = np.array([0] * n_mod_list, dtype=float)

        for i in range(n_components):
            pc_diff = pc_diff + (components_2[i] - components_1[i]) * (
                n_components - i
            ) / sum(range(1, n_components + 1))

        mod_diff_svd = pd.DataFrame({"mod_code": module_set, "pc_diff": pc_diff})
        mod_diff_svd_sorted = mod_diff_svd.iloc[
            mod_diff_svd.pc_diff.abs().sort_values(ascending=False).index, :
        ]

        mod_diff_svd_info = mod_diff_svd_sorted.merge(
            self.mod_info, on="mod_code"
        ).reset_index()

        mod_diff_svd_info["color"] = np.where(
            mod_diff_svd_info.pc_diff > 0, "blue", "red"
        )
        fig = px.bar(
            mod_diff_svd_info.iloc[:topkmods, :],
            x="index",
            y="pc_diff",
            color="color",
            color_discrete_map={"blue": "#636EFA", "red": "#EF553B"},
            hover_data={
                "color": False,
                "mod_code": True,
                "mod_faculty": True,
                "grading_basis": True,
            },
        )
        return mod_diff_svd_info, pca_fig, fig
        # print("It is advised to clear the cache each time after running a graphing function!")

    def attr_perc_change(self, stu_attr=None, mod_attr="mod_faculty"):
        """
        Plot the percentage changes in module attributes. Possible inputs are ['grading_basis', 'mod_faculty', 'mod_activity_type', 'mod_level']
        Note that get_most_different_modules() method needs to be run first.
        """
        if not mod_attr:
            raise ValueError("Please select a module attribute")

        # assert mod_attr in self.kept_attr and stu_attr in self.academic_plans

        ds_coht1 = ds_coht2 = ds_coht1_grouped = ds_coht2_grouped = pd.DataFrame()

        if stu_attr:
            ds_coht1 = self.ds_coht1.loc[
                self.ds_coht1[self.stu_attr_of_interest] == stu_attr, :
            ]
            ds_coht2 = self.ds_coht2.loc[
                self.ds_coht2[self.stu_attr_of_interest] == stu_attr, :
            ]
        else:
            ds_coht1 = self.ds_coht1.copy()
            ds_coht2 = self.ds_coht2.copy()

        ds_coht1 = ds_coht1.drop(self.kept_attr[1:], axis=1).merge(
            self.mod_info, on="mod_code"
        )
        ds_coht2 = ds_coht2.drop(self.kept_attr[1:], axis=1).merge(
            self.mod_info, on="mod_code"
        )

        ds_coht1_grouped = (
            ds_coht1[[mod_attr, "count"]]
            .groupby([mod_attr])
            .sum()
            .rename({"count": self.coht1}, axis=1)
            .reset_index()
        )
        ds_coht2_grouped = (
            ds_coht2[[mod_attr, "count"]]
            .groupby([mod_attr])
            .sum()
            .rename({"count": self.coht2}, axis=1)
            .reset_index()
        )

        # ds_coht1_grouped["Cohort"] = self.coht1
        # ds_coht2_grouped["Cohort"] = self.coht2

        # ds_cohts_stacked = pd.concat(
        #     [ds_coht1_grouped, ds_coht2_grouped], ignore_index=True
        # )

        # mod_focus = self.mod_code_sorted_by_diff.merge(
        #     self.mod_info, on="mod_code"
        # ).astype({attr: "category"})
        # mod_focus_grouped_1 = mod_focus[[self.coht1, attr]].groupby([attr]).sum()
        # mod_focus_grouped_2 = mod_focus[[self.coht2, attr]].groupby([attr]).sum()

        def entropy(lst):
            if len(lst) == 0:
                raise ValueError("No value passed")
            else:
                accu = 0
                for x in lst:
                    assert x > 0 and x < 1
                    accu += -x * np.log2(x)
                return accu

        entropy1 = entropy(
            (ds_coht1_grouped[self.coht1] / (ds_coht1_grouped[self.coht1]).sum()).values
        )
        entropy2 = entropy(
            (ds_coht2_grouped[self.coht2] / (ds_coht2_grouped[self.coht2]).sum()).values
        )

        import plotly.express as px

        fig1 = px.pie(ds_coht1_grouped, names=mod_attr, values=self.coht1)
        fig2 = px.pie(ds_coht2_grouped, names=mod_attr, values=self.coht2)

        # fig_pie = px.pie(
        #     ds_cohts_stacked,
        #     names=mod_attr,
        #     values=self.coht1,
        #     facet_col="Cohort",
        #     category_orders={mod_attr: sorted(ds_cohts_stacked[mod_attr].unique())},
        # )
        # ds_cohts_stacked = None
        custom_legend = dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=10, color="black"),
        )

        fig1.update_layout(legend=custom_legend)
        fig2.update_layout(legend=custom_legend)

        mod_focus_combined = ds_coht1_grouped.merge(ds_coht2_grouped, on=mod_attr)
        mod_focus_combined["enrol_percentage_cohort_1"] = (
            (mod_focus_combined[self.coht1])
            / mod_focus_combined[self.coht1].sum()
            * 100
        )
        mod_focus_combined["enrol_percentage_cohort_2"] = (
            (mod_focus_combined[self.coht2])
            / mod_focus_combined[self.coht2].sum()
            * 100
        )

        mod_focus_combined["percentage_change"] = (
            mod_focus_combined["enrol_percentage_cohort_2"]
            - mod_focus_combined["enrol_percentage_cohort_1"]
        )

        mod_focus_combined["value"] = np.where(
            mod_focus_combined["percentage_change"] > 0, "positive", "negative"
        )
        fig_bar = px.bar(
            mod_focus_combined,
            x=mod_attr,
            y="percentage_change",
            color="value",
            color_discrete_map={"positive": "#636EFA", "negative": "#EF553B"},
            hover_data={
                self.coht1: True,
                self.coht2: True,
                "percentage_change": ":.2f",
            },
        )
        fig_bar.update_xaxes(tickangle=45)
        
        return mod_focus_combined, entropy1, entropy2, fig1, fig2, fig_bar


# class ExcelDataReader():
#     def __init__(self, path, sheet_name, range_from, range_to, index=False, header=True):
#         '''
#         Assume that pandas is already import as pd; xlwings has already been imported as xw.
#         :param range_from: the cell from which records are read.
#         :param range_to: the cell to which records are read.
#         '''
#         self.path = path
#         self.sheet_name = sheet_name
#         self.range_from = range_from
#         self.range_to = range_to
#         wb = xw.Book(path)

#         sheet = wb.sheets[sheet_name]
#         self._dataframe = sheet[range_from+':'+range_to].options(pd.DataFrame, index=index, header=header).value
#         print('Data successfully loaded')

#     @property
#     def dataframe(self):
#         return self._dataframe


# class ModuleMapper:
#     def __init__(self, module_enrolment, base_cohort, comp_cohort, faculty_name="Biz"):
#         """
#         Initialize the module selection vectors for both student cohorts.
#         :param base_cohort: input type is integer
#         :param comp_cohort: input type is integer
#         """
#         self.faculty_name = faculty_name

#         self.input_validation(base_cohort, comp_cohort)

#         self.modules, self.base2vec, self.comp2vec = self.unique_mod(module_enrolment, base_cohort, comp_cohort)

#         # Module codes are all masked, thus it does not hurt to rehash the module codes which start from 0.
#         self.rehash = dict([(self.modules.mod_code[ind],ind) for ind in range(len(self.modules.mod_code))])

#     def input_validation(self, base_cohort, comp_cohort):
#         if type(base_cohort) != int or type(comp_cohort) != int:
#             raise ValueError("Invalid type of input:",type(base_cohort))
#         if base_cohort == comp_cohort:
#             raise ValueError("Two cohorts should not be the same.")
#         if base_cohort not in ACADEMIC_YEARS or comp_cohort not in ACADEMIC_YEARS:
#             raise ValueError("Invalid input for the year of cohort. Should be within the range {}".format(ACADEMIC_YEARS))
#         print("Input validated.")

#     def unique_mod(self, module_enrolment, base_cohort, comp_cohort):
#         """
#         Get the unique modules from two cohorts and desired attributes.
#         Yield the module enrollment vectors for both cohorts.
#         :param module_enrolment: non-empty pandas dataframe
#         """

#         module_enrolment['basevec'] = [x/100 == base_cohort for x in module_enrolment.term]
#         module_enrolment['compvec'] = [x/100 == comp_cohort for x in module_enrolment.term]

#         mods = module_enrolment[module_enrolment.basevec & module_enrolment.compvec][['mod_code','mod_faculty','mod_level',"mod_activity_type"]].drop_duplicates(subset=['mod_code'])
#         base_vec = module_enrolment[['basevec','mod_code']].groupby(['mod_code']).agg(sum)['basevec']
#         comp_vec = module_enrolment[['compvec','mod_code']].groupby(['mod_code']).agg(sum)['compvec']

#         return mods, base_vec, comp_vec

#     def plot_distribution(self):
#         ind = self.rehash.values
#         fig = plt.figure()
#         ax = fig.add_subplot(111)
#         ax.bar(x=ind, height=self.base2vec.values, width=0.35,align='center')
#         ax.bar(x=ind, height=self.comp2vec.values, width=0.35/3,  align='center')

#         plt.xticks(ind, self.rehash.keys)

#         plt.tight_layout()
#         plt.show()
