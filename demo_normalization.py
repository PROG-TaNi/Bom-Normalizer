"""
Live Demo: Watch BOM Normalization Happen
Shows before/after comparison and step-by-step normalization
"""

import requests
import json
from colorama import init, Fore, Back, Style

# Initialize colorama for colored output
init(autoreset=True)

ENV_URL = "http://localhost:7860"

def print_header(text):
    """Print a colored header"""
    print("\n" + "="*80)
    print(Fore.CYAN + Style.BRIGHT + text.center(80))
    print("="*80 + "\n")

def print_row(row, show_status=True):
    """Print a BOM row with colors"""
    status_color = {
        'raw': Fore.RED,
        'normalized': Fore.GREEN,
        'flagged': Fore.YELLOW,
        'merged': Fore.BLUE
    }
    
    color = status_color.get(row['status'], Fore.WHITE)
    status_text = f"[{row['status'].upper()}]" if show_status else ""
    
    print(f"{color}Row {row['row_id']:2d} {status_text:15s} | "
          f"Vendor: {row['vendor_name']:25s} | "
          f"Part: {row['part_number']:15s} | "
          f"Value: {row['value']:10s} | "
          f"Package: {row['package']:10s} | "
          f"Qty: {row['quantity']:3d}")

def print_comparison(before, after):
    """Print before/after comparison"""
    print(Fore.RED + "BEFORE: ", end="")
    print(f"Vendor: {before['vendor_name']:25s} | "
          f"Value: {before['value']:10s} | "
          f"Package: {before['package']:10s}")
    
    print(Fore.GREEN + "AFTER:  ", end="")
    print(f"Vendor: {after['vendor_name']:25s} | "
          f"Value: {after['value']:10s} | "
          f"Package: {after['package']:10s}")

def demo_easy_task():
    """Demo: Easy task - Vendor normalization only"""
    print_header("DEMO 1: EASY TASK - Vendor Name Normalization")
    
    # Reset environment
    print(Fore.YELLOW + " Step 1: Loading messy BOM data...")
    response = requests.post(f"{ENV_URL}/reset?task_id=easy")
    obs = response.json()
    
    print(f"\nTask: {obs['task_description']}")
    print(f"Rows to normalize: {len(obs['rows'])}")
    print(f"Max steps allowed: {obs['max_steps']}")
    print(f"\n{Fore.RED}MESSY DATA (Before Normalization):")
    print("-" * 80)
    
    for row in obs['rows'][:5]:  # Show first 5 rows
        print_row(row)
    
    print(f"\n{Fore.YELLOW}... and {len(obs['rows']) - 5} more rows")
    
    # Show normalization examples
    print_header("Normalization Examples")
    
    normalizations = [
        (1, "TI", "Texas Instruments"),
        (2, "Murata", "Murata Manufacturing"),
        (3, "Vishay", "Vishay Intertechnology"),
    ]
    
    for row_id, messy, clean in normalizations:
        print(f"\n{Fore.CYAN}Normalizing Row {row_id}...")
        print(f"  {Fore.RED}Messy:  '{messy}'")
        print(f"  {Fore.GREEN}Clean:  '{clean}'")
        
        # Take action
        action = {
            "action_type": "normalize_vendor",
            "row_id": row_id,
            "new_value": clean
        }
        
        response = requests.post(f"{ENV_URL}/step?task_id=easy", json=action)
        result = response.json()
        
        reward = result['reward']
        print(f"  {Fore.YELLOW}Reward: {reward['value']:+.2f} - {reward['reason']}")
        print(f"  {Fore.MAGENTA}Cumulative: {reward['cumulative']:.2f}")
    
    # Show final state
    print_header("Current State After 3 Normalizations")
    
    response = requests.get(f"{ENV_URL}/state?task_id=easy")
    obs = response.json()
    
    print(f"Steps taken: {obs['step_count']} / {obs['max_steps']}")
    print(f"Fields remaining: {obs['fields_remaining']}")
    print(f"Cumulative reward: {obs['cumulative_reward']:.2f}")
    print("\nRows status:")
    print("-" * 80)
    
    for row in obs['rows'][:5]:
        print_row(row)

def demo_medium_task():
    """Demo: Medium task - Multi-field normalization"""
    print_header("DEMO 2: MEDIUM TASK - Multi-Field Normalization")
    
    # Reset environment
    print(Fore.YELLOW + "Loading medium difficulty BOM...")
    response = requests.post(f"{ENV_URL}/reset?task_id=medium")
    obs = response.json()
    
    print(f"\nTask: {obs['task_description']}")
    print(f"Rows to normalize: {len(obs['rows'])}")
    print(f"Fields per row: 3 (vendor, value, package)")
    print(f"Total fields to fix: {len(obs['rows']) * 3}")
    
    # Show a messy row
    messy_row = obs['rows'][0]
    print(f"\n{Fore.RED}Example Messy Row:")
    print("-" * 80)
    print_row(messy_row, show_status=False)
    
    # Normalize vendor
    print(f"\n{Fore.CYAN}Step 1: Normalize Vendor Name")
    action = {
        "action_type": "normalize_vendor",
        "row_id": 1,
        "new_value": "Texas Instruments"
    }
    response = requests.post(f"{ENV_URL}/step?task_id=medium", json=action)
    result = response.json()
    print(f"  {Fore.YELLOW}Reward: {result['reward']['value']:+.2f}")
    
    # Normalize value
    print(f"\n{Fore.CYAN}Step 2: Normalize Value (10K → 10000)")
    action = {
        "action_type": "normalize_value",
        "row_id": 1,
        "new_value": "5"
    }
    response = requests.post(f"{ENV_URL}/step?task_id=medium", json=action)
    result = response.json()
    print(f"  {Fore.YELLOW}Reward: {result['reward']['value']:+.2f}")
    
    # Normalize package
    print(f"\n{Fore.CYAN}Step 3: Normalize Package (DIP14 → DIP-14)")
    action = {
        "action_type": "normalize_package",
        "row_id": 1,
        "new_value": "DIP-14"
    }
    response = requests.post(f"{ENV_URL}/step?task_id=medium", json=action)
    result = response.json()
    print(f"  {Fore.YELLOW}Reward: {result['reward']['value']:+.2f}")
    
    # Show normalized row
    response = requests.get(f"{ENV_URL}/state?task_id=medium")
    obs = response.json()
    normalized_row = obs['rows'][0]
    
    print(f"\n{Fore.GREEN}Normalized Row:")
    print("-" * 80)
    print_row(normalized_row)
    
    print(f"\n{Fore.MAGENTA}Total Reward: {obs['cumulative_reward']:.2f}")

def demo_before_after():
    """Demo: Before/After comparison"""
    print_header("DEMO 3: Before/After Comparison")
    
    # Reset and get initial state
    response = requests.post(f"{ENV_URL}/reset?task_id=easy")
    before = response.json()
    
    print(Fore.YELLOW + "Normalizing all 10 rows...")
    print()
    
    # Common vendor normalizations
    vendor_map = {
        1: "Texas Instruments",
        2: "Murata Manufacturing",
        3: "Vishay Intertechnology",
        4: "STMicroelectronics",
        5: "ON Semiconductor",
        6: "NXP Semiconductors",
        7: "Infineon Technologies",
        8: "Texas Instruments",
        9: "Texas Instruments",
        10: "Microchip Technology"
    }
    
    for row_id, correct_vendor in vendor_map.items():
        before_row = before['rows'][row_id - 1]
        
        # Normalize
        action = {
            "action_type": "normalize_vendor",
            "row_id": row_id,
            "new_value": correct_vendor
        }
        response = requests.post(f"{ENV_URL}/step?task_id=easy", json=action)
        result = response.json()
        after_row = result['observation']['rows'][row_id - 1]
        
        # Show comparison
        print(f"{Fore.CYAN}Row {row_id}:")
        print(f"  {Fore.RED}Before: {before_row['vendor_name']:30s} [{before_row['status']}]")
        print(f"  {Fore.GREEN}After:  {after_row['vendor_name']:30s} [{after_row['status']}]")
        print(f"  {Fore.YELLOW}Reward: {result['reward']['value']:+.2f}")
        print()
    
    # Submit and get score
    print(Fore.CYAN + "Submitting for grading...")
    action = {"action_type": "submit"}
    response = requests.post(f"{ENV_URL}/step?task_id=easy", json=action)
    result = response.json()
    
    score = result['info'].get('score', 0.0)
    print(f"\n{Fore.GREEN + Style.BRIGHT}FINAL SCORE: {score:.4f} ({score*100:.1f}%)")
    print(f"{Fore.MAGENTA}Total Reward: {result['reward']['cumulative']:.2f}")

def demo_interactive():
    """Interactive demo - let user see live normalization"""
    print_header("DEMO 4: Interactive Normalization")
    
    # Reset
    response = requests.post(f"{ENV_URL}/reset?task_id=easy")
    obs = response.json()
    
    print(Fore.YELLOW + "Current BOM State:")
    print("-" * 80)
    for row in obs['rows']:
        print_row(row)
    
    print(f"\n{Fore.CYAN}Let's normalize Row 1...")
    print(f"Current vendor: {Fore.RED}{obs['rows'][0]['vendor_name']}")
    print(f"Correct vendor: {Fore.GREEN}Texas Instruments")
    
    input(f"\n{Fore.YELLOW}Press Enter to normalize...")
    
    action = {
        "action_type": "normalize_vendor",
        "row_id": 1,
        "new_value": "Texas Instruments"
    }
    response = requests.post(f"{ENV_URL}/step?task_id=easy", json=action)
    result = response.json()
    
    print(f"\n{Fore.GREEN}✓ Normalized!")
    print(f"Reward: {result['reward']['value']:+.2f}")
    print(f"Reason: {result['reward']['reason']}")
    
    # Show updated state
    print(f"\n{Fore.YELLOW}Updated BOM State:")
    print("-" * 80)
    for row in result['observation']['rows'][:3]:
        print_row(row)

def main():
    """Run all demos"""
    print(Fore.GREEN + Style.BRIGHT + """
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║                  BOM NORMALIZER - LIVE DEMO                              ║
    ║                  Watch Data Normalization Happen!                        ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Check if backend is running
        response = requests.get(f"{ENV_URL}/health", timeout=2)
        if response.status_code != 200:
            print(Fore.RED + "Error: Backend not responding!")
            return
    except:
        print(Fore.RED + "Error: Backend not running!")
        print(Fore.YELLOW + "Please start the backend first:")
        print("  python -m uvicorn bom_normalizer.server:app --reload")
        return
    
    print(Fore.GREEN + "✓ Backend is running!\n")
    
    # Run demos
    demos = [
        ("1", "Easy Task - Vendor Normalization", demo_easy_task),
        ("2", "Medium Task - Multi-Field Normalization", demo_medium_task),
        ("3", "Before/After Comparison", demo_before_after),
        ("4", "Interactive Demo", demo_interactive),
    ]
    
    print(Fore.CYAN + "Available Demos:")
    for num, name, _ in demos:
        print(f"  {num}. {name}")
    print(f"  5. Run All Demos")
    print(f"  0. Exit")
    
    choice = input(f"\n{Fore.YELLOW}Select demo (0-5): ").strip()
    
    if choice == "0":
        print(Fore.GREEN + "Goodbye!")
        return
    elif choice == "5":
        for _, _, demo_func in demos:
            demo_func()
            input(f"\n{Fore.YELLOW}Press Enter to continue...")
    elif choice in ["1", "2", "3", "4"]:
        demos[int(choice) - 1][2]()
    else:
        print(Fore.RED + "Invalid choice!")

if __name__ == "__main__":
    main()
