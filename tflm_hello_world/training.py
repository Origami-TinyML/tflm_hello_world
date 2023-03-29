# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/training.ipynb.

# %% auto 0
__all__ = ['train_model']

# %% ../nbs/training.ipynb 1
import matplotlib.pyplot as plt
import numpy as np
import cv2
import PIL
import tensorflow as tf
import os
import pandas as pd
from io import BytesIO
import subprocess

from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.models import Sequential

# %% ../nbs/training.ipynb 2
class train_model():

  if not os.path.exists('models'):
        os.mkdir('models')

  def __init__(self):
    self.MODELS_DIR = 'models'
    self.MODEL_TF = self.MODELS_DIR + 'model'
    self.MODEL_NO_QUANT_TFLITE = self.MODELS_DIR + '/model_no_quant.tflite'
    self.MODEL_TFLITE = self.MODELS_DIR + '/model.tflite'
    self.MODEL_TFLITE_MICRO = self.MODELS_DIR + '/model.cc'
    self.data_dir = 'data/'

  def load_data(self, img_height, img_width, batch_size):
    """
    Loads data from the directory provided in data_dir
    """

    train_ds = tf.keras.utils.image_dataset_from_directory(
      self.data_dir,
      validation_split=0.2,
      subset="training",
      seed=123,
      image_size=(img_height, img_width),
      batch_size=batch_size,
      color_mode="grayscale",)
    
    val_ds = tf.keras.utils.image_dataset_from_directory(
      self.data_dir,
      validation_split=0.2,
      subset="validation",
      seed=123,
      image_size=(img_height, img_width),
      batch_size=batch_size,
      color_mode="grayscale",)


    return train_ds, val_ds


  def train(self, img_height, img_width, epochs, optim_choice, train_ds, test_ds):
    """Model training 

    Args:
        `img_height` (_int_): image pixel height
        `img_width` (_int_): image pixel width
        `epochs` (_int_): Number of epochs to train
        `optim_choice` (_string_): Loss function to be used

    Returns:
        keras_model, statistics
    """

    class_names = train_ds.class_names
    
    #Enable caching for training
    AUTOTUNE = tf.data.AUTOTUNE
    train = train_ds.cache().prefetch(buffer_size=AUTOTUNE)
    test = test_ds.cache().prefetch(buffer_size=AUTOTUNE)

    num_classes = len(class_names)

    model = Sequential([
      layers.Reshape(target_shape=(img_width, img_height, 1), input_shape=(img_width, img_height)),
      layers.experimental.preprocessing.Rescaling(1./255),
      layers.Conv2D(16, 3, activation='relu', padding='SAME',),
      layers.MaxPooling2D(pool_size=(2, 2)),
      layers.DepthwiseConv2D(8, 3, activation='relu', padding='SAME'),
      layers.MaxPooling2D(pool_size=(2, 2)),
      layers.Flatten(),
      layers.Dense(units=2, activation='softmax'),
    ])

    if optim_choice == "Categorical crossentropy":
      loss_fn = keras.losses.CategoricalCrossentropy(from_logits=True)
    elif optim_choice == "Sparse Categorical crossentropy":
      loss_fn = keras.losses.SparseCategoricalCrossentropy(from_logits=True)


    model.compile(optimizer='adam',
                  loss=loss_fn,
                  metrics=['accuracy'])

    model.summary()

    epochs=epochs

    history = model.fit(
      train,
      validation_data=test,
      epochs=epochs
    )
    
    epochs_range = range(epochs)

    return model, history, epochs_range

  def prediction(self, model, class_names):
    """Predicts on the image provided in the path.

    Args:
        `model` (tflite model): tflite model to be used in the prediction

    Returns:
        img: image predicted, result: formatted string for the result
    """

    path = '/data/1/1.png'
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    img = cv2.resize(img, (96,96))
    img_array = tf.keras.utils.img_to_array(img)
    img_array = tf.expand_dims(img_array, 0) # Create a batch

    predictions = model.predict(img_array)
    score = tf.nn.softmax(predictions[0])

    names = { 1 : "human",
             2: "not human"}
    result = ("This image most likely belongs to {} with a {:.2f} percent confidence.".format(names[np.argmax(score)], 100 * np.max(score)))
    
    return img, result

  def plot_statistics(self, history, epochs_range):
    """Plot model training statistics

    Args:
        `history` (tuple?): tuple containing loss and accuracy values over training
        `epochs_range` (int): amount of epochs used to train over

    Returns:
        BytesIO buffer: Matplotlib figure containing graphs about the training process
    """

    acc = history.history['accuracy']
    val_acc = history.history['val_accuracy']
    loss = history.history['loss']
    val_loss = history.history['val_loss']

    stats = plt.figure(figsize=(8, 8))
    plt.subplot(1, 2, 1)
    plt.plot(epochs_range, acc, label='Training Accuracy')
    plt.plot(epochs_range, val_acc, label='Validation Accuracy')
    plt.legend(loc='lower right')
    plt.title('Training and Validation Accuracy')

    plt.subplot(1, 2, 2)
    plt.plot(epochs_range, loss, label='Training Loss')
    plt.plot(epochs_range, val_loss, label='Validation Loss')
    plt.legend(loc='upper right')
    plt.title('Training and Validation Loss')

    buff = BytesIO()
    stats.savefig(buff, format="png")
    
    return buff

