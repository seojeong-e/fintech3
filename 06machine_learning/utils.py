import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import OneHotEncoder

def ohe_transform(X_train, X_test):
    """_summary_

    Args:
        X_train (DataFrame): OneHotEncodig할 훈련데이터
        X_test (DataFrame): OneHotEncodig할 테스트데이터

    Returns:
        X_train, X_test 
    """
    train_cat_cols = X_train.select_dtypes(include='object')
    train_num_cols = X_train.select_dtypes(exclude='object')
    test_cat_cols = X_test.select_dtypes(include='object')
    test_num_cols = X_test.select_dtypes(exclude='object')
    
    ohe = OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore')
    ohe.fit(train_cat_cols)
    train_temp = ohe.transform(train_cat_cols)
    test_temp = ohe.transform(test_cat_cols)
    
    ohe_cols_name = ohe.get_feature_names_out(train_cat_cols.columns)
    
    train_temp_df = pd.DataFrame(train_temp, index=train_cat_cols.index, columns=ohe_cols_name)
    test_temp_df = pd.DataFrame(test_temp, index=test_cat_cols.index, columns=ohe_cols_name)
    
    train_result = pd.concat([train_temp_df, train_num_cols], axis=1)
    test_result = pd.concat([test_temp_df, test_num_cols], axis=1)
    
    return train_result, test_result