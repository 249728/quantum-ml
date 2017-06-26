import numpy as np
import tensorflow as tf

from tensorflow.contrib import learn
from tensorflow.contrib.learn.python.learn.estimators import model_fn as model_fn_lib

tf.logging.set_verbosity(tf.logging.INFO)

# application logic will be added here
def cnn_model_fn(features,labels,mode):
    '''Model function for CNN'''
    #input layer
    # Why is there a 1 in the last dimension?
    input_layer = tf.reshape(features,[-1,28,28,1])
    
    # Concolutional layer1
    conv1 = tf.layers.conv2d(
        inputs=input_layer,
        filters=32,
        kernel_size=[5,5],
        padding="same",
        activation=tf.nn.relu)

    # Pooling layer1
    pool1 = tf.layers.max_pooling2d(inputs=conv1,pool_size=[2,2],strides=2)

    # Convolutional layer #2 and Pooling layer #2
    conv2 = tf.layers.conv2d(
        inputs=pool1,
        filters=64,
        kernel_size=[5,5],
        padding="same",
        activation=tf.nn.relu)
    pool2 = tf.layers.max_pooling2d(inputs=conv2,pool_size=[2,2],strides=2)

    # Dense layer
    pool2_flat = tf.reshape(pool2,[-1,7*7*64])
    dense = tf.layers.dense(inputs=pool2_flat,units=1024,activation=tf.nn.relu)
    dropout = tf.layers.dropout(inputs=dense,rate=0.4,training=mode == learn.ModeKeys.TRAIN)

    # Logits layer
    logits = tf.layers.dense(inputs=dropout,units=10)

    loss = None
    train_op = None

    # Calculate loss( for both TRAIN AND EVAL modes)
    if mode != learn.ModeKeys.INFER:
        onehot_labels = tf.one_hot(indices=tf.cast(labels,tf.int32),depth=10)
        loss = tf.losses.softmax_cross_entropy(onehot_labels=onehot_labels, logits=logits)

    # Configure the training op (for TRAIN mode)
    if mode == learn.ModeKeys.TRAIN:
        train_op = tf.contrib.layers.optimize_loss(
            loss=loss,
            global_step=tf.contrib.framework.get_global_step(),
            learning_rate=0.001,
            optimizer="SGD")

    # Generate predictions
    predictions= {
        "classes" : tf.argmax(
            input=logits, axis=1),
        "probabilities" : tf.nn.softmax(
            logits, name="softmax_tensor")
    }

    # Returna  ModelFnOps object
    return model_fn_lib.ModelFnOps(mode=mode,predictions=predictions,loss=loss, train_op=train_op)
    
def main(unused_argv):
    # Load training and eval data
    mnist = learn.datasets.load_dataset("mnist")
    train_data = mnist.train.images # return a np array
    train_labels = np.asarray(mnist.train.labels,dtype=np.int32)
    eval_data = mnist.test.images 
    eval_labels = np.asarray(mnist.test.labels,dtype=np.int32)

    # create the estimator
    mnist_classifier = learn.Estimator(model_fn=cnn_model_fn,model_dir="/tmp/mnist_convnet_model")
    
    # set up logging for predictions
    #tensors_to_log = {"probabilities" : "softmax_tensor"}
    tensors_to_log = {}
    logging_hook = tf.train.LoggingTensorHook(tensors=tensors_to_log, every_n_iter=100)
    
    mnist_classifier.fit(
        x=train_data,
        y=train_labels,
        batch_size=100,
        steps=100,
        monitors=[logging_hook])

    metrics = {
        "accuracy" : learn.MetricSpec(metric_fn=tf.metrics.accuracy, prediction_key="classes"),
    }

    eval_results=mnist_classifier.evaluate(x=eval_data,y=eval_labels,metrics=metrics)
    print(eval_results)

if __name__ == "__main__":
    tf.app.run()
