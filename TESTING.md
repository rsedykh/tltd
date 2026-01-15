# TLTD Testing Checklist

## Test Environment Setup
```bash
source venv/bin/activate
python src/main.py
```

## Comprehensive Feature Testing

### 1. Task Creation (c key) - INLINE EDITING
- [ ] Create task in Inbox (default basket) - should show inline editor
- [ ] Create task when no task selected - should add to root with inline editor
- [ ] Create task with task selected - should show inline editor below at same level
- [ ] Create task with nested task selected - should show inline editor at same nesting level with proper indentation
- [ ] Inline editor should show proper indent, checkbox prefix
- [ ] Cancel task creation with ESC - should dismiss inline editor, return to normal view
- [ ] Create task with empty title and press Enter - should dismiss without creating
- [ ] Type text and press Enter - should create task immediately

### 2. Task Editing (Enter key) - INLINE EDITING
- [ ] Edit task title - should show inline editor IN PLACE of task
- [ ] Inline editor should show existing title pre-filled
- [ ] Save edit with Enter - should update task immediately
- [ ] Cancel edit with ESC - should dismiss inline editor, keep original title
- [ ] Edit with empty title and press Enter - should dismiss without saving
- [ ] Inline editor should show proper indent, collapse icon, checkbox prefix

### 3. Task Completion (x key)
- [ ] Complete a task - should show strikethrough
- [ ] Task should stay visible for 5 seconds with strikethrough
- [ ] After 5 seconds, task should disappear (when show_completed is off)
- [ ] Uncomplete a task within 5 seconds - should remove strikethrough
- [ ] Complete multiple tasks rapidly

### 4. Toggle Show Completed (z key)
- [ ] Press z - should show all completed tasks
- [ ] Press z - task pane border (Inbox) should turn grey
- [ ] Press z - basket items should turn grey
- [ ] Press z again - should hide completed tasks
- [ ] Press z again - colors should return to normal (orange/blue)

### 5. Task Deletion (Backspace key)
- [ ] Delete a task without children
- [ ] Delete a task with children - should delete all children too
- [ ] Verify task is removed from data

### 6. Panel Navigation (←/→ keys)
- [ ] Start in tasks panel (heavy orange border)
- [ ] Press ← - should switch to baskets panel (heavy blue border on baskets)
- [ ] Press → - should switch back to tasks panel
- [ ] Up/Down in baskets panel - should change selected basket
- [ ] Up/Down in tasks panel - should navigate tasks

### 7. Basket Switching (in baskets panel with ↑/↓)
- [ ] Navigate through all baskets: Inbox, Monday-Sunday, Later
- [ ] Task pane should show selected basket's tasks
- [ ] Task pane title should update to show basket name

### 8. Task Nesting (e key - nest, q key - unnest)
- [ ] Create two tasks at root level
- [ ] Select second task, press e - should nest under first task
- [ ] Nested task should be indented
- [ ] First task should show collapse icon (▼)
- [ ] Press q on nested task - should unnest to root level
- [ ] Nest multiple levels deep (3-4 levels)
- [ ] Unnest from deep nesting

### 9. Collapsing/Expanding (a key - collapse, d key - expand)
- [ ] Create parent with children
- [ ] Press a on parent - should collapse, show count like "Task (2)"
- [ ] Children should be hidden
- [ ] Press d on parent - should expand, show children
- [ ] Collapsed count should reflect show_completed setting:
  - [ ] With completed hidden: count only non-completed children
  - [ ] With completed visible (z): count all children

### 10. Task Reordering (w key - up, s key - down)
- [ ] Create 3 tasks at root level
- [ ] Select middle task, press w - should move up
- [ ] Press s - should move down
- [ ] At top of list, pressing w - should unnest if nested **AND maintain focus on task**
- [ ] At bottom of list, pressing s - should unnest if nested **AND maintain focus on task**
- [ ] Move nested tasks within parent's children list
- [ ] Move task past collapsed parent - should calculate position correctly
- [ ] **Critical**: Focus should never leave the task being moved, even when unnesting

### 11. Undo (\ key)
- [ ] Create a task, press \ - task should be removed
- [ ] Edit a task, press \ - edit should be undone
- [ ] Delete a task, press \ - task should reappear
- [ ] Complete a task, press \ - task should be uncompleted
- [ ] Undo multiple times (up to 50 actions)
- [ ] Undo should clear recently_completed grace period tracking

### 12. Help Screen (? key)
- [ ] Press ? - help screen should appear
- [ ] Help should list all keybindings correctly
- [ ] Press ESC in help - should close help, not quit app
- [ ] Press Close button - should close help

### 13. Data Persistence
- [ ] Create several tasks
- [ ] Quit app (ESC)
- [ ] Restart app - tasks should still be there
- [ ] Verify data saved to ~/.tltd/tasks.json

### 14. Complex Scenarios
- [ ] Create hierarchy: Parent with 3 children, each child with 2 subchildren
- [ ] Collapse parent - count should show 3
- [ ] Expand, collapse one child - should see that child with count
- [ ] Complete tasks at various levels
- [ ] Toggle show completed - verify all completed visible
- [ ] Move nested task between different parents
- [ ] Reorder tasks with nested children - children should move with parent
- [ ] Undo complex operations

### 15. Basket Operations
- [ ] Create tasks in all baskets (Inbox, Monday-Sunday, Later)
- [ ] Verify basket counts update correctly
- [ ] Switch between baskets and verify tasks appear correctly
- [ ] Move task to different basket with f key - should show basket selector dialog
- [ ] Navigate baskets in dialog with ↑/↓ - selection should move
- [ ] Confirm selection with Enter - task should move to selected basket
- [ ] Cancel basket dialog with ESC - task should stay in original basket

### 16. Edge Cases
- [ ] Empty basket - should show "No tasks" message
- [ ] Very long task title - should display correctly
- [ ] Many nested levels (5+) - should handle gracefully
- [ ] Create 50+ tasks - should perform well
- [ ] Complete all tasks in a basket - basket count should be 0
- [ ] Rapidly press keys - should not cause errors

### 17. Error Conditions
- [ ] Try to nest a task when it's the first/only task - should do nothing
- [ ] Try to unnest a root level task - should do nothing
- [ ] Try to collapse a task with no children - should do nothing
- [ ] Delete all tasks, try to navigate - should handle empty state

## Test Results Summary

Date: _________________
Tester: _________________

### Bugs Found:
1.
2.
3.

### Features Working:
- [ ] All task operations (create/edit/delete)
- [ ] Completion with grace period
- [ ] Nesting/unnesting
- [ ] Collapsing/expanding
- [ ] Reordering
- [ ] Undo
- [ ] Basket navigation
- [ ] Panel switching
- [ ] Help screen
- [ ] Data persistence

### Performance Notes:


### UI/UX Notes:


## Automated Test Coverage

Run unit tests:
```bash
pytest tests/
```

Note: UI interactions cannot be automatically tested without additional test framework integration.
