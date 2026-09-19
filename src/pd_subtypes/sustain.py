"""Compact SuStaIn-style subtype-and-stage inference.

Implements a simplified event-sequence mixture model (SuStaIn; Young et
al., 2014): each subtype is characterized by an ordering in which
biomarkers "become abnormal" (z-score crossing a threshold), and each
subject belongs to a subtype at a particular stage along that sequence.
Parameters are estimated with EM. Simplified but functional on small
synthetic data.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm


class SuStaInModel:
    """Simplified SuStaIn subtype-and-stage inference via EM.

    Parameters
    ----------
    n_subtypes:
        Number of disease subtypes to infer.
    z_threshold:
        Z-score threshold above which a biomarker is considered abnormal
        (an "event").
    n_stages:
        Number of disease stages per sequence. Defaults to the number of
        biomarkers (one event per stage).
    n_init:
        Number of random restarts; the run with the best log-likelihood
        is kept.
    max_iter:
        Maximum EM iterations per restart.
    tol:
        Convergence tolerance on the log-likelihood.
    random_state:
        Seed for reproducibility.
    """

    def __init__(
        self,
        n_subtypes: int = 2,
        z_threshold: float = 1.0,
        n_stages: int | None = None,
        n_init: int = 4,
        max_iter: int = 100,
        tol: float = 1e-4,
        random_state: int = 0,
    ) -> None:
        self.n_subtypes = n_subtypes
        self.z_threshold = z_threshold
        self.n_stages = n_stages
        self.n_init = n_init
        self.max_iter = max_iter
        self.tol = tol
        self.random_state = random_state

    # -- core EM ---------------------------------------------------------

    def fit(self, features: pd.DataFrame) -> "SuStaInModel":
        """Fit the event-sequence mixture model.

        Parameters
        ----------
        features:
            Z-scored feature matrix (subjects x biomarkers); larger values
            indicate greater abnormality.

        Returns
        -------
        SuStaInModel
            Fitted model with ``sequences_``, ``subtype_proba_``,
            ``stages_`` and ``log_likelihood_``.
        """
        X = features.to_numpy(dtype=float)
        n, n_bio = X.shape
        n_stages = self.n_stages or n_bio
        rng = np.random.default_rng(self.random_state)

        best = None
        for _ in range(self.n_init):
            result = self._em_single(X, n_stages, rng)
            if best is None or result["loglik"] > best["loglik"]:
                best = result

        self.sequences_ = best["sequences"]  # (n_subtypes, n_bio) event orders
        self.subtype_proba_ = best["resp"]  # (n, n_subtypes)
        self.subtype_labels_ = best["resp"].argmax(axis=1)
        self.stages_ = best["stages"]  # (n,)
        self.log_likelihood_ = best["loglik"]
        self.n_biomarkers_ = n_bio
        self.n_stages_ = n_stages
        return self

    def _em_single(self, X: np.ndarray, n_stages: int, rng) -> dict:
        n, n_bio = X.shape
        # Random init: random sequence per subtype.
        sequences = np.stack([rng.permutation(n_bio) for _ in range(self.n_subtypes)])
        prev_ll = -np.inf
        for _ in range(self.max_iter):
            # E-step: responsibilities over subtypes, marginalizing stages.
            resp, _, ll = self._e_step(X, sequences, n_stages)
            # M-step: greedy sequence refinement per subtype.
            sequences = self._m_step(X, resp)
            if abs(ll - prev_ll) < self.tol:
                break
            prev_ll = ll

        resp, stage_post, ll = self._e_step(X, sequences, n_stages)
        labels = resp.argmax(axis=1)
        final_stages = stage_post[np.arange(n), labels].argmax(axis=1)
        return {
            "sequences": sequences,
            "resp": resp,
            "stages": final_stages,
            "loglik": ll,
        }

    def _event_pattern(self, seq: np.ndarray, n_stages: int) -> np.ndarray:
        """(n_stages+1, n_bio) boolean: biomarker j abnormal at stage k."""
        pos = np.empty_like(seq)
        pos[seq] = np.arange(len(seq))
        ks = np.arange(n_stages + 1)[:, None]
        # scale positions into [0, n_stages]
        scaled_pos = pos / max(1, len(seq) - 1) * (n_stages - 1)
        return ks > scaled_pos

    def _e_step(self, X, sequences, n_stages):
        n, n_bio = X.shape
        S = self.n_subtypes
        # Per subject, log P(x | subtype, stage): Gaussian around the
        # expected "abnormal" mean under the event pattern. Simplified:
        # abnormal biomarkers should exceed the threshold; normal ones not.
        mu_hi, mu_lo = self.z_threshold, 0.0
        sd = 1.0
        log_stage = np.zeros((n, S, n_stages + 1))
        for s in range(S):
            pat = self._event_pattern(sequences[s], n_stages)  # (K+1, n_bio)
            for k in range(n_stages + 1):
                mu = np.where(pat[k], mu_hi, mu_lo)
                ll = norm.logpdf(X, loc=mu, scale=sd).sum(axis=1)
                log_stage[:, s, k] = ll + np.log(1.0 / S) + np.log(1.0 / (n_stages + 1))
        # log P(x | s) = logsumexp over stages
        from scipy.special import logsumexp

        lse = logsumexp(log_stage, axis=2)  # (n, S)
        log_resp = lse - logsumexp(lse, axis=1, keepdims=True)
        stage_post = np.exp(log_stage - log_stage.max(axis=2, keepdims=True))
        stage_post /= stage_post.sum(axis=2, keepdims=True)
        ll_total = float(logsumexp(lse, axis=1).sum())
        return np.exp(log_resp), stage_post, ll_total

    def _m_step(self, X, resp):
        """Greedy sequence update: order biomarkers by weighted mean abnormality."""
        n, n_bio = X.shape
        S = self.n_subtypes
        seqs = np.zeros((S, n_bio), dtype=int)
        for s in range(S):
            w = resp[:, s]
            if w.sum() < 1e-8:
                seqs[s] = np.arange(n_bio)
                continue
            # Weighted mean per biomarker; biomarkers abnormal earliest get
            # ranked first (use weighted mean z as proxy ordering).
            wm = (w[:, None] * X).sum(axis=0) / w.sum()
            seqs[s] = np.argsort(-wm)  # most abnormal first in sequence
        return seqs

    # -- helpers ---------------------------------------------------------

    def predict_subtype(self, features: pd.DataFrame) -> np.ndarray:
        """Assign new subjects to subtypes (and stages) using fitted sequences."""
        X = features.to_numpy(dtype=float)
        resp, stage_post, _ = self._e_step(X, self.sequences_, self.n_stages_)
        return resp.argmax(axis=1)

    def predict_stage(self, features: pd.DataFrame) -> np.ndarray:
        X = features.to_numpy(dtype=float)
        resp, stage_post, _ = self._e_step(X, self.sequences_, self.n_stages_)
        labels = resp.argmax(axis=1)
        return stage_post[np.arange(X.shape[0]), labels].argmax(axis=1)
