#!/usr/bin/env python3
"""
Analyze benchmark results and generate statistics for visualization.

Usage: uv run analyze_results.py <result_file.json>
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
from decimal import Decimal


# Task type base scores
TASK_TYPE_SCORES = {
    'call': 2.0,
    'checks': 1.5,
    'contains': 1.0,
    'run': 0.0  # Ignored as specified
}

# Task complexity points table
# Maps task names to complexity points
TASK_COMPLEXITY_POINTS = {
    'simple.json': 10.0,
    # Add more task names and their complexity points here as needed
}


def load_results(file_path: str) -> dict:
    """Load results from JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)


def get_task_type_score(task_type: str) -> float:
    """Get base score for a task type."""
    return TASK_TYPE_SCORES.get(task_type.lower(), 0.0)


def get_run_penalty(run: int) -> float:
    """Calculate penalty multiplier based on run number.
    Run 1: 1.0 (full points)
    Run 2: 0.5 (half points)
    Run 3: 0.333... (1/3 points)
    etc.
    """
    if run <= 0:
        return 0.0
    return 1.0 / run


def get_task_complexity(task_name: str) -> float:
    """Get complexity points for a task.
    Raises ValueError if task is not in the complexity table.
    """
    # Extract just the filename if it includes a path
    task_filename = Path(task_name).name
    
    if task_filename not in TASK_COMPLEXITY_POINTS:
        raise ValueError(f"Error: Task '{task_filename}' not found in complexity points table. "
                        f"Available tasks: {list(TASK_COMPLEXITY_POINTS.keys())}")
    
    return TASK_COMPLEXITY_POINTS[task_filename]


def calculate_task_score(result: dict) -> Tuple[float, dict]:
    """Calculate score for a single test result.
    Returns (score, score_details)
    """
    task_type = result.get('task_type', '').lower()
    run = result.get('run', 1)
    task_name = result.get('task_name', '')
    
    # Get base score for task type
    base_score = get_task_type_score(task_type)
    
    # If it's a 'run' type or unknown, score is 0
    if base_score == 0.0:
        return 0.0, {
            'task_type': task_type,
            'base_score': base_score,
            'run': run,
            'run_penalty': 0.0,
            'complexity_points': 0.0,
            'final_score': 0.0
        }
    
    # Check if test succeeded
    success = result.get('success', False)
    if isinstance(success, dict):
        success = success.get('success', False)
    
    if not success:
        return 0.0, {
            'task_type': task_type,
            'base_score': base_score,
            'run': run,
            'success': False,
            'final_score': 0.0
        }
    
    # Apply run penalty
    run_multiplier = get_run_penalty(run)
    adjusted_score = base_score * run_multiplier
    
    # Get complexity points
    try:
        complexity_points = get_task_complexity(task_name)
    except ValueError:
        # If task not in table, return error details
        return 0.0, {
            'task_type': task_type,
            'base_score': base_score,
            'run': run,
            'error': f'Task {task_name} not in complexity table',
            'final_score': 0.0
        }
    
    # Calculate final score
    final_score = adjusted_score * complexity_points
    
    return final_score, {
        'task_type': task_type,
        'base_score': base_score,
        'run': run,
        'run_multiplier': run_multiplier,
        'adjusted_score': adjusted_score,
        'complexity_points': complexity_points,
        'final_score': final_score
    }


def calculate_model_scores_with_points(results: List[dict]) -> Dict[str, dict]:
    """Calculate scores for each model using the new scoring system."""
    model_stats = {}
    missing_tasks = set()
    
    for result in results:
        model = result['model']
        if model not in model_stats:
            model_stats[model] = {
                'total_score': 0.0,
                'total_tests': 0,
                'successful_tests': 0,
                'failed_tests': 0,
                'scores_by_type': {},
                'scores_by_language': {},
                'run_distribution': {},
                'unique_tasks': set()  # Track unique tasks for normalization
            }
        
        model_stats[model]['total_tests'] += 1
        
        # Track unique tasks (combination of task_name and language)
        task_key = (result.get('task_name', ''), result.get('language', ''))
        model_stats[model]['unique_tasks'].add(task_key)
        
        # Calculate score for this result
        try:
            score, details = calculate_task_score(result)
        except ValueError as e:
            # Track missing tasks
            task_name = Path(result.get('task_name', '')).name
            missing_tasks.add(task_name)
            continue
        
        # Update statistics
        success = result.get('success', False)
        if isinstance(success, dict):
            success = success.get('success', False)
        
        if success:
            model_stats[model]['successful_tests'] += 1
        else:
            model_stats[model]['failed_tests'] += 1
        
        model_stats[model]['total_score'] += score
        
        # Track scores by task type
        task_type = result.get('task_type', '').lower()
        if task_type not in model_stats[model]['scores_by_type']:
            model_stats[model]['scores_by_type'][task_type] = {
                'total_score': 0.0,
                'count': 0,
                'successful': 0
            }
        model_stats[model]['scores_by_type'][task_type]['total_score'] += score
        model_stats[model]['scores_by_type'][task_type]['count'] += 1
        if success:
            model_stats[model]['scores_by_type'][task_type]['successful'] += 1
        
        # Track scores by language
        language = result.get('language', '')
        if language not in model_stats[model]['scores_by_language']:
            model_stats[model]['scores_by_language'][language] = {
                'total_score': 0.0,
                'count': 0,
                'successful': 0,
                'unique_tasks': set()  # Track unique tasks per language
            }
        model_stats[model]['scores_by_language'][language]['total_score'] += score
        model_stats[model]['scores_by_language'][language]['count'] += 1
        model_stats[model]['scores_by_language'][language]['unique_tasks'].add(result.get('task_name', ''))
        if success:
            model_stats[model]['scores_by_language'][language]['successful'] += 1
        
        # Track run distribution
        run = result.get('run', 1)
        if run not in model_stats[model]['run_distribution']:
            model_stats[model]['run_distribution'][run] = {
                'count': 0,
                'successful': 0,
                'score': 0.0
            }
        model_stats[model]['run_distribution'][run]['count'] += 1
        if success:
            model_stats[model]['run_distribution'][run]['successful'] += 1
        model_stats[model]['run_distribution'][run]['score'] += score
    
    # Calculate normalized scores (average per unique task)
    for model, stats in model_stats.items():
        num_unique_tasks = len(stats['unique_tasks'])
        stats['num_unique_tasks'] = num_unique_tasks
        stats['normalized_score'] = stats['total_score'] / num_unique_tasks if num_unique_tasks > 0 else 0.0
        
        # Calculate normalized scores per language
        for lang, lang_stats in stats['scores_by_language'].items():
            num_lang_tasks = len(lang_stats['unique_tasks'])
            lang_stats['num_unique_tasks'] = num_lang_tasks
            lang_stats['normalized_score'] = lang_stats['total_score'] / num_lang_tasks if num_lang_tasks > 0 else 0.0
            # Convert set to count for JSON serialization
            del lang_stats['unique_tasks']
        
        # Remove the set from main stats for JSON serialization
        del stats['unique_tasks']
    
    # Check if we encountered missing tasks
    if missing_tasks:
        print(f"\nError: The following tasks are not in the complexity points table:")
        for task in sorted(missing_tasks):
            print(f"  - {task}")
        print(f"\nPlease add these tasks to TASK_COMPLEXITY_POINTS in analyze_results.py")
        sys.exit(1)
    
    return model_stats


def calculate_model_scores(results: List[dict]) -> Dict[str, dict]:
    """Calculate overall success rate for each model across all languages."""
    model_stats = {}
    
    for result in results:
        model = result['model']
        if model not in model_stats:
            model_stats[model] = {'success': 0, 'total': 0}
        
        model_stats[model]['total'] += 1
        # Handle both boolean and nested object success field
        success = result['success']
        if isinstance(success, dict):
            success = success.get('success', False)
        if success:
            model_stats[model]['success'] += 1
    
    # Calculate success rates
    model_scores = []
    for model, stats in model_stats.items():
        if stats['total'] > 0:
            score = (stats['success'] / stats['total']) * 100
            model_scores.append({
                'model': model,
                'score': round(score, 2),
                'success_count': stats['success'],
                'total_count': stats['total']
            })
    
    # Sort by score descending
    model_scores.sort(key=lambda x: x['score'], reverse=True)
    return model_scores


def calculate_best_model_per_language(results: List[dict]) -> Dict[str, dict]:
    """Find the best model for each language based on success rate."""
    language_model_stats = {}
    
    # Collect stats per language-model combination
    for result in results:
        lang = result['language']
        model = result['model']
        
        if lang not in language_model_stats:
            language_model_stats[lang] = {}
        
        if model not in language_model_stats[lang]:
            language_model_stats[lang][model] = {'success': 0, 'total': 0}
        
        language_model_stats[lang][model]['total'] += 1
        # Handle both boolean and nested object success field
        success = result['success']
        if isinstance(success, dict):
            success = success.get('success', False)
        if success:
            language_model_stats[lang][model]['success'] += 1
    
    # Find best model for each language
    best_models = {}
    for lang, models in language_model_stats.items():
        best_model = None
        best_score = -1
        
        for model, stats in models.items():
            if stats['total'] > 0:
                score = (stats['success'] / stats['total']) * 100
                if score > best_score:
                    best_score = score
                    best_model = {
                        'model': model,
                        'score': round(score, 2),
                        'success_count': stats['success'],
                        'total_count': stats['total']
                    }
        
        if best_model:
            best_models[lang] = best_model
    
    return best_models


def generate_2d_diagram_data(results: List[dict], costs: dict, durations: dict) -> List[dict]:
    """Generate data points for 2D visualization (success rate vs cost, with duration as color)."""
    # First, calculate stats for each model-language combination
    model_lang_stats = {}
    
    for result in results:
        model = result['model']
        lang = result['language']
        key = f"{model}|{lang}"
        
        if key not in model_lang_stats:
            model_lang_stats[key] = {
                'model': model,
                'language': lang,
                'success': 0,
                'total': 0,
                'costs': [],
                'durations': []
            }
        
        model_lang_stats[key]['total'] += 1
        # Handle both boolean and nested object success field
        success = result['success']
        if isinstance(success, dict):
            success = success.get('success', False)
        if success:
            model_lang_stats[key]['success'] += 1
        
        # Collect individual costs and durations
        if result.get('cost'):
            model_lang_stats[key]['costs'].append(float(result['cost']))
        if result.get('duration'):
            model_lang_stats[key]['durations'].append(float(result['duration']))
    
    # Also add overall stats for each model (across all languages)
    model_overall_stats = {}
    for result in results:
        model = result['model']
        
        if model not in model_overall_stats:
            model_overall_stats[model] = {
                'model': model,
                'language': 'all',
                'success': 0,
                'total': 0,
                'costs': [],
                'durations': []
            }
        
        model_overall_stats[model]['total'] += 1
        # Handle both boolean and nested object success field
        success = result['success']
        if isinstance(success, dict):
            success = success.get('success', False)
        if success:
            model_overall_stats[model]['success'] += 1
        
        if result.get('cost'):
            model_overall_stats[model]['costs'].append(float(result['cost']))
        if result.get('duration'):
            model_overall_stats[model]['durations'].append(float(result['duration']))
    
    # Generate data points
    data_points = []
    
    # Process model-language combinations
    for key, stats in model_lang_stats.items():
        if stats['total'] > 0:
            success_rate = (stats['success'] / stats['total']) * 100
            
            # Calculate average cost and duration
            avg_cost = sum(stats['costs']) / len(stats['costs']) if stats['costs'] else 0
            avg_duration = sum(stats['durations']) / len(stats['durations']) if stats['durations'] else 0
            
            # Also check if we have aggregate data in costs/durations dicts
            model = stats['model']
            lang = stats['language']
            if model in costs and lang in costs[model]:
                total_cost = float(costs[model][lang])
                # This is total cost, divide by number of runs to get average
                max_run = max(r['run'] for r in results if r['model'] == model and r['language'] == lang)
                avg_cost = total_cost / max_run if max_run > 0 else total_cost
            
            if model in durations and lang in durations[model]:
                total_duration = float(durations[model][lang])
                max_run = max(r['run'] for r in results if r['model'] == model and r['language'] == lang)
                avg_duration = total_duration / max_run if max_run > 0 else total_duration
            
            data_points.append({
                'model': model,
                'language': lang,
                'success_rate': round(success_rate, 2),
                'avg_cost': round(avg_cost, 6),
                'avg_duration': round(avg_duration, 2),
                'total_tests': stats['total']
            })
    
    # Process overall model stats
    for model, stats in model_overall_stats.items():
        if stats['total'] > 0:
            success_rate = (stats['success'] / stats['total']) * 100
            avg_cost = sum(stats['costs']) / len(stats['costs']) if stats['costs'] else 0
            avg_duration = sum(stats['durations']) / len(stats['durations']) if stats['durations'] else 0
            
            data_points.append({
                'model': model,
                'language': 'all',
                'success_rate': round(success_rate, 2),
                'avg_cost': round(avg_cost, 6),
                'avg_duration': round(avg_duration, 2),
                'total_tests': stats['total']
            })
    
    return data_points


def format_model_ranking(model_stats: Dict[str, dict]) -> List[dict]:
    """Format model statistics for ranking display."""
    rankings = []
    
    for model, stats in model_stats.items():
        # Calculate success rate
        success_rate = 0.0
        if stats['total_tests'] > 0:
            success_rate = (stats['successful_tests'] / stats['total_tests']) * 100
        
        rankings.append({
            'model': model,
            'total_score': round(stats['total_score'], 2),
            'normalized_score': round(stats['normalized_score'], 2),
            'success_rate': round(success_rate, 2),
            'total_tests': stats['total_tests'],
            'num_unique_tasks': stats['num_unique_tasks'],
            'successful_tests': stats['successful_tests'],
            'failed_tests': stats['failed_tests'],
            'avg_score_per_test': round(stats['total_score'] / stats['total_tests'], 2) if stats['total_tests'] > 0 else 0
        })
    
    # Sort by normalized score descending (score per unique task)
    rankings.sort(key=lambda x: x['normalized_score'], reverse=True)
    return rankings


def main():
    if len(sys.argv) != 2:
        print("Usage: uv run analyze_results.py <result_file.json>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    if not Path(input_file).exists():
        print(f"Error: File '{input_file}' not found")
        sys.exit(1)
    
    # Load results
    data = load_results(input_file)
    results = data.get('results', [])
    costs = data.get('costs', {})
    durations = data.get('durations', {})
    
    if not results:
        print("No results found in the file")
        sys.exit(1)
    
    # Calculate statistics with new scoring system
    model_stats_with_points = calculate_model_scores_with_points(results)
    model_rankings = format_model_ranking(model_stats_with_points)
    
    # Also calculate traditional statistics
    model_scores = calculate_model_scores(results)
    best_models_by_language = calculate_best_model_per_language(results)
    diagram_data = generate_2d_diagram_data(results, costs, durations)
    
    # Prepare output
    output = {
        'scoring_system': {
            'task_type_scores': TASK_TYPE_SCORES,
            'task_complexity_points': TASK_COMPLEXITY_POINTS
        },
        'model_rankings': model_rankings,
        'detailed_model_stats': model_stats_with_points,
        'traditional_scores': {
            'model_scores': model_scores,
            'best_models_by_language': best_models_by_language
        },
        'diagram_data': diagram_data,
        'metadata': {
            'source_file': input_file,
            'total_results': len(results),
            'unique_models': len(set(r['model'] for r in results)),
            'unique_languages': list(set(r['language'] for r in results))
        }
    }
    
    # Generate output filename
    input_path = Path(input_file)
    output_file = input_path.parent / f"{input_path.stem}_analysis.json"
    
    # Save output
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"Analysis complete! Results saved to: {output_file}")
    print(f"\nSummary:")
    print(f"- Total test results: {len(results)}")
    print(f"- Unique models: {output['metadata']['unique_models']}")
    print(f"- Languages tested: {', '.join(output['metadata']['unique_languages'])}")
    
    print(f"\nTop 5 models by NORMALIZED SCORE (points per unique task):")
    for i, model in enumerate(model_rankings[:5]):
        print(f"  {i+1}. {model['model']}: {model['normalized_score']} pts/task "
              f"(total: {model['total_score']} pts, {model['num_unique_tasks']} unique tasks, "
              f"success: {model['success_rate']}%)")
    
    print(f"\nTop 3 models by SUCCESS RATE (traditional):")
    for i, model in enumerate(model_scores[:3]):
        print(f"  {i+1}. {model['model']}: {model['score']}% ({model['success_count']}/{model['total_count']})")
    
    print(f"\nScoring System:")
    print(f"  Task Types: {TASK_TYPE_SCORES}")
    print(f"  Complexity Points: {list(TASK_COMPLEXITY_POINTS.keys())}")


if __name__ == "__main__":
    main()