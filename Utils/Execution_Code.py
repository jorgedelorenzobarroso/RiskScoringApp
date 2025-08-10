import cloudpickle
import numpy as np
import pandas as pd
import sys
import os
from Utils.FunctionLibraryV1 import *
import warnings

#Deactivate warnings
warnings.filterwarnings("ignore")

def execute(df):

    x= data_quality(df)

    execution_pipe_pd_name = 'execution_pipe_pd.pickle'
    execution_pipe_ead_name = 'execution_pipe_ead.pickle'
    execution_pipe_lgd_name = 'execution_pipe_lgd.pickle'

    # Get the absolute path of the directory where this file is located
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Go up one level (from folder_a to my_project)
    parent_dir = os.path.dirname(current_dir)

    # Go down into Models folder
    folder_models_path = os.path.join(parent_dir, 'Models')

    execution_pipe_pd_path = os.path.join(folder_models_path,execution_pipe_pd_name)

    with open(execution_pipe_pd_path, mode='rb') as file:
       execution_pipe_pd = cloudpickle.load(file)

    execution_pipe_ead_path = os.path.join(folder_models_path,execution_pipe_ead_name)

    with open(execution_pipe_ead_path, mode='rb') as file:
       execution_pipe_ead = cloudpickle.load(file)

    execution_pipe_lgd_path = os.path.join(folder_models_path,execution_pipe_lgd_name)

    with open(execution_pipe_lgd_path, mode='rb') as file:
       execution_pipe_lgd = cloudpickle.load(file)

    #EXECUTE
    pred_pd = execution_pipe_pd.predict_proba(x)[:, 1]
    pred_ead = execution_pipe_ead.predict(x)
    pred_lgd = execution_pipe_lgd.predict(x)

    #CORRECT VALUES TO MAKE SURE THEY ARE IN THE RIGHT LIMITS (0,1)
    pred_pd = np.clip(pred_pd, 0, 1)
    pred_ead = np.clip(pred_ead, 0, 1)
    pred_lgd = np.clip(pred_lgd, 0, 1)

    #CALCULATE EXPECTED LOSS (EL)
    EL = pd.DataFrame({#'client_id': x_pd.index,
                       'principal':x.principal,
                       'pd':pred_pd,
                       'ead':pred_ead,
                       'lgd':pred_lgd},
                      index=x.index)

    EL['expected_loss'] = EL.pd * EL.ead * EL.lgd
    EL['expected_loss_euro'] = EL.principal * EL.expected_loss
    
    return(EL)


