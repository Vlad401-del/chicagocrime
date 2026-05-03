# scripts/train_rf.py
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve
import matplotlib.pyplot as plt

# Load preprocessed train/test data (from preprocess_ml)
data = np.load("data/cleaned/train_data.npz")
X_train = data["X"]
y_train = data["y"]
data = np.load("data/cleaned/test_data.npz")
X_test = data["X"]
y_test = data["y"]
print("Loaded training and test data.")

# Initialize Random Forest with balanced class weights
rf = RandomForestClassifier(
    n_estimators=100,       # number of trees (increase for more accuracy)
    max_depth=None,         # allow full depth (can set to e.g. 10 to reduce overfitting)
    random_state=42,
    class_weight='balanced',
    n_jobs=-1
)
# Train the model
print("Training Random Forest...")
rf.fit(X_train, y_train)
print("Training complete.")

# Save the trained model
joblib.dump(rf, "models/rf_model.pkl")
print("Model saved to 'models/rf_model.pkl' (approx. size will be a few MB).")

# Evaluate on test set
y_pred = rf.predict(X_test)
y_proba = rf.predict_proba(X_test)[:,1]  # probability of arrest (class=1)

# Classification report
report = classification_report(y_test, y_pred, digits=4)
print("Classification Report:\n", report)
with open("models/classification_report.txt", "w") as f:
    f.write(report)

# Confusion matrix
cm = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(5,4))
plt.imshow(cm, cmap=plt.cm.Blues)
plt.title("Confusion Matrix")
plt.colorbar()
plt.xticks([0,1], ["No Arrest (0)", "Arrest (1)"])
plt.yticks([0,1], ["No Arrest (0)", "Arrest (1)"])
for (i, j), val in np.ndenumerate(cm):
    plt.text(j, i, f"{val}", ha="center", va="center", color="white" if val>cm.max()/2 else "black")
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.tight_layout()
plt.savefig("models/confusion_matrix.png")
print("Confusion matrix saved as 'models/confusion_matrix.png'.")

# ROC curve
auc = roc_auc_score(y_test, y_proba)
fpr, tpr, thresholds = roc_curve(y_test, y_proba)
plt.figure(figsize=(5,4))
plt.plot(fpr, tpr, label=f"AUC = {auc:.4f}")
plt.plot([0,1], [0,1], 'k--')
plt.title("ROC Curve")
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.legend(loc="lower right")
plt.tight_layout()
plt.savefig("models/roc_curve.png")
print(f"ROC curve (AUC={auc:.4f}) saved as 'models/roc_curve.png'.")

print("Training and evaluation complete.")
