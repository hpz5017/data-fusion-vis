from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import JsonResponse, HttpRequest
from rest_framework.request import Request

from config.settings.base import STATIC_ROOT, ROOT_DIR, STATICFILES_DIRS

from tslearn.utils import to_time_series_dataset
from tslearn.clustering import TimeSeriesKMeans
from sklearn.decomposition import PCA

import os
import pandas as pd
import json

data = './data/right_hemi_small_simple.csv'

def open_dataset(file):
  entire_file_path = os.path.join(STATICFILES_DIRS[0], file)
  whole_dataset_df = pd.read_csv(open(entire_file_path, 'rU'))
  whole_dataset_df.set_index('idx')

  return whole_dataset_df

# e.g., total 5000 timepoints => chunk every 100 (t_size), which results in 50 chunks (t_num)
def chunk(df, t_num, t_size):
  chunk_list = []
  for t_idx in range(0, t_num):
    chunk = df.loc[ t_idx*t_size : (t_idx+1)*t_size ]
    chunk_mean = chunk.mean()
    chunk_std = chunk.std()
    chunk_list.append({ 'sum':chunk_mean, 'mean': chunk_mean, 'std': chunk_std, 'outlierIndex': 1})

  return chunk_list

# Save each group information as dataframe
# Output: A list of group dataframes
def group_by_kmeans(df, num_groups):
  kmeans = TimeSeriesKMeans(n_clusters=num_groups, max_iter=5, metric='dtw')
  cluster_membership_list = kmeans.fit_predict(df)
  
  return cluster_membership_list

class LoadFile(APIView):
  def get(self, request, format=None):
    entire_file_path = os.path.join(STATICFILES_DIRS[0], data)
    whole_dataset_df = pd.read_csv(open(entire_file_path, 'rU'))

    return Response(whole_dataset_df.to_json(orient='index'))

class LoadUserNames(APIView):
  def get(self, request, format=None):
    entire_file_path = os.path.join(STATICFILES_DIRS[0], data)
    whole_dataset_df = pd.read_csv(open(entire_file_path, 'rU'))

    return Response(json.dumps(list(whole_dataset_df.columns)))

class LoadUsers(APIView):
  def get(self, request, format=None):
    pass
  
  def post(self, request, format=None):
    json_request = json.loads(request.body.decode(encoding='UTF-8'))
    user_ids = json_request['selectedPatients']
    t_num = json_request['tNum']
    t_size = json_request['tSize']

    whole_dataset_df = open_dataset(data)
    df_selected_users = whole_dataset_df[user_ids]

    user_chunks_dict = {}
    for user_id in user_ids:
      user_chunks = chunk(whole_dataset_df[user_id], t_num, t_size)
      user_chunks_dict[user_id] = user_chunks

    return Response(json.dumps(user_chunks_dict))

class ClusterGroups(APIView):
  def get(self, request, format=None):
    pass

  def post(self, request, format=None):
    json_request = json.loads(request.body.decode(encoding='UTF-8'))
    num_groups = json_request['numGroups']
    group_size = json_request['groupSize']
    t_num = json_request['tNum']
    t_size = json_request['tSize']
    method = json_request['clusteringOption']
    print('in ClusterGroups: ', json_request)

    whole_dataset_df = open_dataset(data)

    # Group by clustering algorithm
    groups = []
    patient_ids = list(whole_dataset_df.columns)
    patient_ids.remove('idx')
    
    # Obtain representation (dimension reduction)
    df_for_clustering = whole_dataset_df.drop(['idx'], axis=1).T.values
    pca = PCA(n_components=2)
    df_for_clustering_after_pca = pca.fit_transform(df_for_clustering)
    clustering_result = group_by_kmeans(to_time_series_dataset(df_for_clustering_after_pca), num_groups) # row: # of datapoints (=patients), col: # of timepoints
    pd_patient_cluster = pd.DataFrame({'patient_id': patient_ids, 'cluster': clustering_result})

    # Store patient information per group in a dataframe, then get the list of dataframes
    for group_idx in range(0, num_groups):
      patients_in_cluster = pd_patient_cluster[pd_patient_cluster.cluster==group_idx]['patient_id']
      df_group = whole_dataset_df[patients_in_cluster].sum(axis=1) / len(patients_in_cluster)  # Sum all patients data to get the mean
      groups.append(df_group)

    # Chunk by timepoints
    clusters = {}
    for group_idx, df_group in enumerate(groups):  # Go over each group dataframe
        clusters[group_idx] = []
        chunk_list = chunk(df_group, t_num, t_size)
        clusters[group_idx] = chunk_list

    print(clusters)
    # print(pd.DataFrame(clustering_result, columns=['cluster']))
    # print(pd.DataFrame(df_for_clustering_after_pca, columns=['x', 'y']))
    df_for_dim_reduction_plot = pd.concat([pd.DataFrame(df_for_clustering_after_pca, columns=['x', 'y']), pd.DataFrame(clustering_result, columns=['cluster'])], axis=1)  # Merge pca result and clustering result

    return Response(json.dumps({'groupData': clusters, 'dimReductions': df_for_dim_reduction_plot.to_json(orient='records')}))
    