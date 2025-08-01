"""
Analysis functions for ANTsPyMM
Extracted from mm.py - maintains exact original functionality
"""

import os
import numpy as np
import pandas as pd

try:
    import ants
except ImportError:
    ants = None


# estimate_optimal_pca_components - 36 lines
def estimate_optimal_pca_components(data, variance_threshold=0.80, plot=False):
    """
    Estimate the optimal number of PCA components to represent the given data.

    :param data: The data matrix (samples x features).
    :param variance_threshold: Threshold for cumulative explained variance (default 0.95).
    :param plot: If True, plot the cumulative explained variance graph (default False).
    :return: The optimal number of principal components.
    """
    import numpy as np
    from sklearn.decomposition import PCA
    import matplotlib.pyplot as plt

    # Perform PCA
    pca = PCA()
    pca.fit(data)

    # Calculate cumulative explained variance
    cumulative_variance = np.cumsum(pca.explained_variance_ratio_)

    # Determine the number of components for desired explained variance
    n_components = np.where(cumulative_variance >= variance_threshold)[0][0] + 1

    # Optionally plot the explained variance
    if plot:
        plt.figure(figsize=(8, 4))
        plt.plot(cumulative_variance, linewidth=2)
        plt.axhline(y=variance_threshold, color='r', linestyle='--')
        plt.axvline(x=n_components - 1, color='r', linestyle='--')
        plt.xlabel('Number of Components')
        plt.ylabel('Cumulative Explained Variance')
        plt.title('Explained Variance by Number of Principal Components')
        plt.show()

    return n_components



# calculate_trimmed_mean - 11 lines
def calculate_trimmed_mean(data, proportion_to_trim):
    """
    Calculate the trimmed mean for a given data array.

    :param data: A numpy array of data.
    :param proportion_to_trim: Proportion (0 to 0.5) of data to trim from each end.
    :return: The trimmed mean of the data.
    """
    from scipy import stats
    return stats.trim_mean(data, proportion_to_trim)



# calculate_CBF - 28 lines
def calculate_CBF(Delta_M, M_0, mask,
                  Lambda=0.9, T_1=0.67, Alpha=0.68, w=1.0, Tau=1.5):
    """
    Calculate the Cerebral Blood Flow (CBF) where Delta_M and M_0 are antsImages 
    and the other variables are scalars.  Guesses at default values are used here. 
    We use the pCASL equation.  NOT YET TESTED.

    Parameters:
    Delta_M (antsImage): Change in magnetization (matrix)
    M_0 (antsImage): Initial magnetization (matrix)
    mask ( antsImage ): where to do the calculation
    Lambda (float): Scalar
    T_1 (float): Scalar representing relaxation time
    Alpha (float): Scalar representing flip angle
    w (float): Scalar
    Tau (float): Scalar

    Returns:
    np.ndarray: CBF values (matrix)
    """
    cbf = M_0 * 0.0
    m0thresh = np.quantile( M_0[mask==1], 0.1 )
    sel = mask == 1 and M_0 > m0thresh
    cbf[ sel ] = Delta_M[ sel ] * 60. * 100. * (Lambda * T_1)/( M_0[sel] * 2.0 * Alpha * 
        (np.exp( -w * T_1) - np.exp(-(Tau + w) * T_1)))
    cbf[ cbf < 0.0]=0.0
    return cbf



# calculate_loop_scores_full - 35 lines
def calculate_loop_scores_full(flattened_series, n_neighbors=20, verbose=True ):
    """
    Calculate Local Outlier Probabilities for each volume.
    
    :param flattened_series: A 2D numpy array from flatten_time_series.
    :param n_neighbors: Number of neighbors to use for calculating LOF scores.
    :param verbose: boolean
    :return: An array of LoOP scores.
    """
    from PyNomaly import loop
    from sklearn.neighbors import NearestNeighbors
    from sklearn.preprocessing import StandardScaler
    # replace nans with zero
    if verbose:
        print("loop: nan_to_num")
    flattened_series=np.nan_to_num(flattened_series, nan=0)
    scaler = StandardScaler()
    scaler.fit(flattened_series)
    data = scaler.transform(flattened_series)
    data=np.nan_to_num(data, nan=0)
    if n_neighbors > int(flattened_series.shape[0]/2.0):
        n_neighbors = int(flattened_series.shape[0]/2.0)
    if verbose:
        print("loop: nearest neighbors init")
    neigh = NearestNeighbors(n_neighbors=n_neighbors, metric='minkowski')
    if verbose:
        print("loop: nearest neighbors fit")
    neigh.fit(data)
    d, idx = neigh.kneighbors(data, return_distance=True)
    if verbose:
        print("loop: probability")
    m = loop.LocalOutlierProbability(distance_matrix=d, neighbor_matrix=idx, n_neighbors=n_neighbors).fit()
    return m.local_outlier_probabilities[:]




# novelty_detection_ee - 36 lines
def novelty_detection_ee(df_train, df_test, contamination=0.05):
    """
    This function performs novelty detection using Elliptic Envelope.

    Parameters:

    - df_train (pandas dataframe): training data used to fit the model

    - df_test (pandas dataframe): test data used to predict novelties

    - contamination (float): parameter controlling the proportion of outliers in the data (default: 0.05)

    Returns:

    predictions (pandas series): predicted labels for the test data (1 for novelties, 0 for inliers)
    """
    import pandas as pd
    from sklearn.covariance import EllipticEnvelope
    # Fit the model on the training data
    clf = EllipticEnvelope(contamination=contamination,support_fraction=1)
    df_train[ df_train == math.inf ] = 0
    df_test[ df_test == math.inf ] = 0
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    scaler.fit(df_train)
    clf.fit(scaler.transform(df_train))
    predictions = clf.predict(scaler.transform(df_test))
    predictions[predictions==1]=0
    predictions[predictions==-1]=1
    if str(type(df_train))=="<class 'pandas.core.frame.DataFrame'>":
        return pd.Series(predictions, index=df_test.index)
    else:
        return pd.Series(predictions)





# novelty_detection_svm - 37 lines
def novelty_detection_svm(df_train, df_test, nu=0.05, kernel='rbf'):
    """
    This function performs novelty detection using One-Class SVM.

    Parameters:

    - df_train (pandas dataframe): training data used to fit the model

    - df_test (pandas dataframe): test data used to predict novelties

    - nu (float): parameter controlling the fraction of training errors and the fraction of support vectors (default: 0.05)

    - kernel (str): kernel type used in the SVM algorithm (default: 'rbf')

    Returns:

    predictions (pandas series): predicted labels for the test data (1 for novelties, 0 for inliers)
    """
    from sklearn.svm import OneClassSVM
    # Fit the model on the training data
    df_train[ df_train == math.inf ] = 0
    df_test[ df_test == math.inf ] = 0
    clf = OneClassSVM(nu=nu, kernel=kernel)
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    scaler.fit(df_train)
    clf.fit(scaler.transform(df_train))
    predictions = clf.predict(scaler.transform(df_test))
    predictions[predictions==1]=0
    predictions[predictions==-1]=1
    if str(type(df_train))=="<class 'pandas.core.frame.DataFrame'>":
        return pd.Series(predictions, index=df_test.index)
    else:
        return pd.Series(predictions)





# novelty_detection_lof - 35 lines
def novelty_detection_lof(df_train, df_test, n_neighbors=20):
    """
    This function performs novelty detection using Local Outlier Factor (LOF).

    Parameters:

    - df_train (pandas dataframe): training data used to fit the model

    - df_test (pandas dataframe): test data used to predict novelties

    - n_neighbors (int): number of neighbors used to compute the LOF (default: 20)

    Returns:

    - predictions (pandas series): predicted labels for the test data (1 for novelties, 0 for inliers)

    """
    from sklearn.neighbors import LocalOutlierFactor
    # Fit the model on the training data
    df_train[ df_train == math.inf ] = 0
    df_test[ df_test == math.inf ] = 0
    clf = LocalOutlierFactor(n_neighbors=n_neighbors, algorithm='auto',contamination='auto', novelty=True)
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    scaler.fit(df_train)
    clf.fit(scaler.transform(df_train))
    predictions = clf.predict(scaler.transform(df_test))
    predictions[predictions==1]=0
    predictions[predictions==-1]=1
    if str(type(df_train))=="<class 'pandas.core.frame.DataFrame'>":
        return pd.Series(predictions, index=df_test.index)
    else:
        return pd.Series(predictions)




# novelty_detection_loop - 33 lines
def novelty_detection_loop(df_train, df_test, n_neighbors=20, distance_metric='minkowski'):
    """
    This function performs novelty detection using Local Outlier Factor (LOF).

    Parameters:

    - df_train (pandas dataframe): training data used to fit the model

    - df_test (pandas dataframe): test data used to predict novelties

    - n_neighbors (int): number of neighbors used to compute the LOOP (default: 20)

    - distance_metric : default minkowski

    Returns:

    - predictions (pandas series): predicted labels for the test data (1 for novelties, 0 for inliers)

    """
    from PyNomaly import loop
    from sklearn.neighbors import NearestNeighbors
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    scaler.fit(df_train)
    data = np.vstack( [scaler.transform(df_test),scaler.transform(df_train)])
    neigh = NearestNeighbors(n_neighbors=n_neighbors, metric=distance_metric)
    neigh.fit(data)
    d, idx = neigh.kneighbors(data, return_distance=True)
    m = loop.LocalOutlierProbability(distance_matrix=d, neighbor_matrix=idx, n_neighbors=n_neighbors).fit()
    return m.local_outlier_probabilities[range(df_test.shape[0])]





# novelty_detection_quantile - 27 lines
def novelty_detection_quantile(df_train, df_test):
    """
    This function performs novelty detection using quantiles for each column.

    Parameters:

    - df_train (pandas dataframe): training data used to fit the model

    - df_test (pandas dataframe): test data used to predict novelties

    Returns:

    - quantiles for the test sample at each column where values range in [0,1]
        and higher values mean the column is closer to the edge of the distribution

    """
    myqs = df_test.copy()
    n = df_train.shape[0]
    df_trainkeys = df_train.keys()
    for k in range( df_train.shape[1] ):
        mykey = df_trainkeys[k]
        temp = (myqs[mykey][0] >  df_train[mykey]).sum() / n
        myqs[mykey] = abs( temp - 0.5 ) / 0.5
    return myqs




