"""
Code for processing datasets using scikit-learn.
"""
import numpy as np
from deep_chem.utils.analysis import results_to_csv
from deep_chem.utils.load import load_and_transform_dataset
from deep_chem.utils.preprocess import split_dataset
from deep_chem.utils.preprocess import dataset_to_numpy
from deep_chem.utils.evaluate import eval_model
from deep_chem.utils.evaluate import compute_r2_scores
from deep_chem.utils.evaluate import compute_rms_scores
from deep_chem.utils.evaluate import compute_roc_auc_scores
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import MultiTaskLasso 
from sklearn.linear_model import LogisticRegression
from sklearn.linear_model import LinearRegression
from sklearn.linear_model import RidgeCV
from sklearn.linear_model import LassoCV
from sklearn.linear_model import ElasticNetCV
from sklearn.linear_model import LassoLarsCV
from sklearn.svm import SVR

def fit_singletask_models(per_task_data, modeltype, task_types,
    num_to_train=None):
  """Fits singletask linear regression models to potency.

  Parameters
  ----------
  paths: list 
    List of paths to datasets. 
  modeltype: String
    A string describing the model to be trained. Options are RandomForest,
  splittype: string
    Type of split for train/test. Either random or scaffold.
  seed: int (optional)
    Seed to initialize np.random.
  task_types: dict 
    dict mapping target names to output type. Each output type must be either
    "classification" or "regression".
  output_transforms: dict 
    dict mapping target names to label transform. Each output type must be either
    None or "log". Only for regression outputs.
  """
  all_results = {}
  aucs, r2s, rms = {}, {}, {}
  sorted_targets = sorted(per_task_data.keys())
  if num_to_train:
    sorted_targets = sorted_targets[:num_to_train]
  for index, target in enumerate(sorted_targets):
    print "Building model %d" % index
    (train, X_train, y_train, W_train), (test, X_test, y_test, W_test) = (
        per_task_data[target])
    if modeltype == "rf_regressor":
      model = RandomForestRegressor(n_estimators=500, n_jobs=-1,
          warm_start=True, max_features="sqrt")
    elif modeltype == "rf_classifier":
      model = RandomForestClassifier(n_estimators=500, n_jobs=-1,
          warm_start=True, max_features="sqrt")
    elif modeltype == "logistic":
      model = LogisticRegression(class_weight="auto")
    elif modeltype == "linear":
      model = LinearRegression(normalize=True)
    elif modeltype == "ridge":
      model = RidgeCV(alphas=[0.01, 0.1, 1.0, 10.0], normalize=True) 
    elif modeltype == "lasso":
      model = LassoCV(max_iter=2000, n_jobs=-1) 
    elif modeltype == "lasso_lars":
      model = LassoLarsCV(max_iter=2000, n_jobs=-1) 
    elif modeltype == "elastic_net":
      model = ElasticNetCV(max_iter=2000, n_jobs=-1) 
    else:
      raise ValueError("Invalid model type provided.")
    model.fit(X_train, y_train.ravel())
    results = eval_model(test, model, {target: task_types[target]},
        modeltype="sklearn")
    all_results[target] = results[target]

    target_aucs = compute_roc_auc_scores(results, task_types)
    target_r2s = compute_r2_scores(results, task_types)
    target_rms = compute_rms_scores(results, task_types)
    
    aucs.update(target_aucs)
    r2s.update(target_r2s)
    rms.update(target_rms)
  if aucs:
    print results_to_csv(aucs)
    print "Mean AUC: %f" % np.mean(np.array(aucs.values()))
  if r2s:
    print results_to_csv(r2s)
    print "Mean R^2: %f" % np.mean(np.array(r2s.values()))
  if rms:
    print results_to_csv(rms)
    print "Mean RMS: %f" % np.mean(np.array(rms.values()))
  return all_results

def fit_multitask_rf(train_data, test_data, task_types):
  """Fits a multitask RF model to provided dataset.
  """
  (train, X_train, y_train, W_train), (test, X_train, y_train, W_train) = (
      train_data, test_data) 
  model = RandomForestClassifier(n_estimators=100, n_jobs=-1,
      class_weight="auto")
  model.fit(X_train, y_train)
  results = eval_model(test, model, task_types)
  scores = compute_roc_auc_scores(results)
  print "Mean AUC: %f" % np.mean(np.array(scores.values()))