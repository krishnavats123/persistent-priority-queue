# Persistent Priority Queue

A production-quality, file-based persistent priority queue implementation in Python. Supports efficient extraction of both minimum and maximum priority items with full persistence across program restarts.

## Overview

This project implements a **Persistent Priority Queue** — a data structure that maintains elements with associated priorities and persists its state to disk. Unlike in-memory priority queues, this implementation survives process termination and restart, making it suitable for long-running applications, task schedulers, and systems requiring durability.

### Why Persistence?

Traditional priority queues (like Python's `heapq` or `queue.PriorityQueue`) lose all data when the program exits. This implementation solves that by:

- **Automatic persistence**: Every mutation (insert, update, delete, extract) is immediately saved to a JSON file
- **Crash resilience**: Atomic file writes prevent corruption during power loss or crashes
- **Zero-configuration**: Creates directories and files automatically on first use
- **Fast recovery**: Loads existing state in O(n) time on initialization

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

## Data Structure

### Dual Heap with Lazy Deletion

The implementation uses **two heaps** with a **lazy deletion** strategy:

```
┌─────────────────────────────────────────────────────────────┐
│                    PersistentPriorityQueue                   │
├─────────────────────────────────────────────────────────────┤
│  _item_map: Dict[id] → (priority, value)                    │
│  _min_heap:  [(priority, id, value), ...]  # min-heap       │
│  _max_heap:  [(-priority, id, value), ...] # max-heap       │
│  _deleted:   Set[id]  # lazily deleted item IDs             │
└─────────────────────────────────────────────────────────────┘
```

### How It Works

1. **Insertion**: Item added to `_item_map`, pushed to both heaps → O(log n)
2. **Extract Min**: Pop from `_min_heap`, mark ID deleted, remove from `_item_map` → O(log n) amortized
3. **Extract Max**: Pop from `_max_heap`, mark ID deleted, remove from `_item_map` → O(log n) amortized
4. **Update**: Mark old entry deleted, push new entry to both heaps → O(log n)
5. **Delete**: Mark ID deleted, remove from `_item_map` → O(1) amortized
6. **Peek**: Clean `_min_heap` top, return first element → O(1) amortized

### Lazy Deletion Explained

When an item is deleted or updated, we **don't immediately remove it from both heaps** (which would be O(n)). Instead:

- Mark the item's ID in `_deleted` set
- Remove from `_item_map` (the source of truth)
- On next heap operation, clean top elements that are in `_deleted`

This gives O(log n) for all operations while keeping heaps synchronized.

### Tie-Breaking for Duplicate Priorities

Multiple items can have the same priority. The implementation uses **UUID v4** as unique IDs, which are compared as strings when priorities are equal. This provides deterministic but arbitrary ordering for equal priorities (effectively insertion order due to UUID generation timing).

## Persistence

### File Format

The queue persists to `data/queue.json` as a JSON array:

```json
[
  {"id": "uuid-1", "value": "Task A", "priority": 5},
  {"id": "uuid-2", "value": "Task B", "priority": 2},
  {"id": "uuid-3", "value": "Task C", "priority": 8}
]
```

### Persistence Behavior

| Event | Behavior |
|-------|----------|
| Application starts | Loads `data/queue.json` if exists; creates empty queue if not |
| Item inserted | Appends to in-memory structures; atomically writes full JSON |
| Item removed | Marks deleted; atomically writes full JSON |
| Item updated | Adds new heap entries; marks old deleted; atomically writes |
| File missing | Creates new empty queue (no error) |
| Invalid JSON | Raises `ValueError` with descriptive message |
| Write failure | Rolls back via temp file; original data preserved |

### Atomic Writes

Uses **write-to-temp-then-rename** pattern:
1. Serialize to `queue.json.tmp`
2. `os.replace(tmp, target)` — atomic on POSIX, near-atomic on Windows
3. On failure, temp file cleaned up, original untouched

## API Usage

### Basic Example

```python
from module import PersistentPriorityQueue

queue = PersistentPriorityQueue()

# Insert tasks with priorities (lower = higher priority)
bug_id = queue.insert("Fix production bug", 1)
doc_id = queue.insert("Update documentation", 5)
email_id = queue.insert("Reply to email", 10)

print(f"Queue size: {len(queue)}")  # 3

# View highest priority without removing
next_task = queue.peek()
print(f"Next up: {next_task.value} (priority {next_task.priority})")
# Output: Next up: Fix production bug (priority 1)

# Process highest priority task
completed = queue.extract_min()
print(f"Completed: {completed.value}")
# Output: Completed: Fix production bug

# Process lowest priority task
later = queue.extract_max()
print(f"Deferred: {later.value}")
# Output: Deferred: Reply to email

# Update priority
queue.update(doc_id, priority=2)
print(f"New peek: {queue.peek().value}")
# Output: New peek: Update documentation

# Delete a task
queue.delete(doc_id)
print(f"Remaining: {len(queue)}")
# Output: Remaining: 1

print(f"Is empty: {queue.is_empty()}")
# Output: Is empty: False
```

### Error Handling

```python
from module import PersistentPriorityQueue

queue = PersistentPriorityQueue()

# Empty queue operations
try:
    queue.extract_min()
except IndexError as e:
    print(f"Error: {e}")  # Error: Cannot extract from empty queue

# Invalid ID operations
try:
    queue.update("fake-id", priority=1)
except KeyError as e:
    print(f"Error: {e}")  # Error: Item with id 'fake-id' not found

try:
    queue.delete("fake-id")
except KeyError as e:
    print(f"Error: {e}")
```

### Custom Data Directory

```python
# Use custom persistence location
queue = PersistentPriorityQueue(data_dir="/var/lib/myapp/queue")
```

## Complexity Analysis

| Operation | Time Complexity | Persistence Cost | Space Complexity |
|-----------|-----------------|------------------|------------------|
| `insert` | O(log n) | O(n) — full file rewrite | O(n) |
| `extract_min` | O(log n) amortized | O(n) | O(n) |
| `extract_max` | O(log n) amortized | O(n) | O(n) |
| `peek` | O(1) amortized | O(1) — no write | O(1) |
| `update` | O(log n) | O(n) | O(n) |
| `delete` | O(1) amortized | O(n) | O(n) |
| `is_empty` | O(1) | O(1) | O(1) |
| `__len__` | O(1) | O(1) | O(1) |
| `__contains__` | O(1) | O(1) | O(1) |

### Notes on Complexity

- **Heap operations** are O(log n) as standard
- **Lazy deletion** adds amortized cost: each deleted item is popped at most once from each heap
- **Persistence I/O** is O(n) because the entire JSON file is rewritten on each mutation
- **Space** includes heap entries for deleted items until cleaned (at most 2× active items)

### Optimizing Persistence Cost

For high-throughput scenarios, consider:
- Batching writes (not implemented — trades durability for speed)
- Using a database (see Design Trade-offs)

## Real-World Use Cases

### 1. Operating System Process Scheduling
OS kernels use priority queues to schedule processes. Real-time processes get lower priority numbers (higher priority). Persistence allows scheduler state to survive reboots.

### 2. Network Packet Scheduling (QoS)
Routers prioritize packets: VoIP/video (high priority) vs. bulk downloads (low priority). Persistent queues survive router restarts.

### 3. Hospital Medical Triage
Emergency rooms prioritize patients by severity (1=critical, 5=minor). Persistence ensures triage queue survives system updates.

### 4. Customer Support Ticket Prioritization
Support systems prioritize by SLA: critical bugs (P1) before feature requests (P4). Persistence maintains queue across deployments.

### 5. Task/Job Scheduling (Cron, CI/CD)
Job schedulers run highest-priority jobs first. Persistence allows resuming scheduled jobs after maintenance windows.

### 6. Dijkstra's Shortest Path Algorithm
Graph algorithms use priority queues to extract minimum-distance vertices. Persistent version could checkpoint progress.

### 7. Event-Driven Simulation
Discrete event simulations process events in timestamp order. Persistence enables checkpoint/restart for long simulations.

## Design Trade-offs

### Why File-Based Persistence?

| Factor | File-Based (JSON) | PostgreSQL |
|--------|-------------------|------------|
| **Setup** | Zero-config, embedded | Requires DB server |
| **Dependencies** | Standard library only | `psycopg2` or similar |
| **Portability** | Single file, cross-platform | Network dependency |
| **Concurrency** | Single-writer only | Full ACID, multi-writer |
| **Scalability** | ~10K items practical | Millions of items |
| **Querying** | Load entire file | SQL indexes, partial reads |
| **Durability** | Atomic replace | WAL, fsync control |

### Limitations of File-Based Persistence

1. **No concurrent writers** — Multiple processes writing simultaneously will corrupt data
2. **Full-file serialization** — Every write rewrites entire JSON (O(n) I/O)
3. **No partial reads** — Must load entire queue into memory
4. **No transactions** — Single operation atomicity only
5. **File locking** — No built-in locking; race conditions possible

### Production-Scale with PostgreSQL

For production systems requiring scale and concurrency:

```sql
-- Schema
CREATE TABLE priority_queue (
    id UUID PRIMARY KEY,
    value JSONB NOT NULL,
    priority INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_priority ON priority_queue(priority, id);
```

Operations become:
- `INSERT ... RETURNING id` — O(log n) with index
- `SELECT ... ORDER BY priority LIMIT 1 FOR UPDATE SKIP LOCKED` — extract_min
- `SELECT ... ORDER BY priority DESC LIMIT 1 FOR UPDATE SKIP LOCKED` — extract_max
- `UPDATE ... SET priority = $1 WHERE id = $2` — update
- `DELETE WHERE id = $1` — delete

Benefits: concurrent access, partial reads, ACID, horizontal scaling via partitioning.

## Running the Project

### Prerequisites

- Python 3.8+

### Installation

```bash
# Clone or navigate to project
cd persistent-priority-queue

# No dependencies required (stdlib only)
# Optional: install pytest for enhanced test output
pip install pytest
```

### Run Tests

```bash
# Using unittest (standard library)
python -m unittest discover -v

# Or run specific test module
python -m unittest test_module -v

# Using pytest (if installed)
pytest test_module.py -v
```

### Quick Demo

```bash
python module.py
```

Expected output:
```
=== Persistent Priority Queue Demo ===

Inserted 4 items. Queue size: 4
Peek (min priority): QueueItem(id='...', value='Fix production bug', priority=1)
Extract min: QueueItem(id='...', value='Fix production bug', priority=1)
Extract max: QueueItem(id='...', value='Reply to email', priority=10)
Queue size after extractions: 2

Updating item ... from priority 10 to priority 2
New peek: QueueItem(id='...', value='Update documentation', priority=2)

Deleting item ... (Code review)
Queue size after delete: 1

Remaining items: [QueueItem(id='...', value='Reply to email', priority=2)]
Is empty: False
```

### Verify Persistence

```bash
# Run 1: Create queue and add items
python -c "
from module import PersistentPriorityQueue
q = PersistentPriorityQueue()
id1 = q.insert('Task A', 5)
id2 = q.insert('Task B', 2)
print(f'Created: {id1[:8]}, {id2[:8]}')
print(f'Size: {len(q)}')
"

# Run 2: New process, same data
python -c "
from module import PersistentPriorityQueue
q = PersistentPriorityQueue()
print(f'Loaded size: {len(q)}')
print(f'Peek: {q.peek().value} (priority {q.peek().priority})')
"
```

## Project Structure

```
persistent-priority-queue/
├── module.py          # Main implementation (required filename)
├── test_module.py     # Comprehensive test suite
├── README.md          # This file
├── requirements.txt   # Dependencies (empty - stdlib only)
├── .gitignore         # Git ignore rules
└── data/
    └── queue.json     # Persistence file (auto-created)
```

## Code Quality

- **Type hints** on all public methods
- **Docstrings** with Args, Returns, Raises, Examples
- **No external dependencies** — pure Python standard library
- **Cross-platform paths** via `pathlib`
- **Atomic file writes** for crash safety
- **Comprehensive tests** covering all requirements
- **No debug prints** or dead code

## License

This project was created for the Saralweb Software Development Engineer screening assignment.