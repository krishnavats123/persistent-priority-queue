"""
Persistent Priority Queue Implementation

A file-based persistent priority queue using dual heaps (min-heap and max-heap)
with version-based lazy deletion for efficient extract_min and extract_max operations.

Author: Saralweb SDE Screening Assignment
"""

import json
import uuid
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from heapq import heappush, heappop


@dataclass
class QueueItem:
    """Represents an item in the priority queue."""
    id: str
    value: Any
    priority: int


class PersistentPriorityQueue:
    """
    A persistent priority queue that supports efficient extraction of both
    minimum and maximum priority items.
    
    Uses dual heaps (min-heap and max-heap) with version-based lazy deletion 
    for O(log n) insertion, extraction, update, and deletion operations.
    
    Persistence is handled via JSON file storage with atomic writes.
    
    Example:
        >>> queue = PersistentPriorityQueue()
        >>> item_id = queue.insert("Task A", 5)
        >>> queue.insert("Task B", 2)
        >>> queue.insert("Task C", 8)
        >>> queue.peek()
        QueueItem(id='...', value='Task B', priority=2)
        >>> queue.extract_min()
        QueueItem(id='...', value='Task B', priority=2)
        >>> queue.extract_max()
        QueueItem(id='...', value='Task C', priority=8)
    """
    
    def __init__(self, data_dir: Optional[str] = None, filename: str = "queue.json"):
        """
        Initialize the persistent priority queue.
        
        Args:
            data_dir: Directory for persistence file. Defaults to 'data' subdirectory
                     relative to this module.
            filename: Name of the JSON persistence file. Defaults to 'queue.json'.
        
        Raises:
            ValueError: If the persistence file contains invalid JSON.
            OSError: If there are permission issues with the data directory.
        """
        if data_dir is None:
            # Default to data/ directory relative to this file
            module_dir = Path(__file__).parent
            self.data_dir = module_dir / "data"
        else:
            self.data_dir = Path(data_dir)
        
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.filepath = self.data_dir / filename
        
        # Internal data structures
        # Heap entries: (priority, version, id, value)
        self._min_heap: List[Tuple[int, int, str, Any]] = []
        self._max_heap: List[Tuple[int, int, str, Any]] = []
        # id -> (priority, value, version)
        self._item_map: Dict[str, Tuple[int, Any, int]] = {}
        
        # Load existing state
        self._load()
    
    def _load(self) -> None:
        """Load queue state from persistence file."""
        if not self.filepath.exists():
            return
        
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # Handle empty file gracefully
            if not content:
                return
            
            data = json.loads(content)
            
            if not isinstance(data, list):
                raise ValueError("Invalid queue data format: expected a list of items")
            
            version = 0
            for item_data in data:
                if not isinstance(item_data, dict):
                    continue
                item_id = item_data.get('id')
                value = item_data.get('value')
                priority = item_data.get('priority')
                
                if item_id is None or priority is None:
                    continue
                
                # Rebuild heaps and map with version
                self._item_map[item_id] = (priority, value, version)
                heappush(self._min_heap, (priority, version, item_id, value))
                heappush(self._max_heap, (-priority, version, item_id, value))
                version += 1
                
        except json.JSONDecodeError as e:
            raise ValueError(f"Corrupted persistence file: invalid JSON - {e}")
        except (OSError, IOError) as e:
            raise OSError(f"Failed to read persistence file: {e}")
    
    def _save(self) -> None:
        """Save queue state to persistence file atomically."""
        # Prepare data for serialization (without version)
        items = [
            {"id": item_id, "value": value, "priority": priority}
            for item_id, (priority, value, _) in self._item_map.items()
        ]
        
        # Atomic write: write to temp file then rename
        temp_path = self.filepath.with_suffix('.tmp')
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
            temp_path.replace(self.filepath)
        except (OSError, IOError) as e:
            # Clean up temp file on failure
            if temp_path.exists():
                temp_path.unlink()
            raise OSError(f"Failed to write persistence file: {e}")
    
    def _clean_min_heap(self) -> None:
        """Remove stale entries from min heap top."""
        while self._min_heap:
            priority, version, item_id, value = self._min_heap[0]
            # Check if this entry is still valid
            if item_id in self._item_map:
                _, _, current_version = self._item_map[item_id]
                if current_version == version:
                    break  # Valid entry
            heappop(self._min_heap)
    
    def _clean_max_heap(self) -> None:
        """Remove stale entries from max heap top."""
        while self._max_heap:
            neg_priority, version, item_id, value = self._max_heap[0]
            if item_id in self._item_map:
                _, _, current_version = self._item_map[item_id]
                if current_version == version:
                    break
            heappop(self._max_heap)
    
    def insert(self, value: Any, priority: int) -> str:
        """
        Insert a new item into the priority queue.
        
        Args:
            value: The value to store (can be any JSON-serializable type).
            priority: Integer priority. Lower number = higher priority.
        
        Returns:
            Unique ID of the inserted item.
        
        Raises:
            TypeError: If priority is not an integer.
            ValueError: If value is not JSON-serializable.
        """
        if not isinstance(priority, int):
            raise TypeError("Priority must be an integer")
        
        # Generate unique ID
        item_id = str(uuid.uuid4())
        version = 0
        
        # Add to internal structures
        self._item_map[item_id] = (priority, value, version)
        heappush(self._min_heap, (priority, version, item_id, value))
        heappush(self._max_heap, (-priority, version, item_id, value))
        
        # Persist
        self._save()
        
        return item_id
    
    def extract_min(self) -> QueueItem:
        """
        Remove and return the item with the minimum priority (highest priority).
        
        Returns:
            QueueItem containing the removed item's id, value, and priority.
        
        Raises:
            IndexError: If the queue is empty.
        """
        if self.is_empty():
            raise IndexError("Cannot extract from empty queue")
        
        self._clean_min_heap()
        
        if not self._min_heap:
            raise IndexError("Cannot extract from empty queue")
        
        priority, version, item_id, value = heappop(self._min_heap)
        
        # Verify this entry is still valid (not stale)
        if item_id not in self._item_map:
            # Stale entry, try next
            return self.extract_min()
        
        _, _, current_version = self._item_map[item_id]
        if current_version != version:
            # Stale entry, try next
            return self.extract_min()
        
        # Remove from map
        del self._item_map[item_id]
        
        # Persist
        self._save()
        
        return QueueItem(id=item_id, value=value, priority=priority)
    
    def extract_max(self) -> QueueItem:
        """
        Remove and return the item with the maximum priority (lowest priority).
        
        Returns:
            QueueItem containing the removed item's id, value, and priority.
        
        Raises:
            IndexError: If the queue is empty.
        """
        if self.is_empty():
            raise IndexError("Cannot extract from empty queue")
        
        self._clean_max_heap()
        
        if not self._max_heap:
            raise IndexError("Cannot extract from empty queue")
        
        neg_priority, version, item_id, value = heappop(self._max_heap)
        priority = -neg_priority
        
        # Verify this entry is still valid (not stale)
        if item_id not in self._item_map:
            return self.extract_max()
        
        _, _, current_version = self._item_map[item_id]
        if current_version != version:
            return self.extract_max()
        
        # Remove from map
        del self._item_map[item_id]
        
        # Persist
        self._save()
        
        return QueueItem(id=item_id, value=value, priority=priority)
    
    def peek(self) -> QueueItem:
        """
        Return the item with the minimum priority WITHOUT removing it.
        
        Returns:
            QueueItem containing the highest-priority item's id, value, and priority.
        
        Raises:
            IndexError: If the queue is empty.
        """
        if self.is_empty():
            raise IndexError("Cannot peek empty queue")
        
        self._clean_min_heap()
        
        if not self._min_heap:
            raise IndexError("Cannot peek empty queue")
        
        priority, version, item_id, value = self._min_heap[0]
        
        # Verify entry is valid
        if item_id not in self._item_map:
            # Stale entry at top, clean and retry
            heappop(self._min_heap)
            return self.peek()
        
        _, _, current_version = self._item_map[item_id]
        if current_version != version:
            heappop(self._min_heap)
            return self.peek()
        
        return QueueItem(id=item_id, value=value, priority=priority)
    
    def update(self, item_id: str, priority: int) -> None:
        """
        Update the priority of an existing item.
        
        Args:
            item_id: The unique ID of the item to update.
            priority: New integer priority. Lower number = higher priority.
        
        Raises:
            KeyError: If item_id does not exist.
            TypeError: If priority is not an integer.
        """
        if not isinstance(priority, int):
            raise TypeError("Priority must be an integer")
        
        if item_id not in self._item_map:
            raise KeyError(f"Item with id '{item_id}' not found")
        
        old_priority, value, old_version = self._item_map[item_id]
        
        if old_priority == priority:
            return  # No change needed
        
        # Increment version to invalidate old heap entries
        new_version = old_version + 1
        
        # Update the item map with new priority and version
        self._item_map[item_id] = (priority, value, new_version)
        
        # Add new entries to heaps with new version
        heappush(self._min_heap, (priority, new_version, item_id, value))
        heappush(self._max_heap, (-priority, new_version, item_id, value))
        
        # Persist
        self._save()
    
    def delete(self, item_id: str) -> QueueItem:
        """
        Delete an item from the queue by its ID.
        
        Args:
            item_id: The unique ID of the item to delete.
        
        Returns:
            QueueItem containing the deleted item's id, value, and priority.
        
        Raises:
            KeyError: If item_id does not exist.
        """
        if item_id not in self._item_map:
            raise KeyError(f"Item with id '{item_id}' not found")
        
        priority, value, _ = self._item_map[item_id]
        
        # Remove from map (invalidates all heap entries for this ID)
        del self._item_map[item_id]
        
        # Persist
        self._save()
        
        return QueueItem(id=item_id, value=value, priority=priority)
    
    def is_empty(self) -> bool:
        """
        Check if the queue is empty.
        
        Returns:
            True if the queue contains no items, False otherwise.
        """
        return len(self._item_map) == 0
    
    def __len__(self) -> int:
        """Return the number of items in the queue."""
        return len(self._item_map)
    
    def __contains__(self, item_id: str) -> bool:
        """Check if an item ID exists in the queue."""
        return item_id in self._item_map
    
    def get_all_items(self) -> List[QueueItem]:
        """
        Return all items in the queue (unsorted).
        
        Returns:
            List of QueueItem objects.
        """
        return [
            QueueItem(id=item_id, value=value, priority=priority)
            for item_id, (priority, value, _) in self._item_map.items()
        ]


# Convenience function for direct usage
def create_queue(data_dir: Optional[str] = None) -> PersistentPriorityQueue:
    """
    Factory function to create a PersistentPriorityQueue instance.
    
    Args:
        data_dir: Optional custom data directory path.
    
    Returns:
        PersistentPriorityQueue instance.
    """
    return PersistentPriorityQueue(data_dir=data_dir)


if __name__ == "__main__":
    # Simple demonstration
    queue = PersistentPriorityQueue()
    
    print("=== Persistent Priority Queue Demo ===\n")
    
    # Insert items
    id1 = queue.insert("Fix production bug", 1)
    id2 = queue.insert("Update documentation", 5)
    id3 = queue.insert("Reply to email", 10)
    id4 = queue.insert("Code review", 3)
    
    print(f"Inserted 4 items. Queue size: {len(queue)}")
    print(f"Peek (min priority): {queue.peek()}")
    print(f"Extract min: {queue.extract_min()}")
    print(f"Extract max: {queue.extract_max()}")
    print(f"Queue size after extractions: {len(queue)}")
    
    # Update - use id2 which still exists (documentation task)
    print(f"\nUpdating item {id2[:8]}... from priority 5 to priority 2")
    queue.update(id2, priority=2)
    print(f"New peek: {queue.peek()}")
    
    # Delete
    print(f"\nDeleting item {id4[:8]}... (Code review)")
    queue.delete(id4)
    print(f"Queue size after delete: {len(queue)}")
    
    print(f"\nRemaining items: {queue.get_all_items()}")
    print(f"Is empty: {queue.is_empty()}")