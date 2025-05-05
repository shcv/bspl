#!/usr/bin/env python3
"""
Python implementation of the test script for the 4-logistics exercise.
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

class LogisticsTester:
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
            self.merchant_script = self.script_dir / "merchant.py"
            self.labeler_script = self.script_dir / "labeler.py"
            self.wrapper_script = self.script_dir / "wrapper.py"
            self.packer_script = self.script_dir / "packer.py"
        else:
            print(f"Running in wrapper mode (testing implementation in {self.current_dir})")
            self.script_dir = self.current_dir
            # Look for agent scripts in current directory
            self.merchant_script = self.script_dir / "merchant.py"
            self.labeler_script = self.script_dir / "labeler.py"
            self.wrapper_script = self.script_dir / "wrapper.py"
            self.packer_script = self.script_dir / "packer.py"
        
        # Log files (should be in the directory where the test is run)
        self.logs_dir = self.script_dir / "logs"
        self.merchant_log = self.logs_dir / "merchant.log"
        self.labeler_log = self.logs_dir / "labeler.log"
        self.wrapper_log = self.logs_dir / "wrapper.log"
        self.packer_log = self.logs_dir / "packer.log"
        self.combined_log = self.logs_dir / "combined.log"
        
        # Process IDs for cleanup
        self.merchant_pid = None
        self.labeler_pid = None
        self.wrapper_pid = None
        self.packer_pid = None
        
        # Result tracking
        self.failures = 0
    
    def parse_arguments(self):
        """Parse command line arguments for custom agent scripts."""
        parser = argparse.ArgumentParser(description="Run Logistics Protocol tests")
        parser.add_argument("agent_scripts", nargs="*", help="Custom agent scripts")
        
        args = parser.parse_args()
        
        # Process agent scripts only if provided
        if args.agent_scripts:
            # Override auto-detected scripts with explicitly provided ones
            for script_path in args.agent_scripts:
                # Convert to absolute path if it's not already
                script_path = Path(script_path).absolute()
                filename = script_path.name
                
                if "merchant" in filename:
                    self.merchant_script = script_path
                    print(f"Using custom merchant script: {self.merchant_script}")
                elif "labeler" in filename:
                    self.labeler_script = script_path
                    print(f"Using custom labeler script: {self.labeler_script}")
                elif "wrapper" in filename:
                    self.wrapper_script = script_path
                    print(f"Using custom wrapper script: {self.wrapper_script}")
                elif "packer" in filename:
                    self.packer_script = script_path
                    print(f"Using custom packer script: {self.packer_script}")
                else:
                    print(f"Warning: Unrecognized agent script: {script_path}")
        
        # Verify scripts exist
        for name, script in [
            ("Merchant", self.merchant_script),
            ("Labeler", self.labeler_script),
            ("Wrapper", self.wrapper_script),
            ("Packer", self.packer_script)
        ]:
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
        for log_file in [self.merchant_log, self.labeler_log, self.wrapper_log, self.packer_log, self.combined_log]:
            if log_file.exists():
                log_file.unlink()
            
            # Create empty log files
            with open(log_file, 'w') as f:
                pass
        
        # Setup PYTHONPATH to ensure modules can be found
        os.environ["PYTHONPATH"] = f"{self.script_dir}:{os.environ.get('PYTHONPATH', '')}"
    
    def start_agents(self):
        """Start all the logistics agents."""
        print("Starting logistics agents...")
        
        # Start Labeler
        print(f"Starting Labeler from: {self.labeler_script}")
        labeler_process = subprocess.Popen(
            ["python", str(self.labeler_script)],
            stdout=open(self.labeler_log, 'w'),
            stderr=subprocess.STDOUT,
            env={**os.environ, "BSPL_ADAPTER_DEBUG": "true"}
        )
        self.labeler_pid = labeler_process.pid
        
        # Start Wrapper
        print(f"Starting Wrapper from: {self.wrapper_script}")
        wrapper_process = subprocess.Popen(
            ["python", str(self.wrapper_script)],
            stdout=open(self.wrapper_log, 'w'),
            stderr=subprocess.STDOUT,
            env={**os.environ, "BSPL_ADAPTER_DEBUG": "true"}
        )
        self.wrapper_pid = wrapper_process.pid
        
        # Start Packer
        print(f"Starting Packer from: {self.packer_script}")
        packer_process = subprocess.Popen(
            ["python", str(self.packer_script)],
            stdout=open(self.packer_log, 'w'),
            stderr=subprocess.STDOUT,
            env={**os.environ, "BSPL_ADAPTER_DEBUG": "true"}
        )
        self.packer_pid = packer_process.pid
        
        # Wait for support agents to initialize
        time.sleep(1)
        
        # Start Merchant (which initiates the protocol)
        print(f"Starting Merchant from: {self.merchant_script}")
        merchant_process = subprocess.Popen(
            ["python", str(self.merchant_script)],
            stdout=open(self.merchant_log, 'w'),
            stderr=subprocess.STDOUT,
            env={**os.environ, "BSPL_ADAPTER_DEBUG": "true"}
        )
        self.merchant_pid = merchant_process.pid
        
        # Run for 4 seconds to let the protocol execute
        print("Running logistics protocol for 4 seconds...")
        time.sleep(4)
    
    def stop_agents(self):
        """Stop all the logistics agents."""
        print("Stopping processes...")
        
        # Stop processes
        for pid in [self.labeler_pid, self.wrapper_pid, self.packer_pid, self.merchant_pid]:
            if pid:
                try:
                    os.kill(pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
        
        # Wait for processes to terminate
        time.sleep(1)
        
        # Combine logs for easier analysis
        with open(self.combined_log, 'w') as combined:
            for log_file in [self.merchant_log, self.labeler_log, self.wrapper_log, self.packer_log]:
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
        
        # Test logistics protocol flow
        self.check_pattern("Starting Merchant agent", "Merchant agent started")
        self.check_pattern("Starting Labeler agent", "Labeler agent started")
        self.check_pattern("Starting Wrapper agent", "Wrapper agent started")
        self.check_pattern("Starting Packer agent", "Packer agent started")
        
        # Check for message transmissions in the debug logs
        # Merchant to Labeler communication
        self.check_pattern("Sending.*RequestLabel", "Merchant sent label requests")
        self.check_pattern("Received message: RequestLabel", "Labeler received label requests")
        self.check_pattern("Sending.*Labeled", "Labeler sent labels")
        self.check_pattern("Received message: Labeled", "Packer received labels")
        
        # Merchant to Wrapper communication
        self.check_pattern("Sending.*RequestWrapping", "Merchant sent wrap requests")
        self.check_pattern("Received message: RequestWrapping", "Wrapper received wrap requests")
        self.check_pattern("Sending.*Wrapped", "Wrapper sent wrapped items")
        self.check_pattern("Received message: Wrapped", "Packer received wrapped items")
        
        # Packer to Merchant communication
        self.check_pattern("Sending .*Packed", "Packer sent packed confirmations")
        self.check_pattern("Received message: .*Packed", "Merchant received packed confirmations")
        
        # Check detailed message parameters
        self.check_pattern("RequestLabel.*orderID.*address", "LabelRequest contains required parameters")
        self.check_pattern("Labeled.*orderID.*label", "Label contains required parameters")
        self.check_pattern("RequestWrapping.*itemID.*item", "WrapRequest contains required parameters")
        self.check_pattern("Wrapped.*itemID.*wrapping", "WrappedItem contains required parameters")
        self.check_pattern("Packed.*orderID.*itemID.*status", "Packed contains required parameters")
        
        # Count completed transactions
        packed_items = 0
        label_requests = 0
        wrap_requests = 0
        
        with open(self.combined_log, 'r') as f:
            content = f.read()
            packed_items = len(re.findall("Sending .*Packed", content))
            label_requests = len(re.findall("Sending.*RequestLabel", content))
            wrap_requests = len(re.findall("Sending.*RequestWrapping", content))
        
        print("--------------")
        print("Protocol completion summary:")
        print(f"- Label requests sent: {label_requests}")
        print(f"- Wrap requests sent: {wrap_requests}")
        print(f"- Items packed: {packed_items}")
        
        if packed_items >= 1:
            print("✅ PASS: At least one item was packed completely")
        else:
            print("❌ FAIL: No items were packed")
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
        for log_file in [self.merchant_log, self.labeler_log, self.wrapper_log, self.packer_log, self.combined_log]:
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
    tester = LogisticsTester()
    sys.exit(tester.run())