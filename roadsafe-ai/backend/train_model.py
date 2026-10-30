"""Trains a Random Forest on SYNTHETIC data (demo only). Replace with real, consented, anonymised data."""
import numpy as np, joblib
from sklearn.ensemble import RandomForestClassifier
rng = np.random.default_rng(42)
n = 3000
over = rng.uniform(0, 60, n); brakes = rng.integers(0, 10, n); night = rng.integers(0, 2, n)
score = over * 1.2 + brakes * 5 + night * 10
y = np.digitize(score, [30, 60])  # 0 low, 1 moderate, 2 high
X = np.column_stack([over, brakes, night])
m = RandomForestClassifier(n_estimators=100, random_state=42).fit(X, y)
joblib.dump(m, "model.pkl"); print("Saved model.pkl, accuracy:", m.score(X, y))
