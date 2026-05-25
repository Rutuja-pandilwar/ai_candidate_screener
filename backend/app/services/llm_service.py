import os
import json
import logging
from app.config import settings
from google import genai

logger = logging.getLogger(__name__)

# MOCK_QUESTION_DATA has been removed to ensure the system is entirely dynamic
# and generates questions/answer guidelines on-the-fly based on the candidate's resume.

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
        # Dynamic local regex-based resume analysis fallback
        def get_local_extracted_profile(text: str) -> dict:
            import re
            
            # Clean up text
            t = (text or "").lower()
            
            # 1. Extract name (check first few lines of text)
            lines = [line.strip() for line in (text or "").split("\n") if line.strip()]
            name = "Candidate"
            if lines:
                first_line = lines[0]
                if len(first_line.split()) <= 4 and not any(kw in first_line.lower() for kw in ["resume", "cv", "curriculum", "email", "phone", "profile"]):
                    name = first_line.title()
            
            # 2. Extract email via regex
            email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text or "")
            email = email_match.group(0) if email_match else "candidate@example.com"
            
            # 3. Scan for skills from a comprehensive list of technical keywords
            tech_vocabulary = [
                "python", "javascript", "typescript", "golang", "java", "c++", "c#", "ruby", "rust",
                "fastapi", "flask", "django", "nodejs", "react", "nextjs", "vue", "angular",
                "sqlite", "postgresql", "mysql", "mongodb", "redis", "cassandra", "dynamodb",
                "docker", "kubernetes", "aws", "gcp", "azure", "terraform", "ansible",
                "machine learning", "deep learning", "neural networks", "nlp", "computer vision",
                "pytorch", "tensorflow", "keras", "scikit-learn", "pandas", "numpy", "transformers",
                "sql", "nosql", "git", "ci/cd", "graphql", "grpc", "rest api", "apis", "rabbitmq", "kafka"
            ]
            
            extracted_skills = []
            for skill in tech_vocabulary:
                pattern = r"\b" + re.escape(skill) + r"\b"
                if re.search(pattern, t):
                    # Format appropriately
                    extracted_skills.append(skill.upper() if len(skill) <= 3 else skill.title())
                    
            if not extracted_skills:
                extracted_skills = ["Python", "Software Engineering", "Database Systems"]
                
            # 4. Experience level detection
            experience_level = "mid"
            if any(term in t for term in ["senior", "lead", "architect", "principal", "years experience", "5+ years", "10+ years"]):
                experience_level = "senior"
            elif any(term in t for term in ["junior", "intern", "fresher", "entry level", "student"]):
                experience_level = "junior"
                
            # 5. Domain exposure detection
            domains = []
            domain_glossary = {
                "backend": "Backend Development",
                "frontend": "Frontend Development",
                "cloud": "Cloud Engineering",
                "devops": "DevOps",
                "fullstack": "Full Stack Engineering",
                "nlp": "Natural Language Processing",
                "vision": "Computer Vision",
                "mlops": "MLOps",
                "data scientist": "Data Science",
                "api": "API Architecture",
                "database": "Database Administration"
            }
            for key, val in domain_glossary.items():
                if key in t:
                    domains.append(val)
            if not domains:
                domains = ["Software Engineering"]
                
            return {
                "name": name,
                "email": email,
                "skills": extracted_skills[:10],
                "experience_level": experience_level,
                "domain_exposure": domains[:3]
            }

        if not self.enabled:
            return get_local_extracted_profile(resume_text)

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
            return get_local_extracted_profile(resume_text)

    # ---------------- QUESTION GENERATION ----------------
    def generate_interview_question(self, role, candidate_profile, rag_context, previous_questions=None, previous_questions_text=None):
        prev_q = previous_questions_text if previous_questions_text is not None else (previous_questions if previous_questions is not None else [])
        
        q_idx = len(prev_q)
        
        # Build a dynamic local fallback question based on actual candidate skills
        def get_dynamic_local_fallback():
            import random
            import re
            
            skills = candidate_profile.get("skills", [])
            if not skills:
                skills = ["Python", "Software Engineering", "Databases"]
                
            clean_skills = [s for s in skills if len(s) > 2]
            if not clean_skills:
                clean_skills = skills
                
            # Seed randomly based on candidate name and question index to ensure deterministic and progressive questions
            random.seed(hash(candidate_profile.get("name", "Candidate")) + q_idx)
            
            # Select 1-2 skills
            selected_skills = random.sample(clean_skills, min(2, len(clean_skills)))
            skill1 = selected_skills[0]
            skill2 = selected_skills[1] if len(selected_skills) > 1 else "alternative design options"
            
            # Technical templates targeting different aspects: architecture, data structures, integration, concurrency
            templates = [
                (
                    "Explain the core architectural concepts of {skill1} and how you would apply it to solve scaling or performance challenges in a production environment.",
                    ["architecture", "scale", "performance", "{skill1_clean}"],
                    ["Understands core architecture of {skill1}", "Can apply scaling principles", "Knowledge of production optimizations"],
                    "The core architecture of {skill1} involves managing processes, memory, and routing efficiently to handle scale and performance. Optimizations include caching, connection pooling, and resource tuning."
                ),
                (
                    "In your experience working with {skill1}, what are the biggest design patterns or best practices you follow? Contrast this with alternative approaches like {skill2}.",
                    ["design", "pattern", "practices", "{skill1_clean}", "{skill2_clean}"],
                    ["Applies correct design patterns in {skill1}", "Follows industry best practices", "Can contrast {skill1} with {skill2}"],
                    "Design patterns in {skill1} focus on code reuse, separation of concerns, and clean abstraction. Contrasting with {skill2} highlights trade-offs in complexity, speed, and standard methodologies."
                ),
                (
                    "What is the difference between concurrency and parallelism when building applications using {skill1}? How does it handle heavy workloads?",
                    ["concurrency", "parallelism", "workloads", "threads", "{skill1_clean}"],
                    ["Differentiates concurrency from parallelism", "Knowledge of {skill1} execution model", "Handles async or multi-threaded workloads"],
                    "Concurrency deals with managing multiple tasks at once (async), while parallelism executes them simultaneously on multiple CPU cores. In {skill1}, this is managed using event loops or thread pools."
                ),
                (
                    "How do you handle error logging, unit testing, and continuous integration when deploying services built around {skill1} and {skill2}?",
                    ["testing", "logging", "integration", "{skill1_clean}", "{skill2_clean}"],
                    ["Implements logging and diagnostic practices", "Writes unit tests for {skill1}", "Sets up CI/CD pipeline automation"],
                    "Deploying systems with {skill1} requires structured logging, automated unit tests, and integration testing in CI/CD pipelines to ensure code reliability and rapid, error-free releases."
                )
            ]
            
            template = templates[q_idx % len(templates)]
            
            q_text = template[0].format(skill1=skill1, skill2=skill2)
            
            expected_kws = [k.format(skill1_clean=skill1.lower(), skill2_clean=skill2.lower()) for k in template[1]]
            expected_concs = [c.format(skill1=skill1, skill2=skill2) for c in template[2]]
            expected_sum = template[3].format(skill1=skill1, skill2=skill2)
            
            guideline = {
                "question": q_text,
                "expected_keywords": expected_kws,
                "expected_concepts": expected_concs,
                "expected_answer_summary": expected_sum
            }
            
            diff = "intermediate"
            if q_idx == 0:
                diff = "beginner"
            elif q_idx >= 3:
                diff = "advanced"
                
            return {
                "question_text": q_text,
                "correct_answer_guideline": json.dumps(guideline),
                "difficulty": diff
            }
            
        if not self.enabled:
            return get_dynamic_local_fallback()

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
            return get_dynamic_local_fallback()

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