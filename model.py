# -*- coding: utf-8 -*-
"""Loads images from the FER2013 dataset as numpy arrays and trains it using a 
residual neural network.

The architecture is the mini-Xception model from Octavio Arriaga et al. 
https://github.com/oarriaga/face_classification
"""
from pathlib import Path

from keras.callbacks import CSVLogger, ModelCheckpoint, EarlyStopping
from keras.callbacks import ReduceLROnPlateau
from keras.preprocessing.image import ImageDataGenerator
from keras.layers import Activation, Conv2D
from keras.layers import BatchNormalization
from keras.layers import GlobalAveragePooling2D
from keras.layers import MaxPooling2D, Input
from keras.layers import SeparableConv2D
from keras.models import Model
from keras import layers
from keras.regularizers import l2
import numpy as np

import utils

# Parameters
batch_size = 32
num_epochs = 250
num_classes = 7
wait_time = 50
input_shape = (48, 48, 1)
regularization = l2(0.01)
data_folder = Path('data/fer2013.csv')

# Fine tuning Model, only do with already trained models
fine_tune = True

# Loads saved numpy arrays if available. Otherwise creates it with load_data. 
try:
    X_train = np.load(Path('data/X_train.npy'))
    Y_train = np.load(Path('data/Y_train.npy'))
    X_val = np.load(Path('data/X_val.npy'))
    Y_val = np.load(Path('data/Y_val.npy'))
    X_test = np.load(Path('data/X_test.npy'))
    Y_test = np.load(Path('data/Y_test.npy'))    
    print('NUMPY DATA LOADED.')   
except:  
    print('PREPARING DATA.')
    emotions = ['Angry', 'Disgust', 'Fear', 'Happy',
                'Sad', 'Surprise', 'Neutral']
    
    X_train, Y_train = utils.load_data(emotions,
                                       data_folder,
                                       usage='Training')
    X_val, Y_val     = utils.load_data(emotions,
                                       data_folder,
                                       usage='PublicTest')
    X_test, Y_test   = utils.load_data(emotions,
                                           data_folder,
                                       usage='PrivateTest')
    
    utils.save_data(X_train, Y_train, 'train')
    utils.save_data(X_val, Y_val, 'val')
    utils.save_data(X_test, Y_test, 'test')
    print('NUMPY DATA SAVED..')

# Preprocessing the data
datagen = ImageDataGenerator(featurewise_center=False,
                             featurewise_std_normalization=False,
                             rotation_range=10,
                             width_shift_range=0.1,
                             height_shift_range=0.1,
                             zoom_range=.1,
                             horizontal_flip=True)
    
# Mini-Xception architecture
input_shape = (48, 48, 1)
img_input = Input(input_shape)
x = Conv2D(8, (3, 3), strides=(1, 1),
           kernel_regularizer=regularization,
           use_bias=False)(img_input)   
x = BatchNormalization()(x)
x = Activation('relu')(x)
x = Conv2D(8, (3, 3), strides=(1, 1), 
           kernel_regularizer=regularization,
           use_bias=False)(x)
x = BatchNormalization()(x)
x = Activation('relu')(x)

# Module 1
residual = Conv2D(16, (1, 1), strides=(2, 2),
                  padding='same', use_bias=False)(x)
residual = BatchNormalization()(residual)
x = SeparableConv2D(16, (3, 3), padding='same',
                    kernel_regularizer=regularization,
                    use_bias=False)(x)
x = BatchNormalization()(x)
x = Activation('relu')(x)
x = SeparableConv2D(16, (3, 3), padding='same',
                    kernel_regularizer=regularization,
                    use_bias=False)(x)
x = BatchNormalization()(x)
x = MaxPooling2D((3, 3), strides=(2, 2), padding='same')(x)
x = layers.add([x, residual])

# Module 2
residual = Conv2D(32, (1, 1), strides=(2, 2),
                  padding='same', use_bias=False)(x)
residual = BatchNormalization()(residual)
x = SeparableConv2D(32, (3, 3), padding='same',
                    kernel_regularizer=regularization,
                    use_bias=False)(x)
x = BatchNormalization()(x)
x = Activation('relu')(x)
x = SeparableConv2D(32, (3, 3), padding='same',
                    kernel_regularizer=regularization,
                    use_bias=False)(x)
x = BatchNormalization()(x)
x = MaxPooling2D((3, 3), strides=(2, 2), padding='same')(x)
x = layers.add([x, residual])

# Module 3
residual = Conv2D(64, (1, 1), strides=(2, 2),
                      padding='same', use_bias=False)(x)
residual = BatchNormalization()(residual)
x = SeparableConv2D(64, (3, 3), padding='same',
                        kernel_regularizer=regularization,
                        use_bias=False)(x)
x = BatchNormalization()(x)
x = Activation('relu')(x)
x = SeparableConv2D(64, (3, 3), padding='same',
                        kernel_regularizer=regularization,
                        use_bias=False)(x)
x = BatchNormalization()(x)
x = MaxPooling2D((3, 3), strides=(2, 2), padding='same')(x)
x = layers.add([x, residual])

# Module 4
residual = Conv2D(128, (1, 1), strides=(2, 2),
                      padding='same', use_bias=False)(x)
residual = BatchNormalization()(residual)
x = SeparableConv2D(128, (3, 3), padding='same',
                        kernel_regularizer=regularization,
                        use_bias=False)(x)
x = BatchNormalization()(x)
x = Activation('relu')(x)
x = SeparableConv2D(128, (3, 3), padding='same',
                        kernel_regularizer=regularization,
                        use_bias=False)(x)
x = BatchNormalization()(x)
x = MaxPooling2D((3, 3), strides=(2, 2), padding='same')(x)
x = layers.add([x, residual])

x = Conv2D(num_classes, (3, 3), padding='same')(x)
x = GlobalAveragePooling2D()(x)
output = Activation('softmax', name='predictions')(x)

model = Model(img_input, output)

# Prevents the first couple layers from being trained
if fine_tune:
    for layer in model.layers[:10]:
        layer.trainable = False
        
# Loading saved models, if any
try:
    model.load_weights(Path('models/model.best.hdf5'))
    print('LOADING SAVED MODEL...')
except:
    print('NO SAVED MODEL DETECTED...')

# Optimizers    
model.compile(optimizer='adam', 
              loss='categorical_crossentropy', 
              metrics=['accuracy'])

# Callbacks
log_path = Path('logs/model_log.log')
reduce_lr = ReduceLROnPlateau('val_loss', factor=0.1, 
                              wait_time=int(wait_time/4), verbose=1)
model_names = 'model.best.hdf5'
model_path = str(Path('models/' + model_names))
checkpoint = ModelCheckpoint(model_path, 'val_loss', save_best_only=True)
callback_list = [checkpoint, 
                 CSVLogger(log_path, append=False),
                 EarlyStopping('val_loss', patience=wait_time),
                 reduce_lr]

# Start the training
print('TRAINING THE MODEL....')
model.fit_generator(datagen.flow(X_train, Y_train, batch_size),
                    steps_per_epoch=len(X_train) / batch_size,
                    epochs=num_epochs, 
                    verbose=1,
                    validation_data=(X_val, Y_val), 
                    callbacks=callback_list,
                    validation_steps=len(X_val) / batch_size)