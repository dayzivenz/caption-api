#!/usr/bin/env python3
"""
Create GitHub repo and push CaptionAPI code.

Uses HTTPS with username/password auth (GitHub token).
"""
import subprocess, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

REPO_NAME = "caption-api"
REPO_DIR = r"C:\Users\dayzi\.openclaw\workspace\income\products\caption-api"
GITHUB_USER = "dayzivenz"
GITHUB_TOKEN = "dayzibitch88XX"  # password works as token for HTTPS

os.chdir(REPO_DIR)
print(f"Working dir: {os.getcwd()}")

# 1. Init git if needed
if not os.path.exists(os.path.join(REPO_DIR, ".git")):
    subprocess.run(["git", "init"], check=True)
    print("Git initialized")

# 2. Create .gitignore
gitignore = """__pycache__/
*.pyc
.env
.venv
venv/
*.egg-info/
dist/
build/
.DS_Store
"""
with open(os.path.join(REPO_DIR, ".gitignore"), "w") as f:
    f.write(gitignore)
print(".gitignore created")

# 3. Add all files
subprocess.run(["git", "add", "."], check=True)
print("Files staged")

# 4. Commit
subprocess.run(["git", "commit", "-m", "Initial commit: CaptionAPI v1.0"], check=True)
print("Committed")

# 5. Create repo on GitHub and push
remote_url = f"https://{GITHUB_USER}:{GITHUB_TOKEN}@github.com/{GITHUB_USER}/{REPO_NAME}.git"

# Try pushing (will fail if repo doesn't exist, which is fine)
result = subprocess.run(["git", "remote", "add", "origin", remote_url], capture_output=True, text=True)
if result.returncode != 0 and "already exists" in result.stderr:
    subprocess.run(["git", "remote", "set-url", "origin", remote_url], check=True)

print("Remote configured")

# Push
result = subprocess.run(["git", "push", "-u", "origin", "master"], capture_output=True, text=True)
print(result.stdout[-500:] if result.stdout else "")
print(result.stderr[-500:] if result.stderr else "")

if result.returncode == 0:
    print("\n✅ SUCCESS! CaptionAPI pushed to GitHub!")
else:
    print("\n❌ Push failed. May need to create repo manually or auth issue")
    print("Trying alternative auth method...")
    
    # Remove remote with token, re-add without
    subprocess.run(["git", "remote", "remove", "origin"], capture_output=True)
    subprocess.run(["git", "remote", "add", "origin", f"https://github.com/{GITHUB_USER}/{REPO_NAME}.git"], check=True)
    print("Try: git push -u origin master (will prompt for password)")
