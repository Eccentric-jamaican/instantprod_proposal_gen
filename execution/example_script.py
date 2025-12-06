#!/usr/bin/env python3
"""
Example execution script template.

This demonstrates the structure for deterministic execution scripts
in the 3-layer architecture.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import click

# Load environment variables
load_dotenv()

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent
TMP_DIR = PROJECT_ROOT / ".tmp"
TMP_DIR.mkdir(exist_ok=True)


@click.command()
@click.option('--input', '-i', required=True, help='Input parameter description')
@click.option('--output', '-o', help='Output file path (optional)')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def main(input: str, output: str, verbose: bool):
    """
    Brief description of what this script does.
    
    This script is called by the orchestration layer (AI agent) to perform
    deterministic operations. It should:
    - Handle errors gracefully
    - Provide clear logging
    - Return meaningful exit codes
    - Store intermediate files in .tmp/
    """
    
    if verbose:
        click.echo(f"Running with input: {input}")
    
    try:
        # Your deterministic logic here
        result = process_input(input)
        
        # Save to output if specified
        if output:
            save_result(result, output)
            click.echo(f"✓ Results saved to: {output}")
        else:
            click.echo(f"✓ Processing complete")
            click.echo(f"Result: {result}")
        
        return 0
        
    except Exception as e:
        click.echo(f"✗ Error: {str(e)}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        return 1


def process_input(input_data: str):
    """
    Core processing logic.
    Keep this separate from CLI handling for testability.
    """
    # Example processing
    return f"Processed: {input_data}"


def save_result(result, output_path: str):
    """
    Save results to file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write(str(result))


if __name__ == '__main__':
    sys.exit(main())
