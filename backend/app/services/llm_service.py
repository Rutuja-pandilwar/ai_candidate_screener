import os
import json
import logging
from app.config import settings
from google import genai

logger = logging.getLogger(__name__)

MOCK_QUESTION_DATA = {
    "ai_ml_engineer": [
        {
            "question_text": "What is the difference between supervised and unsupervised learning, and how do you mitigate overfitting in Decision Trees?",
            "expected_keywords": ["supervised", "unsupervised", "overfitting", "pruning", "labeled", "features"],
            "expected_concepts": ["Supervised learning uses labeled data", "Unsupervised learning finds hidden patterns", "Pruning mitigates overfitting", "Decision trees split nodes to maximize gain"],
            "expected_answer_summary": "Supervised learning relies on labeled training pairs, whereas unsupervised learning identifies patterns in unlabeled data. Decision tree overfitting is controlled using post-pruning or setting max depth limits.",
            "difficulty": "intermediate"
        },
        {
            "question_text": "Explain the bias-variance tradeoff and how Support Vector Machines (SVM) maximize the margin between classes.",
            "expected_keywords": ["bias", "variance", "tradeoff", "margin", "hyperplane", "support", "vectors"],
            "expected_concepts": ["High bias causes underfitting", "High variance causes overfitting", "SVM maximizes the margin", "Support vectors define boundary"],
            "expected_answer_summary": "The bias-variance tradeoff balances model complexity to prevent underfitting and overfitting. SVM finds the optimal hyperplane that maximizes the geometric margin between class boundaries.",
            "difficulty": "intermediate"
        },
        {
            "question_text": "Explain Bayes Theorem and how Maximum Likelihood Estimation (MLE) differs from Maximum A Posteriori (MAP).",
            "expected_keywords": ["bayes", "theorem", "mle", "map", "prior", "posterior", "likelihood"],
            "expected_concepts": ["Bayes theorem computes posterior", "MLE maximizes likelihood only", "MAP incorporates prior probability", "Estimation of parameters"],
            "expected_answer_summary": "Bayes Theorem calculates posterior probability. MLE estimates parameters solely based on observed data, whereas MAP includes prior beliefs or distributions in its formulation.",
            "difficulty": "advanced"
        },
        {
            "question_text": "How does backpropagation work in neural networks, and what regularization methods (like L1/L2 or dropout) do you use?",
            "expected_keywords": ["backpropagation", "gradient", "descent", "regularization", "dropout", "weights", "chain", "rule"],
            "expected_concepts": ["Backpropagation uses the chain rule", "Gradients flow backwards", "L1/L2 adds penalty to loss", "Dropout randomly deactivates neurons"],
            "expected_answer_summary": "Backpropagation computes loss gradients using the calculus chain rule, propagating errors backwards to update weights. Dropout and weight decay (L2) prevent network overfitting.",
            "difficulty": "advanced"
        },
        {
            "question_text": "What is Retrieval-Augmented Generation (RAG), and how does it improve LLM response accuracy compared to standard prompt tuning?",
            "expected_keywords": ["retrieval", "augmented", "generation", "embeddings", "vector", "database", "grounded", "context"],
            "expected_concepts": ["RAG retrieves external chunks", "Vector search matches query", "Grounded context prevents hallucination", "Improves LLM facts without retraining"],
            "expected_answer_summary": "RAG retrieves relevant external text from a vector database and inserts it as context into the prompt, reducing LLM hallucinations and grounding responses in facts.",
            "difficulty": "advanced"
        }
    ],
    "backend_engineer": [
        {
            "question_text": "What are the main differences between REST, GraphQL, and gRPC, and when would you choose one over the others?",
            "expected_keywords": ["rest", "graphql", "grpc", "http", "protobuf", "endpoints", "query"],
            "expected_concepts": ["REST uses HTTP verbs and endpoints", "GraphQL allows client query select", "gRPC uses HTTP/2 and Protobuf", "Payload size and roundtrips"],
            "expected_answer_summary": "REST uses standard resource endpoints and HTTP verbs. GraphQL lets clients specify required fields in a single query. gRPC utilizes Protobuf over HTTP/2 for high-performance RPC.",
            "difficulty": "intermediate"
        },
        {
            "question_text": "Explain the ACID properties of relational databases and how they differ from BASE properties in NoSQL systems.",
            "expected_keywords": ["acid", "base", "relational", "transactions", "nosql", "consistency", "availability"],
            "expected_concepts": ["Atomicity Consistency Isolation Durability", "Basically Available Soft-state Eventual", "Relational transaction safety", "NoSQL high scalability trade-off"],
            "expected_answer_summary": "ACID guarantees absolute reliability and transactional isolation in RDBMS. BASE prioritizes availability and eventual consistency for distributed NoSQL databases.",
            "difficulty": "intermediate"
        },
        {
            "question_text": "What is the CAP Theorem, and how do databases like MongoDB and Cassandra choose between Consistency and Availability?",
            "expected_keywords": ["cap", "theorem", "consistency", "availability", "partition", "tolerance", "cassandra", "mongodb"],
            "expected_concepts": ["Cannot have C, A, and P together", "Network partition occurs", "MongoDB prioritizes Consistency (CP)", "Cassandra prioritizes Availability (AP)"],
            "expected_answer_summary": "CAP theorem states distributed systems can only achieve two of Consistency, Availability, and Partition Tolerance. MongoDB is CP, sacrificing availability; Cassandra is AP, sacrificing consistency.",
            "difficulty": "advanced"
        },
        {
            "question_text": "What are the differences between Cache-Aside and Write-Through caching, and how do you handle cache eviction like LRU?",
            "expected_keywords": ["cache", "aside", "through", "eviction", "lru", "hit", "miss", "invalidation"],
            "expected_concepts": ["Cache-aside loads on miss", "Write-through updates cache and DB", "LRU evicts least recently used", "Eviction policies maintain size limits"],
            "expected_answer_summary": "Cache-Aside queries cache first, loading from DB on miss. Write-Through writes to cache and DB simultaneously. LRU discards the oldest accessed keys when full.",
            "difficulty": "intermediate"
        },
        {
            "question_text": "Explain the difference between Concurrency and Parallelism, and how message queues like RabbitMQ or Kafka handle asynchronous task processing.",
            "expected_keywords": ["concurrency", "parallelism", "queues", "kafka", "rabbitmq", "asynchronous", "broker", "partitions"],
            "expected_concepts": ["Concurrency is dealing with multiple tasks", "Parallelism is executing tasks at once", "RabbitMQ uses smart broker routing", "Kafka uses high throughput partitions"],
            "expected_answer_summary": "Concurrency is managing multiple tasks at once; parallelism is running them simultaneously. RabbitMQ routes messages using exchanges, while Kafka logs events in ordered partitions.",
            "difficulty": "advanced"
        }
    ],
    "data_scientist": [
        {
            "question_text": "What is Exploratory Data Analysis (EDA), and how do you identify and handle outliers using the IQR (Interquartile Range) method?",
            "expected_keywords": ["eda", "outliers", "iqr", "percentile", "quartile", "distribution", "handling"],
            "expected_concepts": ["EDA discovers data patterns", "IQR is Q3 minus Q1", "Outliers are beyond 1.5 IQR limits", "Imputation or removal of outliers"],
            "expected_answer_summary": "EDA explores dataset trends visually and statistically. The IQR method flags outliers lying 1.5 times the interquartile range outside the first and third quartiles.",
            "difficulty": "intermediate"
        },
        {
            "question_text": "What are the differences between standardization (z-score) and normalization (min-max scaling), and when is each preferred?",
            "expected_keywords": ["standardization", "normalization", "scaler", "z-score", "min-max", "scaling", "features"],
            "expected_concepts": ["Standardization shifts to mean 0 variance 1", "Normalization bounds to 0 and 1 range", "Standardization handles extreme outliers better", "Min-max fits bounded algorithms"],
            "expected_answer_summary": "Standardization centers data to zero mean and unit variance. Normalization scales attributes between 0 and 1. Standardization is preferred when outliers are present.",
            "difficulty": "intermediate"
        },
        {
            "question_text": "Explain Gini Impurity and how Ensemble Methods like Random Forest improve on single Decision Trees.",
            "expected_keywords": ["gini", "impurity", "ensemble", "random", "forest", "variance", "bagging"],
            "expected_concepts": ["Gini measures node split purity", "Ensemble aggregates predictions", "Random Forest uses bagging and features", "Reduces variance of single trees"],
            "expected_answer_summary": "Gini Impurity measures the probability of misclassifying a random element. Random Forest aggregates multiple randomized decision trees to reduce overall variance.",
            "difficulty": "advanced"
        },
        {
            "question_text": "How do boosting algorithms like XGBoost, AdaBoost, and LightGBM work, and how do they differ from bagging?",
            "expected_keywords": ["boosting", "xgboost", "adaboost", "lightgbm", "bagging", "sequential", "residuals"],
            "expected_concepts": ["Bagging runs trees in parallel", "Boosting builds trees sequentially", "Each tree fits previous residuals", "XGBoost uses gradient regularization"],
            "expected_answer_summary": "Bagging builds parallel models independently. Boosting builds sequential trees where each subsequent estimator corrects the errors of its predecessor.",
            "difficulty": "advanced"
        },
        {
            "question_text": "What metrics would you use to evaluate a highly imbalanced classification model? Explain Precision, Recall, F1-Score, and ROC-AUC.",
            "expected_keywords": ["precision", "recall", "f1-score", "roc-auc", "imbalanced", "positives", "negatives"],
            "expected_concepts": ["Accuracy is misleading for imbalance", "Precision is TP divided by TP+FP", "Recall is TP divided by TP+FN", "F1-Score is harmonic mean"],
            "expected_answer_summary": "In imbalanced classes, standard accuracy is misleading. Instead, use Precision (true positive rate among predictions) and Recall (sensitivity), combined in the F1-Score.",
            "difficulty": "advanced"
        }
    ]
}


class LLMService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
        self.enabled = bool(self.api_key)

        if self.enabled:
            try:
                self.client = genai.Client(api_key=self.api_key)
                logger.info("Gemini API successfully configured.")
            except Exception as e:
                logger.error(f"Failed to configure Gemini API: {e}")
                self.enabled = False
        else:
            logger.warning("GEMINI_API_KEY not found. Running in MOCK mode.")

    def _parse_json(self, text: str) -> dict:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        return json.loads(text)

    # ---------------- EMBEDDINGS ----------------
    def get_embedding(self, text: str) -> list:
        if not self.enabled:
            import random
            random.seed(hash(text))
            return [random.uniform(0.001, 0.1) for _ in range(768)]

        try:
            response = self.client.models.embed_content(
                model="text-embedding-004",
                contents=text
            )
            return response.embeddings[0].values

        except Exception as e:
            logger.error(f"Embedding error: {e}")
            import random
            return [random.uniform(0.001, 0.1) for _ in range(768)]

    # ---------------- RESUME ANALYSIS ----------------
    def analyze_resume(self, resume_text: str) -> dict:
        default_profile = {
            "name": "Candidate",
            "email": "candidate@example.com",
            "skills": ["Python", "Machine Learning", "Software Engineering"],
            "experience_level": "mid",
            "domain_exposure": ["API Design"]
        }

        if not self.enabled:
            return default_profile

        prompt = f"""
Extract structured resume info:

Return JSON:
{{
"name": "",
"email": "",
"skills": [],
"experience_level": "junior|mid|senior",
"domain_exposure": []
}}

Resume:
\"\"\"{resume_text}\"\"\"
"""

        try:
            response = self.client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt
            )
            return json.loads(response.text)

        except Exception as e:
            logger.error(f"Resume analysis error: {e}")
            return default_profile

    # ---------------- QUESTION GENERATION ----------------
    def generate_interview_question(self, role, candidate_profile, rag_context, previous_questions=None, previous_questions_text=None):
        prev_q = previous_questions_text if previous_questions_text is not None else (previous_questions if previous_questions is not None else [])
        
        # Get fallback question data matching current role and session progress
        q_idx = len(prev_q)
        role_questions = MOCK_QUESTION_DATA.get(role, MOCK_QUESTION_DATA["backend_engineer"])
        mock_data = role_questions[q_idx % len(role_questions)]
        
        # Structure fallback output
        fallback_guideline = {
            "question": mock_data["question_text"],
            "expected_keywords": mock_data["expected_keywords"],
            "expected_concepts": mock_data["expected_concepts"],
            "expected_answer_summary": mock_data["expected_answer_summary"]
        }
        
        if not self.enabled:
            return {
                "question_text": mock_data["question_text"],
                "correct_answer_guideline": json.dumps(fallback_guideline),
                "difficulty": mock_data["difficulty"]
            }

        prompt = f"""
You are an expert technical interviewer generating an interview question.

Role: {role}
Skills: {candidate_profile.get("skills", [])}
Experience: {candidate_profile.get("experience_level", "")}

Context:
{rag_context}

Previous Questions to avoid:
{prev_q}

Instructions:
1. Generate ONE highly relevant, specific technical question based on the role and context.
2. Generate/define the expected keywords, expected concepts, and expected answer summary for that question.
3. The expected concepts must cover the critical technical parts of the answer.
4. The expected answer summary should represent the ideal comprehensive explanation of the answer.

Return strictly a JSON object with this exact shape:
{{
  "question_text": "<the_interview_question>",
  "correct_answer_guideline": {{
    "question": "<the_interview_question>",
    "expected_keywords": ["keyword1", "keyword2", "keyword3"],
    "expected_concepts": ["concept sentence 1", "concept sentence 2"],
    "expected_answer_summary": "<comprehensive_ideal_answer_summary>"
  }},
  "difficulty": "beginner|intermediate|advanced"
}}
"""

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            res = self._parse_json(response.text)
            
            # Ensure correct_answer_guideline is a JSON string of the structured fields
            if isinstance(res.get("correct_answer_guideline"), dict):
                res["correct_answer_guideline"] = json.dumps(res["correct_answer_guideline"])
            elif isinstance(res.get("correct_answer_guideline"), str):
                try:
                    json.loads(res["correct_answer_guideline"])
                except Exception:
                    wrapper = {
                        "question": res["question_text"],
                        "expected_keywords": [w for w in res["question_text"].split() if len(w) > 4][:5],
                        "expected_concepts": [res["question_text"]],
                        "expected_answer_summary": res["correct_answer_guideline"]
                    }
                    res["correct_answer_guideline"] = json.dumps(wrapper)
            return res

        except Exception as e:
            logger.error(f"Question generation error: {e}")
            return {
                "question_text": mock_data["question_text"],
                "correct_answer_guideline": json.dumps(fallback_guideline),
                "difficulty": mock_data["difficulty"]
            }

    # ---------------- ANSWER EVALUATION ----------------
    def evaluate_candidate_answer(self, question_text, guideline=None, correct_guideline=None, answer_text=None, candidate_answer=None):
        g = correct_guideline if correct_guideline is not None else guideline
        ans = candidate_answer if candidate_answer is not None else answer_text
        
    # ---------------- ANSWER EVALUATION ----------------
    def evaluate_candidate_answer(self, question_text, guideline=None, correct_guideline=None, answer_text=None, candidate_answer=None):
        g = correct_guideline if correct_guideline is not None else guideline
        ans = candidate_answer if candidate_answer is not None else answer_text
        
        import json
        import re
        
        expected_keywords = []
        expected_concepts = []
        expected_summary = ""
        
        # Try to parse the guideline as JSON-serialized dictionary from our upgraded generator
        if g:
            try:
                g_str = g.strip()
                if g_str.startswith("{") and g_str.endswith("}"):
                    data = json.loads(g_str)
                    expected_keywords = data.get("expected_keywords", [])
                    expected_concepts = data.get("expected_concepts", [])
                    expected_summary = data.get("expected_answer_summary", "")
            except Exception as e:
                logger.error(f"Error parsing correct_guideline JSON: {e}")
                
        # Dynamic extraction fallback if not structured or parse failed
        if not expected_summary:
            expected_summary = g or "Should demonstrate conceptual clarity and structural breakdown."
            
        if not expected_keywords:
            stop_words = {"explain", "describe", "what", "which", "system", "using", "with", "framework", "library", "should", "demonstrate", "conceptual", "clarity", "structural", "breakdown"}
            all_words = re.findall(r"\b\w{4,}\b", ((question_text or "") + " " + expected_summary).lower())
            expected_keywords = list(set(w for w in all_words if w not in stop_words))
            
        if not expected_concepts:
            expected_concepts = [w.capitalize() for w in expected_keywords[:5]]
        
        # Define dynamic fallback evaluator using scikit-learn cosine similarity and concept checks
        def get_dynamic_evaluation():
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            
            ans_clean = (ans or "").strip().lower()
            
            # Meaningless or short filler responses
            invalid_words = {
                "no", "yes", "idk", "ok", "okay", "nothing", "hmm", "hmmm", "none",
                "na", "n/a", "don't know", "dont know", "i dont know", "i do not know",
                "nothing to say", "pass", "skip", "i pass", "hello", "hi", "hey",
                "bye", "testing", "test", "demo", "xyz", "abc", "blah"
            }
            
            # Remove basic punctuation to catch "no.", "ok!", etc.
            ans_stripped = re.sub(r"[^\w\s]", "", ans_clean).strip()
            
            # Common multi-word filler/unhelpful phrases
            phrase_fillers = ["dont know", "do not know", "nothing to say", "no idea", "not sure", "no clue", "dont care", "skip this"]
            
            # If the response is empty, matches invalid words, is under 4 words, contains fillers, or all words are filler tokens
            is_invalid = (
                not ans_stripped or
                ans_stripped in invalid_words or
                len(ans_stripped.split()) < 4 or
                any(pf in ans_stripped for pf in phrase_fillers) or
                all(w in invalid_words or len(w) <= 3 for w in ans_stripped.split())
            )
            
            if is_invalid:
                formatted_feedback = (
                    "### 📊 Scorecard Breakdown\n"
                    "* 💻 **Technical Knowledge**: 0.0/10\n"
                    "* 🎯 **Relevance**: 0.0/10\n"
                    "* 🗣️ **Communication Clarity**: 0.0/10\n"
                    "* 📋 **Completeness**: 0.0/10\n\n"
                    "---\n\n"
                    "### 📝 AI Interviewer Assessment\n"
                    "- Answer does not address the asked question\n"
                    "- Response is too short for technical evaluation\n"
                    "- No relevant technical concepts were explained\n"
                    "- Technical explanation is missing completely"
                )
                return {
                    "score": 0.0,
                    "evaluation_feedback": formatted_feedback
                }

            # 1. Compute TF-IDF Cosine Similarity with Expected Answer Summary
            vectorizer = TfidfVectorizer(stop_words='english')
            try:
                tfidf = vectorizer.fit_transform([expected_summary.lower(), ans_clean])
                sim_score = float(cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0])
            except Exception:
                sim_score = 0.0
                
            # 2. Also check against question text to see if any alignment exists
            try:
                tfidf_q = vectorizer.fit_transform([question_text.lower(), ans_clean])
                sim_score_q = float(cosine_similarity(tfidf_q[0:1], tfidf_q[1:2])[0][0])
            except Exception:
                sim_score_q = 0.0
                
            max_sim = max(sim_score, sim_score_q)

            # 3. Check exact keyword matching ratio
            matching_keywords = [w for w in expected_keywords if w.lower() in ans_clean]
            match_ratio = len(matching_keywords) / max(1, len(expected_keywords))
            
            # 4. Gatekeeper Topic Mismatch Check
            # If the candidate's answer shares no significant semantic overlap and lacks expected keywords, trigger mismatch
            is_mismatch = (max_sim < 0.12 and match_ratio < 0.15)
            
            if is_mismatch:
                asked_chunk = [w for w in (question_text or "").lower().split() if len(w) > 4 and w not in {"explain", "describe", "what", "which", "system", "using", "with"}]
                asked_topic = asked_chunk[0] if asked_chunk else "the asked technology"
                
                user_chunk = [w for w in ans_clean.split() if len(w) > 4 and w not in {"explain", "describe", "what", "which", "system", "using", "with", "framework", "library", "application"}]
                user_topic = user_chunk[0] if user_chunk else "unrelated concepts"
                
                formatted_feedback = (
                    "### 📊 Scorecard Breakdown\n"
                    "* 💻 **Technical Knowledge**: 1.0/10\n"
                    "* 🎯 **Relevance**: 1.0/10\n"
                    "* 🗣️ **Communication Clarity**: 1.0/10\n"
                    "* 📋 **Completeness**: 0.0/10\n\n"
                    "---\n\n"
                    "### 📝 AI Interviewer Assessment\n"
                    "- Answer is unrelated to the asked question\n"
                    f"- Response discusses {user_topic} instead of {asked_topic}\n"
                    f"- Expected {', '.join(expected_keywords[:3]) if expected_keywords else 'domain'} concepts are missing\n"
                    "- Technical explanation is incorrect for the given question"
                )
                return {
                    "score": 1.0,
                    "evaluation_feedback": formatted_feedback
                }

            # 5. Stemming-resilient concept coverage score
            concept_matches = 0
            for concept in expected_concepts:
                words = re.findall(r"\b\w{3,}\b", concept.lower())
                content_words = [w for w in words if w not in {"extract", "reduce", "perform", "automatically", "layers", "classes", "from", "with", "into", "onto", "uses", "using"}]
                if not content_words:
                    if concept.lower() in ans_clean:
                        concept_matches += 1
                    continue
                
                matched_count = 0
                for cw in content_words:
                    stem = cw[:4]
                    if cw in ans_clean or (len(cw) > 4 and stem in ans_clean):
                        matched_count += 1
                
                if matched_count / len(content_words) >= 0.5:
                    concept_matches += 1
                    
            concept_ratio = concept_matches / max(1, len(expected_concepts))
            
            # Compute multi-dimensional scores
            tech_score = 3.0 + (sim_score * 4.0) + (concept_ratio * 3.0)
            tech_score = round(min(9.8, max(2.0, float(tech_score))), 1)
            
            relevance_score = 4.0 + (sim_score * 6.0)
            relevance_score = round(min(9.8, max(2.0, float(relevance_score))), 1)
            
            # More realistic communication scoring logic (casing, transitions, completeness)
            comm_score = 4.0
            
            # Sentence structure check
            sentences = [s.strip() for s in re.split(r"[.!?]+", ans) if s.strip()]
            if len(sentences) >= 2:
                comm_score += 1.5
            elif len(sentences) == 1 and len(sentences[0].split()) > 10:
                comm_score += 0.5
                
            # Transition & connector word check
            connectors = {"because", "therefore", "however", "furthermore", "specifically", "consequently", "although", "whereas", "such as", "for example"}
            connector_matches = sum(1 for c in connectors if c in ans_clean)
            comm_score += min(2.0, connector_matches * 0.5)
            
            # Vocabulary diversity (ratio of unique words)
            word_count = len(ans_clean.split())
            if word_count > 0:
                vocab_diversity = len(set(ans_clean.split())) / word_count
                comm_score += min(1.5, vocab_diversity * 2.0)
                
            # Completeness alignment
            comm_score += min(1.0, concept_ratio * 1.5)
            
            # Deduct for all-lowercase input (lack of punctuation/proper structure)
            if not any(char.isupper() for char in ans if char.isalpha()):
                comm_score -= 1.0
                
            comm_score = round(min(9.8, max(1.0, float(comm_score))), 1)
            
            completeness_score = round(min(10.0, (concept_ratio * 8.0) + (match_ratio * 2.0)), 1)
            
            overall_score = (tech_score * 0.5) + (relevance_score * 0.2) + (completeness_score * 0.2) + (comm_score * 0.1)
            overall_score = round(min(10.0, max(1.0, overall_score)), 1)
            
            # Point-wise technical critique (no emojis, no positive appreciation lines)
            critique_points = []
            if sim_score >= 0.4:
                critique_points.append(f"- Answer shows strong conceptual alignment with {expected_concepts[0] if expected_concepts else 'the target domain'}")
            else:
                critique_points.append(f"- Explanation has moderate conceptual overlap but should explain the relationship with {expected_concepts[0] if expected_concepts else 'the asked topic'}")
                
            missing = [c for c in expected_concepts if c.lower() not in ans_clean]
            if missing:
                critique_points.append(f"- Important concepts are missing: {', '.join(missing[:3])}")
            else:
                critique_points.append("- Satisfies key conceptual coverage and expected guidelines")
                
            if word_count < 25:
                critique_points.append("- Technical explanation is correct but lacks production depth and context")
            else:
                critique_points.append("- Provides relevant technical details and structural reasoning")

            formatted_feedback = (
                f"### 📊 Scorecard Breakdown\n"
                f"* 💻 **Technical Knowledge**: {tech_score}/10\n"
                f"* 🎯 **Relevance**: {relevance_score}/10\n"
                f"* 🗣️ **Communication Clarity**: {comm_score}/10\n"
                f"* 📋 **Completeness**: {completeness_score}/10\n\n"
                f"---\n\n"
                f"### 📝 AI Interviewer Assessment\n"
                + "\n".join(critique_points)
            )
            
            return {
                "score": overall_score,
                "evaluation_feedback": formatted_feedback
            }

        if not self.enabled:
            return get_dynamic_evaluation()

        prompt = f"""
You are a highly rigorous, senior technical interviewer.
Evaluate the candidate's answer based on the given technical question, expected keywords, expected concepts, and ideal answer summary.

Input:
- Question: {question_text}
- Expected Keywords: {expected_keywords}
- Expected Concepts: {expected_concepts}
- Expected Answer Summary: {expected_summary}
- Candidate's Answer: {ans}

Instructions:
1. Invalid Response Check: If the candidate's response is empty, extremely short (under 4-5 words), or contains meaningless/filler answers (such as 'no', 'idk', 'ok', 'don't know', 'hmm', etc.), you MUST bypass semantic scoring and:
   - Set ALL scores (tech_score, relevance_score, comm_score, completeness_score, overall_score) strictly to 0.0
   - Set the detailed_critique strictly to:
     - Answer does not address the asked question
     - Response is too short for technical evaluation
     - No relevant technical concepts were explained
     - Technical explanation is missing completely
2. Topic Mismatch Check: If the response is not an invalid/filler answer but is completely unrelated to the asked question (for example, explaining "Flask" when asked about "CNN architecture"), you must:
   - Cap "tech_score" at 1.0
   - Cap "relevance_score" at 1.0
   - Cap "completeness_score" at 0.0
   - Cap "overall_score" at 1.0
   - Set "detailed_critique" strictly to a point-wise list (no emojis, no generic appreciation phrases) explaining the mismatch:
     - Answer is unrelated to the asked question
     - Response discusses [User Answer Topic] instead of [Asked Question Topic]
     - Expected [Asked Keywords] concepts are missing
     - Technical explanation is incorrect for the given question
3. If the answer is on-topic, grade the candidate critically across these categories between 0.0 and 10.0:
   - Technical Knowledge (How technically accurate and deep is the answer?)
   - Relevance (Does it directly address the question without dodging or talking about unrelated topics?)
   - Communication Clarity (Is the explanation structured, coherent, and well-phrased? Rate structure, casing, transition words, and spelling rather than length alone.)
   - Completeness (Does it cover the key items from the expected guideline and concepts?)
4. For on-topic answers, calculate the overall average score (weighted: 50% Technical, 20% Relevance, 20% Completeness, 10% Clarity).
5. Provide a structured point-wise technical critique (3-4 bullet points maximum). Highlight what they explained correctly, followed by the exact missing concepts, gaps, and improvements.
6. Strict constraints:
   - No emojis anywhere in your response.
   - No fake positive responses or generic appreciation lines (do NOT say "Good job", "Well done", "Partially correct but...", etc.).

Return your response strictly as a JSON object with this exact shape:
{{
  "tech_score": <float_between_0.0_and_10.0>,
  "relevance_score": <float_between_0.0_and_10.0>,
  "comm_score": <float_between_0.0_and_10.0>,
  "completeness_score": <float_between_0.0_and_10.0>,
  "overall_score": <float_between_0.0_and_10.0>,
  "detailed_critique": "<detailed_point_wise_critique_string>"
}}
"""

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            res = self._parse_json(response.text)
            overall_score = float(res.get("overall_score", 5.0))
            
            # Formulate the rich markdown scorecard
            formatted_feedback = (
                f"### 📊 Scorecard Breakdown\n"
                f"* 💻 **Technical Knowledge**: {res.get('tech_score', 5.0)}/10\n"
                f"* 🎯 **Relevance**: {res.get('relevance_score', 5.0)}/10\n"
                f"* 🗣️ **Communication Clarity**: {res.get('comm_score', 5.0)}/10\n"
                f"* 📋 **Completeness**: {res.get('completeness_score', 5.0)}/10\n\n"
                f"---\n\n"
                f"### 📝 AI Interviewer Assessment\n"
                f"{res.get('detailed_critique', 'No critique available.')}"
            )
            
            return {
                "score": overall_score,
                "evaluation_feedback": formatted_feedback
            }

        except Exception as e:
            logger.error(f"Evaluation error: {e}")
            return get_dynamic_evaluation()


    # ---------------- FINAL REPORT ----------------
    def generate_final_report(self, candidate_name, role, qa_pairs):
        def get_dynamic_report():
            # Dynamic fallback report compilation based on actual candidate answers
            scores = [q.get("score", 5.0) for q in qa_pairs if q.get("score") is not None]
            avg_score = sum(scores) / len(scores) if scores else 5.0
            
            # Map strengths and improvement areas dynamically from qa_pairs
            strengths = []
            weaknesses = []
            
            for idx, qa in enumerate(qa_pairs):
                q_text = qa.get("question", "").lower()
                q_score = qa.get("score", 5.0)
                
                # Dynamic mapping of concepts
                concept = "general domain principles"
                if "supervised" in q_text or "decision" in q_text or "tree" in q_text:
                    concept = "Supervised Algorithms & Overfitting Mitigation"
                elif "bias" in q_text or "svm" in q_text or "variance" in q_text:
                    concept = "Bias-Variance Tradeoff & Margin Maximization"
                elif "rest" in q_text or "graphql" in q_text or "grpc" in q_text:
                    concept = "API Protocols & Web Architecture"
                elif "acid" in q_text or "database" in q_text or "transaction" in q_text:
                    concept = "Database Transactions & ACID Properties"
                elif "cap" in q_text or "nosql" in q_text:
                    concept = "CAP Theorem & NoSQL Partitioning"
                elif "cache" in q_text or "eviction" in q_text:
                    concept = "Caching Eviction Models (LRU/LFU)"
                elif "concurrency" in q_text or "parallelism" in q_text:
                    concept = "Concurrency & Asynchronous Processing"
                elif "backpropagation" in q_text or "neural" in q_text:
                    concept = "Neural Networks & Regularization"
                elif "rag" in q_text or "retrieval" in q_text or "llm" in q_text:
                    concept = "RAG & LLM System Integration"
                elif "eda" in q_text or "outlier" in q_text:
                    concept = "Exploratory Data Analysis & Outlier Handling"
                elif "boosting" in q_text or "xgboost" in q_text:
                    concept = "Ensemble Methods & Gradient Boosting"
                elif "metric" in q_text or "imbalance" in q_text or "f1" in q_text:
                    concept = "Model Evaluation & Imbalanced Datasets"
                    
                if q_score >= 7.0:
                    strengths.append(f"Demonstrated good command over {concept}")
                else:
                    weaknesses.append(f"Needs more technical detail in {concept}")
                    
            if not strengths:
                strengths = [
                    "Demonstrates clear structural layout of answers.",
                    "Strong foundational understanding of role requirements.",
                    "Provides clear logical structure in problem solving."
                ]
            if not weaknesses:
                weaknesses = [
                    "Could expand on production-level deployment scenarios.",
                    "Recommend studying advanced concurrency and scaling challenges.",
                    "Review specific mathematical proofs and statistical foundations."
                ]
                
            role_display = role.replace('_', ' ').title()
            summary = (
                f"The candidate successfully completed the technical evaluation for the {role_display} role. "
                f"Across the assessment questions, the candidate demonstrated an overall rating of {round(avg_score, 1)}/10. "
                f"They showed their highest competency in areas such as {', '.join([s.split('over ')[-1] for s in strengths[:2]])}. "
                f"There are notable opportunities for technical growth, particularly in {', '.join([w.split('in ')[-1] for w in weaknesses[:2]])}."
            )
                
            return {
                "overall_score": float(round(avg_score, 1)),
                "strengths": strengths[:3],
                "areas_for_improvement": weaknesses[:3],
                "summary": summary
            }

        if not self.enabled:
            return get_dynamic_report()

        prompt = f"""
You are an expert executive talent assessor.
Compile a comprehensive technical interview evaluation report for the candidate based on their screening Q&A pairs.

Candidate Name: {candidate_name}
Target Role: {role}
Interview Q&A Pairs:
{json.dumps(qa_pairs, indent=2)}

Instructions:
1. Provide a professional and personalized executive 'summary' (minimum 3-4 sentences) assessing the candidate's overall technical preparedness, depth of knowledge, communication, and performance for the target role.
2. List 2 to 3 highly specific 'strengths' based on their best-performing answers. Specify what domains or concepts they excelled in.
3. List 2 to 3 constructive and concrete 'areas_for_improvement' indicating what specific technical topics, architectures, or implementation details they need to review or strengthen.
4. Calculate an accurate 'overall_score' (between 0.0 and 10.0) reflecting their average performance. It should be a float.

Return your response strictly as a JSON object with this exact shape:
{{
  "overall_score": <float_between_0.0_and_10.0>,
  "strengths": [
    "<specific_strength_1>",
    "<specific_strength_2>"
  ],
  "areas_for_improvement": [
    "<specific_improvement_area_1>",
    "<specific_improvement_area_2>"
  ],
  "summary": "<personalized_executive_summary_string>"
}}
"""

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return self._parse_json(response.text)

        except Exception as e:
            logger.error(f"Report error: {e}")
            return get_dynamic_report()