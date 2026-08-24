# Persistent Priority Queue

This project implements a persistent priority queue in Python. It maintains separate min-heap and max-heap structures so that both minimum and maximum priority items can be extracted efficiently. The queue state is stored in a JSON file so that it can be restored after the process is restarted.

## Overview

The `PersistentPriorityQueue` class provides a priority queue with the usual operations (insert, extract min/max, peek, update, delete) and persists its state to `data/queue.json`. Lower priority numbers mean higher priority.

## Features

| Operation | Description |
|-----------|-------------|
| `insert(value, priority)` | Add item, returns unique ID |
| `extract_min()` | Remove and return highest-priority item (lowest number) |
| `extract_max()` | Remove and return lowest-priority item (highest number) |
| `peek()` | View highest-priority item without removal |
| `update(item_id, priority)` | Change priority of existing item |
| `delete(item_id)` | Remove specific item by ID |
| `is_empty()` | Check if queue has no items |
| `len(queue)` | Get item count |
| `item_id in queue` | Check if item exists |

## Implementation

### Dual Heaps

The implementation uses two heaps:

- `_min_heap`: list of tuples `(priority, version, item_id, value)` — min-heap ordered by priority, then version, then item_id
- `_max_heap`: list of tuples `(-priority, version, item_id, value)` — max-heap using negated priority, then version, then item_id

The current state of each item is stored in `_item_map: Dict[str, Tuple[int, Any, int]]` mapping `item_id` to `(priority, value, version)`.

### Version-Based Lazy Deletion

Instead of removing items from both heaps immediately on update or delete (which would be O(n)), the implementation uses version numbers:

- Each item in `_item_map` has a version counter starting at 0.
- On `update()`, the version is incremented, the new `(priority, value, version)` is stored in `_item_map`, and new entries are pushed to both heaps with the new version.
- On `delete()`, the item is removed from `_item_map`. All heap entries for that item_id become stale because they no longer have a matching entry in `_item_map`.
- When a heap operation reaches the top, `_clean_min_heap()` or `_clean_max_heap()` compares the heap entry's version against the current version in `_item_map` (or checks if the item_id exists at all). Stale entries are popped and discarded.

This keeps heap operations at O(log n) while deferring cleanup.

### Persistence

- State is stored in `data/queue.json` as a JSON array of objects: `{"id": "...", "value": "...", "priority": N}`.
- The file is created automatically on first use.
- On initialization, `_load()` reads the file and rebuilds both heaps and `_item_map` with version 0 for each item.
- Every mutating operation (`insert`, `extract_min`, `extract_max`, `update`, `delete`) calls `_save()` after modifying the in-memory structures.
- `_save()` writes to a temporary file (`queue.json.tmp`) first, then replaces the target file using `os.replace()`. If the write fails before replacement, the temporary file is cleaned up and the existing persistence file is left unchanged.
- The in-memory structures are modified before `_save()` is called. If persistence fails, the in-memory state is not rolled back.

## API Usage

```python
from module import PersistentPriorityQueue

queue = PersistentPriorityQueue()

# Insert tasks (lower number = higher priority)
bug_id = queue.insert("Fix production bug", 1)
doc_id = queue.insert("Update documentation", 5)
email_id = queue.insert("Reply to email", 10)

print(f"Queue size: {len(queue)}")  # 3

# View highest priority without removing
next_task = queue.peek()
print(f"Next up: {next_task.value} (priority {next_task.priority})")

# Process highest priority task
completed = queue.extract_min()
print(f"Completed: {completed.value}")

# Process lowest priority task
later = queue.extract_max()
print(f"Deferred: {later.value}")

# Update priority
queue.update(doc_id, priority=2)
print(f"New peek: {queue.peek().value}")

# Delete a task
queue.delete(doc_id)
print(f"Remaining: {len(queue)}")

print(f"Is empty: {queue.is_empty()}")
```

### Error Handling

```python
from module import PersistentPriorityQueue

queue = PersistentPriorityQueue()

# Empty queue operations raise IndexError
try:
    queue.extract_min()
except IndexError as e:
    print(f"Error: {e}")

# Invalid ID operations raise KeyError
try:
    queue.update("fake-id", priority=1)
except KeyError as e:
    print(f"Error: {e}")

try:
    queue.delete("fake-id")
except KeyError as e:
    print(f"Error: {e}")
```

### Custom Data Directory

```python
queue = PersistentPriorityQueue(data_dir="/var/lib/myapp/queue")
```

## Complexity Analysis

| Operation | In-memory | Persistence I/O |
|-----------|-----------|-----------------|
| `insert` | O(log n) | O(n) |
| `extract_min` | O(log n) amortized | O(n) |
| `extract_max` | O(log n) amortized | O(n) |
| `peek` | O(1) amortized* | O(1) |
| `update` | O(log n) | O(n) |
| `delete` | O(1) | O(n) |
| `is_empty` | O(1) | O(1) |
| `__len__` | O(1) | O(1) |
| `__contains__` | O(1) | O(1) |

* `peek()` calls `_clean_min_heap()` which may pop multiple stale entries. In the worst case it is O(k log n) where k is the number of stale entries at the top, but each stale entry is removed at most once, so the amortized cost over a sequence of operations is O(1).

**Persistence note**: Every mutating operation serializes the entire `_item_map` to JSON, which is O(n) I/O. The heaps are not persisted directly; they are rebuilt from `_item_map` on load.

**Space**: The heaps can accumulate stale entries from updates and deletes until they reach the top and are cleaned. In the worst case the heaps hold O(m) entries where m is the total number of insert/update operations since the last cleanup of those entries.

## Design Choice: File-Based Persistence

This assignment allowed either file-based storage or PostgreSQL. File-based persistence was chosen because:

- Zero external dependencies (standard library only)
- Easy setup and demonstration for an SDE screening assignment
- Sufficient for the scope of this assignment

Limitations compared with PostgreSQL:
- No concurrent writers (simultaneous processes will corrupt data)
- Full-file serialization on every mutation (O(n) I/O)
- Must load entire queue into memory
- No built-in locking or transactions beyond atomic file replacement

PostgreSQL would be preferable for concurrent or large-scale workloads.

## Real-World Priority Queue Use Cases

Priority queues are used in:

- Task/job scheduling (CI/CD, cron)
- Operating system process scheduling
- Network packet prioritization (QoS)
- Customer support ticket prioritization
- Shortest-path algorithms (Dijkstra's algorithm)
- Event-driven simulation

These are general applications of priority queues; this specific JSON-based implementation is intended for the assignment scope.

## Running the Project

### Prerequisites
- Python 3.8+

### Installation
```bash
cd persistent-priority-queue
# No dependencies required (stdlib only)
```

### Run Tests
```bash
python -m unittest discover -v
```

### Quick Demo
```bash
python module.py
```

### Verify Persistence (PowerShell compatible)

```powershell
# Run 1: Create queue and add items
python -c "from module import PersistentPriorityQueue; q = PersistentPriorityQueue(); id1 = q.insert('Task A', 5); id2 = q.insert('Task B', 2); print(f'Created: {id1[:8]}, {id2[:8]}'); print(f'Size: {len(q)}')"

# Run 2: New process, same data
python -c "from module import PersistentPriorityQueue; q = PersistentPriorityQueue(); print(f'Loaded size: {len(q)}'); print(f'Peek: {q.peek().value} (priority {q.peek().priority})')"
```

## Testing

The test suite (`test_module.py`) uses Python's standard `unittest` framework and covers:
- Basic operations (insert, peek, extract_min, extract_max, is_empty)
- Update (increase/decrease priority)
- Delete (existing and nonexistent items)
- Duplicate priorities
- Persistence across instances
- Empty queue operations
- Invalid IDs
- Corrupted persistence data (malformed JSON, empty file, invalid format)

Run with:
```bash
python -m unittest discover -v
```

## Project Structure

```
persistent-priority-queue/
├── module.py          # Main implementation (required filename)
├── test_module.py     # Test suite
├── README.md          # This file
├── requirements.txt   # Dependencies (empty - stdlib only)
├── .gitignore         # Git ignore rules
└── data/
    └── queue.json     # Persistence file (auto-created)
```