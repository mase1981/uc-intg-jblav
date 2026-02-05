# v1.0.6 - Fix Entity Availability After Initial Setup

## Issue Fixed

**Problem**: After completing setup flow, all entities showed as UNAVAILABLE. After Remote restart, entities came online and worked perfectly.

**Root Cause**: Entity subscription timing mismatch during initial setup.

### Detailed Analysis

**Initial Setup Flow (FAILED):**
```
1. Setup completes (15:13:54.294)
2. Framework auto-triggers "connect" event (15:13:54.317) - 23ms later
3. Device connects to JBL receiver
4. Queries sent, responses received
5. _notify_entities() emits UPDATE events
6. ❌ Entities still in [available], NOT in [configured] yet
7. Framework can't find entities → "entity not found" errors
8. User sees UNAVAILABLE entities
```

**After Remote Reboot (WORKED):**
```
1. Integration starts with config.json present
2. User navigates to integration in UI
3. subscribe_events received (15:19:19.373)
4. ✅ Entities moved from [available] to [configured]
5. "connect" event fires (15:19:19.388) - 15ms after subscription
6. Device connects, queries sent, responses received
7. _notify_entities() emits UPDATE events
8. ✅ Framework finds entities in [configured]
9. All entities show correct state
```

**The Problem**: During initial setup, `subscribe_events` does NOT happen automatically - only on manual user navigation. The framework auto-connects the device immediately after setup, but entities aren't subscribed yet.

## Solution

Implemented **Deferred Entity Update Mechanism** in device.py:

### Changes Made

1. **Added State Tracking Flags**:
   - `_entities_configured`: Tracks if entities have been successfully updated (in [configured])
   - `_pending_state_update`: Flag indicating state needs to be emitted
   - `_retry_task`: Async task handle for retry mechanism

2. **Modified `_notify_entities()` Method**:
   - Checks if entities are confirmed configured
   - If NOT configured yet → defers update and starts retry task
   - If configured → emits immediately (normal flow)

3. **Created `_retry_entity_updates()` Task**:
   - Waits 3 seconds between retry attempts
   - Tries up to 10 times (~30 seconds total)
   - Calls `_emit_entity_updates()` to attempt emission
   - Stops when entities are successfully updated

4. **Created `_emit_entity_updates()` Method**:
   - Contains all entity emission logic (moved from `_notify_entities()`)
   - Emits UPDATE events for all 10 entities
   - Marks `_entities_configured` as True after first successful emission

### How It Works

**Initial Setup (Now Fixed):**
```
1. Setup completes → "connect" fires immediately
2. Device connects, queries sent, responses arrive
3. _notify_entities() called
4. ❌ Entities NOT configured yet → defer update
5. Retry task starts, waits 3 seconds
6. User navigates to integration (normal user flow)
7. subscribe_events fires → entities moved to [configured]
8. Retry task attempts emission
9. ✅ Emission succeeds → entities_configured = True
10. User sees all entities with correct state
```

**After Reboot (Still Works):**
```
1. Integration starts
2. User navigates to integration → subscribe_events fires
3. Entities moved to [configured]
4. "connect" event fires
5. Device connects, queries sent, responses arrive
6. _notify_entities() called
7. First emission attempt succeeds
8. ✅ entities_configured = True
9. All future updates emit immediately
```

**Ongoing Updates (Both Scenarios):**
```
State changes → _notify_entities() → entities_configured = True → emit immediately
```

## Testing Required

1. **Clean Setup Test**: Delete existing config, run setup flow, verify entities appear within 3-10 seconds
2. **Reboot Test**: Restart Remote, verify entities still work
3. **State Updates Test**: Change volume, input, power - verify updates work immediately
4. **Edge Case Test**: Complete setup but don't navigate to integration for 30+ seconds

## Files Modified

- `intg_jblav/device.py`:
  - Added `_entities_configured`, `_pending_state_update`, `_retry_task` flags
  - Modified `_notify_entities()` to check configuration state
  - Created `_retry_entity_updates()` async task
  - Created `_emit_entity_updates()` method
- `driver.json`: Version bumped to 1.0.6

## Expected Behavior

After uploading v1.0.6:
- User completes setup flow
- Entities show UNAVAILABLE initially (0-3 seconds)
- Retry mechanism kicks in
- When user navigates to integration (normal next step), subscribe_events fires
- Entities appear with correct state within 3-10 seconds
- No Remote restart needed
- All future updates work immediately
