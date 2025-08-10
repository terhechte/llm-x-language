"""Parallel task executor using multiprocessing.Pool for improved performance."""

import os
import time
import logging
from multiprocessing import Pool, Manager, Process, Queue
from typing import Dict, List, Any, Tuple, Optional
from decimal import Decimal, getcontext
from dataclasses import dataclass
import queue
import json

from task import Language, load_all_tasks
from executor import Executor
from llm import model_info, ModelInfo
from utils import TaskResult, Result


@dataclass
class WorkItem:
    """Represents a single unit of work for parallel processing."""
    model: str
    language: Language
    task: Any  # TaskCall, TaskRun, TaskCheck, or TaskContains
    run: int
    model_info: ModelInfo
    skip_lang_specific: bool


@dataclass
class ProcessedResult:
    """Result from processing a single task."""
    success: bool
    model: str
    language: str
    task_name: str
    result_data: Dict[str, Any]
    cost: Decimal
    duration: float
    error: Optional[str] = None


class RateLimiter:
    """Simple rate limiter for LLM API calls across processes."""
    
    def __init__(self, manager, max_per_minute: int = 30):
        self.max_per_minute = max_per_minute
        self.call_times = manager.list()
        self.lock = manager.Lock()
    
    def acquire(self):
        """Wait if necessary to respect rate limit."""
        with self.lock:
            now = time.time()
            # Remove calls older than 1 minute
            self.call_times[:] = [t for t in self.call_times if now - t < 60]
            
            # If at limit, wait
            if len(self.call_times) >= self.max_per_minute:
                sleep_time = 60 - (now - self.call_times[0]) + 0.1
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    # Clean up again after sleeping
                    now = time.time()
                    self.call_times[:] = [t for t in self.call_times if now - t < 60]
            
            # Record this call
            self.call_times.append(now)


# Global rate limiter instance (will be initialized in main)
rate_limiter = None


def init_worker(rl):
    """Initialize worker process with shared rate limiter."""
    global rate_limiter
    rate_limiter = rl
    # Set decimal precision in each worker
    getcontext().prec = 16
    # Configure logging for worker
    logging.basicConfig(
        level=logging.INFO,
        format='[%(process)d] %(asctime)s - %(levelname)s - %(message)s'
    )


def process_single_task(work_item: WorkItem) -> ProcessedResult:
    """
    Worker function that processes a single task completely.
    Runs in separate process for isolation.
    """
    try:
        # Rate limit LLM calls
        if rate_limiter:
            rate_limiter.acquire()
        
        start_time = time.time()
        
        # Log task start
        logging.info(f"Processing {work_item.task.filename} for {work_item.model} in {work_item.language.value}")
        
        # Execute the task
        executor = Executor(work_item.language)
        result = executor.call(work_item.task, work_item.model, work_item.run)
        
        duration = time.time() - start_time
        
        # Calculate costs
        pricing = Decimal(work_item.model_info.prompt_pricing)
        completion = Decimal(work_item.model_info.completion_pricing)
        prompt_tokens = Decimal(result.tokens[0])
        completion_tokens = Decimal(result.tokens[1])
        cost = pricing * prompt_tokens + completion * completion_tokens
        
        # Prepare result data
        result_data = {
            'result': result.result.success,  # Fixed: Extract boolean from Result object
            'prompt': work_item.task.prompt,
            'code': result.code,
            'run': work_item.run,
            'task_type': work_item.task.__class__.__name__,
            'response': result.response,
            'output': result.output,
            'expected_output': result.expected_output,
            'errors': result.errors,
            'is_lang_specific': work_item.task.is_lang_specific,
            'mutated_code': result.mutated_code,
        }
        
        logging.info(f"Completed {work_item.task.filename}: {'SUCCESS' if result.result else 'FAILURE'} in {duration:.2f}s")
        
        return ProcessedResult(
            success=True,
            model=work_item.model,
            language=work_item.language.value,
            task_name=work_item.task.filename,
            result_data=result_data,
            cost=cost,
            duration=duration
        )
        
    except Exception as e:
        logging.error(f"Error processing {work_item.task.filename}: {str(e)}")
        # Ensure expected_output is always a string
        expected = getattr(work_item.task, 'expected_output', '')
        if not isinstance(expected, str):
            expected = json.dumps(expected)
        
        return ProcessedResult(
            success=False,
            model=work_item.model,
            language=work_item.language.value,
            task_name=work_item.task.filename,
            result_data={
                'result': False,
                'errors': [str(e)],
                'run': work_item.run,
                'task_type': work_item.task.__class__.__name__,
                'prompt': work_item.task.prompt,
                'code': '',
                'response': '',
                'output': '',
                'expected_output': expected,  # Fixed: Always ensure it's a string
                'is_lang_specific': work_item.task.is_lang_specific,
                'mutated_code': '',
            },
            cost=Decimal(0),
            duration=time.time() - start_time if 'start_time' in locals() else 0,
            error=str(e)
        )


def process_task_batch(task_batch: List[WorkItem]) -> List[ProcessedResult]:
    """Process a batch of tasks sequentially within a worker."""
    results = []
    for work_item in task_batch:
        result = process_single_task(work_item)
        results.append(result)
    return results


class ProgressTracker:
    """Track and display progress across all workers."""
    
    def __init__(self, total_tasks: int):
        self.total_tasks = total_tasks
        self.completed = 0
        self.start_time = time.time()
        self.lock = Manager().Lock()
    
    def update(self, count: int = 1):
        """Update progress counter."""
        with self.lock:
            self.completed += count
            self._display_progress()
    
    def _display_progress(self):
        """Display current progress."""
        elapsed = time.time() - self.start_time
        rate = self.completed / elapsed if elapsed > 0 else 0
        remaining = (self.total_tasks - self.completed) / rate if rate > 0 else 0
        
        print(f"\rProgress: {self.completed}/{self.total_tasks} "
              f"({self.completed/self.total_tasks*100:.1f}%) "
              f"Rate: {rate:.2f} tasks/sec "
              f"ETA: {remaining/60:.1f} min", end='', flush=True)


def create_work_items(
    models: List[str],
    languages: List[Language],
    model_infos: Dict[str, ModelInfo],
    skip_lang_specific: bool,
    limit: Optional[str] = None,
    existing_results: Optional[Any] = None
) -> List[WorkItem]:
    """Create all work items, filtering out already completed tasks."""
    work_items = []
    
    for model in models:
        model_info = model_infos[model]
        for language in languages:
            tasks = load_all_tasks(language, skip_lang_specific)
            
            for task in tasks:
                # Skip if limit is set and doesn't match
                if limit and task.filename != limit:
                    continue
                
                # Skip if already processed
                if existing_results and existing_results.has_result(
                    1, task.filename, model, language.value
                ):
                    logging.info(f"Skipping {task.filename} for {model}/{language.value} - already exists")
                    continue
                
                work_items.append(WorkItem(
                    model=model,
                    language=language,
                    task=task,
                    run=1,  # For now, only support single run
                    model_info=model_info,
                    skip_lang_specific=skip_lang_specific
                ))
    
    return work_items


def parallel_execute(
    models: List[str],
    languages: List[Language],
    db: Any,  # ResultDB instance
    skip_lang_specific: bool = True,
    limit: Optional[str] = None,
    worker_processes: int = 8,
    batch_size: int = 1,
    llm_rate_limit: int = 30
) -> None:
    """
    Execute benchmark tasks in parallel using multiprocessing.Pool.
    
    Args:
        models: List of model identifiers
        languages: List of languages to test
        db: ResultDB instance for storing results
        skip_lang_specific: Whether to skip language-specific tasks
        limit: Optional filename to limit execution to single task
        worker_processes: Number of worker processes
        batch_size: Number of tasks to process per worker call
        llm_rate_limit: Maximum LLM API calls per minute
    """
    # Get model information
    model_infos = model_info(models)
    
    # Create work items
    print("Preparing work items...")
    work_items = create_work_items(
        models, languages, model_infos, skip_lang_specific, limit, db
    )
    
    if not work_items:
        print("No tasks to process.")
        return
    
    print(f"Total tasks to process: {len(work_items)}")
    
    # Set up progress tracking
    progress = ProgressTracker(len(work_items))
    
    # Create manager for shared state
    manager = Manager()
    rl = RateLimiter(manager, llm_rate_limit)
    
    # Initialize accumulators for costs and durations
    model_language_costs = {}
    model_language_durations = {}
    model_language_start_times = {}
    
    # Record start times for each model/language combination
    for model in models:
        for language in languages:
            key = (model, language.value)
            model_language_costs[key] = Decimal(0)
            model_language_durations[key] = 0
            model_language_start_times[key] = time.time()
    
    # Process with pool
    print(f"Starting {worker_processes} worker processes...")
    
    with Pool(
        processes=worker_processes,
        initializer=init_worker,
        initargs=(rl,)
    ) as pool:
        
        # Process in batches
        if batch_size > 1:
            # Group into batches
            batches = [
                work_items[i:i+batch_size]
                for i in range(0, len(work_items), batch_size)
            ]
            
            # Process batches
            for batch_results in pool.imap_unordered(process_task_batch, batches):
                for result in batch_results:
                    # Create Result object to pass to add_result
                    task_result = Result(
                        success=result.result_data['result'], 
                        errors=result.result_data['errors']
                    )
                    
                    # Add to database (both successful and failed executions)
                    db.add_result(
                        result=task_result,
                        model=result.model,
                        task_name=result.task_name,
                        prompt=result.result_data.get('prompt', ''),
                        code=result.result_data.get('code', ''),
                        run=result.result_data['run'],
                        task_type=result.result_data['task_type'],
                        response=result.result_data.get('response', ''),
                        output=result.result_data.get('output', ''),
                        expected_output=result.result_data.get('expected_output', ''),
                        language=Language(result.language),
                        errors=result.result_data['errors'],
                        cost=result.cost,
                        duration=result.duration,
                        is_lang_specific=result.result_data.get('is_lang_specific', False),
                        mutated_code=result.result_data.get('mutated_code', ''),
                    )
                    
                    # Accumulate costs
                    key = (result.model, result.language)
                    model_language_costs[key] += result.cost
                    
                    progress.update(1)
                
                # Periodic save
                if progress.completed % 50 == 0:
                    db.save_db()
        
        else:
            # Process individual tasks
            for result in pool.imap_unordered(process_single_task, work_items):
                # Create Result object to pass to add_result
                task_result = Result(
                    success=result.result_data['result'], 
                    errors=result.result_data['errors']
                )
                
                # Add to database (both successful and failed executions)
                db.add_result(
                    result=task_result,
                    model=result.model,
                    task_name=result.task_name,
                    prompt=result.result_data.get('prompt', ''),
                    code=result.result_data.get('code', ''),
                    run=result.result_data['run'],
                    task_type=result.result_data['task_type'],
                    response=result.result_data.get('response', ''),
                    output=result.result_data.get('output', ''),
                    expected_output=result.result_data.get('expected_output', ''),
                    language=Language(result.language),
                    errors=result.result_data['errors'],
                    cost=result.cost,
                    duration=result.duration,
                    is_lang_specific=result.result_data.get('is_lang_specific', False),
                    mutated_code=result.result_data.get('mutated_code', ''),
                )
                
                # Accumulate costs
                key = (result.model, result.language)
                model_language_costs[key] += result.cost
                
                progress.update(1)
                
                # Periodic save
                if progress.completed % 50 == 0:
                    db.save_db()
    
    print("\n\nProcessing complete!")
    
    # Calculate and save total costs/durations per model/language
    print("Calculating totals...")
    
    # Calculate durations and set totals in the database
    for model in models:
        for language in languages:
            key = (model, language.value)
            if key in model_language_costs:
                # Calculate total duration for this model/language
                duration = time.time() - model_language_start_times[key]
                
                # Set totals in database
                db.set_total_costs(model, language.value, model_language_costs[key])
                db.set_total_duration(model, language.value, duration)
    
    # Final save
    db.save_db()
    print("Results saved.")
    
    # Print analysis
    print("\n" + db.analyze())