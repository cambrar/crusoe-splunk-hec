# Event Deduplication Strategies

This document outlines approaches to eliminate duplicate audit logs that may occur due to the 30-second overlap window in daemon mode.

## 🔧 **Implemented Solution: Splunk HEC Event ID**

**Status: ✅ IMPLEMENTED**

The application automatically generates unique event IDs for each audit log entry using a deterministic hash of key fields:

- `start_time` - When the action started
- `actor_id` - Who performed the action  
- `action` - What action was performed
- `target_type` - Type of resource affected
- `organization_id` - Organization context

**How it works:**
1. Each event gets a unique `id` field in the Splunk HEC payload
2. Splunk automatically deduplicates events with the same ID
3. No duplicate events are stored, even if sent multiple times

**Example event with ID:**
```json
{
  "time": 1693737063.941,
  "event": { ... audit log data ... },
  "sourcetype": "crusoe:audit",
  "source": "crusoe_api",
  "id": "a1b2c3d4e5f6789..." 
}
```

## 🔍 **Alternative Solutions**

### **1. Code-Level Deduplication**

**Option A: Local State Tracking**
```python
# Track sent event IDs in memory/file
sent_events = set()
if event_id not in sent_events:
    send_to_splunk(event)
    sent_events.add(event_id)
```

**Pros:** Complete elimination of duplicates  
**Cons:** Memory usage, state persistence challenges, complexity

**Option B: Database Tracking**
Store sent event IDs in SQLite/PostgreSQL database.

**Pros:** Persistent deduplication across restarts  
**Cons:** Additional dependency, storage overhead

### **2. Splunk Search-Time Deduplication**

**Option A: Dedup Command**
```splunk
index=your_index sourcetype=crusoe:audit 
| dedup start_time actor_id action target_type
```

**Option B: Event Hash Field**
```splunk
index=your_index sourcetype=crusoe:audit 
| eval event_hash=md5(start_time.actor_id.action.target_type) 
| dedup event_hash
```

**Pros:** No application changes needed  
**Cons:** Duplicates still stored, uses more storage

### **3. Splunk Data Models**

Create a data model that automatically deduplicates based on event characteristics.

**Pros:** Automatic, built into Splunk  
**Cons:** Requires Splunk configuration

## 📊 **Performance Comparison**

| Method | Duplicates Stored | App Complexity | Storage Impact | Real-time |
|--------|------------------|----------------|----------------|-----------|
| **HEC Event ID** ✅ | None | Low | None | Yes |
| Local State | None | High | None | Yes |
| Database State | None | High | Low | Yes |
| Search-time Dedup | All duplicates | None | High | No |

## ✅ **Recommendation**

**Use the implemented HEC Event ID solution** because:

1. **Zero duplicate storage** - Splunk automatically prevents duplicates
2. **No additional complexity** - Built into Splunk HEC protocol
3. **Real-time deduplication** - Works immediately as events arrive
4. **No state management** - Stateless, no persistence needed
5. **Performance efficient** - MD5 hash is fast and deterministic

## 🧪 **Testing Deduplication**

To verify deduplication is working:

1. **Send the same event twice:**
   ```bash
   python3 main.py forward-recent --hours=1
   python3 main.py forward-recent --hours=1  # Same time range
   ```

2. **Check in Splunk:**
   ```splunk
   index=your_index sourcetype=crusoe:audit 
   | stats count by start_time actor_id action 
   | where count > 1
   ```
   
   Should return no results if deduplication is working.

3. **Verify event IDs:**
   ```splunk
   index=your_index sourcetype=crusoe:audit 
   | table _time start_time action actor_id _event_id
   ```

## 🔧 **Configuration**

No additional configuration required. Event ID generation is automatic and based on audit log content.

The 30-second overlap in daemon mode ensures no logs are missed while Splunk's native deduplication prevents any duplicates from being stored.
