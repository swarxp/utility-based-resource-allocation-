import numpy as np
from collections import defaultdict

class ResourceAllocationGame:
    def __init__(self, resources, processes):
        """
        Initialize the game with available resources and process requirements
        
        resources: Dictionary mapping resource names to available units
        processes: List of dictionaries with process details
        """
        self.available = resources.copy()  # Available resources
        self.max_resources = resources.copy()  # Maximum available resources
        self.process_count = len(processes)
        self.resource_count = len(resources)
        self.resource_names = list(resources.keys())
        
        # Initialize process data structures
        self.processes = processes
        self.allocated = {}  # Currently allocated resources
        self.need = {}  # Resources still needed
        
        # Initialize allocation matrices
        for p in processes:
            pid = p['pid']
            self.allocated[pid] = {r: 0 for r in self.resource_names}
            self.need[pid] = {r: p['max_claim'].get(r, 0) for r in self.resource_names}
    
    def is_safe_state(self):
    
        # Create working copies
        work = self.available.copy()
        finish = {p['pid']: False for p in self.processes}
        sequence = []
        
        # Try to find a safe sequence
        found = True
        while found:
            found = False
            for p in self.processes:
                pid = p['pid']
                if not finish[pid]:
                    # Check if this process's needs can be satisfied
                    if all(self.need[pid][r] <= work[r] for r in self.resource_names):
                        # This process can complete
                        found = True
                        finish[pid] = True
                        sequence.append(pid)
                        
                        # Return resources to the pool
                        for r in self.resource_names:
                            work[r] += self.allocated[pid][r]
                        break
            
        # If all processes are finished, we have a safe sequence
        if all(finish.values()):
            return True, sequence
        else:
            return False, None
    
    def utility_function(self, pid):
        """
        Calculate utility for a process based on:
        - Resources already allocated
        - Priority/urgency of the process
        - Waiting time
        """
        process = next((p for p in self.processes if p['pid'] == pid), None)
        if not process:
            return 0
            
        # Calculate allocation ratio (how much of what it needs does it have)
        total_needed = sum(process['max_claim'].values())
        total_allocated = sum(self.allocated[pid].values())
        allocation_ratio = total_allocated / total_needed if total_needed > 0 else 0
        
        # Factor in process priority
        priority = process.get('priority', 1)
        
        # Calculate waiting time penalty
        waiting_time = process.get('waiting_time', 0)
        waiting_penalty = 1 / (1 + waiting_time) if waiting_time > 0 else 1
        
        # Return composite utility score
        return (allocation_ratio * 0.5 + priority * 0.3) * waiting_penalty
    
    def next_best_allocation(self):
        """
        Determine the next best allocation using game theory approach
        Returns: (pid, resource, amount) or None if no safe allocation possible
        """
        best_move = None
        best_utility = -1
        
        # For each process that still needs resources
        for process in self.processes:
            pid = process['pid']
            
            # For each resource type the process needs
            for resource in self.resource_names:
                current_need = self.need[pid][resource]
                
                # Skip if process doesn't need this resource
                if current_need <= 0:
                    continue
                
                # Try allocating 1 unit (could optimize to allocate more)
                if self.available[resource] >= 1:
                    # Simulate the allocation
                    self.available[resource] -= 1
                    self.allocated[pid][resource] += 1
                    self.need[pid][resource] -= 1
                    
                    # Check if this leads to a safe state
                    is_safe, _ = self.is_safe_state()
                    
                    # Calculate utility of this move
                    if is_safe:
                        utility = self.utility_function(pid)
                        if utility > best_utility:
                            best_utility = utility
                            best_move = (pid, resource, 1)
                    
                    # Undo the simulation
                    self.available[resource] += 1
                    self.allocated[pid][resource] -= 1
                    self.need[pid][resource] += 1
        
        return best_move
    
    def build_safe_schedule(self):
        """
        Build a complete safe allocation schedule using game theory optimization
        Returns: (strategy_description, allocation_sequence, execution_sequence)
        """
        allocation_sequence = []
        execution_sequence = []
        
        # Loop until all processes have all their resources or we can't make progress
        progress = True
        completed_processes = set()
        strategy = "BANKER'S ALGORITHM WITH UTILITY OPTIMIZATION"
        
        while progress and len(completed_processes) < len(self.processes):
            # Find next optimal allocation
            next_move = self.next_best_allocation()
            
            if not next_move:
                # No more safe allocations possible
                progress = False
                continue
            
            # Apply the allocation
            pid, resource, amount = next_move
            self.available[resource] -= amount
            self.allocated[pid][resource] += amount
            self.need[pid][resource] -= amount
            allocation_sequence.append((pid, resource, amount))
            
            # Check if process is fully allocated
            process = next((p for p in self.processes if p['pid'] == pid), None)
            if all(self.need[pid][r] == 0 for r in self.resource_names):
                # This process can now execute and release resources
                if pid not in completed_processes:
                    completed_processes.add(pid)
                    execution_sequence.append(pid)
                    
                    # Return resources to pool
                    for r in self.resource_names:
                        self.available[r] += self.allocated[pid][r]
                        self.allocated[pid][r] = 0
        
        # Check if all processes were allocated
        if len(completed_processes) == len(self.processes):
            return strategy, allocation_sequence, execution_sequence
        else:
            # We couldn't find a complete safe schedule
            return "DEADLOCK UNAVOIDABLE", allocation_sequence, execution_sequence

def get_resources_from_user():
    """Get resource availability from the user with resource names R1, R2, etc."""
    print("\n=== Resource Configuration ===")
    num_resources = int(input("Enter number of resources: "))
    
    resources = {}
    for i in range(1, num_resources + 1):
        name = f"R{i}"
        units = int(input(f"Enter units available for {name}: "))
        resources[name] = units
    
    return resources

def get_processes_from_user(resource_names):
    """Get process details from the user with process names P1, P2, etc."""
    print("\n=== Process Configuration ===")
    num_processes = int(input("Enter number of processes: "))
    
    processes = []
    for i in range(1, num_processes + 1):
        pid = f"P{i}"
        process = {"pid": pid, "max_claim": {}, "priority": 1, "waiting_time": 0}
        print(f"\nProcess {pid} Configuration:")
        
        print(f"Available resources: {list(resource_names)}")
        for resource in resource_names:
            max_need = int(input(f"Maximum units of {resource} needed by {pid}: "))
            process["max_claim"][resource] = max_need
            
        priority = int(input(f"Priority of {pid} (1-10, higher is more important): "))
        process["priority"] = min(max(priority, 1), 10)  # Clamp between 1-10
        
        processes.append(process)
    
    return processes

def display_allocation_schedule(strategy, allocation_sequence, execution_sequence):
    """Display the allocation strategy and sequence"""
    print("\n=== Deadlock Prevention Analysis ===")
    print(f"Strategy used: {strategy}")
    
    print("\nResource Allocation Sequence:")
    for i, (pid, resource, amount) in enumerate(allocation_sequence):
        print(f"Step {i+1}: Allocate {amount} unit(s) of {resource} to Process {pid}")
    
    print("\nSafe Execution Sequence:")
    for i, pid in enumerate(execution_sequence):
        print(f"{i+1}. Process {pid}")

def main():
    print("=== Deadlock Prevention System using Game Theory ===")
    
    # Get resources and processes from user
    resources = get_resources_from_user()
    processes = get_processes_from_user(resources.keys())
    
    # Initialize the game
    game = ResourceAllocationGame(resources, processes)
    
    # Check initial safety
    initially_safe, initial_sequence = game.is_safe_state()
    if initially_safe:
        print("\nInitial state is safe!")
        print(f"A possible safe sequence is: {' → '.join(map(str, initial_sequence))}")
    else:
        print("\nInitial state is not safe. Additional coordination required.")
    
    # Build and display optimal safe schedule
    strategy, allocation_sequence, execution_sequence = game.build_safe_schedule()
    display_allocation_schedule(strategy, allocation_sequence, execution_sequence)
    
    if not execution_sequence or len(execution_sequence) < len(processes):
        print("\nWARNING: Could not find a complete safe schedule that prevents deadlock!")
        print("Resource requirements may need to be adjusted.")

if __name__ == "__main__":
    main()