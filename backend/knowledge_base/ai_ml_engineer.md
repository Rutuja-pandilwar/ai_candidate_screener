# AI & Machine Learning Engineering Knowledge Base

## Chapter 1: Introduction to Machine Learning (Tom Mitchell)
Machine Learning is defined as: A computer program is said to learn from experience E with respect to some class of tasks T and performance measure P, if its performance at tasks in T, as measured by P, improves with experience E.
- **Concept Learning**: Acquiring the definition of a general category given a sample of positive and negative training examples. It search through a predefined space of hypotheses to find the hypothesis that best fits the training examples.
- **Decision Trees**: A method for approximating discrete-valued target functions. They classify instances by sorting them down the tree from the root to some leaf node, which provides the classification.
  - **ID3 Algorithm**: Uses Entropy and Information Gain to select the attribute that best splits the data.
  - **Entropy**: Measures the impurity of a sample S. $Entropy(S) = -p_+ \log_2 p_+ - p_- \log_2 p_-$.
  - **Information Gain**: The expected reduction in entropy caused by partitioning the examples according to an attribute.
- **Overfitting**: A hypothesis $h$ is said to overfit the training data if there exists some alternative hypothesis $h'$ such that $h$ has a smaller error than $h'$ over the training examples, but $h'$ has a smaller error than $h$ over the entire distribution of instances.
  - **Mitigation**: Pruning (reduced error pruning, rule post-pruning), early stopping, and regularisation.

## Chapter 2: The Hundred-Page Machine Learning Book (Andriy Burkov)
- **Supervised Learning**: The algorithm is given training data that includes the correct labels.
  - **Support Vector Machines (SVM)**: Finds the hyperplane that maximizes the margin between two classes. The margin is the distance between the hyperplane and the closest training points (support vectors). Uses kernel trick for non-linear decision boundaries (RBF, Polynomial, Sigmoid).
  - **Logistic Regression**: Standard linear model for binary classification that outputs probabilities using the sigmoid function: $\sigma(z) = 1 / (1 + e^{-z})$.
  - **Linear Regression**: Predicts a continuous value $y = w \cdot x + b$ by minimizing the Mean Squared Error (MSE).
- **Unsupervised Learning**: Finding hidden patterns in unlabeled data.
  - **K-Means Clustering**: Partitions data into $k$ clusters. Iteratively assigns data points to the nearest centroid, then updates centroids to be the mean of the points in the cluster.
  - **Dimensionality Reduction**: Principal Component Analysis (PCA) projects data onto orthogonal axes (principal components) that maximize variance.
- **Bias-Variance Tradeoff**:
  - **Bias**: Error due to erroneous or oversimplified assumptions in the model. High bias leads to underfitting.
  - **Variance**: Error due to sensitivity to small fluctuations in the training set. High variance leads to overfitting.
  - **Generalization Error** = Bias² + Variance + Irreducible Error.

## Chapter 3: Pattern Recognition and Machine Learning (Christopher Bishop)
- **Probability Theory**:
  - **Bayes' Theorem**: $P(Y|X) = \frac{P(X|Y)P(Y)}{P(X)}$. Represents updating belief based on new evidence.
  - **Maximum Likelihood Estimation (MLE)**: Chooses parameters that maximize the probability of the observed data. Can lead to overfitting.
  - **Maximum A Posteriori (MAP)**: Integrates prior beliefs. $w_{MAP} = \arg\max_w P(w|D) = \arg\max_w P(D|w)P(w)$. Equivalent to L2 regularization (Ridge) when the prior is Gaussian.
- **Neural Networks & Deep Learning**:
  - **Feedforward Networks**: Composed of layered neurons. Each neuron applies an activation function (ReLU, Sigmoid, Tanh) to a weighted sum of inputs.
  - **Backpropagation**: Efficient algorithm for computing gradients of the loss function with respect to the weights using the chain rule of calculus.
  - **Regularization**: L1 (Lasso) encourages sparsity ($|w|$ penalty). L2 (Ridge) encourages small weights ($w^2$ penalty). Dropout randomly deactivates neurons during training to prevent co-adaptation.
  - **Activation Functions**: Relu ($max(0, x)$), Leaky Relu, GELU. Used to introduce non-linearity.

## Chapter 4: Generative AI and RAG (Retrieval-Augmented Generation)
- **Large Language Models (LLMs)**: Deep transformer-based networks (e.g. Decoder-only architectures like GPT) trained on next-token prediction.
- **Retrieval-Augmented Generation (RAG)**: A technique that optimizes LLM output by querying an external knowledge base of documents before generating a response.
  - **Ingestion**: Document -> Chunks -> Vector Embeddings -> Vector Database.
  - **Retrieval**: User query -> Embedding -> Vector Search (Cosine Similarity) -> Top-K context chunks.
  - **Generation**: Prompt Template(Context + User Query) -> LLM -> Grounded Answer.
- **Evaluation of RAG**:
  - **Faithfulness**: Is the answer grounded only in the retrieved context?
  - **Answer Relevance**: Does the answer address the user query?
  - **Context Recall**: Were all relevant context chunks successfully retrieved?
