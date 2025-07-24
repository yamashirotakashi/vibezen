#!/usr/bin/env python3
"""
Test script to verify VIBEZEN integration with spec_to_implementation_workflow.py
"""

import asyncio
import sys
import subprocess
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "memory-integration-project"))


async def test_integration():
    """Test VIBEZEN integration"""
    print("=" * 60)
    print("VIBEZEN Integration Test")
    print("=" * 60)
    
    # Test project details
    test_project = "vibezen_test_project"
    test_description = "Test project for VIBEZEN integration"
    project_path = f"/mnt/c/Users/tky99/dev/{test_project}"
    
    # Check if VIBEZEN is importable
    try:
        from vibezen.integration.workflow_adapter import create_vibezen_adapter
        print("✅ VIBEZEN import successful")
    except ImportError as e:
        print(f"❌ VIBEZEN import failed: {e}")
        print("\nPlease install VIBEZEN first:")
        print("  cd /mnt/c/Users/tky99/dev/vibezen")
        print("  pip install -e .")
        return
    
    # Test workflow import
    try:
        from src.integration.spec_to_implementation_workflow import SpecToImplementationWorkflow, VIBEZEN_AVAILABLE
        print(f"✅ Workflow import successful (VIBEZEN_AVAILABLE={VIBEZEN_AVAILABLE})")
    except ImportError as e:
        print(f"❌ Workflow import failed: {e}")
        return
    
    # Test commands
    commands = [
        # Without VIBEZEN
        f"python /mnt/c/Users/tky99/dev/memory-integration-project/src/integration/spec_to_implementation_workflow.py {test_project} --description '{test_description}' --path {project_path} --force",
        
        # With VIBEZEN
        f"python /mnt/c/Users/tky99/dev/memory-integration-project/src/integration/spec_to_implementation_workflow.py {test_project}_vibezen --description '{test_description} with VIBEZEN' --path {project_path}_vibezen --enable-vibezen --force",
        
        # With VIBEZEN options
        f"python /mnt/c/Users/tky99/dev/memory-integration-project/src/integration/spec_to_implementation_workflow.py {test_project}_vibezen_nocache --description '{test_description} with VIBEZEN no cache' --path {project_path}_vibezen_nocache --enable-vibezen --vibezen-no-cache --force"
    ]
    
    print("\n" + "=" * 60)
    print("Test Commands:")
    print("=" * 60)
    
    for i, cmd in enumerate(commands, 1):
        print(f"\n{i}. Command:")
        print(f"   {cmd}")
        print(f"\n   To run: {cmd}")
    
    print("\n" + "=" * 60)
    print("Direct Integration Test")
    print("=" * 60)
    
    # Direct integration test
    try:
        # Create VIBEZEN adapter
        vibezen = create_vibezen_adapter(enable=True)
        print("✅ VIBEZEN adapter created")
        
        # Create workflow with VIBEZEN
        workflow = SpecToImplementationWorkflow(project_path + "_direct", vibezen_adapter=vibezen)
        print("✅ Workflow created with VIBEZEN")
        
        # Test phase enhancement
        async def mock_phase():
            return {"result": "test"}
        
        enhanced_result = await vibezen.enhance_phase(1, mock_phase)
        print(f"✅ Phase enhancement works: {enhanced_result}")
        
        # Test AI call protection
        protected_result = await vibezen.call_ai_with_protection(
            "Test prompt", 
            provider="openai",
            model="gpt-4"
        )
        print(f"✅ AI call protection works: {protected_result[:50]}...")
        
        # Get metrics
        metrics = await vibezen.get_metrics()
        print(f"✅ Metrics collection works: {list(metrics.keys())}")
        
    except Exception as e:
        print(f"❌ Direct integration test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Integration Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run one of the test commands above")
    print("2. Check for VIBEZEN messages in the output")
    print("3. Look for vibezen_metrics.json in the project directory")
    print("4. Compare results with and without --enable-vibezen")


if __name__ == "__main__":
    asyncio.run(test_integration())