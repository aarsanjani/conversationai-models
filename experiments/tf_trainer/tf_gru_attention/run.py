"""Experiments with Toxicity Dataset"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import nltk
import tensorflow as tf

from tf_trainer.common import base_model
from tf_trainer.common import model_trainer
from tf_trainer.common import serving_input
from tf_trainer.common import text_preprocessor
from tf_trainer.common import tfrecord_input
from tf_trainer.common import types
from tf_trainer.tf_gru_attention import model as tf_gru_attention



FLAGS = tf.app.flags.FLAGS

tf.app.flags.DEFINE_string("embeddings_path",
                           "local_data/glove.6B/glove.6B.100d.txt",
                           "Path to the embeddings file.")
tf.app.flags.DEFINE_integer("batch_size", 32,
                            "The batch size to use during training.")
tf.app.flags.DEFINE_integer("train_steps", 100000,
                            "The number of steps to train for.")
tf.app.flags.DEFINE_integer("eval_period", 800,
                            "The number of steps per eval period.")
tf.app.flags.DEFINE_integer("eval_steps", 50,
                            "The number of steps to eval for.")


def main(argv):
  del argv  # unused

  embeddings_path = FLAGS.embeddings_path

  preprocessor = text_preprocessor.TextPreprocessor(embeddings_path)

  nltk.download("punkt")
  train_preprocess_fn = preprocessor.train_preprocess_fn(nltk.word_tokenize)
  dataset = tfrecord_input.TFRecordInputWithTokenizer(
      train_preprocess_fn=train_preprocess_fn,
      batch_size=FLAGS.batch_size)

  # TODO: Move embedding *into* Keras model.
  model_tf = tf_gru_attention.TFRNNModel(dataset.labels())
  model = preprocessor.add_embedding_to_model(
      model_tf, base_model.TOKENS_FEATURE_KEY)

  trainer = model_trainer.ModelTrainer(dataset, model)
  trainer.train_with_eval(FLAGS.train_steps, FLAGS.eval_period, FLAGS.eval_steps)

  serving_input_fn = serving_input.create_serving_input_fn(
      word_to_idx=preprocessor._word_to_idx,
      unknown_token=preprocessor._unknown_token,
      text_feature_name=base_model.TOKENS_FEATURE_KEY)
  trainer.export(serving_input_fn)


if __name__ == "__main__":
  tf.logging.set_verbosity(tf.logging.INFO)
  tf.app.run(main)
