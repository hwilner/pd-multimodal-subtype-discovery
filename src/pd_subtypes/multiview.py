"""Multi-view clustering comparator.

Computes a per-view embedding (PCA) and clustering per modality, then
combines them via consensus (co-association) clustering to obtain a
multimodal solution. Used as a comparator to SuStaIn subtyping.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score


def per_view_embeddings(
    views: dict[str, pd.DataFrame], n_components: int = 2
) -> dict[str, np.ndarray]:
    """PCA embedding per view (modality)."""
    return {
        name: PCA(
            n_components=min(n_components, X.shape[1]), random_state=0
        ).fit_transform(X)
        for name, X in views.items()
    }


def per_view_clustering(
    views: dict[str, pd.DataFrame], n_clusters: int, n_components: int = 2
) -> dict[str, np.ndarray]:
    """KMeans clustering of each view's PCA embedding."""
    emb = per_view_embeddings(views, n_components)
    return {
        name: KMeans(n_clusters=n_clusters, n_init=10, random_state=0).fit_predict(E)
        for name, E in emb.items()
    }


def consensus_clustering(
    views: dict[str, pd.DataFrame], n_clusters: int, n_components: int = 2
) -> np.ndarray:
    """Consensus (co-association) clustering across views.

    Builds the average co-association matrix over per-view clusterings
    and applies agglomerative clustering to the consensus distance.
    """
    labels = per_view_clustering(views, n_clusters, n_components)
    subjects = next(iter(views.values())).index
    n = len(subjects)
    coassoc = np.zeros((n, n))
    for lab in labels.values():
        coassoc += (lab[:, None] == lab[None, :]).astype(float)
    coassoc /= len(labels)
    distance = 1.0 - coassoc
    return AgglomerativeClustering(
        n_clusters=n_clusters, metric="precomputed", linkage="average"
    ).fit_predict(distance)


def multiview_agreement(labels_a: np.ndarray, labels_b: np.ndarray) -> float:
    """Adjusted Rand index between two labelings (e.g. SuStaIn vs consensus)."""
    return float(adjusted_rand_score(labels_a, labels_b))
