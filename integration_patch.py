"""
Patch generator for integrating VIBEZEN into spec_to_implementation_workflow.py

This script generates the necessary code changes to integrate VIBEZEN
into the existing workflow without breaking compatibility.
"""

import textwrap


def generate_import_section():
    """Generate import statements for VIBEZEN."""
    return textwrap.dedent("""
    # VIBEZEN Integration
    try:
        from vibezen.integration.workflow_adapter import create_vibezen_adapter
        VIBEZEN_AVAILABLE = True
    except ImportError:
        VIBEZEN_AVAILABLE = False
        logger.warning("VIBEZEN not available - continuing without quality assurance features")
    """)


def generate_argument_parser_addition():
    """Generate argument parser addition for --enable-vibezen flag."""
    return textwrap.dedent("""
    parser.add_argument(
        "--enable-vibezen",
        action="store_true",
        help="Enable VIBEZEN AI quality assurance features"
    )
    parser.add_argument(
        "--vibezen-provider",
        default="openai",
        help="Primary AI provider for VIBEZEN (default: openai)"
    )
    parser.add_argument(
        "--vibezen-no-cache",
        action="store_true",
        help="Disable VIBEZEN caching features"
    )
    parser.add_argument(
        "--vibezen-no-semantic",
        action="store_true",
        help="Disable semantic caching (use exact match only)"
    )
    """)


def generate_initialization_code():
    """Generate VIBEZEN initialization code."""
    return textwrap.dedent("""
    # Initialize VIBEZEN if enabled
    vibezen = None
    if args.enable_vibezen and VIBEZEN_AVAILABLE:
        vibezen_config = {
            "primary_provider": args.vibezen_provider,
            "enable_caching": not args.vibezen_no_cache,
            "enable_semantic_cache": not args.vibezen_no_semantic,
        }
        vibezen = create_vibezen_adapter(enable=True, **vibezen_config)
        logger.info("VIBEZEN quality assurance enabled")
    elif args.enable_vibezen and not VIBEZEN_AVAILABLE:
        logger.error("VIBEZEN requested but not available - install with: pip install -e /path/to/vibezen")
    """)


def generate_phase_wrapper():
    """Generate a helper function to wrap phases with VIBEZEN."""
    return textwrap.dedent("""
    async def run_phase_with_vibezen(phase_num, phase_func, vibezen, *args, **kwargs):
        \"\"\"Run a phase with optional VIBEZEN enhancement.\"\"\"
        if vibezen:
            return await vibezen.enhance_phase(phase_num, phase_func, *args, **kwargs)
        else:
            return await phase_func(*args, **kwargs)
    """)


def generate_ai_call_wrapper():
    """Generate wrapper for AI calls."""
    return textwrap.dedent("""
    async def call_ai_with_vibezen(prompt, provider, model, vibezen, **kwargs):
        \"\"\"Call AI with optional VIBEZEN protection.\"\"\"
        if vibezen:
            return await vibezen.call_ai_with_protection(prompt, provider, model, **kwargs)
        else:
            # Original AI call logic here
            # This is a placeholder - replace with actual implementation
            from src.integration.o3_mcp_integration import O3MCPIntegration
            o3_integration = O3MCPIntegration()
            response = await o3_integration.search(prompt)
            return response.get("result", "No response")
    """)


def generate_phase_modifications():
    """Generate example phase modifications."""
    return textwrap.dedent("""
    # Example of modifying Phase 3 (implementation):
    # Original:
    # implementation_result = await implement_tasks(tasks, spec)
    
    # With VIBEZEN:
    implementation_result = await run_phase_with_vibezen(
        3, implement_tasks, vibezen, tasks, spec
    )
    
    # Example of AI call modification:
    # Original:
    # response = await o3_integration.search(prompt)
    
    # With VIBEZEN:
    response = await call_ai_with_vibezen(
        prompt, provider="openai", model="gpt-4", vibezen=vibezen
    )
    """)


def generate_validation_addition():
    """Generate code for post-implementation validation."""
    return textwrap.dedent("""
    # Add after implementation phase
    if vibezen and implementation_result:
        logger.info("Running VIBEZEN implementation validation...")
        validation_result = await vibezen.validate_implementation(
            spec=specification,
            code=implementation_result.get("code", "")
        )
        
        if validation_result.get("status") == "validated":
            logger.info("✓ Implementation passed VIBEZEN validation")
        else:
            logger.warning("⚠ VIBEZEN validation found issues:")
            logger.warning(validation_result.get("validation_result", ""))
    """)


def generate_metrics_collection():
    """Generate code for collecting metrics at the end."""
    return textwrap.dedent("""
    # Add at the end of workflow
    if vibezen:
        logger.info("Collecting VIBEZEN metrics...")
        metrics = await vibezen.get_metrics()
        
        # Log key metrics
        cache_stats = metrics.get("cache_stats", {})
        if cache_stats:
            logger.info(f"Cache hit rate: {cache_stats.get('hit_rate', 0):.2%}")
        
        error_stats = metrics.get("error_recovery_stats", {})
        if error_stats:
            logger.info(f"Retries performed: {error_stats.get('retries', 0)}")
        
        # Save metrics to file if needed
        metrics_path = project_dir / "vibezen_metrics.json"
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"VIBEZEN metrics saved to {metrics_path}")
    """)


def main():
    """Generate the complete integration patch."""
    print("VIBEZEN Integration Patch for spec_to_implementation_workflow.py")
    print("=" * 60)
    
    sections = [
        ("1. Add imports after existing imports:", generate_import_section()),
        ("2. Add arguments to argument parser:", generate_argument_parser_addition()),
        ("3. Add initialization after argument parsing:", generate_initialization_code()),
        ("4. Add helper functions:", generate_phase_wrapper() + "\n" + generate_ai_call_wrapper()),
        ("5. Modify phase calls (example):", generate_phase_modifications()),
        ("6. Add validation after implementation:", generate_validation_addition()),
        ("7. Add metrics collection at end:", generate_metrics_collection()),
    ]
    
    for title, code in sections:
        print(f"\n{title}")
        print("-" * len(title))
        print(code)
    
    print("\n" + "=" * 60)
    print("Integration Steps:")
    print("1. Apply the above changes to spec_to_implementation_workflow.py")
    print("2. Replace placeholder AI calls with actual implementation")
    print("3. Test with: python spec_to_implementation_workflow.py --enable-vibezen")
    print("4. Monitor logs for VIBEZEN messages and metrics")


if __name__ == "__main__":
    main()