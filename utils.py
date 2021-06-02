import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
#import xlwings as xw

ACADEMIC_YEARS = [10+x for x in range(9)]

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

    
class CohortAnalyzer():
    def __init__(self, mod_enrol, coht1, coht2):
        self.coht1 = 'Cohort'+str(coht1)
        self.coht2 = 'Cohort'+str(coht2)
        assert coht1 in ACADEMIC_YEARS and coht2 in ACADEMIC_YEARS
        
        self.mod_enrol = mod_enrol
        self.ds_coht1 = mod_enrol[[int(x/100) == coht1 for x in mod_enrol.term]]
        self.ds_coht2 = mod_enrol[[int(x/100) == coht2 for x in mod_enrol.term]]

        self.ds_coht1['count'] = 1
        self.ds_coht2['count'] = 1

        ds_coht_agg1 = self.ds_coht1[['count','mod_code']].groupby(['mod_code']).sum().reset_index()
        ds_coht_agg2 = self.ds_coht2[['count','mod_code']].groupby(['mod_code']).sum().reset_index()
 
        mod_agg = ds_coht_agg1.merge(ds_coht_agg2,on="mod_code").fillna(0).rename({'count_x':self.coht1,'count_y':self.coht2},axis=1)

        self.mod_agg = mod_agg
        self.mod_agg['mod_code_hash'] = list(range(mod_agg.shape[0]))
    
    def unload_dataframes():

        from streamlit import caching
        caching.clear_cache()

    
    @property
    def _mod_agg(self):
        return self.mod_agg
    
    def integrate_module_information(self):
        self.kept_attr = ['mod_code','grading_basis','mod_faculty','mod_activity_type','mod_level']
        for attr in self.kept_attr:
            assert attr in self.mod_enrol.columns
        mod_info = self.mod_enrol[self.kept_attr].drop_duplicates()

        mod_info_agg = mod_info.groupby(['mod_code']).agg({'grading_basis':' '.join,'mod_faculty':max,'mod_activity_type':set,'mod_level':max})
        
        mod_info_agg.mod_activity_type = mod_info_agg.mod_activity_type.apply(list).apply(sorted).apply(','.join)
        
        def gradingBasis(string):
            if 'CSU' in string:
                return 'CSU'
            elif 'SNU' in string:
                return 'SNU'
            elif 'GRD' in string:
                return 'GRD'
            else:
                return 'NON'
        mod_info_agg['grading_basis'] = mod_info_agg['grading_basis'].apply(gradingBasis)

        self.mod_info = mod_info_agg
        print('Module information successfully integrated.')
        
    @property
    def _mod_info(self):
        return self.mod_info  

    def stata_analysis(self):
        from scipy.stats import ttest_ind, f_oneway
        #print('Running t-test')
        t_sta_ttest, p_value_ttest = ttest_ind(self.mod_agg[self.coht1],self.mod_agg[self.coht2])
        #print('t test result: t-statistics:',t-sta,',p value:'p_value)
        # if p_value < 0.05:
        #     print("There is significant difference in the mean student enrolments between two cohorts. And the p-value for t test is",p_value)
        # else:
        #     print("There isn't significant difference in the mean student enrolments between two cohorts.")

        # print('Running one-way anova test')
        t_sta_oneway, p_value_oneway = f_oneway(self.mod_agg[self.coht1],self.mod_agg[self.coht2])
        # print('ANOVA test result: t-statistics:',t-sta,',p value:'p_value)
        # if p_value < 0.05:
        #     print("There is significant difference in the selection variances between two cohorts. And the p-value for anova test is",p_value)
        # else:
        #     print("There isn't significant difference in the selection variances between two cohorts.")

        return t_sta_ttest, p_value_ttest, t_sta_oneway, p_value_oneway
    

    def plot_popular_modules(self, n=10):
        '''
        Plot the module enrolment sorted by module popularity.
        :param thres: Filter only modules with at least thres amount of students enrolled.
        '''
        # Sort the modules by the sum of enrolled students in the two academic years.
        mod_agg_sorted = self.mod_agg.iloc[(self.mod_agg[self.coht1] + self.mod_agg[self.coht2]).sort_values(ascending=False).index,:].reset_index(drop=True)
        
        # Filter modules with total enrolment > thres
        #mod_agg_sorted_filter = mod_agg_sorted[[x > thres for x in (mod_agg_sorted[self.coht1] + mod_agg_sorted[self.coht2]).values]]

        mod_melted = pd.melt(mod_agg_sorted.iloc[:n,:].drop(['mod_code'],axis=1),id_vars='mod_code_hash')

        import plotly.express as px
        fig = px.bar(mod_melted, x='mod_code_hash', y='value', color='variable',barmode='group')
        return fig
        #print("It is advised to clear the cache each time after running a graphing function!")

    def get_most_different_modules(self, n=10):
        '''
        Obtain the module list sorted by normalized enrolment difference between the two academic years.
        :param n: Keep top n most different modules.
        '''
        # Modules with the largest differences
        mod_agg = self.mod_agg.copy()
        
        mod_agg['diff_'] = abs(mod_agg[self.coht1] - mod_agg[self.coht2])
        mod_agg['normalized_diff'] = abs(mod_agg[self.coht1] - mod_agg[self.coht2]) / mod_agg[[self.coht1, self.coht2]].max(axis=1)

        mod_code_sorted_by_diff = mod_agg[['mod_code',self.coht1,self.coht2]].iloc[(mod_agg.diff_ * mod_agg.normalized_diff).sort_values(ascending=False).index,:].reset_index(drop=True)

        mod_code_sorted_by_diff.reset_index(inplace=True)

        self.mod_code_sorted_by_diff = mod_code_sorted_by_diff
        #mod_diff_melted = pd.melt(mod_code_sorted_by_diff.iloc[:n,:].drop(['mod_code'],axis=1),id_vars='index')

        #sns.factorplot(x='index',y='value',hue='variable',data=mod_diff_melted,kind='bar')
        #plt.show()
        print("Most different module list obtained.")

    def plot_topk_diff_mod_info(self,k=10):
        '''
        Note that get_most_different_modules() method needs to be run first.
        '''
        mod_diff = self.mod_code_sorted_by_diff.copy()

        mod_diff_melted = pd.melt(mod_diff.iloc[:k,:].drop(['mod_code'],axis=1),id_vars='index')

        mod_diff_info = mod_diff.merge(self.mod_info,on='mod_code')
        
        for attr in self.kept_attr:
            mod_diff_melted[attr] = mod_diff_info.loc[:k-1,attr].tolist()*2

        import plotly.express as px
        fig = px.bar(mod_diff_melted, x='index', y='value', color='variable',barmode="group",hover_data=self.kept_attr)
        return fig
        #print("It is advised to clear the cache each time after running a graphing function!")

    def PCAnalysis(self, n_components=5, n_iters=7, random_state=47, topkmods=10):
        stu_mod_1 = self.ds_coht1[['student_token','mod_code']].drop_duplicates().groupby(['student_token']).agg(list).reset_index()
        stu_mod_2 = self.ds_coht2[['student_token','mod_code']].drop_duplicates().groupby(['student_token']).agg(list).reset_index()
        student_set = set(stu_mod_1.student_token).intersection(set(stu_mod_2.student_token))
        module_set = list(set(self.ds_coht1.mod_code).union(set(self.ds_coht2.mod_code)))

        stu_mod_vec_1 = list()
        stu_mod_vec_2 = list()

        n_mod_list = len(module_set)

        for row in stu_mod_1.iterrows():
            if row[1].student_token in student_set:
                vec = [0] * n_mod_list
                for mod in row[1].mod_code:
                    vec[module_set.index(mod)] = 1
                stu_mod_vec_1.append(vec)

        for row in stu_mod_2.iterrows():
            if row[1].student_token in student_set:
                vec = [0] * n_mod_list
                for mod in row[1].mod_code:
                    vec[module_set.index(mod)] = 1
                stu_mod_vec_2.append(vec)
        
        from sklearn.decomposition import TruncatedSVD

        svd1 = TruncatedSVD(n_components=n_components, n_iter=n_iters, random_state=random_state)
        svd1.fit(stu_mod_vec_1)

        svd2 = TruncatedSVD(n_components=n_components, n_iter=n_iters, random_state=random_state)
        svd2.fit(stu_mod_vec_2)

        print('SVD Model successfully trained.')

        pcs_1 = svd1.components_
        pcs_2 = svd2.components_

        pc_diff = np.array([0]*n_mod_list,dtype=float)

        for i in range(n_components):
            pc_diff = pc_diff + (pcs_2[i] - pcs_1[i])*(n_components-i)/sum(range(1,n_components+1))

        mod_diff_svd = pd.DataFrame({'mod_code':module_set,'pc_diff':pc_diff})
        mod_diff_svd_sorted = mod_diff_svd.iloc[mod_diff_svd.pc_diff.abs().sort_values(ascending=False).index,:]    

        mod_diff_svd_info = mod_diff_svd_sorted.merge(self.mod_info,on='mod_code').reset_index()
                
        import plotly.express as px

        mod_diff_svd_info['color'] = np.where(mod_diff_svd_info.pc_diff > 0,'blue','red')
        fig = px.bar(mod_diff_svd_info.iloc[:topkmods,:], x='index', y='pc_diff',color='color',hover_data={'color':False, 'mod_code':True})
        return mod_diff_svd_info, fig     
        #print("It is advised to clear the cache each time after running a graphing function!")

    def attr_perc_change(self, attr='mod_faculty'):
        '''
        Plot the percentage changes in module attributes. Possible inputs are ['grading_basis', 'mod_faculty', 'mod_activity_type', 'mod_level']
        Note that get_most_different_modules() method needs to be run first.
        '''
        assert attr in self.kept_attr
        mod_focus = self.mod_code_sorted_by_diff.merge(self.mod_info,on='mod_code').astype({attr: 'category'})
        mod_focus_grouped_1 = mod_focus[[self.coht1,attr]].groupby([attr]).sum()
        mod_focus_grouped_2 = mod_focus[[self.coht2,attr]].groupby([attr]).sum()
        
        mod_focus_combined = mod_focus_grouped_1.join(mod_focus_grouped_2).reset_index()
        mod_focus_combined['enrol_percentage_cohort_1'] = (mod_focus_combined[self.coht1]) / mod_focus_combined[self.coht1].sum() * 100
        mod_focus_combined['enrol_percentage_cohort_2'] = (mod_focus_combined[self.coht2]) / mod_focus_combined[self.coht2].sum() * 100
        mod_focus_combined['percentage_change'] = mod_focus_combined['enrol_percentage_cohort_2'] - mod_focus_combined['enrol_percentage_cohort_1']

        import plotly.express as px
        mod_focus_combined["color"] = np.where(mod_focus_combined["percentage_change"]>0, 'blue', 'red')
        fig = px.bar(mod_focus_combined,x=attr, y='percentage_change',color='color',hover_data={self.coht1:True,self.coht2:True,'percentage_change':':.2f'})
        return mod_focus_combined, fig  

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
