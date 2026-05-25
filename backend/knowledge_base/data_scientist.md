# Data Science & Applied Machine Learning Knowledge Base

## Chapter 1: Exploratory Data Analysis & Statistics
- **Exploratory Data Analysis (EDA)**: The process of summarizing, visualizing, and understanding the main characteristics of a dataset before formal modeling.
  - Key techniques: correlation matrices, histograms, scatter plots, box plots (outlier detection via Interquartile Range: $IQR = Q3 - Q1$; outliers are defined as values outside $[Q1 - 1.5 \times IQR, Q3 + 1.5 \times IQR]$).
- **Statistical Hypothesis Testing**:
  - **Null Hypothesis ($H_0$)**: A statement of no effect or no difference.
  - **Alternative Hypothesis ($H_a$)**: The statement we hope to support.
  - **p-value**: The probability of observing results at least as extreme as those measured, assuming $H_0$ is true. If $p < \alpha$ (usually 0.05), we reject the null hypothesis.
  - **Type I Error ($\alpha$)**: Rejecting the null hypothesis when it is true (False Positive).
  - **Type II Error ($\beta$)**: Failing to reject the null hypothesis when it is false (False Negative).
  - **Statistical Power**: $1 - \beta$, the probability of correctly rejecting a false null hypothesis.
- **Central Limit Theorem (CLT)**: The distribution of the sum (or average) of a large number of independent, identically distributed variables will be approximately normal, regardless of the underlying distribution.

## Chapter 2: Feature Engineering & Data Preprocessing
- **Feature Selection**: Identifying the most relevant features to avoid the Curse of Dimensionality.
  - **Filter methods**: ANOVA, Chi-Square, Pearson Correlation.
  - **Wrapper methods**: Forward selection, backward elimination, recursive feature elimination.
  - **Embedded methods**: Lasso regression (L1 regularization forces some coefficients to absolute zero, acting as feature selection).
- **Data Preprocessing**:
  - **Standardization**: Scaling data to have a mean of 0 and a standard deviation of 1. $x_{std} = \frac{x - \mu}{\sigma}$. Important for models sensitive to scale like SVM, KNN, Neural Networks.
  - **Normalization (Min-Max Scaling)**: Scaling data to a range (usually $[0, 1]$). $x_{norm} = \frac{x - x_{min}}{x_{max} - x_{min}}$.
  - **Imputation**: Handling missing data using mean, median, mode, or predictive models like KNN-Imputer.
  - **Categorical Encoding**: One-Hot Encoding (for nominal values, watch out for the dummy variable trap) and Ordinal/Label Encoding (for ordered categories).

## Chapter 3: Classical ML & Ensemble Methods
- **Supervised Algorithms**:
  - **Linear & Logistic Regression**: Linear combination of inputs mapped to continuous outputs or probability outputs (via sigmoid).
  - **Decision Trees**: Hierarchical split nodes based on Gini impurity or Entropy. prone to overfitting.
- **Ensemble Methods**: Combining multiple base estimators to improve generalization and stability.
  - **Bagging (Bootstrap Aggregating)**: Fits independent base learners in parallel on bootstrap samples of the training set. Reduces variance.
    - **Random Forest**: An ensemble of decision trees where each tree is trained on a bootstrap sample of data, and node splits are chosen from a random subset of features.
  - **Boosting**: Fits base learners sequentially, where each new learner corrects the errors made by previous ones. Reduces bias.
    - **AdaBoost**: Adjusts instance weights, focusing more on misclassified points.
    - **Gradient Boosting (GBM, XGBoost, LightGBM)**: Fits trees to the negative gradient of the loss function (pseudo-residuals). Extremely powerful for structured tabular data.

## Chapter 4: Model Evaluation and Metrics
- **Classification Metrics**:
  - **Confusion Matrix**: Contains True Positives (TP), False Positives (FP), True Negatives (TN), False Negatives (FN).
  - **Accuracy**: $\frac{TP + TN}{TP + TN + FP + FN}$. Misleading for highly imbalanced datasets.
  - **Precision**: $\frac{TP}{TP + FP}$. Out of all predicted positives, how many were actually positive? Focus on reducing False Positives.
  - **Recall (Sensitivity)**: $\frac{TP}{TP + FN}$. Out of all actual positives, how many did we predict positive? Focus on reducing False Negatives.
  - **F1-Score**: Harmonic mean of Precision and Recall. $F_1 = 2 \times \frac{Precision \times Recall}{Precision + Recall}$.
  - **ROC-AUC**: Receiver Operating Characteristic Curve plots True Positive Rate vs False Positive Rate at various thresholds. AUC (Area Under Curve) represents the model's ability to distinguish between classes.
- **Regression Metrics**:
  - **Mean Absolute Error (MAE)**: Mean of absolute errors. Robust to outliers.
  - **Mean Squared Error (MSE)**: Mean of squared errors. Penalizes larger errors heavily.
  - **Root Mean Squared Error (RMSE)**: Square root of MSE. Keeps metrics in target variable units.
  - **R-squared ($R^2$)**: Coefficient of determination. The proportion of variance in the dependent variable predictable from the independent variables.
- **Cross-Validation**: K-Fold, Stratified K-Fold (for imbalanced classes), Time-Series Split. Helps estimate generalization error.
