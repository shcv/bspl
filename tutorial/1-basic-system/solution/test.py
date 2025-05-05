#!/usr/bin/env python3
"""
Python implementation of the test script for the 1-basic-system exercise.
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

class BasicSystemTester:
    def __init__(self):
        # Get the absolute path of the real script (not symlink)
        self.real_script_path = Path(os.path.realpath(__file__))
        self.solution_dir = self.real_script_path.parent
        self.parent_dir = self.solution_dir.parent
        
        # Determine execution mode based on the current directory
        self.current_dir = Path.cwd()
        
        # Get the path used to invoke this script
        invoke_path = Path(sys.argv[0])
        
        # Check if we're running from the solution directory directly or through a symlink from parent
        self.is_solution_mode = (self.current_dir.samefile(self.solution_dir) or 
                                "solution" in invoke_path.parts)
        
        # Determine script directory based on mode
        if self.is_solution_mode:
            print("Running in solution mode (testing solution implementation)")
            self.script_dir = self.solution_dir
            # Use solution's agent scripts
            self.buyer_script = self.script_dir / "buyer.py"
            self.seller_script = self.script_dir / "seller.py"
        else:
            print(f"Running in wrapper mode (testing implementation in {self.current_dir})")
            self.script_dir = self.current_dir
            # Look for agent scripts in current directory
            self.buyer_script = self.script_dir / "buyer.py"
            self.seller_script = self.script_dir / "seller.py"
        
        # Log files (should be in the directory where the test is run)
        self.logs_dir = self.script_dir / "logs"
        self.buyer_log = self.logs_dir / "buyer.log"
        self.seller_log = self.logs_dir / "seller.log"
        self.combined_log = self.logs_dir / "combined.log"
        
        # Process IDs for cleanup
        self.buyer_pid = None
        self.seller_pid = None
        
        # Result tracking
        self.failures = 0
        
    def parse_arguments(self):
        """Parse command line arguments for custom agent scripts."""
        parser = argparse.ArgumentParser(description="Run Basic System tests")
        parser.add_argument("agent_scripts", nargs="*", help="Custom agent scripts")
        
        args = parser.parse_args()
        
        # Process agent scripts only if provided
        if args.agent_scripts:
            # Override auto-detected scripts with explicitly provided ones
            for script_path in args.agent_scripts:
                # Convert to absolute path if it's not already
                script_path = Path(script_path).absolute()
                filename = script_path.name
                
                if "buyer" in filename:
                    self.buyer_script = script_path
                    print(f"Using custom buyer script: {self.buyer_script}")
                elif "seller" in filename:
                    self.seller_script = script_path
                    print(f"Using custom seller script: {self.seller_script}")
                else:
                    print(f"Warning: Unrecognized agent script: {script_path}")
        
        # Verify scripts exist
        for name, script in [("Buyer", self.buyer_script), ("Seller", self.seller_script)]:
            if not Path(script).exists():
                print(f"Error: {name} script not found at {script}")
                sys.exit(1)
    
    def check_port_usage(self, ports=[8001, 8002]):
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
        for log_file in [self.buyer_log, self.seller_log, self.combined_log]:
            if log_file.exists():
                log_file.unlink()
            
            # Create empty log files
            with open(log_file, 'w') as f:
                pass
        
        # Setup PYTHONPATH to ensure modules can be found
        os.environ["PYTHONPATH"] = f"{self.script_dir}:{os.environ.get('PYTHONPATH', '')}"
    
    def resolve_script_path(self, script_name):
        """Resolve the full path to an agent script."""
        script_path = Path(script_name)
        
        # Handle absolute path
        if script_path.is_absolute():
            return script_path
        
        # Handle relative path
        if script_path.parts[0] in ['.', '..'] or '/' in str(script_path):
            # Assuming relative to script_dir
            return self.script_dir / script_path
        
        # Handle just script name
        return self.script_dir / script_path
    
    def start_agents(self):
        """Start the buyer and seller agents."""
        # Resolve paths
        seller_path = self.resolve_script_path(self.seller_script)
        buyer_path = self.resolve_script_path(self.buyer_script)
        
        # Start Seller
        print(f"Starting Seller from: {seller_path}")
        seller_process = subprocess.Popen(
            ["python", str(seller_path)],
            stdout=open(self.seller_log, 'w'),
            stderr=subprocess.STDOUT,
            env={**os.environ, "BSPL_ADAPTER_DEBUG": "true"}
        )
        self.seller_pid = seller_process.pid
        
        # Wait for Seller to initialize
        time.sleep(1)
        
        # Start Buyer
        print(f"Starting Buyer from: {buyer_path}")
        buyer_process = subprocess.Popen(
            ["python", str(buyer_path)],
            stdout=open(self.buyer_log, 'w'),
            stderr=subprocess.STDOUT,
            env={**os.environ, "BSPL_ADAPTER_DEBUG": "true"}
        )
        self.buyer_pid = buyer_process.pid
        
        # Run for 3 seconds to let the protocol execute
        print("Running purchase protocol for 3 seconds...")
        time.sleep(3)
    
    def stop_agents(self):
        """Stop the buyer and seller agents."""
        print("Stopping processes...")
        
        # Stop processes
        for pid in [self.seller_pid, self.buyer_pid]:
            if pid:
                try:
                    os.kill(pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
        
        # Wait for processes to terminate
        time.sleep(1)
        
        # Combine logs for easier analysis
        with open(self.combined_log, 'w') as combined:
            for log_file in [self.seller_log, self.buyer_log]:
                if log_file.exists():
                    with open(log_file, 'r') as f:
                        combined.write(f.read())
    
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
        
        # Test purchase protocol flow (agent startup)
        self.check_pattern("Starting Buyer agent", "Buyer agent started")
        self.check_pattern("Starting Seller agent", "Seller agent started")
        
        # Check for message transmissions in the debug logs
        self.check_pattern("Received message: .*RFQ", "Seller received RFQ messages")
        self.check_pattern("Sending .*Quote", "Seller sent quotes")
        self.check_pattern("Received message: .*Quote", "Buyer received quotes")
        self.check_pattern("Sending .*Buy", "Buyer sent Buy messages")
        self.check_pattern("Sending .*Reject", "Buyer sent Reject messages")
        self.check_pattern("Received message: .*Buy", "Seller received Buy messages")
        self.check_pattern("Received message: .*Reject", "Seller received Reject messages")
        
        # Check detailed message parameters
        self.check_pattern("RFQ.*ID.*item", "RFQ contains required parameters")
        self.check_pattern("Quote.*ID.*item.*price", "Quote contains required parameters")
        self.check_pattern("Buy.*ID.*item.*price.*done", "Buy contains required parameters")
        self.check_pattern("Reject.*ID.*price.*done", "Reject contains required parameters")
        
        # Count completed transactions
        buy_count = 0
        reject_count = 0
        
        with open(self.combined_log, 'r') as f:
            content = f.read()
            buy_count = len(re.findall("Sending .*Buy", content))
            reject_count = len(re.findall("Sending .*Reject", content))
        
        total_count = buy_count + reject_count
        
        print("--------------")
        print("Protocol completion summary:")
        print(f"- Accepted offers: {buy_count}")
        print(f"- Rejected offers: {reject_count}")
        print(f"- Total transactions: {total_count}")
        
        if total_count >= 1:
            print("✅ PASS: At least one transaction completed")
        else:
            print("❌ FAIL: No transactions completed")
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
        for log_file in [self.buyer_log, self.seller_log, self.combined_log]:
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
    tester = BasicSystemTester()
    sys.exit(tester.run())