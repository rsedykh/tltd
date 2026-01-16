# Future Feature Ideas for TLTD

This document contains feature suggestions for future development, organized by implementation effort.

## Tier 2: Medium Effort Features

### Multi-Select Operations
- **Select multiple tasks**: Shift+arrow or `m` to mark tasks
- **Bulk complete**: Complete all selected tasks at once
- **Bulk move**: Move selected tasks to another basket
- **Bulk delete**: Delete multiple tasks at once

### ~~Task Notes/Descriptions~~ ✅ IMPLEMENTED
- ~~**Multi-line descriptions**: Press `v` on a task to add/edit a longer description~~
- ~~**Collapsible notes**: Show first line in tree, expand to see full note~~
- **Markdown support**: Basic formatting in notes (bold, italic, lists) - *not yet*

### Search and Filter
- **Global search**: Press `/` to open search, filter tasks across all baskets by title
- **Filter by completion state**: Quick toggle to show only incomplete tasks
- **Regex search support**: For power users who need pattern matching

### Data Export/Import
- **Export to JSON**: Already supported via `~/.tltd/tasks.json`
- **Export to Markdown**: Generate a readable task list
- **Export to CSV**: For spreadsheet workflows
- **Import from other formats**: Todoist, Things, plain text

### Weekly Reset
- **Week number display**: Show "Monday W03/25" format on weekday baskets
- **Auto-reset on new week**: When week changes, move all uncompleted tasks from Mon-Sun to Inbox
- **Fresh start**: Begin each week with empty weekday baskets, plan from Inbox
- **Optional confirmation**: Ask before moving or do it silently on first launch of new week

### Recurring Tasks
- **Daily/Weekly recurrence**: Task reappears after completion
- **Custom intervals**: Every N days
- **Skip/snooze**: Defer a recurring instance
- **Recurrence indicators**: Visual marker showing task is recurring

### Keyboard Macro Recording
- **Record sequences**: Record and replay common task workflows
- **Named macros**: Save macros for repeated use
- **Testing**: Try to use these macros for automating testing

### Task Statistics
- **Completion rate**: Tasks completed per day/week
- **Time in basket**: How long tasks sit before completion
- **Productivity graphs**: ASCII charts in terminal

---

## Tier 3: Large Effort Features

### Cloud Sync
- **Server component**: Self-hosted sync server
- **Conflict resolution**: Handle simultaneous edits
- **Offline support**: Queue changes when disconnected
- **End-to-end encryption**: Secure sync

### Mobile Companion
- **Quick capture API**: Add tasks via HTTP endpoint
- **iOS/Android widgets**: View tasks on phone
- **Push notifications**: Reminders on mobile

### Custom Baskets
- **Create/delete baskets**: User-defined organization
- **Basket ordering**: Arrange baskets in custom order
- **Basket colors**: Visual differentiation
- **Basket templates**: Pre-configured basket sets (e.g., "Agile Sprint", "GTD")

### Due Dates and Reminders
- **Date picker**: Assign due dates to tasks
- **Overdue highlighting**: Visual indicator for past-due tasks
- **Today's tasks view**: Aggregate tasks due today across all baskets
- **Calendar integration**: Export to iCal/Google Calendar
- **Desktop notifications**: System alerts for upcoming deadlines

### Time Tracking
- **Start/stop timer**: Track time spent on tasks
- **Time estimates**: Set expected duration
- **Actual vs estimated reports**: Compare predictions to reality
- **Pomodoro mode**: Built-in focus timer

### Collaboration Features
- **Shared baskets**: Multiple users access same basket
- **Task assignment**: Assign tasks to team members
- **Comments**: Discussion threads on tasks
- **Activity log**: Who did what and when

### Plugin System
- **Extension API**: Third-party feature additions
- **Hook system**: Custom actions on events (task created, completed, etc.)
- **Theme marketplace**: Community-created visual themes

### Natural Language Input
- **Smart parsing**: "Buy milk tomorrow" creates task with date
- **Relative dates**: "next Monday", "in 3 days"
- **Basket inference**: Auto-assign to basket based on content

### Advanced Hierarchy Features
- **Task dependencies**: Block tasks until prerequisites complete
- **Critical path**: Show dependency chain
- **Gantt-style view**: Timeline visualization (ASCII-based)

---

## Implementation Notes

### Priority Recommendations

If implementing these features, consider this order:

1. **Search** - High value, medium effort, improves usability significantly
2. **Export formats** - Data portability is important
3. **Custom baskets** - Flexibility for different workflows
4. **Due dates** - Enables time-based task management

*(Task notes - completed)*

### Technical Considerations

- **Search**: Could use simple substring matching initially, upgrade to fuzzy matching later
- ~~**Notes**: Store as additional field in Task model, update JSON schema~~ ✅ Done
- **Custom baskets**: Replace hardcoded `BASKETS` list with user configuration
- **Due dates**: Add `due_date: Optional[str]` field, implement date parsing
- **Cloud sync**: Consider existing sync protocols (WebDAV, CalDAV for tasks)

### Breaking Changes

Some features may require data migration:
- Custom baskets: Need to handle case where saved data has baskets not in config
- ~~Task notes: Need to add field to existing tasks (default to empty string)~~ ✅ Done
- Due dates: Need to add field to existing tasks (default to None)

Always implement backwards-compatible loading with sensible defaults.
