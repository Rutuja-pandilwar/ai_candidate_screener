import os
import sys
import json

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))

# Force stdout to support UTF-8 formatting in Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.services.llm_service import LLMService

def run_mismatch_test():
    llm = LLMService()
    
    question = "Explain CNN architecture and why it is used in image classification."
    
    # We will pass a mock guideline representing CNN expected concepts
    guideline = {
        "question": question,
        "expected_keywords": ["cnn", "convolution", "pooling", "features", "classification", "layers"],
        "expected_concepts": [
            "Convolutional layers extract spatial features",
            "Pooling layers reduce dimensionality",
            "CNNs perform image classification automatically",
            "Fully connected layers map features to classes"
        ],
        "expected_answer_summary": "CNN is a deep learning architecture that extracts spatial image features using convolution and pooling operations to perform image classification."
    }
    
    guideline_json = json.dumps(guideline)
    
    # Mismatch Candidate Answer (Flask instead of CNN)
    mismatch_answer = "Flask is a Python framework used for APIs and backend development."
    
    # Valid Candidate Answer (on-topic)
    valid_answer = "CNN architecture uses convolution layers to extract spatial features from images, followed by pooling layers for downsampling, and fully connected layers for final classification."
    
    print("==================================================")
    print("RUNNING TOPIC MISMATCH SYSTEM VERIFICATION")
    print("==================================================")
    
    print("\n--- CASE 1: UNRELATED RESPONSE (Flask API instead of CNN) ---")
    print(f"Question: '{question}'")
    print(f"Candidate Answer: '{mismatch_answer}'")
    
    # Evaluate
    result_mismatch = llm.evaluate_candidate_answer(
        question_text=question,
        correct_guideline=guideline_json,
        candidate_answer=mismatch_answer
    )
    
    print("\nScoring Output:")
    print(f"Overall Score: {result_mismatch['score']}")
    print("\nFeedback Generated:")
    print(result_mismatch['evaluation_feedback'])
    
    # Assertions to ensure strict penalty requirements are met
    feedback_lower = result_mismatch['evaluation_feedback'].lower()
    
    # Check scorecaps
    assert "technical knowledge**: 1.0/10" in feedback_lower, "Technical score must be capped at 1.0 for mismatch"
    assert "relevance**: 1.0/10" in feedback_lower, "Relevance score must be capped at 1.0 for mismatch"
    assert "completeness**: 0.0/10" in feedback_lower, "Completeness score must be capped at 0.0 for mismatch"
    assert result_mismatch['score'] == 1.0, "Overall score must be 1.0 for mismatch"
    
    # Check pointwise assessment content
    assert "unrelated to the asked question" in feedback_lower, "Feedback must explain that the answer is unrelated"
    assert "discusses" in feedback_lower, "Feedback must mention what candidate discussed"
    assert "missing" in feedback_lower, "Feedback must list missing concepts"
    
    print("\n[+] Case 1 Assertions PASSED successfully! Extreme mismatch penalty was applied perfectly.")
    
    print("\n--- CASE 2: CORRECT ON-TOPIC RESPONSE ---")
    print(f"Question: '{question}'")
    print(f"Candidate Answer: '{valid_answer}'")
    
    result_valid = llm.evaluate_candidate_answer(
        question_text=question,
        correct_guideline=guideline_json,
        candidate_answer=valid_answer
    )
    
    print("\nScoring Output:")
    print(f"Overall Score: {result_valid['score']}")
    print("\nFeedback Generated:")
    print(result_valid['evaluation_feedback'])
    
    # On-topic answers should score reasonably high
    assert result_valid['score'] >= 6.0, "On-topic response should score >= 6.0"
    assert "relevance**: 1.0/10" not in result_valid['evaluation_feedback'].lower(), "On-topic response should not be capped at 1.0"
    
    print("\n[+] Case 2 Assertions PASSED successfully! On-topic response scored high.")
    
    print("\n--- CASE 3: INVALID/MEANINGLESS RESPONSE (no) ---")
    invalid_answer = "no"
    print(f"Question: '{question}'")
    print(f"Candidate Answer: '{invalid_answer}'")
    
    result_invalid = llm.evaluate_candidate_answer(
        question_text=question,
        correct_guideline=guideline_json,
        candidate_answer=invalid_answer
    )
    
    print("\nScoring Output:")
    print(f"Overall Score: {result_invalid['score']}")
    print("\nFeedback Generated:")
    print(result_invalid['evaluation_feedback'])
    
    feedback_invalid_lower = result_invalid['evaluation_feedback'].lower()
    
    # Assertions to ensure zero-scores across all categories
    assert "technical knowledge**: 0.0/10" in feedback_invalid_lower, "Technical score must be 0.0 for invalid response"
    assert "relevance**: 0.0/10" in feedback_invalid_lower, "Relevance score must be 0.0 for invalid response"
    assert "communication clarity**: 0.0/10" in feedback_invalid_lower, "Clarity score must be 0.0 for invalid response"
    assert "completeness**: 0.0/10" in feedback_invalid_lower, "Completeness score must be 0.0 for invalid response"
    assert result_invalid['score'] == 0.0, "Overall score must be 0.0 for invalid response"
    
    # Check invalid assessment feedback content
    assert "does not address the asked question" in feedback_invalid_lower, "Feedback should say answer does not address question"
    assert "too short for technical evaluation" in feedback_invalid_lower, "Feedback should say response too short"
    assert "no relevant technical concepts" in feedback_invalid_lower, "Feedback should say no relevant concepts explained"
    assert "technical explanation is missing completely" in feedback_invalid_lower, "Feedback should say technical explanation is missing"
    
    print("\n[+] Case 3 Assertions PASSED successfully! Meaningless answer was rejected and scored zero perfectly.")
    
    print("\n==================================================")
    print("SYSTEM VERIFICATION CONCLUDED: 100% SUCCESS")
    print("==================================================")

if __name__ == "__main__":
    run_mismatch_test()
