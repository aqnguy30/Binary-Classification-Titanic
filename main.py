#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 30 17:32:16 2020

@author: anhnguyen
"""
#import libraries
import os
import pandas as pd
import numpy as np
import openpyxl

#defining Binary class
class Binary:   
    #defining attributes
    train = ''
    test = ''
    trueclass_train = ''
    format_perfsheet= True   
    
    #initializing dataframe    
    df_result = pd.DataFrame
    df_prediction = pd.DataFrame 
    df_successrate = pd.DataFrame
        
    #define initialization function
    def __init__(self,train,test,trueclass_train):
        self.train = train
        self.test = test
        self.trueclass_train = trueclass_train
        result_data = {'feature':[],'category':[],'survived':[]}
        self.df_result = pd.DataFrame(result_data)  
    
    #define function to contruct OneR model    
    def oner_model(self,col_name,is_test):
        #intializing
        if is_test:
            df = self.test
            df_column = self.test[col_name]
        else:
            df = self.train
            df_column = self.train[col_name]            
        #check null values and forward fill
        if df_column.isnull().values.any():
            df_column = df_column.fillna(method ='ffill') 
        unique_values = np.unique(df_column)        
        self.df_prediction = df.filter(items = ['ID'])
        self.df_prediction['Prediction'] = np.NaN                 
        #calculating majority survival value if each column
        for category in unique_values:
            is_category = (df_column == category)
            if is_test:
                classifier = self.df_result['survived'][(self.df_result['category']==category) & 
                                                        (self.df_result['feature'] == col_name)]
                self.df_prediction.loc[is_category,'Prediction'] = int(classifier)
            else:
                ser_survived_count = self.trueclass_train[is_category].value_counts()
                #saving majority survival value as classifier
                if ser_survived_count.size == 2:
                    classifier = ser_survived_count[1] > ser_survived_count[0]
                else:
                    classifier = ser_survived_count.index[0]
                #creating dataframe with ID and prediction                
                self.df_prediction.loc[is_category,'Prediction'] = int(classifier)
                #saving it in a dataframe
                append_data = {'feature':col_name,'category':category,'survived':classifier}
                self.df_result = self.df_result.append(append_data,ignore_index = True)

        #writing given column name to excel sheet 
        req_sheetname = col_name+ "_Based_Prediction"
        if is_test:
            filename_dest = "titanic_test_predictions.xlsx"
            self.write_excel(filename_dest,req_sheetname)
            
        return self.df_result
      
    #defining write_excel function
    def write_excel(self,filename_dest,sheetname_dest):
        #checking for name
        if sheetname_dest == 'gender_Based_Prediction':
            sheetname_dest = 'Gender_Based_Prediction'            
        df_source = pd.read_excel(filename_dest, sheet_name=sheetname_dest)
        df_source = df_source.filter(items = ['ID','Ground truth'])
        df_final = pd.merge(df_source, self.df_prediction, on='ID', how='inner')
        success_rate = self.cal_success(df_final)        
        sheet_performance = 'Prediction_Success_Rate'        
        Feature = sheetname_dest        
        self.write_success(filename_dest,sheet_performance,success_rate,Feature)        
        self.Del_Sheet(filename_dest,sheetname_dest)
        #writing info
        if not os.path.isfile(filename_dest):
            write_mode = 'w'
        else:
            write_mode= 'a'    
        with pd.ExcelWriter(filename_dest,engine='openpyxl',mode=write_mode) as writer:
            df_final.to_excel(writer, sheet_name=sheetname_dest,index=False)
            # closing file
            writer.save()
            
    #defining cal_success function    
    def cal_success(self,df_input):
        pred_difference = sum(abs(df_input['Ground truth']-df_input['Prediction']))
        total_rows = df_input['Ground truth'].shape[0]
        error_rate = pred_difference/total_rows
        success_rate = round(1-error_rate,2)

        return success_rate
    
    #defining write_success function
    def write_success(self,filename_dest,sheet_performance,success_rate,Feature):
        df_source = pd.read_excel(filename_dest, sheet_name=sheet_performance)
        
        is_category = (df_source['Feature'] == Feature)
        if self.format_perfsheet:
            df_source.loc[is_category,'Success Rate '] = success_rate
            format = lambda x: (x*100)
            df_source['Success Rate '] = df_source['Success Rate '].map(format)
            self.format_perfsheet = False
        else:
            df_source.loc[is_category,'Success Rate '] = success_rate*100
        
        #assigning result to class' attribute
        self.df_successrate = df_source
        #deleting existing sheet
        self.Del_Sheet(filename_dest,sheet_performance)
        #creating new sheet with updated data
        with pd.ExcelWriter(filename_dest,engine='openpyxl',mode='a') as writer:
            df_source.to_excel(writer, sheet_name=sheet_performance,index=False)
            # saving file
            writer.save()
        
    #deleting existing sheet
    def Del_Sheet(self,filename_dest,sheetname_dest):        
        workbook=openpyxl.load_workbook(filename_dest)        
        del workbook[sheetname_dest]        
        workbook.save(filename_dest)
        workbook.close()
        
#reading the training set and testing set
train_file_name = "titanic_traning.xlsx"
test_file_name = "titanic_test.xlsx"
df_train = pd.read_excel(train_file_name)
df_test = pd.read_excel(test_file_name)
trueclass_train = df_train['survived']

#creating object of Binary classifier class
result = Binary(df_train,df_test,trueclass_train)
result.oner_model('gender',is_test = False)
result.oner_model('pclass',is_test = False)
result.oner_model('sibsp',is_test = False)
result.oner_model('parch',is_test = False)
result.oner_model('embarked',is_test = False)
print(result.df_result)
result.oner_model('gender',is_test = True)
result.oner_model('pclass',is_test = True)
result.oner_model('sibsp',is_test = True)
result.oner_model('parch',is_test = True)
result.oner_model('embarked',is_test = True)
print(result.df_successrate)
