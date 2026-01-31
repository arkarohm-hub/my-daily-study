import time

# This Dictionary acts as our "Redis"
cache = {}

def slow_database_query(user_id):
    print(f"   [DB] Fetching User {user_id} from Hard Disk... (Slow)")
    time.sleep(2) # Simulate 2 second delay
    return f"User_Data_{user_id}"

def get_user(user_id):
    # 1. CHECK CACHE (The "Hit")
    if user_id in cache:
        print(f"✅ [Cache] Found User {user_id} instantly!")
        return cache[user_id]
    
    # 2. CACHE MISS (The "Miss")
    print(f"❌ [Cache] User {user_id} not found.")
    
    # 3. FETCH FROM DB
    data = slow_database_query(user_id)
    
    # 4. SAVE TO CACHE (For next time)
    cache[user_id] = data
    return data

# --- SIMULATION ---

print("--- Request 1: User 55 (First Time) ---")
start = time.time()
print(f"Result: {get_user(55)}")
print(f"Time Taken: {time.time() - start:.2f} seconds\n")

print("--- Request 2: User 55 (Second Time) ---")
start = time.time()
print(f"Result: {get_user(55)}")
print(f"Time Taken: {time.time() - start:.2f} seconds")
