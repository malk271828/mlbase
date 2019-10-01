import os
import sys
import warnings
sys.path.insert(0, os.getcwd())
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

# Machine Learning Libraries
from sklearn.datasets import *
from sklearn.metrics import classification_report
from sklearn.preprocessing import MinMaxScaler
from keras.optimizers import Adam

from vae import *

def test_1d_binary():
    """binary classification test
    Reference:
        https://www.programcreek.com/python/example/104690/sklearn.datasets.load_breast_cancer
    """
    X, y = load_breast_cancer(return_X_y=True)
    assert len(X) == len(y)
    input_shape = X[0].shape
    print("\n--------------------------------------")
    print("%d samples" % len(X))
    print("input_shape:", input_shape)
    print("--------------------------------------")
    scaler = MinMaxScaler()
    scaler.fit(X)
    enable_graph = False

    vae, encoder, decoder = build_vae(input_shape, enable_mse=False,
                                        enable_graph=enable_graph)
    vae.compile(optimizer=Adam(0.0002, 0.5))
    vae.fit(scaler.transform(X), batch_size=128, epochs=100)
    reconstruct_X = vae.predict(X)

    #print(classification_report(y, predicted_y))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    help_ = "Load h5 model trained weights"
    parser.add_argument("-w", "--weights", help=help_)
    help_ = "Use mse loss instead of binary cross entropy (default)"
    parser.add_argument("-m",
                        "--mse",
                        help=help_, action='store_true')
    args = parser.parse_args()

    # MNIST dataset
    (x_train, y_train), (x_test, y_test) = mnist.load_data()
    data = (x_test, y_test)

    image_size = x_train.shape[1]
    original_dim = image_size * image_size
    x_train = np.reshape(x_train, [-1, original_dim])
    x_test = np.reshape(x_test, [-1, original_dim])
    x_train = x_train.astype('float32') / 255
    x_test = x_test.astype('float32') / 255

    # network parameters
    input_shape = (original_dim, )
    batch_size = 128
    epochs = 50
    enable_graph = False

    vae, encoder, decoder = build_vae(input_shape, enable_mse=args.mse,
                                        enable_graph=enable_graph)
    models = (encoder, decoder)

    vae.compile(optimizer='adam')
    vae.summary()
    if enable_graph:
        plot_model(vae, to_file='vae_mlp.png', show_shapes=True)

    if args.weights:
        vae.load_weights(args.weights)
    else:
        # train the autoencoder
        vae.fit(x_train,
                epochs=epochs,
                batch_size=batch_size,
                validation_data=(x_test, None))
        vae.save_weights('vae_mlp_mnist.h5')

    plot_results(models,
                 data,
                 batch_size=batch_size,
                 model_name="vae_mlp")
