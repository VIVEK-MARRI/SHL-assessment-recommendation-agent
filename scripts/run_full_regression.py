"""Full End-to-End Regression Orchestrator."""
import os
import sys
import time
import subprocess
import requests
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def wait_for_server(url: str, timeout: int = 30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{url}/health")
            if r.status_code == 200 and r.json().get("status") == "healthy":
                return True
        except requests.ConnectionError:
            pass
        time.sleep(1)
    return False

def run_script(script_name: str) -> bool:
    print(f"\n======================================")
    print(f"Executing: {script_name}")
    print(f"======================================")
    script_path = ROOT / "scripts" / script_name
    python_exe = sys.executable
    
    # We use subprocess.run with sys.executable to ensure we use the same venv
    result = subprocess.run([python_exe, str(script_path)], cwd=str(ROOT))
    if result.returncode != 0:
        print(f"\n[ERROR] {script_name} failed with exit code {result.returncode}")
        return False
    return True

def run_module(module_name: str) -> bool:
    print(f"\n======================================")
    print(f"Executing Module: {module_name}")
    print(f"======================================")
    python_exe = sys.executable
    result = subprocess.run([python_exe, "-m", module_name], cwd=str(ROOT))
    if result.returncode != 0:
        print(f"\n[ERROR] {module_name} failed with exit code {result.returncode}")
        return False
    return True

def main():
    print("Starting Full End-to-End Regression...")
    server_process = None
    success = True
    try:
        # 1. Start Server
        python_exe = sys.executable
        server_script = ROOT / "scripts" / "run_server.py"
        print("Starting FastAPI server in background...")
        server_process = subprocess.Popen([python_exe, str(server_script)], cwd=str(ROOT))
        
        if not wait_for_server("http://localhost:8000"):
            print("Server failed to start within timeout.")
            sys.exit(1)
            
        print("Server is healthy.")
        
        # 2. Run automated validation
        scripts = [
            "run_behavior_probes.py",
            "validate_llm_hallucinations.py"
        ]
        
        for script in scripts:
            if not run_script(script):
                success = False
                break
            time.sleep(15)
                
        # 3. Run official evaluation module
        if success:
            if not run_module("scripts.run_official_evaluation"):
                success = False
            time.sleep(5)
                
        # 4. Generate final report
        if success:
            if not run_script("generate_final_report.py"):
                success = False
                
    finally:
        if server_process:
            print("\nShutting down server...")
            server_process.terminate()
            server_process.wait(timeout=5)
            
    if not success:
        print("\nREGRESSION FAILED.")
        sys.exit(1)
    else:
        print("\nREGRESSION PASSED SUCCESSFULLY.")

if __name__ == "__main__":
    main()
