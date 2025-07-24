#!/usr/bin/env python3
"""
Test script for VIBEZEN Sequential Thinking Engine
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.vibezen.thinking.sequential_thinking import SequentialThinkingEngine
from src.vibezen.thinking.thinking_types import ThinkingContext, ThinkingPhase


async def test_sequential_thinking():
    """Test Sequential Thinking Engine"""
    print("=" * 60)
    print("VIBEZEN Sequential Thinking Engine Test")
    print("=" * 60)
    
    # Configuration
    config = {
        'thinking': {
            'min_steps': {
                'spec_understanding': 3,
                'implementation_choice': 3,
                'quality_check': 2
            },
            'confidence_threshold': 0.7,
            'max_steps_per_phase': 5
        },
        'primary_provider': 'openai',
        'thinking_model': 'gpt-4'
    }
    
    # Create engine
    engine = SequentialThinkingEngine(config)
    print("✅ Sequential Thinking Engine created")
    
    # Test 1: Spec Understanding
    print("\n" + "=" * 60)
    print("Test 1: Spec Understanding")
    print("=" * 60)
    
    spec_context = ThinkingContext(
        task="Understand a web scraping project specification",
        spec="""
        Create a web scraper for e-commerce products with the following requirements:
        - Extract product name, price, and description
        - Support multiple pages
        - Handle rate limiting
        - Store data in JSON format
        - Must be resilient to page structure changes
        """,
        phase=ThinkingPhase.SPEC_UNDERSTANDING,
        min_steps=3,
        confidence_threshold=0.7
    )
    
    print("\nStarting sequential thinking process...")
    spec_result = await engine.think_through_task(spec_context)
    
    print(f"\n✅ Thinking completed!")
    print(f"Total steps: {spec_result.total_steps}")
    print(f"Final confidence: {spec_result.final_confidence:.2f}")
    print(f"Success: {spec_result.success}")
    print(f"\nSummary: {spec_result.summary}")
    print(f"\nRecommendations:")
    for rec in spec_result.recommendations:
        print(f"  - {rec}")
    
    # Test 2: Implementation Choice
    print("\n" + "=" * 60)
    print("Test 2: Implementation Choice")
    print("=" * 60)
    
    impl_context = ThinkingContext(
        task="Choose the best approach for implementing the web scraper",
        spec=spec_context.spec,
        phase=ThinkingPhase.IMPLEMENTATION_CHOICE,
        constraints=[
            "Use Python",
            "Minimize external dependencies",
            "Ensure maintainability",
            "Consider performance"
        ],
        min_steps=3,
        confidence_threshold=0.75
    )
    
    print("\nStarting implementation choice thinking...")
    impl_result = await engine.think_through_task(impl_context)
    
    print(f"\n✅ Implementation thinking completed!")
    print(f"Total steps: {impl_result.total_steps}")
    print(f"Final confidence: {impl_result.final_confidence:.2f}")
    print(f"\nApproach: {impl_result.summary}")
    
    # Test 3: Quality Check
    print("\n" + "=" * 60)
    print("Test 3: Quality Check")
    print("=" * 60)
    
    sample_code = """
import requests
from bs4 import BeautifulSoup
import json
import time

class EcommerceScraper:
    def __init__(self):
        self.base_url = "https://example.com"
        self.products = []
        
    def scrape_page(self, page_num):
        url = f"{self.base_url}/products?page={page_num}"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for product in soup.find_all('div', class_='product'):
            self.products.append({
                'name': product.find('h2').text,
                'price': product.find('span', class_='price').text,
                'description': product.find('p').text
            })
        
        time.sleep(1)  # Rate limiting
        
    def save_data(self):
        with open('products.json', 'w') as f:
            json.dump(self.products, f, indent=2)
"""
    
    quality_result = await engine.analyze_implementation_quality(
        spec=spec_context.spec,
        code=sample_code
    )
    
    print(f"\n✅ Quality analysis completed!")
    print(f"Total steps: {quality_result.total_steps}")
    print(f"Final confidence: {quality_result.final_confidence:.2f}")
    print(f"\nAnalysis: {quality_result.summary}")
    
    if quality_result.warnings:
        print(f"\n⚠️ Warnings:")
        for warning in quality_result.warnings:
            print(f"  - {warning}")
    
    # Display metrics
    print("\n" + "=" * 60)
    print("Thinking Engine Metrics")
    print("=" * 60)
    
    metrics = engine.get_metrics()
    print(f"\nThinking Statistics:")
    print(f"  Total sessions: {metrics['thinking_stats']['total_sessions']}")
    print(f"  Average steps per session: {metrics['thinking_stats']['average_steps']:.1f}")
    print(f"  Average confidence improvement: {metrics['thinking_stats']['average_confidence_improvement']:.2f}")
    
    print(f"\nPhase Statistics:")
    for phase, stats in metrics['phase_statistics'].items():
        print(f"\n  {phase}:")
        print(f"    Sessions: {stats['total_sessions']}")
        print(f"    Average steps: {stats['total_steps'] / max(stats['total_sessions'], 1):.1f}")
        print(f"    Success rate: {stats['success_rate']:.1%}")
        print(f"    Average confidence: {stats['average_confidence']:.2f}")


async def test_workflow_integration():
    """Test Sequential Thinking in workflow context"""
    print("\n" + "=" * 60)
    print("Test: Workflow Integration")
    print("=" * 60)
    
    from src.vibezen.integration.workflow_integration import VIBEZENWorkflowIntegration, VIBEZENConfig
    
    # Create config with Sequential Thinking enabled
    config = VIBEZENConfig(
        enable_sequential_thinking=True,
        thinking_confidence_threshold=0.75,
        thinking_min_steps={
            'spec_understanding': 4,
            'implementation_choice': 3
        }
    )
    
    # Create integration
    integration = VIBEZENWorkflowIntegration(config)
    print("✅ VIBEZEN Workflow Integration created with Sequential Thinking")
    
    # Test validation with thinking
    spec = {
        "name": "Calculator API",
        "requirements": [
            "Basic arithmetic operations",
            "Error handling for division by zero",
            "Support for decimal numbers"
        ]
    }
    
    code = """
def add(a, b):
    return a + b

def divide(a, b):
    if b == 0:
        raise ValueError("Division by zero")
    return a / b
"""
    
    print("\nValidating implementation with Sequential Thinking...")
    validation_result = await integration.validate_implementation(spec, code)
    
    print(f"\n✅ Validation completed!")
    print(f"Status: {validation_result['status']}")
    print(f"Score: {validation_result['score']:.2f}")
    
    if 'thinking_analysis' in validation_result:
        thinking = validation_result['thinking_analysis']
        print(f"\nThinking Analysis:")
        print(f"  Confidence: {thinking['confidence']:.2f}")
        print(f"  Total steps: {thinking['total_steps']}")
        print(f"  Summary: {thinking['summary'][:200]}...")
        
        if thinking['recommendations']:
            print(f"\n  Recommendations:")
            for rec in thinking['recommendations'][:3]:
                print(f"    - {rec}")
    
    if validation_result['warnings']:
        print(f"\n⚠️ Warnings:")
        for warning in validation_result['warnings']:
            print(f"  - {warning}")


async def main():
    """Run all tests"""
    try:
        # Test Sequential Thinking Engine
        await test_sequential_thinking()
        
        # Test workflow integration
        await test_workflow_integration()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())