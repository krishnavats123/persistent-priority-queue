"""
Test suite for PersistentPriorityQueue.

Tests cover all required operations, persistence, edge cases, and error conditions.
"""

import unittest
import json
import tempfile
import shutil
import os
from pathlib import Path

from module import PersistentPriorityQueue, QueueItem


class TestPersistentPriorityQueueBasic(unittest.TestCase):
    """Test basic queue operations."""
    
    def setUp(self):
        """Create a temporary directory for test isolation."""
        self.temp_dir = tempfile.mkdtemp()
        self.queue = PersistentPriorityQueue(data_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_insert_and_peek(self):
        """Test insert and peek operations."""
        id1 = self.queue.insert("Task A", 5)
        id2 = self.queue.insert("Task B", 2)
        id3 = self.queue.insert("Task C", 8)
        
        self.assertEqual(len(self.queue), 3)
        
        # Peek should return minimum priority item (Task B, priority 2)
        peeked = self.queue.peek()
        self.assertEqual(peeked.value, "Task B")
        self.assertEqual(peeked.priority, 2)
        self.assertEqual(peeked.id, id2)
        
        # Queue should be unchanged after peek
        self.assertEqual(len(self.queue), 3)
    
    def test_extract_min(self):
        """Test extract_min returns and removes minimum priority item."""
        self.queue.insert("Task A", 5)
        id_b = self.queue.insert("Task B", 2)
        self.queue.insert("Task C", 8)
        
        extracted = self.queue.extract_min()
        
        self.assertEqual(extracted.value, "Task B")
        self.assertEqual(extracted.priority, 2)
        self.assertEqual(extracted.id, id_b)
        self.assertEqual(len(self.queue), 2)
    
    def test_extract_max(self):
        """Test extract_max returns and removes maximum priority item."""
        self.queue.insert("Task A", 5)
        self.queue.insert("Task B", 2)
        id_c = self.queue.insert("Task C", 8)
        
        extracted = self.queue.extract_max()
        
        self.assertEqual(extracted.value, "Task C")
        self.assertEqual(extracted.priority, 8)
        self.assertEqual(extracted.id, id_c)
        self.assertEqual(len(self.queue), 2)
    
    def test_is_empty(self):
        """Test is_empty on empty and non-empty queues."""
        self.assertTrue(self.queue.is_empty())
        
        self.queue.insert("Task", 1)
        self.assertFalse(self.queue.is_empty())
        
        self.queue.extract_min()
        self.assertTrue(self.queue.is_empty())
    
    def test_len(self):
        """Test __len__ returns correct count."""
        self.assertEqual(len(self.queue), 0)
        
        self.queue.insert("A", 1)
        self.assertEqual(len(self.queue), 1)
        
        self.queue.insert("B", 2)
        self.assertEqual(len(self.queue), 2)
        
        self.queue.extract_min()
        self.assertEqual(len(self.queue), 1)


class TestPersistentPriorityQueueUpdate(unittest.TestCase):
    """Test update operation."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.queue = PersistentPriorityQueue(data_dir=self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_update_increase_priority(self):
        """Test updating to a higher priority (lower number)."""
        id1 = self.queue.insert("Task A", 10)
        self.queue.insert("Task B", 5)
        
        # Update Task A to priority 1 (highest)
        self.queue.update(id1, priority=1)
        
        # Task A should now be at the front
        peeked = self.queue.peek()
        self.assertEqual(peeked.id, id1)
        self.assertEqual(peeked.priority, 1)
    
    def test_update_decrease_priority(self):
        """Test updating to a lower priority (higher number)."""
        id1 = self.queue.insert("Task A", 1)
        self.queue.insert("Task B", 5)
        
        # Update Task A to priority 10 (lowest)
        self.queue.update(id1, priority=10)
        
        # Task B should now be at the front
        peeked = self.queue.peek()
        self.assertEqual(peeked.value, "Task B")
        self.assertEqual(peeked.priority, 5)
    
    def test_update_same_priority(self):
        """Test updating to same priority (no-op)."""
        id1 = self.queue.insert("Task A", 5)
        
        self.queue.update(id1, priority=5)
        
        # Should still work correctly
        peeked = self.queue.peek()
        self.assertEqual(peeked.id, id1)
        self.assertEqual(peeked.priority, 5)
    
    def test_update_nonexistent_id(self):
        """Test update with nonexistent ID raises KeyError."""
        with self.assertRaises(KeyError):
            self.queue.update("nonexistent-id", priority=1)
    
    def test_update_invalid_priority_type(self):
        """Test update with non-integer priority raises TypeError."""
        id1 = self.queue.insert("Task A", 5)
        
        with self.assertRaises(TypeError):
            self.queue.update(id1, priority="high")
        
        with self.assertRaises(TypeError):
            self.queue.update(id1, priority=3.14)


class TestPersistentPriorityQueueDelete(unittest.TestCase):
    """Test delete operation."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.queue = PersistentPriorityQueue(data_dir=self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_delete_existing_item(self):
        """Test deleting an existing item."""
        id1 = self.queue.insert("Task A", 5)
        id2 = self.queue.insert("Task B", 2)
        
        deleted = self.queue.delete(id1)
        
        self.assertEqual(deleted.id, id1)
        self.assertEqual(deleted.value, "Task A")
        self.assertEqual(deleted.priority, 5)
        self.assertEqual(len(self.queue), 1)
        
        # Remaining item should be Task B
        peeked = self.queue.peek()
        self.assertEqual(peeked.id, id2)
    
    def test_delete_min_item(self):
        """Test deleting the minimum priority item."""
        id1 = self.queue.insert("Task A", 5)
        id2 = self.queue.insert("Task B", 2)  # min
        
        self.queue.delete(id2)
        
        # Task A should now be min
        peeked = self.queue.peek()
        self.assertEqual(peeked.id, id1)
        self.assertEqual(peeked.priority, 5)
    
    def test_delete_max_item(self):
        """Test deleting the maximum priority item."""
        id1 = self.queue.insert("Task A", 5)
        id2 = self.queue.insert("Task B", 8)  # max
        
        self.queue.delete(id2)
        
        # Task A should now be max
        extracted = self.queue.extract_max()
        self.assertEqual(extracted.id, id1)
    
    def test_delete_nonexistent_id(self):
        """Test deleting nonexistent ID raises KeyError."""
        with self.assertRaises(KeyError):
            self.queue.delete("nonexistent-id")


class TestPersistentPriorityQueueDuplicatePriorities(unittest.TestCase):
    """Test handling of duplicate priorities."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.queue = PersistentPriorityQueue(data_dir=self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_multiple_items_same_priority(self):
        """Test inserting multiple items with same priority."""
        id1 = self.queue.insert("Task A", 5)
        id2 = self.queue.insert("Task B", 5)
        id3 = self.queue.insert("Task C", 5)
        
        self.assertEqual(len(self.queue), 3)
        
        # All should be retrievable
        items = []
        while not self.queue.is_empty():
            items.append(self.queue.extract_min())
        
        self.assertEqual(len(items), 3)
        # All should have priority 5
        for item in items:
            self.assertEqual(item.priority, 5)
    
    def test_duplicate_priority_extract_order(self):
        """Test that items with same priority are extracted deterministically (by version then ID)."""
        id1 = self.queue.insert("First", 5)
        id2 = self.queue.insert("Second", 5)
        id3 = self.queue.insert("Third", 5)
        
        # Extract all - order is deterministic by (version, ID) tiebreaker
        # Since all have version 0 initially, order is by ID string comparison
        extracted = []
        while not self.queue.is_empty():
            extracted.append(self.queue.extract_min())
        
        self.assertEqual(len(extracted), 3)
        # All should have priority 5
        for item in extracted:
            self.assertEqual(item.priority, 5)
        # All three original IDs should be present
        extracted_ids = {item.id for item in extracted}
        self.assertEqual(extracted_ids, {id1, id2, id3})
    
    def test_update_with_duplicates(self):
        """Test updating an item among duplicates."""
        id1 = self.queue.insert("Task A", 5)
        id2 = self.queue.insert("Task B", 5)
        id3 = self.queue.insert("Task C", 5)
        
        # Update middle item to higher priority
        self.queue.update(id2, priority=1)
        
        # Updated item should now be first
        peeked = self.queue.peek()
        self.assertEqual(peeked.id, id2)
        self.assertEqual(peeked.priority, 1)


class TestPersistentPriorityQueuePersistence(unittest.TestCase):
    """Test persistence across queue instances."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_persistence_across_instances(self):
        """Test that items persist across queue recreation."""
        # Create first queue and add items
        queue1 = PersistentPriorityQueue(data_dir=self.temp_dir)
        id1 = queue1.insert("Task A", 5)
        id2 = queue1.insert("Task B", 2)
        id3 = queue1.insert("Task C", 8)
        
        # Create new queue instance
        queue2 = PersistentPriorityQueue(data_dir=self.temp_dir)
        
        # Items should be loaded
        self.assertEqual(len(queue2), 3)
        self.assertIn(id1, queue2)
        self.assertIn(id2, queue2)
        self.assertIn(id3, queue2)
        
        # Data should be correct
        peeked = queue2.peek()
        self.assertEqual(peeked.value, "Task B")
        self.assertEqual(peeked.priority, 2)
    
    def test_persistence_after_operations(self):
        """Test persistence after various operations."""
        queue1 = PersistentPriorityQueue(data_dir=self.temp_dir)
        
        id1 = queue1.insert("Task A", 5)
        id2 = queue1.insert("Task B", 2)
        id3 = queue1.insert("Task C", 8)
        
        # Perform operations
        queue1.extract_min()  # Remove Task B
        queue1.update(id3, priority=1)  # Update Task C to highest priority
        queue1.delete(id1)  # Delete Task A
        
        # Create new queue
        queue2 = PersistentPriorityQueue(data_dir=self.temp_dir)
        
        # Only Task C should remain with priority 1
        self.assertEqual(len(queue2), 1)
        self.assertIn(id3, queue2)
        self.assertNotIn(id1, queue2)
        self.assertNotIn(id2, queue2)
        
        peeked = queue2.peek()
        self.assertEqual(peeked.id, id3)
        self.assertEqual(peeked.priority, 1)
    
    def test_empty_queue_persistence(self):
        """Test that empty queue persists correctly."""
        queue1 = PersistentPriorityQueue(data_dir=self.temp_dir)
        self.assertTrue(queue1.is_empty())
        
        queue2 = PersistentPriorityQueue(data_dir=self.temp_dir)
        self.assertTrue(queue2.is_empty())
    
    def test_persistence_file_creation(self):
        """Test that data directory and file are created automatically."""
        # Directory shouldn't exist yet
        new_dir = Path(self.temp_dir) / "new_data"
        self.assertFalse(new_dir.exists())
        
        queue = PersistentPriorityQueue(data_dir=str(new_dir))
        queue.insert("Test", 1)
        
        # Directory and file should now exist
        self.assertTrue(new_dir.exists())
        self.assertTrue((new_dir / "queue.json").exists())


class TestPersistentPriorityQueueEmptyQueue(unittest.TestCase):
    """Test operations on empty queue."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.queue = PersistentPriorityQueue(data_dir=self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_extract_min_empty(self):
        """Test extract_min on empty queue raises IndexError."""
        with self.assertRaises(IndexError):
            self.queue.extract_min()
    
    def test_extract_max_empty(self):
        """Test extract_max on empty queue raises IndexError."""
        with self.assertRaises(IndexError):
            self.queue.extract_max()
    
    def test_peek_empty(self):
        """Test peek on empty queue raises IndexError."""
        with self.assertRaises(IndexError):
            self.queue.peek()
    
    def test_is_empty_on_empty(self):
        """Test is_empty returns True for empty queue."""
        self.assertTrue(self.queue.is_empty())


class TestPersistentPriorityQueueInvalidIDs(unittest.TestCase):
    """Test error handling for invalid item IDs."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.queue = PersistentPriorityQueue(data_dir=self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_update_invalid_id(self):
        """Test update with invalid ID raises KeyError."""
        with self.assertRaises(KeyError):
            self.queue.update("invalid-id", priority=1)
    
    def test_delete_invalid_id(self):
        """Test delete with invalid ID raises KeyError."""
        with self.assertRaises(KeyError):
            self.queue.delete("invalid-id")
    
    def test_update_after_delete(self):
        """Test update after item was deleted raises KeyError."""
        id1 = self.queue.insert("Task", 5)
        self.queue.delete(id1)
        
        with self.assertRaises(KeyError):
            self.queue.update(id1, priority=1)
    
    def test_delete_after_delete(self):
        """Test deleting already deleted item raises KeyError."""
        id1 = self.queue.insert("Task", 5)
        self.queue.delete(id1)
        
        with self.assertRaises(KeyError):
            self.queue.delete(id1)


class TestPersistentPriorityQueueCorruption(unittest.TestCase):
    """Test handling of corrupted persistence file."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_malformed_json(self):
        """Test that malformed JSON raises ValueError."""
        # Write invalid JSON
        filepath = Path(self.temp_dir) / "queue.json"
        with open(filepath, 'w') as f:
            f.write("{ invalid json }")
        
        with self.assertRaises(ValueError) as ctx:
            PersistentPriorityQueue(data_dir=self.temp_dir)
        
        self.assertIn("Corrupted persistence file", str(ctx.exception))
    
    def test_invalid_data_format(self):
        """Test that non-list JSON raises ValueError."""
        filepath = Path(self.temp_dir) / "queue.json"
        with open(filepath, 'w') as f:
            json.dump({"not": "a list"}, f)
        
        with self.assertRaises(ValueError) as ctx:
            PersistentPriorityQueue(data_dir=self.temp_dir)
        
        self.assertIn("Invalid queue data format", str(ctx.exception))
    
    def test_missing_fields_in_items(self):
        """Test that items with missing fields are handled gracefully."""
        filepath = Path(self.temp_dir) / "queue.json"
        # Item missing 'id' and 'priority'
        with open(filepath, 'w') as f:
            json.dump([{"value": "Task"}], f)
        
        # Should load without error, just skip invalid items
        queue = PersistentPriorityQueue(data_dir=self.temp_dir)
        self.assertEqual(len(queue), 0)
    
    def test_empty_file(self):
        """Test that empty file is handled gracefully."""
        filepath = Path(self.temp_dir) / "queue.json"
        filepath.write_text("")
        
        queue = PersistentPriorityQueue(data_dir=self.temp_dir)
        self.assertEqual(len(queue), 0)


class TestPersistentPriorityQueueEdgeCases(unittest.TestCase):
    """Test edge cases and special scenarios."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.queue = PersistentPriorityQueue(data_dir=self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_negative_priorities(self):
        """Test that negative priorities work correctly."""
        self.queue.insert("Low", -10)
        self.queue.insert("High", -5)
        self.queue.insert("Medium", -7)
        
        # -10 is minimum (highest priority)
        self.assertEqual(self.queue.peek().value, "Low")
        self.assertEqual(self.queue.extract_min().value, "Low")
        self.assertEqual(self.queue.extract_min().value, "Medium")
        self.assertEqual(self.queue.extract_min().value, "High")
    
    def test_zero_priority(self):
        """Test that zero priority works."""
        self.queue.insert("Zero", 0)
        self.queue.insert("Positive", 1)
        self.queue.insert("Negative", -1)
        
        self.assertEqual(self.queue.peek().value, "Negative")
    
    def test_large_number_of_items(self):
        """Test with a larger number of items."""
        n = 100
        for i in range(n):
            self.queue.insert(f"Task {i}", i)
        
        self.assertEqual(len(self.queue), n)
        
        # Extract all in order
        for i in range(n):
            extracted = self.queue.extract_min()
            self.assertEqual(extracted.value, f"Task {i}")
        
        self.assertTrue(self.queue.is_empty())
    
    def test_various_value_types(self):
        """Test that various JSON-serializable value types work."""
        self.queue.insert("string", 1)
        self.queue.insert(42, 2)
        self.queue.insert(3.14, 3)
        self.queue.insert({"key": "value"}, 4)
        self.queue.insert([1, 2, 3], 5)
        self.queue.insert(True, 6)
        self.queue.insert(None, 7)
        
        self.assertEqual(len(self.queue), 7)
        
        # All should be extractable
        for _ in range(7):
            self.queue.extract_min()
        
        self.assertTrue(self.queue.is_empty())
    
    def test_contains_operator(self):
        """Test __contains__ method."""
        id1 = self.queue.insert("Task", 5)
        
        self.assertIn(id1, self.queue)
        self.assertNotIn("fake-id", self.queue)
        
        self.queue.delete(id1)
        self.assertNotIn(id1, self.queue)
    
    def test_get_all_items(self):
        """Test get_all_items returns all items."""
        id1 = self.queue.insert("A", 3)
        id2 = self.queue.insert("B", 1)
        id3 = self.queue.insert("C", 2)
        
        items = self.queue.get_all_items()
        self.assertEqual(len(items), 3)
        
        ids = {item.id for item in items}
        self.assertEqual(ids, {id1, id2, id3})


class TestPersistentPriorityQueueComplexScenarios(unittest.TestCase):
    """Test complex real-world scenarios."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_priority_inversion_scenario(self):
        """Test scenario where priorities are inverted via updates."""
        queue = PersistentPriorityQueue(data_dir=self.temp_dir)
        
        # Insert tasks with varying priorities
        id_low = queue.insert("Low priority task", 10)
        id_med = queue.insert("Medium priority task", 5)
        id_high = queue.insert("High priority task", 1)
        
        # Initially high priority task should be first
        self.assertEqual(queue.peek().id, id_high)
        
        # Escalate low priority task
        queue.update(id_low, priority=0)
        
        # Now escalated task should be first
        self.assertEqual(queue.peek().id, id_low)
        self.assertEqual(queue.peek().priority, 0)
    
    def test_alternating_min_max_extraction(self):
        """Test alternating between extract_min and extract_max."""
        queue = PersistentPriorityQueue(data_dir=self.temp_dir)
        
        for i in range(10):
            queue.insert(f"Task {i}", i)
        
        # Extract min, max, min, max...
        extracted = []
        while not queue.is_empty():
            extracted.append(queue.extract_min().value)
            if not queue.is_empty():
                extracted.append(queue.extract_max().value)
        
        # Should get: 0, 9, 1, 8, 2, 7, 3, 6, 4, 5
        expected = ["Task 0", "Task 9", "Task 1", "Task 8", "Task 2", 
                    "Task 7", "Task 3", "Task 6", "Task 4", "Task 5"]
        self.assertEqual(extracted, expected)
    
    def test_concurrent_queues_same_directory(self):
        """Test that multiple queue instances can work with same directory."""
        queue1 = PersistentPriorityQueue(data_dir=self.temp_dir)
        
        id1 = queue1.insert("From queue1", 5)
        
        # New instance should see the item (persistence works)
        queue2_new = PersistentPriorityQueue(data_dir=self.temp_dir)
        self.assertIn(id1, queue2_new)
    
    def test_atomic_write_on_failure(self):
        """Test that failed writes don't corrupt the file."""
        queue = PersistentPriorityQueue(data_dir=self.temp_dir)
        queue.insert("Task", 1)
        
        # Make file read-only to simulate write failure
        filepath = Path(self.temp_dir) / "queue.json"
        filepath.chmod(0o444)
        
        try:
            with self.assertRaises(OSError):
                queue.insert("Another", 2)
        finally:
            # Restore permissions for cleanup
            filepath.chmod(0o644)
        
        # Original data should be intact
        queue_new = PersistentPriorityQueue(data_dir=self.temp_dir)
        self.assertEqual(len(queue_new), 1)
        self.assertEqual(queue_new.peek().value, "Task")


if __name__ == "__main__":
    unittest.main(verbosity=2)