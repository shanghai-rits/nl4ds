import os
os.system('pip list >> installed_libraries.txt')
with open('/content/installed_libraries.txt','r') as f:
  installed_libraries_string = f.read()
installed_libraries = [line.split()[0] for line in installed_libraries_string.split('\n')[2:] if line!='']

from IPython.core.display import clear_output

clear_output()

# import warnings
# warnings.filterwarnings('ignore')

import time
print('Loading packages, this may take a minute ...')
time.sleep(1)
from datetime import datetime, timedelta
from random import random

import pandas as pd
import numpy as np
import re

from matplotlib import pyplot as plt
from matplotlib import cm
from matplotlib.patches import Polygon as mpb_polygon
plt.rcParams["font.serif"] = "cmr10" 

import ast
import shutil
from glob import glob
import gc

import pickle
import json

from collections import Counter

import cv2
from google.colab.patches import cv2_imshow
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

from shapely.geometry import Polygon as shapely_polygon
from shapely.geometry import Point as shapely_point

if 'rasterio' not in installed_libraries:
  os.system('pip install rasterio')
import rasterio
from rasterio.windows import Window
from rasterio.transform import Affine
from rasterio.plot import reshape_as_image

if 'tqdm' not in installed_libraries:
  os.system('pip install tqdm')
from tqdm import tqdm
tqdm.pandas()

if 'pyproj' not in installed_libraries:
  os.system('pip install pyproj')
import pyproj
from pyproj import Geod

if 'iteround' not in installed_libraries:
  os.system('pip install iteround')
from iteround import saferound

if 'colorsys' not in installed_libraries:
  os.system('pip install colorsys')
import colorsys

if 'sklearn' not in installed_libraries:
  os.system('pip install sklearn')
import sklearn
from sklearn.cluster import DBSCAN

if 'scipy' not in installed_libraries:
  os.system('pip install scipy')
import scipy
from scipy.cluster.vq import whiten
from scipy.cluster.vq import kmeans
from scipy.cluster.vq import vq

if 'plotly' not in installed_libraries:
  os.system('pip install plotly')
import plotly

if 'plotly-express' not in installed_libraries:
  os.system('pip install plotly-express')
import plotly.express as px
import plotly.graph_objs as go

if 'python-Levenshtein' not in installed_libraries:
  os.system('pip install python-Levenshtein')
if 'thefuzz' not in installed_libraries:
  os.system('pip install thefuzz')
if 'networkx' not in installed_libraries:
  os.system('pip install networkx')
from thefuzz import fuzz, process
import networkx as nx

if 'fiona' not in installed_libraries:
  os.system('pip install fiona')
import fiona

clear_output()

#======================================== COMMON UTILS ============================================#

def flatten_list(l):
  return [item for sublist in l for item in sublist]

def unique_preserving_order(l):
    """
    Reference:http://www.peterbe.com/plog/uniqifiers-benchmark
    """
    seen = set()
    seen_add = seen.add
    return [x for x in l if not (x in seen or seen_add(x))]

def get_outliers(data_names, data_values):
  data_names = np.array(data_names)
  data_values = np.array(data_values)
  upper_hinge = np.percentile(data_values,75)
  lower_hinge = np.percentile(data_values,25)
  iqr = upper_hinge - lower_hinge
  outlier_mask = (data_values > upper_hinge + 1.5*iqr) | (data_values < lower_hinge - 1.5*iqr)
  outlier_data_values = data_values[outlier_mask]
  outlier_data_names = data_names[outlier_mask]
  return dict(zip(outlier_data_names, outlier_data_values))

def get_non_single_elements(data, field):
  value_cnts = data[field].value_counts()
  non_single_elements = value_cnts[value_cnts>=2].index.tolist()
  return non_single_elements

def try_length_is_zero(x):
  try:
    if isinstance(x,int):
      return False
    return len(x)==0
  except:
    return True

def create_mapping_from_df(dataframe, key, value, drop_nan_value = True, drop_empty_value = True):
  temp_df = dataframe[[key,value]].copy()
  if drop_empty_value:
    temp_df[value] = temp_df[value].apply(lambda x: np.nan if try_length_is_zero(x) else x)
    drop_nan_value = True
  if drop_nan_value:
    temp_df = temp_df.dropna()
  return temp_df.set_index(key)[value].to_dict()

remove_special_characters_and_shrink_whitespace = lambda x: re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9\s]', '', x.lower())).strip() if isinstance(x,str) else ''
remove_bracket_x_pattern = lambda x: '' if re.sub(r'(\[)?x+(\])?','',x)=='' else x

#==================================================================================================#






#=========================================== MS OCR ===============================================#

need_ocr_call = input('\nDo you need OCR calls? [y/n]\n')
if need_ocr_call[0].lower() == 'y':
  os.system('pip install --upgrade azure-cognitiveservices-vision-computervision')
  clear_output()
  from azure.cognitiveservices.vision.computervision import ComputerVisionClient
  from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
  from msrest.authentication import CognitiveServicesCredentials
  computervision_client = ComputerVisionClient(input('\nEndpoint?\n'), CognitiveServicesCredentials(input('\nKey?\n')))
clear_output()

def get_ms_ocr_result(read_image_path, wait_interval=10): 

  # Open the image
  read_image = open(read_image_path, "rb")

  # Call API with image and raw response (allows you to get the operation location)
  read_response = computervision_client.read_in_stream(read_image, raw=True)
  # Get the operation location (URL with ID as last appendage)
  read_operation_location = read_response.headers["Operation-Location"]
  # Take the ID off and use to get results
  operation_id = read_operation_location.split("/")[-1]
  # Call the "GET" API and wait for the retrieval of the results
  while True:
    read_result = computervision_client.get_read_result(operation_id)
    if read_result.status.lower() not in ['notstarted', 'running']:
      break
    # print('Waiting for result...')
    time.sleep(wait_interval)
  return read_result.as_dict()

def parse_ms_ocr_result(ms_ocr_result, return_words=True, confidence_threshold=0):

  operation_result = ms_ocr_result['status']
  operation_creation_time = ms_ocr_result['created_date_time']
  operation_last_update_time = ms_ocr_result['last_updated_date_time']
  operation_api_version = ms_ocr_result['analyze_result']['version']
  operation_model_versoin = ms_ocr_result['analyze_result']['model_version']

  assert(len(ms_ocr_result['analyze_result']['read_results']) == 1)
  read_result = ms_ocr_result['analyze_result']['read_results'][0]

  result_page_num = read_result['page']
  result_angle = read_result['angle']
  result_width = read_result['width']
  result_height = read_result['height']
  result_unit = read_result['unit']
  result_lines = read_result['lines']

  if len(result_lines) == 0:  # if no lines found, return an empty components_df directly
    return pd.DataFrame(columns=['bounding_box', 'text', 'confidence', 'frame_anchor'])

  lines_df = pd.DataFrame(result_lines)

  if return_words:
    words_df = pd.DataFrame(flatten_list(lines_df['words']))
    words_df = words_df[words_df['confidence'] >= confidence_threshold]
    components_df = words_df.reset_index(drop=True)
  else:
    components_df = lines_df

  return components_df

def mark_ms_ocr_result(input_image_filepath, components_df, output_image_filepath='', fontsize=10, figsize=(20,20), dpi=150, clear_plot=False):

  components_df = components_df.copy()
  
  image = Image.open(input_image_filepath)

  plt.figure(figsize=figsize, dpi=dpi)
  ax = plt.imshow(image, cmap=cm.gray)

  for _, row in components_df.iterrows():

    bbox, ocr_text, confidence, right_side_center = row['bounding_box'], row['text'], row['confidence'], row.get('bbox_right_side_center',None)
    
    # bounding box
    if all([isinstance(x,list) and len(x)==2 for x in bbox]):
      vertices = bbox
    else:
      vertices = [(bbox[i], bbox[i + 1]) for i in range(0, len(bbox), 2)]
    
    polygon_patch = mpb_polygon(vertices, closed=True, fill=False, linewidth=0.6, color='b', alpha=confidence)
    ax.axes.add_patch(polygon_patch)
    
    # text
    plt.text(vertices[1][0], vertices[1][1], ocr_text, fontsize=fontsize, color='r', va="top")

    if right_side_center != None:
      # right side center dot
      plt.text(right_side_center[0], right_side_center[1], '.', fontsize=8, color='#66FF66', ha='left', va="baseline")

  if output_image_filepath != '':
    plt.savefig(output_image_filepath, bbox_inches='tight', pad_inches=0)

  if clear_plot: ## usefulness to be tested, created to release memory during batch plotting
    # Clear the current axes
    plt.cla() 
    # Clear the current figure
    plt.clf() 
    # Closes all the windows
    plt.close('all')   
    del ax
    gc.collect()


def save_dict_to_json(dic, filepath):
  with open(filepath, 'w') as f:
    json.dump(dic, f)

def read_dict_from_json(filepath):
  with open(filepath, 'r') as f:
    dic = json.load(f)
  return dic

############# QUICK ACCESS OCR #############

def ms_ocr(img_path, mark_image = True, show_numeric = False, fontsize = 10, figsize = (20,20), dpi = 150, clear_plot=False):

  raw_ocr_result_filepath = img_path.split('.')[0] + '_raw_ocr_result.txt'
  if not os.path.exists(raw_ocr_result_filepath):
    result = get_ms_ocr_result(img_path)
    save_dict_to_json(result, raw_ocr_result_filepath)
  else:
    print('Raw OCR result found.')
    result = read_dict_from_json(raw_ocr_result_filepath)

  ocr_result_table_filepath = img_path.split('.')[0] + '_ocr_result_table.csv'
  if not os.path.exists(ocr_result_table_filepath):
    comp_df = parse_ms_ocr_result(result)
    comp_df.to_csv(ocr_result_table_filepath, index=False)
  else:
    print('OCR result table found.')
    comp_df = pd.read_csv(ocr_result_table_filepath)
    comp_df['bounding_box'] = comp_df['bounding_box'].apply(ast.literal_eval)

  if mark_image:
    if not show_numeric:
      comp_df = comp_df[~(comp_df['text'].str.isnumeric())]
    ocr_result_marked_img_path = img_path.split('.')[0] + '_ocr_result_marked_img.' + img_path.split('.')[1]
    mark_ms_ocr_result(img_path, comp_df, output_image_filepath=ocr_result_marked_img_path, fontsize=fontsize, figsize=figsize, dpi=dpi, clear_plot=clear_plot)

############# UTILS FOR BASCI PREPROCESSING BEFORE OCR #############

def make_greyscale_img(img_path):
  out_img_path = img_path.replace('.', '_grey.')
  if not os.path.exists(out_img_path):
    grey_img = cv2.imread(img_path, 0)
    im = Image.fromarray(grey_img)
    im.save(out_img_path)
    return out_img_path
  else:
    print('Greyscale version of the image already exists.')
    return out_img_path


def resize_img(img_path, target_size):
  img = cv2.imread(img_path)
  img_shape = img.shape
  if img_shape[0] != img_shape[1]:
    raise '[Error] Input image not a square shape.'
  orig_size = img_shape[0]
  out_img_path = img_path.replace('.', '_' + str(orig_size) + '_to_' + str(target_size) + '.')
  out_img_path = re.sub(r'(000)(_|\.)', r'k\2', out_img_path)
  if not os.path.exists(out_img_path):
    resized_img = cv2.resize(img, (target_size, target_size))
    if len(img_shape) == 3:
      resized_img = cv2.cvtColor(resized_img, cv2.COLOR_BGR2RGB)
    im = Image.fromarray(resized_img)
    im.save(out_img_path)
    return out_img_path
  else:
    print('Resized version of the image already exists.')
    return out_img_path

def rotate_180_degree(img_filepath):
  img = cv2.imread(img_filepath)[:,:,:3]
  rotated_img = cv2.flip(cv2.flip(img, 0), 1)
  rotated_img_path = '/'.join(img_filepath.split('/')[:-1])+'/'+img_filepath.split('/')[-1].split('.')[0]+'__rotated.png'
  cv2.imwrite(rotated_img_path, rotated_img)
  return rotated_img_path

def invert_binary(img):
  return cv2.bitwise_not(img)
def adaptive_threshold(img, size = 9, C = 18):
  return cv2.adaptiveThreshold(img.copy(), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, size, C)
def otsu_threshold(img, verbose=False):
  threshold_value, binarized_img = cv2.threshold(img,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
  if verbose:
    print('The threshold value found is', threshold_value)
  return binarized_img

#==================================================================================================#










#=============================== COLOR AND COLOR CODE CONVERSION ==================================#

def rgb_to_grey(img):
  return cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
def bgr_to_grey(img):
  return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
def bgr_to_rgb(img):
  return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
def rgb_to_bgr(img):
  return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
def grey_to_bgr(img):
  return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
def grey_to_rgb(img):
  return cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
def hsv2rgb(h,s=1.0,v=1.0):
    return tuple(round(i * 255) for i in colorsys.hsv_to_rgb(h,s,v))
def hsv2bgr(h,s=1.0,v=1.0):
  r,g,b = hsv2rgb(h,s,v)
  return (b,g,r)

def rgb_code_to_hsv_code(rgb_tuple):
  pixel = np.zeros((1,1,3),dtype=np.uint8)
  pixel[0,0,:] = rgb_tuple
  return tuple([int(v) for v in list(cv2.cvtColor(pixel, cv2.COLOR_RGB2HSV)[0][0])])
def rgb_code_to_lab_code(rgb_tuple):
  pixel = np.zeros((1,1,3),dtype=np.uint8)
  pixel[0,0,:] = rgb_tuple if isinstance(rgb_tuple,tuple) else tuple(rgb_tuple)
  return tuple([int(v) for v in list(cv2.cvtColor(pixel, cv2.COLOR_RGB2LAB)[0][0])])
def lab_code_to_rgb_code(lab_tuple):
  pixel = np.zeros((1,1,3),dtype=np.uint8)
  pixel[0,0,:] = lab_tuple if isinstance(lab_tuple,tuple) else tuple(lab_tuple)
  return tuple([int(v) for v in list(cv2.cvtColor(pixel, cv2.COLOR_LAB2RGB)[0][0])])

#==================================================================================================#










#===================================== GET BBOX FEATURES ==========================================#

###### UTILS FOR GET_BBOX_FEATURES ######
def euc_dist(pt1, pt2, rounding = 1):
  return np.round(np.linalg.norm(pt2-pt1), rounding)
def dist_from_point_to_line(p1, p2, p3):
  """Return distance from P3 perpendicular to a line going through P1 and P2"""
  return np.abs(np.cross(p2-p1, p1-p3)) / np.linalg.norm(p2-p1)
def get_vector_direction(vector, rounding = 1):
  """np_arctan2_in_degree (-180 to 180 reference angle is the positive direction of x axis in cartesian space)""" 
  x, y = vector
  return np.round(np.arctan2(y, x) * 180 / np.pi, rounding)

def cv2_contourize(np_bbox): 
  return np.array(np_bbox).reshape((-1,1,2)).astype(np.int32)
  
def get_bbox_features(bbox):

  widths = euc_dist(bbox[0], bbox[1]), euc_dist(bbox[2], bbox[3])
  width = np.mean(widths)
  diff_in_widths = np.abs(np.diff(widths))
  width_diff_prop = np.round((diff_in_widths/width)[0], 2)

  heights = [ dist_from_point_to_line(bbox[2], bbox[3], bbox[0]),  dist_from_point_to_line(bbox[2], bbox[3], bbox[1]),  dist_from_point_to_line(bbox[0], bbox[1], bbox[2]),  dist_from_point_to_line(bbox[0], bbox[1], bbox[3]) ] 
  height = np.mean(heights)
  diff_in_heights = np.abs(np.diff(heights))
  height_diff_prop = np.round((diff_in_heights/height)[0], 2)

  left_side_center = np.mean((bbox[0], bbox[3]), axis=0)
  right_side_center = np.mean((bbox[1], bbox[2]), axis=0)
  reading_direction_vector = right_side_center - left_side_center
  reading_direction = get_vector_direction(reading_direction_vector)

  center = bbox.mean(axis=0)

  return width, width_diff_prop, height, height_diff_prop, reading_direction, center, left_side_center, right_side_center

def add_bbox_features_to_table(map_ocr_results_table, ocr_entry_id_start = 1):

  # Calculate bounding box features and add them as columns
  map_ocr_results_table[['bbox_'+col for col in 'width, width_diff_prop, height, height_diff_prop, reading_direction, center, left_side_center, right_side_center'.split(', ')]] = pd.DataFrame(map_ocr_results_table['bounding_box'].apply(get_bbox_features).tolist(), index = map_ocr_results_table.index)
  # Convert numpy ndarray column to nested list format for better I/O from/to CSV
  map_ocr_results_table['bounding_box'] = map_ocr_results_table['bounding_box'].apply(lambda x: x.tolist())
  map_ocr_results_table['bbox_center'] = map_ocr_results_table['bbox_center'].apply(lambda x: x.tolist())
  map_ocr_results_table['bbox_left_side_center'] = map_ocr_results_table['bbox_left_side_center'].apply(lambda x: x.tolist())
  map_ocr_results_table['bbox_right_side_center'] = map_ocr_results_table['bbox_right_side_center'].apply(lambda x: x.tolist())

  # Add a unique id for each ocr entry (each row in the table), this is unique within the original full image/map.
  map_ocr_results_table['ocr_entry_id'] = range(ocr_entry_id_start, ocr_entry_id_start + len(map_ocr_results_table))

  return map_ocr_results_table[['map_id', 'ocr_entry_id', 'text', 'confidence', 'bounding_box', 'bbox_width', 'bbox_width_diff_prop', 'bbox_height', 'bbox_height_diff_prop', 'bbox_reading_direction',  'bbox_center', 'bbox_left_side_center', 'bbox_right_side_center']]

#==================================================================================================#





#======================================== CUT / CROP / RE-COMBINE IMAGE ========================================#

############# UTILS FOR CUT / CROP IMAGE #############

def get_area_size_from_geo_point_list(geo_point_list):
  """Input: geo_point_list in format of [(lon, lat), ...]
  Output: size of area in m^2
  # Reference: https://stackoverflow.com/questions/68118907/shapely-pyproj-find-area-in-m2-of-a-polygon-created-from-latitude-and-longi
  """
  polygon = shapely_polygon(geo_point_list)
  geod = Geod(ellps="WGS84")
  try:
    poly_area, poly_perimeter = geod.geometry_area_perimeter(polygon)
    return int(poly_area)
  except:
    return -1

def calculate_area_per_pixel(raw_image_filepath):
  if raw_image_filepath.endswith('.tif'):
    dataset = rasterio.open(raw_image_filepath)
    transform_matrix = dataset.transform
  elif raw_image_filepath.endswith('.png'):
    dataset = cv2.imread(raw_image_filepath)
    transform_matrix = create_transform_matrix(read_geotransform_parameters(raw_image_filepath.replace('.png','.png.aux.xml')))

  h, w = dataset.shape[0], dataset.shape[1]
  image_pixel_area_size = w*h
  corner_geo_point_list = [tuple([float(x) for x in np.round(transform_matrix * point,6)]) for point in [(0,0), (0,h), (w,h), (w,0), (0,0)]]

  image_geo_area_size = get_area_size_from_geo_point_list(corner_geo_point_list)

  area_per_pixel = image_geo_area_size/image_pixel_area_size
  area_per_pixel = round(area_per_pixel,6)
  return area_per_pixel

def calculate_area_per_pixel_list(raw_image_filepaths, verbose = False):
  area_per_pixel_list = []
  for raw_image_index in tqdm(range(0, len(raw_image_filepaths))):
    raw_image_filepath = raw_image_filepaths[raw_image_index]
    if verbose:
      print('------------------- raw image index '+str(raw_image_index)+' -------------------')
      print(raw_image_filepath.split('/')[-1])
    area_per_pixel = calculate_area_per_pixel(raw_image_filepath)
    if verbose:
      print('area_per_pixel:', area_per_pixel)
    area_per_pixel_list.append(area_per_pixel)
  return area_per_pixel_list

def read_geotransform_parameters(aux_xml_filepath):
  with open(aux_xml_filepath, 'r') as f:
    raw = f.read()
  geotransform_parameters = [ast.literal_eval(v.strip()) for v in re.findall('<GeoTransform>(.*?)</GeoTransform>',raw)[0].split(',')]
  return geotransform_parameters

def create_transform_matrix(para):
  transform_matrix = Affine(para[1], para[2], para[0], para[4], para[5] , para[3])
  return transform_matrix

######################################################

def cut_tiff_into_pngs(path, window_side_length, window_stride = None, output_directory_path = None, skip_if_directory_exists = False):

  if window_stride is None:
    window_stride = window_side_length - window_side_length//5

  dataset = rasterio.open(path)
  dataset_name = dataset.name.split('/')[-1].split('.')[0]
  if output_directory_path is None:
    output_directory_path = '/'.join(path.split('/')[:-1]) +'/'+ dataset_name+'__wsl_'+str(window_side_length)+'_ws_'+str(window_stride)
  else:
    output_directory_path = output_directory_path.rstrip('/')

  if not os.path.exists(output_directory_path):
    os.mkdir(output_directory_path)
  else:
    if skip_if_directory_exists:
      return []
    else:
      raise ValueError("[Error] Output directory already exists, please check and resolve.")

  area_per_pixel = calculate_area_per_pixel(path)
  
  dataset_meta = dict(dataset.meta)
  dataset_meta['area_per_pixel'] = area_per_pixel
  print(dataset_meta)

  dataset_meta_string = str(dataset_meta)
  dataset_meta_string = dataset_meta_string.replace('\n','')
  dataset_meta_string = re.sub(r'CRS\.from_epsg\((\d+)\)',r"'epsg:\1'",dataset_meta_string)
  dataset_meta_string = re.sub(r'Affine\((.*?)\)',r'[\1]',dataset_meta_string)
  
  with open(output_directory_path +'/'+ 'metadata.txt', 'w') as f:
    f.write(dataset_meta_string)

  dataset_band_count = dataset.count
  dataset_width = dataset.width
  dataset_height = dataset.height
  window_width_indices = range(dataset_width//window_stride+1)
  window_height_indices = range(dataset_height//window_stride+1)
  
  offset_pair_list = []
  for window_width_index in window_width_indices:
    col_off = window_width_index * window_stride
    col_off = col_off if col_off + window_side_length <= dataset_width else dataset_width - window_side_length
    for window_height_index in window_height_indices:
      row_off = window_height_index * window_stride
      row_off = row_off if row_off + window_side_length <= dataset_height else dataset_height - window_side_length
      offset_pair_list.append((col_off, row_off))

  cropped_image_filepath_list = []
  for col_off, row_off in tqdm(offset_pair_list):
    bands = []
    for band_index in range(1,dataset_band_count+1):
      bands.append( dataset.read(band_index, window = Window(col_off, row_off, window_side_length, window_side_length)) )
    window_img = np.stack(bands, axis=2)
    
    # check to ensure image is not completely empty
    if window_img[:,:,0].sum() != 0:
      im = Image.fromarray(window_img)
      output_path = output_directory_path +'/'+ dataset_name+'_xoff'+str(col_off)+'_yoff'+str(row_off)+'_wsl_'+str(window_side_length)+'.png'
      im.save(output_path)

      # check if the border of the image is transparent on all 4 sides, meaning the actual raster data is fully contained
      if window_img[0,:,0].sum() + window_img[:,0,0].sum() + window_img[-1,:,0].sum() + window_img[:,-1,0].sum() == 0:
        for p in cropped_image_filepath_list:
          os.remove(p)
        cropped_image_filepath_list = [output_path]
        break # if so, break out out loop and return the current crop only

      cropped_image_filepath_list.append(output_path)
      
  cropped_image_filepath_list = sorted(set(cropped_image_filepath_list))
  return cropped_image_filepath_list

######################################################

def cut_image_into_pngs(path, window_side_length, window_stride = None, output_directory_path = None, skip_if_directory_exists = False, georeferenced = False):

  dataset_name = path.split('/')[-1].split('.')[0]

  if window_stride is None:
    window_stride = window_side_length - window_side_length//5

  im_bgr = cv2.imread(path)
  im_rgb = cv2.cvtColor(im_bgr, cv2.COLOR_BGR2RGB)

  if output_directory_path is None:
    output_directory_path = '/'.join(path.split('/')[:-1]) +'/'+ dataset_name+'__wsl_'+str(window_side_length)+'_ws_'+str(window_stride)
  else:
    output_directory_path = output_directory_path.rstrip('/')

  if not os.path.exists(output_directory_path):
    os.mkdir(output_directory_path)
  else:
    if skip_if_directory_exists:
      return []
    else:
      raise ValueError("[Error] Output directory already exists, please check and resolve.")

  dataset_height, dataset_width, dataset_band_count = im_rgb.shape

  file_extension = path.split('.')[-1]
  aux_xml_filepath = path.replace('.'+file_extension,'.'+file_extension+'.aux.xml')
  if georeferenced and os.path.exists(aux_xml_filepath) and aux_xml_filepath != path:
    affine_info_string = repr(create_transform_matrix(read_geotransform_parameters(aux_xml_filepath)))
    area_per_pixel = calculate_area_per_pixel(path)
    dataset_meta_string = "{'driver': 'GTiff', 'dtype': 'uint8', 'nodata': None, 'width': "+str(dataset_width)+", 'height': "+str(dataset_height)+", 'count': 4, 'crs': CRS.from_epsg(4326), 'transform': "+affine_info_string+", 'area_per_pixel':"+str(area_per_pixel)+"}"
    print(dataset_meta_string)
    dataset_meta_string = str(dataset_meta)
    dataset_meta_string = dataset_meta_string.replace('\n','')
    dataset_meta_string = re.sub(r'CRS\.from_epsg\((\d+)\)',r"'epsg:\1'",dataset_meta_string)
    dataset_meta_string = re.sub(r'Affine\((.*?)\)',r'[\1]',dataset_meta_string)
    with open(output_directory_path +'/'+ 'metadata.txt', 'w') as f:
      f.write(dataset_meta_string)
  
  window_width_indices = range(dataset_width//window_stride+1)
  window_height_indices = range(dataset_height//window_stride+1)

  offset_pair_list = []
  for window_width_index in window_width_indices:
    col_off = window_width_index * window_stride
    col_off = col_off if col_off + window_side_length <= dataset_width else dataset_width - window_side_length
    for window_height_index in window_height_indices:
      row_off = window_height_index * window_stride
      row_off = row_off if row_off + window_side_length <= dataset_height else dataset_height - window_side_length
      offset_pair_list.append((col_off, row_off))

  cropped_image_filepath_list = []

  for col_off, row_off in tqdm(offset_pair_list):
    window_img = im_rgb[row_off:row_off+window_side_length, col_off:col_off+window_side_length, :]
      
    # check to ensure image is not completely empty
    if window_img[:,:,0].sum() != 0:
      im = Image.fromarray(window_img)
      output_path = output_directory_path +'/'+ dataset_name+'_xoff'+str(col_off)+'_yoff'+str(row_off)+'_wsl_'+str(window_side_length)+'.png'
      im.save(output_path)

      # check if the border of the image is transparent on all 4 sides, meaning the actual raster data is fully contained
      if window_img[0,:,0].sum() + window_img[:,0,0].sum() + window_img[-1,:,0].sum() + window_img[:,-1,0].sum() == 0:
        for p in cropped_image_filepath_list:
          os.remove(p)
        cropped_image_filepath_list = [output_path]
        break # if so, break out out loop and return the current crop only

      cropped_image_filepath_list.append(output_path)

  cropped_image_filepath_list = sorted(set(cropped_image_filepath_list))
  return cropped_image_filepath_list  

######################################################

def combine_relative_tables(relative_table_filepath_list, rotated = False):

  map_ocr_results_table = pd.DataFrame()
  for ocr_result_table_path in relative_table_filepath_list:
    ### For each crop of map ###
    table = pd.read_csv(ocr_result_table_path)
    # Take data in the filename and put them into the table
    table_filename = ocr_result_table_path.split('/')[-1]
    map_id = int(table_filename.split('_')[0])
    wsl = int(re.findall('_wsl_(\d+)_',table_filename)[0])
    table['map_id'] = map_id
    table['x_offset'] = int(re.findall('_xoff(\d+)_',table_filename)[0])
    table['y_offset'] = int(re.findall('_yoff(\d+)_',table_filename)[0])
    table['wsl'] = wsl
    map_ocr_results_table = map_ocr_results_table.append(table, ignore_index=True)

  # Rename "bounding box" column in the raw table to be "relative bounding box"
  map_ocr_results_table = map_ocr_results_table.rename(columns={'bounding_box':'relative_bounding_box'})

  # Evaluate relative bounding box, string -> list
  map_ocr_results_table['relative_bounding_box'] = map_ocr_results_table['relative_bounding_box'].apply(ast.literal_eval)

  if rotated:
    map_ocr_results_table['relative_bounding_box'] =   map_ocr_results_table['relative_bounding_box'].apply(lambda li: [[wsl - li[0], wsl - li[1]], [wsl - li[2], wsl - li[3]], [wsl - li[4], wsl - li[5]], [wsl - li[6], wsl - li[7]]])

  # Add x and y offsets so that "relative bounding box" become "bounding box" in the original full image/map
  map_ocr_results_table['bounding_box'] = map_ocr_results_table[['relative_bounding_box','x_offset','y_offset']].apply(lambda row: np.array(row['relative_bounding_box']).reshape(-1,2) + np.array((row['x_offset'], row['y_offset'])), axis=1)

  return map_ocr_results_table

#==================================================================================================#





#======================================== COLOR ANALYZER ==========================================#

def analyze_color(input_image, transparency_threshold = 50, plot_3d = False, plot_bar = True, n_cluster = None, max_cluster = 10, ignore_pure_black = True, use_sample = True, return_colors = True):

  # Copy to prevent modification (useful but mechanism needs clarification)
  input_image = input_image.copy()

  # Check input shape
  assert(len(input_image.shape) == 3)
  assert(input_image.shape[-1] in {3,4})

  # Turn color info of pixels into dataframe, filter by transparency if RGBA image is passed
  if input_image.shape[-1] == 4:
    color_df = pd.DataFrame(input_image.reshape(-1,4), columns=list('rgba'))
    # Get the rgb info of pixels in the non-transparent part of the image
    color_df = color_df[color_df['a']>=transparency_threshold]
  if input_image.shape[-1] == 3:
    color_df = pd.DataFrame(input_image.reshape(-1,3), columns=list('rgb'))

  if ignore_pure_black:
    color_df = color_df[~((color_df['r']==0)&(color_df['g']==0)&(color_df['b']==0))]

  # Handle large pixel color_df
  if len(color_df)>1e5:
      if use_sample:
        sample_or_not = (input('Large image detected, would you like to sample the pixels in this image? (Y/N) ')).lower()[0] == 'y'
      if sample_or_not:
        print('Sampled 100,000 pixels from the image, note that you can also resize the image before passing it to this function.')
        color_df = color_df.sample(n = int(1e5), random_state = 0)
      else:
        print('Not sampling performed, but note that rendering 3D plot for the pixels may crash your session and K-means clustering will be slow.')

  # Get std for reverse-transform the kmeans results to a meaningful rgb palette
  r_std, g_std, b_std = color_df[list('rgb')].std()
  reverse_whiten_array = np.array((r_std, g_std, b_std))

  # Normalize observations on a per feature basis, forcing features to have unit variance
  # Doc: https://docs.scipy.org/doc/scipy/reference/generated/scipy.cluster.vq.whiten.html
  for color in list('rgb'):
    color_df['scaled_'+color] = whiten(color_df[color])


  ## 3D scatter plot showing color groups
  if plot_3d:
    trace = go.Scatter3d(x=color_df['r'], y=color_df['g'], z=color_df['b'], mode='markers',
                        marker=dict(color=['rgb({},{},{})'.format(r,g,b) for r,g,b in zip(color_df['r'].values, color_df['g'].values, color_df['b'].values)],
                                    size=1, opacity=1))
    layout = go.Layout(margin=dict(l=0, r=0, b=0, t=0))
    fig = go.Figure(data=[trace], layout=layout)
    fig.show()

  ## Use K-means to identify main colors
  cluster_centers_list = []
  avg_distortion_list = []

  if n_cluster != None:
    n_cluster_range = [n_cluster-1] # note minus 1 to get exactly n
  else:
    n_cluster_range = range(max_cluster+1)

  if plot_bar:
    # Initialize plt graph
    f, ax = plt.subplots(len(n_cluster_range), 1, figsize=(10,10))

  for n in n_cluster_range:

    ###### Train clusters ######

    cluster_centers, avg_distortion = kmeans(color_df[['scaled_r', 'scaled_g', 'scaled_b']], n + 1)

    ###### Assign labels ######

    labels, distortions = vq( color_df[['scaled_r', 'scaled_g', 'scaled_b']] , cluster_centers)

    color_df['label'] = labels
    color_df['distortion'] = distortions

    ###### Build palette ######

    # These parameter affects visual style only and can be exposed to user later
    height = 200
    width = 1000
    gap_size = 5
    palette = np.zeros((height, width, 3), np.uint8)

    # Count how many pixels falls under which category, let this decides the color's relative width in the palette
    cluster_proportion = color_df['label'].value_counts().sort_index()/len(color_df)
    cluster_width_list = (cluster_proportion * width).to_list()
    cluster_width_list = [int(x) for x in saferound(cluster_width_list, places=0)]

    # Reorder clusters and widths according to the proportion, largest to smallest
    reordered_cluster_df = pd.DataFrame(zip(cluster_centers, cluster_width_list),columns=['cluster','width']).sort_values('width',ascending=False)
    cluster_centers = reordered_cluster_df['cluster'].tolist()
    cluster_width_list = reordered_cluster_df['width'].tolist()

    # Storing information
    cluster_centers_list.append(cluster_centers)
    avg_distortion_list.append(avg_distortion)

    if plot_bar:
      # Coloring the palette canvas based on color and width
      endpoints = list(np.cumsum(cluster_width_list))
      startpoints = [0]+endpoints[:-1]
      for cluster_index in range(len(cluster_centers)):
        # Notice here we apply the reverse_whiten_array to get meaningful RGB colors
        palette[:, startpoints[cluster_index]+gap_size:endpoints[cluster_index], :] = cluster_centers[cluster_index] * reverse_whiten_array
        palette[:, startpoints[cluster_index]:startpoints[cluster_index]+gap_size, :] = (255,255,255)

      # Displaying the palette when performing K-means with parameter n
      if n_cluster != None:
        ax.imshow(palette)
        ax.axis('off')
      else:
        ax[n].imshow(palette)
        ax[n].axis('off')

  if plot_bar:
    ### Show the entire palette
    f.tight_layout()
    plt.show()
    ### Show the elbow plot for choosing best n_cluster parameter for K-means
    fig = plt.figure()
    plt.scatter(x = n_cluster_range, y = avg_distortion_list)
    fig.suptitle('Elbow Plot for K-means')
    plt.xlabel('Number of Clusters')
    plt.ylabel('Average Distortion')
    print()

  if return_colors:
    if n_cluster != None:
      return (cluster_centers_list[0]*reverse_whiten_array).astype(np.uint8)
    else:
      return [(cluster_centers*reverse_whiten_array).astype(np.uint8) for cluster_centers in cluster_centers_list]

#==================================================================================================#






#======================================== MPL IMAGE SAVING ========================================#

def imsave(img, filename):
  plt.imsave(filename, img, cmap=cm.gray)

def get_w_h_ratio(img):
  return img.shape[1]/img.shape[0]
  
def imshow(img, width = 9, dpi = 90):
    
  w_h_ratio = get_w_h_ratio(img)
  plt.figure(figsize=(width,round(width*w_h_ratio,1)), dpi=dpi)
  plt.grid(False)
  if len(img.shape)==2:
    plt.imshow(img, cmap='gray', vmin=0, vmax=255)
  else:
    plt.imshow(img)

def save_graph(filename = '', dpi = 150, padding = 0.3, transparent = False, add_title = False, folder = None):

  orig_filename = filename

  if not os.path.exists('saved_graphs'):
    os.mkdir('saved_graphs')

  if filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg') or filename.lower().endswith('.png'):
    filename = filename+'.png'

  if filename == '':
    image_paths = [p.split('/')[-1].split('.')[0] for p in glob('./saved_graphs/*')]
    available_indices = [int(p) for p in image_paths if p.isnumeric()]
    if len(available_indices) == 0:
      next_index = 1
    else:
      next_index = max(available_indices)+1
    filename = str(next_index).zfill(2)+'.png'


  if add_title:
    if orig_filename!='':
      plt.suptitle(orig_filename)

  if folder == None:
    plt.savefig('./saved_graphs/'+filename, dpi=dpi, bbox_inches='tight', transparent=transparent, pad_inches=padding)
  else:
    plt.savefig(folder+filename, dpi=dpi, bbox_inches='tight', transparent=transparent, pad_inches=padding)
  print('Graph "'+filename+'" saved.')

#==================================================================================================#








#========================= HIGH LEVEL GEOMETRY BASED FEATURE EXTRACTOR ============================#

###### FIND CONTOURS ######

def create_hierarchy_df(hierarchy):
  # Reference: https://docs.opencv.org/4.x/d9/d8b/tutorial_py_contours_hierarchy.html
  hierarchy = hierarchy[0]
  hierarchy_df = pd.DataFrame(hierarchy, columns=['next','prev','child','parent'])
  import networkx as nx
  G = nx.DiGraph()
  for index, row in hierarchy_df.query('parent != -1').iterrows():
    G.add_edge(row['parent'], index)
  root_nodes = hierarchy_df.query('parent == -1 & child != -1').index.tolist()
  node_depth_mapping = {}
  for root_node in root_nodes:
    node_depth_mapping.update( nx.shortest_path_length(G, root_node) )
  hierarchy_df['level'] = hierarchy_df.index.map(node_depth_mapping).fillna(0)
  hierarchy_df['level'] = hierarchy_df['level'].apply(int)
  return hierarchy_df

def get_contour_area_size(cnt):
  try:
    return cv2.contourArea(cnt)
  except TypeError as e:
    return cv2.contourArea(np.float32(cnt))

def find_contours(img, min_area_size = 1000, max_area_size = None, top_k = None, color_mode = 'rainow', border_width = 2, show = True, only_exterior = False, only_lowest_k = None, verbose = True):

  img = img.copy()

  if only_exterior:
    contours, hierarchy = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
  elif only_lowest_k != None:
    contours, hierarchy = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    hierarchy_df = create_hierarchy_df(hierarchy)
    contours_indices = hierarchy_df.loc[hierarchy_df['level'].isin(  sorted(hierarchy_df['level'].unique())[:only_lowest_k]  )].index.tolist()
    contours = np.array(contours, dtype=object)[contours_indices]
  else:
    contours, hierarchy = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

  contours = [cnt for cnt in contours if get_contour_area_size(cnt)>=min_area_size]
  if max_area_size != None:
    contours = [cnt for cnt in contours if get_contour_area_size(cnt)<=max_area_size]
  contours = sorted(contours, key=lambda cnt: get_contour_area_size(cnt), reverse = True)
  if verbose:
    print(len(contours),'contours found.')

  if top_k != None:
    print('Showing the',top_k,'largest contours.')
    contours = contours[:top_k]

  if show:

    if color_mode == 'red':

      # Draw contours in red
      colored_img = grey_to_bgr(img)
      for cnt in contours:
        colored_img = cv2.drawContours(colored_img, [cnt], 0, (255,0,0), border_width)
      imshow(colored_img)

    elif color_mode == 'rainbow':
      
      # Draw contours in rainbow colors
      n_colors = 8
      color_range = range(1,n_colors*10+1,n_colors)
      colors = [hsv2rgb(num/100) for num in color_range]

      colored_img = grey_to_bgr(img)

      for i in range(len(contours)):
          cnt = contours[i]
          color = colors[i%len(color_range)]
          colored_img = cv2.drawContours(colored_img , [cnt] , -1, color , border_width)

      imshow(colored_img)
  
  return contours

###### SMOOTH/SIMPLIFY CONTOURS ######
def approximate_contours(contours = [], precision_level = 0.01, border_width = 2, show = False, img = None):
  approx_contours = []
  for cnt in contours:
    hull = cv2.convexHull(cnt)
    epsilon = precision_level*cv2.arcLength(hull,True)
    approx = cv2.approxPolyDP(cnt,epsilon,True)
    approx_contours.append(approx)
  approx_contours = [cnt for cnt in approx_contours if len(cnt)>2]
  contour_count_change = len(contours) - len(approx_contours)
  if contour_count_change>0:
    print(str(contour_count_change) + ' contours are dropped because they have less than 3 edges.')
  if show:
    colored_img = grey_to_bgr(img)
    for approx in approx_contours:
      colored_img = cv2.drawContours(colored_img, [approx], 0, (255,0,0), border_width)
    imshow(colored_img)
  return approx_contours

###### SMOOTH/SIMPLIFY CONTOURS (EXPERIMENTAL) ######
def get_movement_direction(x_diff, y_diff):
  return np.arctan2(x_diff,y_diff)/np.pi*180
def get_movement_distance(x_diff, y_diff):
  return np.linalg.norm((x_diff, y_diff))
def angle_diff(sourceA,targetA):
  a = targetA - sourceA
  a = (a + 180) % 360 - 180
  return a
def get_contour_info_df(cnt):
  movements = np.diff(cnt,axis=0)
  directions = [get_movement_direction(*mov[0]) for mov in movements]
  distances = [get_movement_distance(*mov[0]) for mov in movements]
  cnt_info = pd.DataFrame(zip([(i-1,i) for i in range(1,len(movements))],[mov[0] for mov in movements],distances,directions), columns=['point_index','movement','distance','direction'])
  cnt_info['prev_direction'] = cnt_info.direction.shift(1)
  cnt_info['direction_change'] = cnt_info.apply(lambda row: angle_diff(row['prev_direction'],row['direction']), axis=1)
  cnt_info = cnt_info = cnt_info.drop('prev_direction',axis=1)
  return cnt_info
def keep_segments_longer_than(cnt, min_segment_len):
  cnt_info = get_contour_info_df(cnt)
  preserved_point_indices = flatten_list( cnt_info.loc[cnt_info['distance']>=min_segment_len,'point_index'].tolist() )
  preserved_cnt = cnt[preserved_point_indices]
  return preserved_cnt
def get_length_of_segments(cnt, order = 'original'):
  cnt_with_head_at_tail = np.array(list(cnt)+list(cnt[:1]))
  length_of_segments = list(np.round(np.sqrt(np.sum(np.square((cnt_with_head_at_tail[:-1] - cnt_with_head_at_tail[1:])), axis=2)).flatten(),1))
  if order.startswith('orig'):
    return length_of_segments
  elif order.startswith('asc'):
    return sorted(length_of_segments)
  elif order.startswith('des'):
    return sorted(reversed(length_of_segments))
def stop_at_abrupt_change(contours, sudden_change_ratio = 10):
  output_contours = []
  prev_cnt_size = 0
  for cnt in contours:
    cnt_size = cv2.contourArea(cnt)
    if cnt_size < 1e4 or prev_cnt_size/cnt_size > sudden_change_ratio:
      break
    output_contours.append(cnt)
    prev_cnt_size = cnt_size
  return output_contours

###### VISUALIZE CONTOURS ######
def draw_many_contours(img, contours, text_content_list=None, dpi=None, border_width=2, n_colors = 10, font_scale = 1, is_bgr = True, save_not_show = False):
  
  color_range = range(1,n_colors*10+1,n_colors)
  colors = [hsv2bgr(num/100) if is_bgr else hsv2rgb(num/100) for num in color_range]

  if len(img.shape)==2:
    colored_img = grey_to_bgr(img)
  elif len(img.shape)==3:
    if is_bgr:
      colored_img = img.copy()
    else:
      colored_img = rgb_to_bgr(img)

  text_content_list = range(len(contours)) if text_content_list is None else text_content_list

  for i in range(len(contours)):
    cnt = contours[i]
    color = colors[i%n_colors]
    colored_img = cv2.drawContours(colored_img, [cnt], 0, color, border_width)

    M = cv2.moments(cnt)
    cx = int(M['m10']/M['m00'])
    cy = int(M['m01']/M['m00'])
    text_position = (cx, cy)
    
    text_content = str(text_content_list[i])
    font_family = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = font_scale
    color = color
    thickness = 2
    line_type = cv2.LINE_AA

    colored_img = cv2.putText(colored_img, text_content , text_position, font_family, font_scale, color, thickness, line_type)
  
  if save_not_show:

    return colored_img

  else:

    if dpi != None:
      imshow(colored_img, dpi = dpi)
    else:
      imshow(colored_img)

###### SELECT WITH CONTOURS ######
def mask_with_contours(img, contours):
  # img = img.copy()
  mask_color = 255 if len(img.shape)==2 else (255,255,255) if len(img.shape)==3 else 255
  contours_mask = cv2.drawContours(np.zeros(img.shape, dtype=np.uint8), contours, -1, mask_color, -1)
  masked_img = cv2.bitwise_and(img, contours_mask)
  return masked_img

###### CONTOUR I/O WITH CSV ######
def stringify_contour(contour):
  return '|'.join([','.join(map(str,list(point[0]))) for point in contour])
def recover_contour_from_string(contour_string):
  list_of_points = [list(point.split(',')) for point in contour_string.split('|')]
  return np.array(list_of_points, dtype=np.int32)

###### FIND LINES ######
def find_lines(img, canny_lower_thresh = 50, canny_upper_thresh = 200, rho = 1, theta = np.pi / 180, threshold = 25, min_line_length = 100, max_line_gap = 20, show = True, return_lines = False, return_layer = True):
  # rho              # distance resolution in pixels of the Hough grid
  # theta            # angular resolution in radians of the Hough grid
  # threshold        # minimum number of votes (intersections in Hough grid cell)
  # min_line_length  # minimum number of pixels making up a line
  # max_line_gap     # maximum gap in pixels between connectable line segments

  img = img.copy()

  edges = cv2.Canny(img,canny_lower_thresh,canny_upper_thresh)

  # `lines` contain endpoints of detected line segments
  lines = cv2.HoughLinesP(edges, rho, theta, threshold, np.array([]), min_line_length, max_line_gap)

  if show:
    # draw lines on a RGB layer
    lines_layer_rgb = np.zeros((*img.shape, 3), dtype = np.uint8)
    for line in lines:
      for x1,y1,x2,y2 in line:
        cv2.line(lines_layer_rgb,(x1,y1),(x2,y2),(255,0,0),1)
    overlayed = cv2.addWeighted(grey_to_rgb(img), 0.8, lines_layer_rgb, 1, 0)
    imshow(overlayed)

  if return_lines:
    return lines

  if return_layer:
    # draw lines on a binary layer
    lines_layer = np.zeros(img.shape, dtype = np.uint8)
    for line in lines:
      for x1,y1,x2,y2 in line:
        cv2.line(lines_layer,(x1,y1),(x2,y2),255,1)
    return lines_layer

#==================================================================================================#






#=========================== HIGH LEVEL COLOR BASED FEATURE EXTRACTOR =============================#

###### UTILS ######
def random_sample_position_of_certain_value(ndarray, value, format = 'xy'):
  yx = np.unravel_index( np.random.choice(np.where(ndarray.flatten() == value)[0]), ndarray.shape )
  if format == 'xy':
    return tuple(reversed(yx))
  elif format == 'yx':
    return yx
def get_vicinity(img,pixel_pos,radius): # pixel_pos in (x,y) format
  x, y = pixel_pos
  vicinity = img[max(0,y-radius):min(y+radius+1,img.shape[0]), max(0,x-radius):min(x+radius+1,img.shape[1])].copy()
  return vicinity
def test_moving_point(seed_pixel_pool, contour, potential_seed, move_point):
  dist_to_contour = cv2.pointPolygonTest(contour, potential_seed, measureDist=True)
  seed_vicinity = get_vicinity(seed_pixel_pool, potential_seed, radius = 2)
  seed_vicinity_not_all_bright = invert_binary(seed_vicinity).sum() > 0
  # initialize prev_dist_to_contour with a large value
  prev_dist_to_contour = max(seed_pixel_pool.shape)
  while dist_to_contour <= 0 or seed_vicinity_not_all_bright:
    # moving point
    potential_seed = move_point(*potential_seed)
    # get dist to contour and check vicinity all bright or not
    dist_to_contour = cv2.pointPolygonTest(contour, potential_seed, measureDist=True)
    seed_vicinity = get_vicinity(seed_pixel_pool, potential_seed, radius = 2)
    seed_vicinity_not_all_bright = invert_binary(seed_vicinity).sum() > 0
    # check if going in the wrong direction outside the contour
    if dist_to_contour <= 0 and abs(dist_to_contour) > abs(prev_dist_to_contour):
      return None
    # save current dist as prev for comparison in the next iteration
    prev_dist_to_contour = dist_to_contour
  # exiting whilte looping meaning seed meet criteria
  return potential_seed
def create_range_around(hsv_code, radius = (3,10,10)):
  lower_bound, upper_bound = [], []
  for i in range(len(hsv_code)):
    lower_value = hsv_code[i]-radius[i]
    upper_value = hsv_code[i]+radius[i]
    if i == 0:
      lower_value = lower_value % 180
      upper_value = upper_value % 180
    else:
      lower_value = np.clip(lower_value, 0, 255)
      upper_value = np.clip(upper_value, 0, 255)
    lower_bound.append(lower_value)
    upper_bound.append(upper_value)
  return tuple(lower_bound), tuple(upper_bound)

def find_area_of_color(img, hsv_cde, radius, alpha = 0.5, dpi = 150, overlay = True, show = True, return_mask = False):

  img = img.copy()
  img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

  lower_bound, upper_bound = create_range_around(hsv_code = hsv_cde, radius = radius)

  if lower_bound[0]>upper_bound[0]: # for color hue like red that are on the edge of hue range
    lower_mask = cv2.inRange(img_hsv, (0,lower_bound[1],lower_bound[2]), (lower_bound[0],upper_bound[1],upper_bound[2]))
    upper_mask = cv2.inRange(img_hsv, (upper_bound[0],lower_bound[1],lower_bound[2]), (180,upper_bound[1],upper_bound[2]))
    mask = cv2.bitwise_or(lower_mask, upper_mask)
  else:  # for other color not on the edge
    mask = cv2.inRange(img_hsv, lower_bound, upper_bound )

  cropped_hsv = cv2.bitwise_and(img_hsv, img_hsv, mask=mask)
  cropped = cv2.cvtColor(cropped_hsv, cv2.COLOR_HSV2BGR)
  if show:
    if overlay:
      overlayed = cv2.addWeighted(cropped, alpha, img, 1-alpha, 0.0)
      imshow(overlayed, dpi = dpi)
    else:
      imshow(cropped, dpi = dpi)
  if return_mask:
    return mask

def flood_fill(img, seed_pixel, return_mask = False, fill_value = (0,0,0), color_variation = 5, neighbor = 4):

  if isinstance( seed_pixel, list ):
    seed_pixel_list = seed_pixel
  else:
    seed_pixel_list = [seed_pixel]

  flood_img = img.copy()

  if fill_value != (0,0,0):
    black_pixels = np.where((flood_img[:, :, 0] == 0) & (flood_img[:, :, 1] == 0) & (flood_img[:, :, 2] == 0))
    flood_img[black_pixels] = fill_value

  h, w = flood_img.shape[:2]

  mask_list = []
  for seed_pixel in seed_pixel_list:
    num, flood_img, mask, rect = cv2.floodFill(flood_img, np.zeros((h+2,w+2),np.uint8), seed_pixel, fill_value, tuple([color_variation]*3), tuple([color_variation]*3), neighbor)
    mask_list.append(mask)

  combined_mask = mask_list.pop(0)
  while mask_list:
    combined_mask = cv2.bitwise_or(combined_mask, mask_list.pop())
  combined_mask = combined_mask[1:-1,1:-1]
  combined_mask = combined_mask*255

  if return_mask:
    return flood_img, combined_mask
  return flood_img

#==================================================================================================#






#================================== UTILS FOR GDRIVE FOLDER =======================================#
 
def move_shallow_folder(from_folder, to_folder, copy = False, exclude_regex = None):

  from_folder = from_folder.rstrip('/')
  to_folder = to_folder.rstrip('/')

  if glob(to_folder+'/*'):
    decision = input('[Warning] to_folder is not empty, do you want to "overwrite" or "append" or "stop"?')
    if decision == 'overwrite':
      for p in glob(to_folder+'/*'):
        os.remove(p)
    elif decision == 'stop':
      return
    elif decision != 'append':
      raise ValueError('[Error] Invalid decision code.')
  
  from_filepaths = glob(from_folder+'/*')
  if exclude_regex is not None:
    from_filepaths = [p for p in from_filepaths if not re.findall(exclude_regex, p)]
  if not os.path.exists(to_folder):
    print('Creating to_folder at:', to_folder)
    os.mkdir(to_folder)

  for from_p in tqdm(from_filepaths):
    to_p = to_folder + '/' + from_p[::-1].split('/', maxsplit = 1)[0][::-1]
    if copy:
      shutil.copy(from_p, to_p)
    else:
      shutil.move(from_p, to_p)

#==================================================================================================#








#======================================= SELF FUZZY CLUSTER =======================================#

def self_fuzzy_cluster(data, field, correct_term_min_freq=1, scorer=fuzz.partial_ratio, score_cutoff=90, verbose=False):
  
  """For each fuzzy cluster, choose most frequent term as exemplar, if there is a tie, use the longer term."""

  temp_df = data[field].dropna().value_counts().reset_index().rename(columns = {'index':'term',field:'freq'})
  temp_df['term_length'] = temp_df['term'].apply(len)
  temp_df['freq_length_tuple'] = list(zip(temp_df['freq'], temp_df['term_length']))

  term_to_freq_length_tuple_mapping = temp_df.set_index('term')['freq_length_tuple'].to_dict()

  all_terms = temp_df.loc[temp_df['freq']>=correct_term_min_freq,'term'].tolist()

  if verbose:
    temp_df['thresholded_matches'] = temp_df['term'].progress_apply(lambda x: [term for term,freq in process.extractBests(x, all_terms, scorer=scorer, score_cutoff=score_cutoff)])
  else:
    temp_df['thresholded_matches'] = temp_df['term'].apply(lambda x: [term for term,freq in process.extractBests(x, all_terms, scorer=scorer, score_cutoff=score_cutoff)])

  G = nx.Graph()

  for row in temp_df[['term','thresholded_matches']].itertuples():
    term = row.term
    for match in row.thresholded_matches:
      G.add_edge(term, match)

  term_groups = [list(group) for group in list(nx.connected_components(G))]

  term_to_most_frequent_term_mapping = {}

  for term_group in term_groups:
    most_frequent_term = max(term_group, key = lambda x: term_to_freq_length_tuple_mapping[x])
    term_to_most_frequent_term_mapping.update( dict(zip(term_group, [most_frequent_term]*len(term_group))) )

  temp_df['most_common_term'] = temp_df['term'].map(term_to_most_frequent_term_mapping)

  temp_df = temp_df.dropna(subset=['most_common_term'])
  
  term_correction_mapping = temp_df.set_index('term')['most_common_term'].to_dict()
  
  return term_correction_mapping

#==================================================================================================#







#=================================== DEDUPLICATE OCR RESULT =======================================#

def get_dbscan_labels(data, field, radius = 0.5):
  clusterer = DBSCAN(eps=radius, algorithm='auto', metric='euclidean', min_samples=2)
  coorindates_array = np.array(data[field].tolist())
  clusterer.fit(coorindates_array)
  clabels = clusterer.labels_
  return clabels

def detect_duplicates(df, minimum_text_area_side_length = 20, minimum_area_thres = None, dbscan_radius = None, fuzzy_scorer=fuzz.partial_ratio, fuzzy_score_cutoff=80, intersection_cover_smaller_shape_by = 0.8, no_numeric = False):

  ## If not explicitly specified, initialize thresholds based on minimum_text_area_side_length (measured in pixels)
  if minimum_area_thres is None:
    minimum_area_thres = int(minimum_text_area_side_length**2)
  if dbscan_radius is None: # scale by 5, an experience based choice which can be fine-tuned
    dbscan_radius = int(2 * minimum_text_area_side_length)

  ## Placeholder for outputs
  ocr_entry_ids_to_drop = []
  backup_ids_mapping = {} # for data provenance and backtracking errors

  ## -------------------------------------------------------------------------------------------------

  ## "basic quality check" within "the whole image"
    
  # criteria is 'cleaned text is not empty & cleaned text is not numeric & bounding box area size > thres'
  # some entries with low ocr confidence are correct, so not using ocr confidence as criteria
  poor_quality_filter = (df['cleaned_text'].apply(len)==0) | (df['bbox_area']<minimum_area_thres)
  if no_numeric:
    poor_quality_filter = poor_quality_filter | (df['cleaned_text'].str.isnumeric())
  poor_quality_ocr_entry_ids = df.loc[poor_quality_filter, 'ocr_entry_id'].tolist()
  ocr_entry_ids_to_drop += poor_quality_ocr_entry_ids
  backup_ids_mapping[-1] = poor_quality_ocr_entry_ids
  df = df[~df['ocr_entry_id'].isin(ocr_entry_ids_to_drop)].copy()

  ## -------------------------------------------------------------------------------------------------

  ## For de-duplication purpose, cluster the ocr bounding box by their centers' locations on the image

  ## "intersection based de-duplications" within "clusters"

  df['dbscan_cluster_id'] = get_dbscan_labels(df, 'bbox_center', radius = dbscan_radius)

  cluster_id_list = get_non_single_elements(df, 'dbscan_cluster_id')
  if -1 in cluster_id_list:
    cluster_id_list.remove(-1)

  for cluster_id in tqdm(cluster_id_list):

    cluster_df = df[df['dbscan_cluster_id'] == cluster_id].copy()

    cluster_df['fuzzy_matched_text'] = cluster_df['text'].map(self_fuzzy_cluster(cluster_df, 'text', scorer = fuzzy_scorer, score_cutoff = fuzzy_score_cutoff))

    repeated_terms = get_non_single_elements(cluster_df, 'fuzzy_matched_text')

    for term in repeated_terms:
      
      same_term_group = cluster_df[cluster_df['fuzzy_matched_text']==term].copy()
      same_term_group['shapely_polygon'] = same_term_group['bounding_box'].apply(lambda x: shapely_polygon(x))
      same_term_group['shapely_polygon_area_size'] = same_term_group['shapely_polygon'].apply(lambda x: x.area)
      same_term_group = same_term_group.sort_values('shapely_polygon_area_size', ascending=False).reset_index(drop=True)

      for i in range(len(same_term_group)-1):
        # print('i:',i)
        larger_shape_ocr_entry_id = same_term_group['ocr_entry_id'][i]
        if larger_shape_ocr_entry_id in ocr_entry_ids_to_drop:
          # print('skip large')
          continue
        larger_shape = same_term_group['shapely_polygon'][i]

        for j in range(i+1, len(same_term_group)):
          # print('j:',j)
          smaller_shape_ocr_entry_id = same_term_group['ocr_entry_id'][j]
          if smaller_shape_ocr_entry_id in ocr_entry_ids_to_drop:
            # print('skip small')
            continue
          smaller_shape = same_term_group['shapely_polygon'][j]

          smaller_shape_area_size = same_term_group['shapely_polygon_area_size'][j]
          
          ## try except to catch the error where one or both of the shapes are invalid
          try:
            intersection_area_size = larger_shape.intersection(smaller_shape).area
          except:
            intersection_area_size = None

          if intersection_area_size == None or intersection_area_size/smaller_shape_area_size > intersection_cover_smaller_shape_by:  
            # If intersection between larger and smaller shapes cover the majority of the smaller shape, 
            # then we can say that the smaller shape is contained in the larger shape, thus likely a duplicate
            ocr_entry_ids_to_drop.append(smaller_shape_ocr_entry_id)
            backup_ids_mapping[larger_shape_ocr_entry_id] = backup_ids_mapping.get(larger_shape_ocr_entry_id, [])+[smaller_shape_ocr_entry_id]

  df = df[~df['ocr_entry_id'].isin(ocr_entry_ids_to_drop)].copy()

  ## -------------------------------------------------------------------------------------------------

  return ocr_entry_ids_to_drop, backup_ids_mapping

#==================================================================================================#








#===================================== WRITE SHAPEFILE ============================================#

def get_dtype_as_string(x):
  return 'int' if isinstance(x,int) else 'float' if isinstance(x,float) else 'str'

def create_shapefile_from_df(filepath, dataframe, properties_columns, geometry_column, geometry_type = 'Polygon', crs = 'EPSG:4326'):

  ##############################
  # Copy dataframe & reset index
  dataframe = dataframe.copy().reset_index(drop=True)

  ##############################
  # Build schema based on inputs
  sample_value_dict = dataframe[:1].T.to_dict()[0]
  schema = {'properties': [( col,  get_dtype_as_string(sample_value_dict[col])  ) for col in properties_columns], 
  'geometry': geometry_type}

  ##############################
  # Open a fiona object
  shp_file = fiona.open(filepath, mode = 'w', driver = 'ESRI Shapefile', schema = schema, crs = crs)
  # Create records
  records = []
  for _, row in dataframe.iterrows():
    records.append({
        'properties': {col: row[col] for col in properties_columns} ,
        'geometry' : {'type': geometry_type, 'coordinates': [ row[geometry_column] ]} , # remember to keep the outer square brackets
    })
  # Write records
  shp_file.writerecords(records)
  # Close fiona object
  shp_file.close()

#==================================================================================================#




#========================================= Geospatial =============================================#

def latlon_to_xy(latlon_pair, affine_transform_object):
  transform_string = repr(affine_transform_object)
  transform_string = re.findall(r'\((.*?)\)',transform_string.replace('\n',''))[0]
  num_string_list = re.split(r'\,\s+',transform_string)
  transform_matrix = np.array([eval(x) for x in num_string_list]+[0,0,1]).reshape((3,3))
  product_vector = np.array([latlon_pair[1], latlon_pair[0], 1])
  xy = np.linalg.solve(transform_matrix, product_vector)[:2]
  return xy

#==================================================================================================#







#======================================= Image Matching ===========================================#

def point_in_orig_to_point_in_georef(point_in_orig, matching_table):
  try:
    matching_table['distance_on_orig'] = matching_table['keypoints0'].apply(lambda tup: np.linalg.norm(np.array(point_in_orig) - np.array(tup)))
    nearest_four_points_on_orig_and_their_matches = matching_table.sort_values('distance_on_orig')[:4]
    nearest_four_points_on_orig_and_their_matches = nearest_four_points_on_orig_and_their_matches[~nearest_four_points_on_orig_and_their_matches.index.isin([626])]
    input_pts = np.array(nearest_four_points_on_orig_and_their_matches['keypoints0'].tolist()).astype(np.float32)
    output_pts = np.array(nearest_four_points_on_orig_and_their_matches['keypoints1'].tolist()).astype(np.float32)
    M = cv2.getPerspectiveTransform(input_pts, output_pts)
    point_in_georef = tuple(np.round(cv2.perspectiveTransform(np.array([[point_in_orig]], dtype=np.float32), M),0).astype(int)[0][0])
  except:
    point_in_georef = (-1,-1)
  return point_in_georef

def get_angle_diff(angle1, angle2):
  return min(abs(angle1-angle2),360-abs(angle1-angle2))
def get_average_angle(arr):
  arr = np.array(arr)
  return np.round(np.degrees(np.arctan2(np.mean(np.sin(np.radians(arr))),  np.mean(np.cos(np.radians(arr))))),1)
def rotate_coordinate(p, origin=(0, 0), degrees=0):
  # Reference: https://stackoverflow.com/a/58781388
  angle = np.deg2rad(degrees)
  R = np.array([[np.cos(angle), -np.sin(angle)],
                [np.sin(angle),  np.cos(angle)]])
  o = np.atleast_2d(origin)
  p = np.atleast_2d(p)
  return np.squeeze((R @ (p.T-o.T) + o.T).T).astype(np.int32)

#==================================================================================================#





clear_output()
print('\nImage data mining (IDM) module is ready. Enjoy exploring!\n')

#========================================= References =============================================#

# https://stackoverflow.com/questions/16705721/opencv-floodfill-with-mask
# https://blog.csdn.net/qq_37385726/article/details/82313004
# https://stackoverflow.com/questions/60197665/opencv-how-to-use-floodfill-with-rgb-image
# https://rasterio.readthedocs.io/en/latest/topics/georeferencing.html
# https://hatarilabs.com/ih-en/how-to-create-a-pointlinepolygon-shapefile-with-python-and-fiona-tutorial

#==================================================================================================#


