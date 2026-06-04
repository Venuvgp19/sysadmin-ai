"""Command safety and whitelisting."""

import re
from typing import List, Set


class CommandSafety:
    """Ensures only safe, read-only and diagnostic commands are executed."""
    
    # Commands that are allowed without further inspection
    SAFE_COMMANDS: Set[str] = {
        # Diagnostics
        "top", "htop", "free", "df", "du", "ps", "ss", "netstat",
        "iostat", "vmstat", "mpstat", "uptime", "who", "w",
        "journalctl", "systemctl", "service", "dmesg",
        "cat", "head", "tail", "grep", "awk", "sed",
        "ls", "find", "stat", "file", "lsof",
        "ping", "curl", "nslookup", "dig", "traceroute",
        "ip", "ifconfig", "route", "iptables", "nft",
        # Windows equivalents
        "wmic", "tasklist", "netstat", "sc", "systeminfo",
        "ipconfig", "netsh", "get-process", "get-service",
        # Read-only
        "less", "more", "cut", "sort", "uniq", "wc",
        "sha256sum", "md5sum",
        # Nginx / Apache / DB checks
        "nginx", "apachectl", "mysql", "pg_isready", "psql",
        # Python
        "python", "python3", "pip", "pip3",
    }
    
    # Patterns that are absolutely blocked
    DANGEROUS_PATTERNS: List[str] = [
        r"\brm\s+-rf?\b", r"\bdd\b", r"\bmkfs\b", r"\bfdisk\b",
        r"\bformat\b", r"\bshred\b", r"\b wipe\b",
        r"[>;]\s*rm", r"\beval\b", r"\bexec\b",
        r"\bsudo\b", r"\bsu\b", r"\bpasswd\b",
        r"\buserdel\b", r"\bgroupdel\b",
        r"[|].*rm", r"[|].*dd",
    ]
    
    # Characters that suggest shell metacharacters for redirection/destruction
    # Note: '|' is allowed for filtering (e.g., findstr, grep, head, tail, sort)
    # because these are read-only diagnostic patterns. Destructive pipe patterns
    # are already blocked by DANGEROUS_PATTERNS.
    BLOCKED_CHARS: Set[str] = {">", "<", "&", ";", "$", "`", "\x00"}
    
    # Commands that are safe to appear on the right side of a pipe
    SAFE_PIPE_COMMANDS: Set[str] = {
        "findstr", "find", "grep", "head", "tail", "sort", "uniq", "wc",
        "awk", "sed", "cut", "tr", "more", "less", "select-string", "select"
    }
    
    def is_safe(self, command: str) -> bool:
        """Return True if the command passes safety checks."""
        command = command.strip()
        if not command:
            return False
        
        # Block dangerous patterns
        lower_cmd = command.lower()
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, lower_cmd):
                return False
        
        # Block shell metacharacters (except '|' which is handled below)
        for char in command:
            if char in self.BLOCKED_CHARS:
                return False
        
        # Check if command uses pipes - validate pipe targets are safe
        if "|" in command:
            parts = [p.strip() for p in command.split("|")]
            # First command must be safe
            first_base = parts[0].split()[0].lower().replace(".exe", "")
            if first_base not in self.SAFE_COMMANDS:
                return False
            # All subsequent commands must be in safe pipe commands
            for part in parts[1:]:
                if not part:
                    continue
                pipe_base = part.split()[0].lower().replace(".exe", "")
                if pipe_base not in self.SAFE_PIPE_COMMANDS:
                    return False
            return True
        
        # Allow if base command is in safe list
        base = command.split()[0].lower()
        # Strip common extensions like .exe on Windows
        base = base.replace(".exe", "")
        if base in self.SAFE_COMMANDS:
            return True
        
        # Default deny
        return False
