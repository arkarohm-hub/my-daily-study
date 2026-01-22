import time

# 1. Setup
print("Building database...")
N = 10_000_000
my_list = list(range(N))
my_set = set(range(N)) # This uses a Hash Map internally
target = 9_999_999

print("Race starting...")

# 2. Test List Search (Linear Search - O(n))
start = time.time()
found = target in my_list
end = time.time()
print(f"List Search Time: {end - start:.10f} seconds")

# 3. Test Set Search (Hash Map Search - O(1))
start = time.time()
found = target in my_set
end = time.time()
print(f"Set  Search Time: {end - start:.10f} seconds")