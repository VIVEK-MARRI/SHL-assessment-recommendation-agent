"""Runner script for the official SHL Evaluation."""

import sys
from evaluation.official_evaluator import OfficialEvaluator

def main():
    print("Initializing Official Evaluator...")
    evaluator = OfficialEvaluator()
    
    print("Running evaluations...")
    result = evaluator.evaluate()
    
    print("\n--- EVALUATION RESULTS ---")
    print(f"Hard Evaluation Pass Rate:   {result.hard_eval_pass_rate * 100:.2f}%")
    print(f"Mean Recall@10:              {result.mean_recall_at_10:.4f}")
    print(f"Behavior Probe Pass Rate:    {result.behavior_probe_pass_rate * 100:.2f}%")
    print(f"Average Retrieval Latency:   {result.average_retrieval_latency_ms:.2f} ms")
    print(f"Total Cases:                 {result.total_cases}")
    
    evaluator.write_reports(result)
    print("\nReports written to:")
    print("- FINAL_EVALUATION_REPORT.md")
    print("- reports/retrieval_report.md")
    
    if result.hard_eval_pass_rate < 1.0 or result.behavior_probe_pass_rate < 1.0:
        print("\n[WARNING] Some strict criteria failed! Check FINAL_EVALUATION_REPORT.md for failures.")

if __name__ == "__main__":
    main()
