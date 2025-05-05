#!/usr/bin/env python3
"""
Python implementation of the test script for the 2-bilateral exercise.
This replaces the Bash test.sh script with a more portable Python version.

This script can be run in two ways:
1. From the solution directory - tests the solution implementation
2. From the parent directory - tests the user's implementation using the solution test harness
"""

import os
import sys
import time
import subprocess
import signal
import re
import socket
import argparse
from pathlib import Path
from datetime import datetime

class BilateralTester:
    def __init__(self):
        # Get the absolute path of the real script (not symlink)
        self.real_script_path = Path(os.path.realpath(__file__))
        self.solution_dir = self.real_script_path.parent
        self.parent_dir = self.solution_dir.parent
        
        # Determine execution mode based on the current directory
        self.current_dir = Path.cwd()
        
        # Check if we're running from the solution directory
        self.is_solution_mode = self.current_dir.samefile(self.solution_dir)
        
        # Determine script directory based on mode
        if self.is_solution_mode:
            print("Running in solution mode (testing solution implementation)")
            self.script_dir = self.solution_dir
            # Use solution's agent scripts
            self.party_script = self.script_dir / "party.py"
            self.counterparty_script = self.script_dir / "counterparty.py"
        else:
            print(f"Running in wrapper mode (testing implementation in {self.current_dir})")
            self.script_dir = self.current_dir
            # Look for agent scripts in current directory
            self.party_script = self.script_dir / "party.py"
            self.counterparty_script = self.script_dir / "counterparty.py"
        
        # Log files (should be in the directory where the test is run)
        self.logs_dir = self.script_dir / "logs"
        self.party_log = self.logs_dir / "party.log"
        self.counterparty_log = self.logs_dir / "counterparty.log"
        self.combined_log = self.logs_dir / "combined.log"
        
        # Process IDs for cleanup
        self.party_pid = None
        self.counterparty_pid = None
        
        # Test duration
        self.test_duration = 1.5  # in seconds
        
        # Start time for duration calculation
        self.start_time = None
        
        # Result tracking
        self.failures = 0
        
    def parse_arguments(self):
        """Parse command line arguments for custom agent scripts."""
        parser = argparse.ArgumentParser(description="Run Bilateral Agreement tests")
        parser.add_argument("agent_scripts", nargs="*", help="Custom agent scripts")
        
        args = parser.parse_args()
        
        # Process agent scripts only if provided
        if args.agent_scripts:
            # Override auto-detected scripts with explicitly provided ones
            for script_path in args.agent_scripts:
                # Convert to absolute path if it's not already
                script_path = Path(script_path).absolute()
                filename = script_path.name
                
                if "party" in filename and "counter" not in filename:
                    self.party_script = script_path
                    print(f"Using custom party script: {self.party_script}")
                elif "counterparty" in filename:
                    self.counterparty_script = script_path
                    print(f"Using custom counterparty script: {self.counterparty_script}")
                else:
                    print(f"Warning: Unrecognized agent script: {script_path}")
        
        # Verify scripts exist
        for name, script in [("Party", self.party_script), ("CounterParty", self.counterparty_script)]:
            if not Path(script).exists():
                print(f"Error: {name} script not found at {script}")
                sys.exit(1)
    
    def check_port_usage(self, ports=[8001, 8002, 8003, 8004]):
        """Check if any ports required for testing are already in use."""
        ports_in_use = False
        
        for port in ports:
            # Create a socket to test if port is in use
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:  # Port is in use
                print(f"⚠️ WARNING: Port {port} is in use")
                ports_in_use = True
        
        if ports_in_use:
            print("\n⚠️ ========================================================== ⚠️")
            print("  Some ports required for testing are already in use.")
            print("  This might cause test failures or unexpected behavior.")
            print("\n  To kill processes using these ports, you can run:")
            ports_str = ", ".join(map(str, ports))
            print(f"  lsof -i:{ports_str} | grep -v PID | awk '{{print $2}}' | xargs kill -9")
            print("  or for a specific port:")
            print("  lsof -ti:PORT_NUMBER | xargs kill -9")
            print("⚠️ ========================================================== ⚠️\n")
    
    def prepare_environment(self):
        """Set up the environment for testing."""
        # Create logs directory if it doesn't exist
        self.logs_dir.mkdir(exist_ok=True)
        
        # Clean up old logs
        for log_file in [self.party_log, self.counterparty_log, self.combined_log]:
            if log_file.exists():
                log_file.unlink()
            
            # Create empty log files
            with open(log_file, 'w') as f:
                pass
        
        # Setup PYTHONPATH to ensure modules can be found
        os.environ["PYTHONPATH"] = f"{self.script_dir}:{os.environ.get('PYTHONPATH', '')}"
        
        # Record start time
        self.start_time = time.time()
    
    def start_agents(self):
        """Start the party and counterparty agents."""
        # Start CounterParty first
        print(f"Starting CounterParty from: {self.counterparty_script}")
        counterparty_process = subprocess.Popen(
            ["python", str(self.counterparty_script)],
            stdout=open(self.counterparty_log, 'w'),
            stderr=subprocess.STDOUT,
            env={**os.environ, "BSPL_ADAPTER_DEBUG": "true"}
        )
        self.counterparty_pid = counterparty_process.pid
        
        # Wait for CounterParty to initialize
        time.sleep(0.5)
        
        # Start Party
        print(f"Starting Party from: {self.party_script}")
        party_process = subprocess.Popen(
            ["python", str(self.party_script)],
            stdout=open(self.party_log, 'w'),
            stderr=subprocess.STDOUT,
            env={**os.environ, "BSPL_ADAPTER_DEBUG": "true"}
        )
        self.party_pid = party_process.pid
        
        # Run for test_duration seconds to let the protocol execute
        print(f"Running bilateral agreement protocol for {self.test_duration} seconds...")
        time.sleep(self.test_duration)
    
    def stop_agents(self):
        """Stop the party and counterparty agents."""
        print("Stopping processes...")
        
        # Stop processes
        for pid in [self.counterparty_pid, self.party_pid]:
            if pid:
                try:
                    os.kill(pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
        
        # Wait for processes to terminate
        time.sleep(0.5)
        
        # Calculate end time and display duration
        end_time = time.time()
        duration = end_time - self.start_time
        print(f"Test ran for approximately {duration:.1f} seconds")
        
        # Check if logs exist and have content
        for log_file, name in [(self.party_log, "Party"), (self.counterparty_log, "CounterParty")]:
            if not log_file.exists() or log_file.stat().st_size == 0:
                print(f"ERROR: {name} log file is empty. Check if agent started properly.")
        
        # Combine logs for easier analysis
        with open(self.combined_log, 'w') as combined:
            for log_file in [self.party_log, self.counterparty_log]:
                if log_file.exists():
                    with open(log_file, 'r') as f:
                        combined.write(f.read())
        
        # Make sure we have something in the combined log
        if not self.combined_log.exists() or self.combined_log.stat().st_size == 0:
            print("ERROR: Combined log is empty. Tests will fail.")
    
    def check_pattern(self, pattern, description):
        """Check if a pattern exists in the combined log."""
        found = False
        pattern_context = None
        
        with open(self.combined_log, 'r') as f:
            content = f.read()
            found = re.search(pattern, content) is not None
            
            if not found:
                # Try to find some context for debugging
                pattern_base = pattern.split('.')[0] if '.' in pattern else pattern
                context_matches = re.findall(f".*{pattern_base}.*", content)
                if context_matches:
                    pattern_context = context_matches[:3]  # Just show a few matches
        
        if found:
            print(f"✅ PASS: {description}")
            return True
        else:
            print(f"❌ FAIL: {description}")
            print(f"      Pattern not found: {pattern}")
            if pattern_context:
                print("      Similar patterns found:")
                for line in pattern_context:
                    print(f"      {line.strip()}")
            else:
                print("      No similar patterns found")
            
            self.failures += 1
            return False
    
    def check_agent_errors(self):
        """Check for agent initialization errors in the logs."""
        error_patterns = [
            "KeyError", "ModuleNotFoundError", "ImportError", 
            "AttributeError", "SyntaxError"
        ]
        error_context = []
        
        with open(self.combined_log, 'r') as f:
            content = f.read()
            for pattern in error_patterns:
                matches = re.findall(f".*{pattern}.*", content)
                error_context.extend(matches)
        
        if error_context:
            print("⚠️ WARNING: Detected agent initialization errors:")
            for i, line in enumerate(error_context[:10]):  # Show at most 10 error lines
                print(line.strip())
                if i < len(error_context) - 1:
                    print("--")
            
            print("   Common causes:")
            print("   - Incomplete configuration.py (missing agent addresses or system configuration)")
            print("   - Missing or incorrect imports")
            print("   - Incomplete agent implementation")
            
            print("⚠️ Agent initialization errors detected - some tests may fail due to incomplete setup")
            print("--------------")
            return True
        
        return False
    
    def run_tests(self):
        """Run the actual tests on the protocol execution."""
        print("Running tests...")
        print("--------------")
        
        # Check for initialization errors first
        self.check_agent_errors()
        
        # Test bilateral agreement protocol flow (agent startup)
        self.check_pattern("Starting Party agent", "Party agent started")
        self.check_pattern("Starting CounterParty agent", "CounterParty agent started")
        
        # Check for message transmissions in the debug logs
        self.check_pattern("Sending .*Request", "CounterParty sent Request messages")
        self.check_pattern("Sending .*Propose", "Party sent Propose messages")
        self.check_pattern("Received message: .*Propose", "CounterParty received Propose messages")
        self.check_pattern("Sending .*Accept", "CounterParty sent Accept messages")
        self.check_pattern("Sending .*Reject", "CounterParty sent Reject messages")
        self.check_pattern("Received message: .*Accept", "Party received Accept messages")
        self.check_pattern("Received message: .*Reject", "Party received Reject messages")
        self.check_pattern("Sending .*Execute", "Party sent Execute messages")
        self.check_pattern("Sending .*Ack", "Party sent Acknowledge messages")
        self.check_pattern("Received message: .*Execute", "CounterParty received Execute messages")
        self.check_pattern("Received message: .*Ack", "CounterParty received Acknowledge messages")
        self.check_pattern("Sending .*Withdraw", "Party sent Withdraw messages")
        self.check_pattern("Received message: .*Withdraw", "CounterParty received Withdraw messages")
        
        # Check detailed message parameters
        self.check_pattern("Request.*ID.*type", "Request contains required parameters")
        self.check_pattern("Propose.*ID.*type.*proposal", "Propose contains required parameters")
        self.check_pattern("Accept.*ID.*proposal.*signature", "Accept contains required parameters")
        self.check_pattern("Reject.*ID.*proposal.*decision", "Reject contains required parameters")
        self.check_pattern("Execute.*ID.*signature.*closed", "Execute contains required parameters")
        self.check_pattern("Ack.*ID", "Acknowledge contains required parameters")
        self.check_pattern("Withdraw.*ID.*proposal.*decision", "Withdraw contains required parameters")
        
        # Count completed transactions
        executed_count = 0
        rejected_count = 0
        withdrawn_count = 0
        
        with open(self.combined_log, 'r') as f:
            content = f.read()
            executed_count = len(re.findall("Sending .*Execute", content))
            rejected_count = len(re.findall("Sending .*Ack", content))
            withdrawn_count = len(re.findall("Sending .*Withdraw", content))
        
        total_count = executed_count + rejected_count + withdrawn_count
        
        print("--------------")
        print("Protocol completion summary:")
        print(f"- Executed agreements: {executed_count}")
        print(f"- Rejected proposals: {rejected_count}")
        print(f"- Withdrawn proposals: {withdrawn_count}")
        print(f"- Total completed: {total_count}")
        
        if total_count >= 1:
            print("✅ PASS: At least one agreement completed")
        else:
            print("❌ FAIL: No agreements completed")
            self.failures += 1
    
    def print_summary(self):
        """Print test summary and log details."""
        print("--------------")
        print("Test Summary:")
        if self.failures == 0:
            print("✅ All tests passed!")
        else:
            print(f"❌ {self.failures} test(s) failed")
        
        print("--------------")
        print(f"Test logs written to {self.logs_dir}/ directory")
        
        # Show a summary of log sizes
        print("Log file sizes:")
        for log_file in [self.party_log, self.counterparty_log, self.combined_log]:
            if log_file.exists():
                print(f"{log_file}: {log_file.stat().st_size} bytes")
        
        print("Done.")
    
    def run(self):
        """Main method to run the test suite."""
        self.parse_arguments()
        self.check_port_usage()
        self.prepare_environment()
        self.start_agents()
        self.stop_agents()
        self.run_tests()
        self.print_summary()
        
        # Return exit code (0 for success, 1 for failure)
        return 1 if self.failures > 0 else 0


if __name__ == "__main__":
    tester = BilateralTester()
    sys.exit(tester.run())