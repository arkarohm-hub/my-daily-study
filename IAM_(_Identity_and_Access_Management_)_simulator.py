# --- THE IAM SYSTEM ---
users = {
    "admin_user": {"permissions": ["read", "write", "delete"]},
    "junior_dev": {"permissions": ["read"]} # No write, no delete
}

def execute_command(user, command):
    print(f"\n👤 User '{user}' is trying to: {command.upper()}")
    
    # 1. Check if user exists
    if user not in users:
        print("   ⛔ ACCESS DENIED: User unknown.")
        return

    # 2. Check Permissions (The Gatekeeper)
    user_perms = users[user]["permissions"]
    
    if command == "delete_db":
        if "delete" in user_perms:
            print("   ✅ ACCESS GRANTED: Database deleted. (Hope you meant to do that!)")
        else:
            print("   🛡️  SECURITY SHIELD: ACCESS DENIED. You lack 'delete' permission.")
            
    elif command == "read_logs":
        if "read" in user_perms:
             print("   ✅ ACCESS GRANTED: Showing logs...")

# --- SIMULATION ---
execute_command("admin_user", "read_logs")
execute_command("junior_dev", "read_logs")

execute_command("admin_user", "delete_db")
execute_command("junior_dev", "delete_db") # <--- WATCH THIS FAIL
