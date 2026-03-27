import secrets
import bcrypt
import os
import sys
from pathlib import Path

def setup_auth_credentials():
    print("\n" + "="*50)
    print("SOCIAL TRACKER - AUTH CREDENTIALS GENERATOR")
    print("="*50)
    
    # 1. Get Username
    current_username = os.environ.get("ADMIN_USERNAME", "admin")
    username = input(f"\nEnter the username (default '{current_username}'): ") or current_username
    
    # 2. Get Password
    password = input("Enter the new password for the dashboard: ")
    if not password:
        print("Error: Password cannot be empty.")
        return
        
    # 3. Hash the password
    print("Hashing password...")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    # 4. Generate JWT Secret Key (Optional change)
    current_jwt = os.environ.get("JWT_SECRET_KEY", "")
    change_jwt = input("\nDo you want to generate a new JWT_SECRET_KEY? (y/N): ").lower() == 'y'
    jwt_secret = secrets.token_hex(32) if change_jwt or not current_jwt else current_jwt
    
    print("\n" + "-"*50)
    print("YOUR NEW CREDENTIALS:")
    print("-"*50)
    print(f"ADMIN_USERNAME={username}")
    print(f"ADMIN_PASSWORD_HASH={hashed_password}")
    print(f"JWT_SECRET_KEY={jwt_secret}")
    
    update = input("\nDo you want to update the .env file automatically? (y/N): ").lower() == 'y'
    
    if update:
        env_path = Path(__file__).resolve().parent.parent / ".env"
        lines = []
        
        # Read existing .env if it exists
        if env_path.exists():
            with open(env_path, "r") as f:
                lines = f.readlines()
        
        # Update or append
        updated = {"username": False, "hash": False, "jwt": False}
        new_lines = []
        for line in lines:
            if line.startswith("ADMIN_USERNAME="):
                new_lines.append(f"ADMIN_USERNAME={username}\n")
                updated["username"] = True
            elif line.startswith("ADMIN_PASSWORD_HASH="):
                new_lines.append(f"ADMIN_PASSWORD_HASH={hashed_password}\n")
                updated["hash"] = True
            elif line.startswith("JWT_SECRET_KEY="):
                new_lines.append(f"JWT_SECRET_KEY={jwt_secret}\n")
                updated["jwt"] = True
            else:
                new_lines.append(line)
        
        # Append missing
        if not updated["username"]: new_lines.append(f"ADMIN_USERNAME={username}\n")
        if not updated["hash"]: new_lines.append(f"ADMIN_PASSWORD_HASH={hashed_password}\n")
        if not updated["jwt"]: new_lines.append(f"JWT_SECRET_KEY={jwt_secret}\n")
        
        with open(env_path, "w") as f:
            f.writelines(new_lines)
            
        print("\nSUCCESS: .env file has been updated!")
    else:
        print("\nPlease copy the credentials above and paste them into your .env file manually.")
    
    print("="*50 + "\n")

if __name__ == "__main__":
    setup_auth_credentials()
