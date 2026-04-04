#!/usr/bin/env python3
"""
Quick Validation Script
Verifies all competition requirements before submission
"""

import sys
import os
import json
from pathlib import Path


def check_file_exists(filepath, required=True):
    """Check if a file exists"""
    exists = Path(filepath).exists()
    status = "✅" if exists else ("❌" if required else "⚠️")
    req_text = "REQUIRED" if required else "OPTIONAL"
    print(f"{status} {filepath} ({req_text})")
    return exists


def check_environment_variables():
    """Check if required environment variables are defined in inference.py"""
    print("\n📋 Environment Variables in inference.py:")
    
    with open('inference.py', 'r') as f:
        content = f.read()
    
    required_vars = ['API_BASE_URL', 'MODEL_NAME', 'HF_TOKEN']
    all_found = True
    
    for var in required_vars:
        found = var in content
        status = "✅" if found else "❌"
        print(f"{status} {var}")
        if not found:
            all_found = False
    
    return all_found


def check_structured_logging():
    """Check if inference.py has structured logging"""
    print("\n📋 Structured Logging Format:")
    
    with open('inference.py', 'r') as f:
        content = f.read()
    
    required_logs = ['[START]', '[STEP]', '[END]']
    all_found = True
    
    for log in required_logs:
        found = log in content
        status = "✅" if found else "❌"
        print(f"{status} {log} format")
        if not found:
            all_found = False
    
    return all_found


def check_openai_client():
    """Check if OpenAI client is used"""
    print("\n📋 OpenAI Client Usage:")
    
    with open('inference.py', 'r') as f:
        content = f.read()
    
    checks = [
        ('from openai import OpenAI', 'OpenAI import'),
        ('client = OpenAI', 'Client initialization'),
        ('temperature=0.0', 'Temperature = 0.0')
    ]
    
    all_found = True
    for check_str, desc in checks:
        found = check_str in content
        status = "✅" if found else "❌"
        print(f"{status} {desc}")
        if not found:
            all_found = False
    
    return all_found


def check_pydantic_models():
    """Check if Pydantic models are defined"""
    print("\n📋 Pydantic Models:")
    
    try:
        from bom_normalizer.models import Action, Observation, Reward, BOMRow
        print("✅ Action model")
        print("✅ Observation model")
        print("✅ Reward model")
        print("✅ BOMRow model")
        return True
    except ImportError as e:
        print(f"❌ Failed to import models: {e}")
        return False


def check_environment_methods():
    """Check if environment has required methods"""
    print("\n📋 Environment Methods:")
    
    try:
        from bom_normalizer.env import BOMEnv
        env = BOMEnv('easy')
        
        methods = ['reset', 'step', 'state']
        all_found = True
        
        for method in methods:
            has_method = hasattr(env, method)
            status = "✅" if has_method else "❌"
            print(f"{status} {method}() method")
            if not has_method:
                all_found = False
        
        return all_found
    except Exception as e:
        print(f"❌ Failed to check environment: {e}")
        return False


def check_tasks():
    """Check if all 3 tasks are defined"""
    print("\n📋 Tasks:")
    
    try:
        from bom_normalizer.env import BOMEnv
        
        tasks = ['easy', 'medium', 'hard']
        all_work = True
        
        for task_id in tasks:
            try:
                env = BOMEnv(task_id=task_id)
                obs = env.reset()
                print(f"✅ {task_id.upper()} task: {len(obs.rows)} rows, {obs.max_steps} max steps")
            except Exception as e:
                print(f"❌ {task_id.upper()} task failed: {e}")
                all_work = False
        
        return all_work
    except Exception as e:
        print(f"❌ Failed to check tasks: {e}")
        return False


def check_grader():
    """Check if grader works"""
    print("\n📋 Grader:")
    
    try:
        from bom_normalizer.env import BOMEnv
        from bom_normalizer.grader import grade
        
        all_work = True
        for task_id in ['easy', 'medium', 'hard']:
            try:
                env = BOMEnv(task_id=task_id)
                obs = env.reset()
                score = grade(env._rows, env._gold, task_id)
                
                if 0.0 <= score <= 1.0:
                    print(f"✅ {task_id.upper()} grader: score={score:.4f}")
                else:
                    print(f"❌ {task_id.upper()} grader: score out of range ({score})")
                    all_work = False
            except Exception as e:
                print(f"❌ {task_id.upper()} grader failed: {e}")
                all_work = False
        
        return all_work
    except Exception as e:
        print(f"❌ Failed to check grader: {e}")
        return False


def check_openenv_yaml():
    """Check openenv.yaml structure"""
    print("\n📋 openenv.yaml:")
    
    try:
        import yaml
        with open('openenv.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        required_fields = ['name', 'version', 'description', 'tasks', 'action_space', 
                          'observation_space', 'reward', 'endpoints', 'runtime']
        all_found = True
        
        for field in required_fields:
            found = field in config
            status = "✅" if found else "❌"
            print(f"{status} {field}")
            if not found:
                all_found = False
        
        # Check tasks
        if 'tasks' in config:
            task_count = len(config['tasks'])
            if task_count >= 3:
                print(f"✅ {task_count} tasks defined")
            else:
                print(f"❌ Only {task_count} tasks (need 3+)")
                all_found = False
        
        return all_found
    except Exception as e:
        print(f"❌ Failed to parse openenv.yaml: {e}")
        return False


def main():
    """Run all validation checks"""
    print("=" * 60)
    print("🔍 BOM Normalizer - Competition Validation")
    print("=" * 60)
    
    # Change to project directory
    os.chdir(Path(__file__).parent)
    
    results = {}
    
    # File checks
    print("\n📁 Required Files:")
    results['inference.py'] = check_file_exists('inference.py', required=True)
    results['openenv.yaml'] = check_file_exists('openenv.yaml', required=True)
    results['Dockerfile'] = check_file_exists('Dockerfile', required=True)
    results['requirements.txt'] = check_file_exists('requirements.txt', required=True)
    results['README.md'] = check_file_exists('README.md', required=True)
    
    print("\n📁 Optional Files:")
    check_file_exists('tests/', required=False)
    check_file_exists('data/', required=False)
    
    # Code checks
    results['env_vars'] = check_environment_variables()
    results['logging'] = check_structured_logging()
    results['openai_client'] = check_openai_client()
    results['models'] = check_pydantic_models()
    results['methods'] = check_environment_methods()
    results['tasks'] = check_tasks()
    results['grader'] = check_grader()
    results['openenv_yaml'] = check_openenv_yaml()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    percentage = (passed / total) * 100
    
    print(f"\nPassed: {passed}/{total} ({percentage:.0f}%)")
    
    if percentage == 100:
        print("\n✅ ALL CHECKS PASSED!")
        print("🎉 Your submission is ready for deployment!")
        print("\nNext steps:")
        print("1. Deploy to HuggingFace Space")
        print("2. Run actual inference")
        print("3. Update README with real scores")
        return 0
    elif percentage >= 80:
        print("\n⚠️ MOST CHECKS PASSED")
        print("Fix the failing checks before submission.")
        return 1
    else:
        print("\n❌ MULTIPLE CHECKS FAILED")
        print("Please fix the issues above before submission.")
        return 2


if __name__ == '__main__':
    sys.exit(main())
