import os

# 1. Define the correct content
content = """streamlit
st-gsheets-connection
pandas
plotly
"""

# 2. Force-write the file (overwriting any garbage)
with open("requirements.txt", "w") as f:
    f.write(content)

print("✅ requirements.txt has been rewritten successfully.")

# 3. Verify content
print("--- New File Content ---")
with open("requirements.txt", "r") as f:
    print(f.read())
print("------------------------")

# 4. Automate the Git Push
os.system("git add requirements.txt")
os.system("git commit -m 'Fix requirements.txt via python script'")
os.system("git push")
print("🚀 Changes pushed to GitHub!")
