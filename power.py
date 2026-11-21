#!/usr/bin/env python3
"""Размер выборки и MDE для сравнения двух долей с поправкой на кластеры (группы)."""
import argparse
from math import ceil, sqrt
from statistics import NormalDist
Z = NormalDist().inv_cdf


def deff(m, icc): return 1 + (m - 1) * icc


def n_per_arm(p0, p1, alpha=.05, power=.8, d=1.0):
    pb = (p0 + p1) / 2
    n = (Z(1 - alpha / 2) * sqrt(2 * pb * (1 - pb)) + Z(power) * sqrt(p0 * (1 - p0) + p1 * (1 - p1))) ** 2 / (p0 - p1) ** 2
    return ceil(n * d)


def mde(p0, n, alpha=.05, power=.8, d=1.0):
    lo, hi = 1e-6, p0 - 1e-6
    for _ in range(60):
        mid = (lo + hi) / 2
        if n_per_arm(p0, p0 - mid, alpha, power, d) <= n: hi = mid
        else: lo = mid
    return hi


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--p0", type=float, required=True)
    ap.add_argument("--p1", type=float); ap.add_argument("--n", type=int, help="наблюдений на группу сравнения → MDE")
    ap.add_argument("--m", type=float, default=1.0, help="среднее число наблюдений в кластере")
    ap.add_argument("--icc", type=float, default=0.0); ap.add_argument("--alpha", type=float, default=.05)
    ap.add_argument("--power", type=float, default=.8); a = ap.parse_args()
    d = deff(a.m, a.icc)
    if a.p1 is not None: print(f"design effect={d:.3f}; нужно на группу: {n_per_arm(a.p0, a.p1, a.alpha, a.power, d)}")
    if a.n: x = mde(a.p0, a.n, a.alpha, a.power, d); print(f"MDE при n={a.n}: {x*100:.2f} п.п. (p1≈{(a.p0-x)*100:.1f}%)")
