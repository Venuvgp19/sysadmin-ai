#!/usr/bin/env python3
"""SysAdmin AI Agent — Local Linux/Windows Troubleshooting Agent"""

import os
import sys
import json
import subprocess
import time
import platform
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from agent.settings import AGENT_CONFIG
from agent.safety import CommandSafety
from agent.knowledge_manager import KnowledgeManager


class SysAdminAgent:
    def __init__(self, model_name: str = None):
        self.model_name = model_name or AGENT_CONFIG.get("model", "qwen2.5:7b")
        self.base_dir = PROJECT_ROOT
        self.logs_dir = self.base_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        self.safety = CommandSafety()
        self.knowledge = KnowledgeManager()
        self.knowledge._init_db()  # Eager-init so collection is ready
        
        # Try to initialize Ollama; fall back gracefully if unavailable
        self.llm = None
        self.embeddings = None
        self._init_ollama()
    
    def _init_ollama(self):
        """Initialize Ollama LLM and embeddings if available."""
        try:
            from langchain_ollama import OllamaLLM, OllamaEmbeddings
            
            host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
            self.llm = OllamaLLM(
                model=self.model_name,
                temperature=0.3,
                base_url=host,
            )
            self.embeddings = OllamaEmbeddings(
                model="nomic-embed-text",
                base_url=host,
            )
            print(f"[OK] Connected to Ollama at {host} (model: {self.model_name})")
        except Exception as e:
            print(f"[!] Ollama not available: {e}")
            print("    Agent will run in diagnostic-only mode (no AI analysis).")
    
    def log_action(self, action: str, result: str, status: str = "info"):
        """Log all agent actions."""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "action": action,
            "result": str(result)[:2000],
            "status": status,
        }
        log_file = self.logs_dir / f"agent-{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def run_command(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute a safe system command."""
        if not self.safety.is_safe(command):
            return {
                "success": False,
                "output": "",
                "error": f"Command blocked by safety policy: {command}",
                "command": command,
            }
        
        # On Windows, ensure shell=True uses cmd.exe for pipes/findstr
        is_windows = platform.system() == "Windows"
        
        try:
            if is_windows:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=str(self.base_dir),
                    executable=None,  # uses default shell (cmd.exe)
                )
            else:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=str(self.base_dir),
                )
            output = result.stdout + result.stderr
            success = result.returncode == 0
            self.log_action(command, output, "success" if success else "error")
            return {
                "success": success,
                "output": output[:5000],
                "error": result.stderr if not success else "",
                "command": command,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": f"Command timed out after {timeout}s",
                "command": command,
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "command": command,
            }
    
    def analyze_system(self) -> Dict[str, Any]:
        """Run comprehensive system diagnostics."""
        diagnostics = {}
        is_windows = platform.system() == "Windows"
        
        if is_windows:
            commands = [
                ("cpu", "wmic cpu get loadpercentage /value"),
                ("memory", "wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /value"),
                ("disk", "wmic logicaldisk get size,freespace,caption /value"),
                ("processes", "tasklist /fo table"),
                ("services", "sc query | findstr SERVICE_NAME"),
                ("network", "netstat -an | findstr LISTENING"),
                ("uptime", "systeminfo | find \"Boot Time\""),
            ]
        else:
            commands = [
                ("cpu", "top -bn1 | head -20"),
                ("memory", "free -h"),
                ("disk", "df -h"),
                ("processes", "ps aux --sort=-%mem | head -20"),
                ("network", "ss -tlnp"),
                ("services", "systemctl list-units --type=service --state=failed"),
                ("logs", "journalctl --since \"1 hour ago\" --no-pager | tail -50"),
                ("load", "uptime"),
            ]
        
        for name, cmd in commands:
            diagnostics[name] = self.run_command(cmd)
            time.sleep(0.1)
        
        return diagnostics
    
    def diagnose(self, problem: str) -> Dict[str, Any]:
        """Main diagnosis method."""
        print(f"\n[+] Analyzing: {problem}")
        print("=" * 60)
        
        print("\n[*] Gathering system diagnostics...")
        diagnostics = self.analyze_system()
        
        context = self._build_context(diagnostics)
        
        # Knowledge base lookup
        kb_context = ""
        try:
            kb_results = self.knowledge.search(problem, k=3)
            kb_context = "\n".join(kb_results)
        except Exception as e:
            kb_context = f"Knowledge base unavailable: {e}"
        
        # If LLM available, get AI analysis; otherwise use rule-based output
        if self.llm:
            print("\n[AI] Querying AI model...")
            try:
                analysis = self._llm_analyze(problem, context, kb_context)
            except Exception as e:
                print(f"[!] LLM query failed: {e}")
                analysis = self._rule_based_analysis(problem, context, kb_context)
        else:
            analysis = self._rule_based_analysis(problem, context, kb_context)
        
        self.log_action(f"DIAGNOSE: {problem}", analysis, "success")
        
        return {
            "problem": problem,
            "timestamp": datetime.now().isoformat(),
            "diagnostics": diagnostics,
            "analysis": analysis,
            "model": self.model_name if self.llm else "none",
        }
    
    def _build_context(self, diagnostics: Dict) -> str:
        """Build readable context from diagnostics."""
        lines = []
        for name, result in diagnostics.items():
            if result.get("success") and result.get("output"):
                lines.append(f"\n--- {name.upper()} ---")
                lines.append(result["output"][:1000])
        return "\n".join(lines)
    
    def _llm_analyze(self, problem: str, context: str, kb_context: str) -> str:
        """Use LLM to analyze the problem."""
        prompt = f"""You are an expert system administrator. Analyze the following system diagnostics and provide a clear diagnosis with actionable fixes.

PROBLEM: {problem}

SYSTEM DIAGNOSTICS:
{context}

RELEVANT KNOWLEDGE:
{kb_context}

Provide your response in this exact format:

## Diagnosis
[What you believe is the root cause]

## Evidence
[Specific data points from the diagnostics that support your conclusion]

## Recommended Fixes
1. [First fix with exact command]
2. [Second fix if applicable]
3. [Third fix if applicable]

## Prevention
[How to prevent this in the future]
"""
        return self.llm.invoke(prompt)
    
    def _rule_based_analysis(self, problem: str, context: str, kb_context: str) -> str:
        """Fallback analysis when LLM is unavailable."""
        lines = [
            "## Diagnosis",
            f"Running in diagnostic-only mode (Ollama unavailable). Problem reported: {problem}",
            "",
            "## Evidence",
            "System diagnostics collected. Key findings:",
        ]
        # Simple keyword-based suggestions
        problem_lower = problem.lower()
        if "disk" in problem_lower or "space" in problem_lower:
            lines.append("- Check disk usage in diagnostics above.")
            lines.append("- Consider cleaning temp files and logs.")
        if "cpu" in problem_lower or "slow" in problem_lower:
            lines.append("- Review top CPU consumers in process list.")
        if "memory" in problem_lower or "oom" in problem_lower:
            lines.append("- Check memory usage and consider restarting heavy services.")
        if "network" in problem_lower or "connect" in problem_lower:
            lines.append("- Verify network interfaces and listening ports.")
        lines.append("")
        lines.append("## Recommended Fixes")
        lines.append("1. Review diagnostics output above.")
        lines.append("2. Install and start Ollama for AI-powered analysis.")
        lines.append("3. Consult knowledge base documents in the knowledge/ folder.")
        lines.append("")
        lines.append("## Prevention")
        lines.append("- Set up regular monitoring and alerting.")
        lines.append("- Keep Ollama running for AI-assisted troubleshooting.")
        return "\n".join(lines)


def main():
    """CLI entry point."""
    print("\n" + "=" * 60)
    print("  [BOT] SysAdmin AI -- System Troubleshooting Agent")
    print("=" * 60 + "\n")
    
    agent = SysAdminAgent()
    
    print("Agent initialized. Type your problem or 'quit' to exit.")
    print("Examples: 'server is slow', 'disk is full', 'ssh not working'")
    print("-" * 60 + "\n")
    
    while True:
        try:
            problem = input("[>] Problem: ").strip()
            
            if problem.lower() in ["quit", "exit", "q"]:
                print("\n[X] Goodbye! Logs saved to sysadmin-ai/logs/")
                break
            
            if not problem:
                continue
            
            result = agent.diagnose(problem)
            
            print("\n" + "=" * 60)
            print(result["analysis"])
            print("=" * 60 + "\n")
            
        except KeyboardInterrupt:
            print("\n\n[X] Interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n[!] Error: {e}\n")


if __name__ == "__main__":
    main()
