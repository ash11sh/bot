from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import time
import json

import numpy as np
from PIL import Image
import tflite_runtime.interpreter as tflite


def load_labels(filename):
  with open(filename, 'r') as f:
    return [line.strip() for line in f.readlines()]

def get_pred(img):
  input_std = 127.5
  input_mean = 127.5
  interpreter = tflite.Interpreter(model_path='model.tflite', num_threads=None)
  interpreter.allocate_tensors()

  input_details = interpreter.get_input_details()
  output_details = interpreter.get_output_details()

  # check the type of the input tensor
  floating_model = input_details[0]['dtype'] == np.float32

  # NxHxWxC, H:1, W:2
  height = input_details[0]['shape'][1]
  width = input_details[0]['shape'][2]
  img = Image.open(img).resize((width, height))

  # add N dim
  input_data = np.expand_dims(img, axis=0)

  if floating_model:
    input_data = (np.float32(input_data) - input_mean) / input_std

  interpreter.set_tensor(input_details[0]['index'], input_data)

  start_time = time.time()
  interpreter.invoke()
  stop_time = time.time()

  output_data = interpreter.get_tensor(output_details[0]['index'])
  results = np.squeeze(output_data)

  top_k = results.argsort()[-5:][::-1]
  labels = load_labels('labels.txt')
  predictions = []
  for i in top_k:
    if floating_model:
      #  print('{:08.6f}: {}'.format(float(results[i]), labels[i]))
       prediction = {"label": labels[i], "proba": float(results[i])}
       predictions.append(prediction)
    else:
      # print('{:08.6f}: {}'.format(float(results[i] / 255.0), labels[i]))
      prediction = {"label": labels[i], "proba": float(results[i] / 255.0)}
      predictions.append(prediction)

  # print('time: {:.3f}ms'.format((stop_time - start_time) * 1000))
  # return predictions
  json_response = {'predictions': predictions}
  prediction_list = list(json_response['predictions'])
  result = ''
  for index, prediction in enumerate(prediction_list):
    label = prediction['label']
    proba = prediction['proba']
    result += '{} ({:.4f})\n'.format(label, proba)
  return result
