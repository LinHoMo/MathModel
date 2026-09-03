import base64, json, urllib.request, os, sys

urls = {
    "SKILL.md": "https://api.github.com/repos/LiXiang106991/MathModelAgent/contents/SKILL.md",
    "SKILL_1.md": "https://api.github.com/repos/LiXiang106991/MathModelAgent/contents/SKILL%20(1).md",
    "SKILL_2.md": "https://api.github.com/repos/LiXiang106991/MathModelAgent/contents/SKILL%20(2).md",
    "SKILL_3.md": "https://api.github.com/repos/LiXiang106991/MathModelAgent/contents/SKILL%20(3).md",
    "SKILL_4.md": "https://api.github.com/repos/LiXiang106991/MathModelAgent/contents/SKILL%20(4).md",
    "SKILL_5.md": "https://api.github.com/repos/LiXiang106991/MathModelAgent/contents/SKILL%20(5).md",
}

out_dir = r"C:\Users\Lin\Desktop\Programs\MathModel\.fetch"
os.makedirs(out_dir, exist_ok=True)

for name, url in urls.items():
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github.v3+json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = base64.b64decode(data["content"]).decode("utf-8")
        path = os.path.join(out_dir, f"MathModelAgent_{name}")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"OK {name}: {len(content)} chars -> {path}")
    except Exception as e:
        print(f"ERROR {name}: {e}")
