#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import requests

env_vars = ["ATOMGIT_USER", "ATOMGIT_EMAIL", "ATOMGIT_TOKEN"]
for var in env_vars:
    if not os.getenv(var):
        sys.exit(f"Error: Environment variable {var} is missing.")

ATOMGIT_USER = os.getenv("ATOMGIT_USER")
ATOMGIT_EMAIL = os.getenv("ATOMGIT_EMAIL")
ATOMGIT_TOKEN = os.getenv("ATOMGIT_TOKEN")
UPSTREAM_API = "https://formulae.brew.sh/api/formula.jws.json"
ATOMGIT_REPO = f"https://{ATOMGIT_USER}:{ATOMGIT_TOKEN}@atomgit.com/{ATOMGIT_USER}/homebrew-core.git"


def run_cmd(cmd, cwd=None):
    """运行 Shell 命令并返回输出"""
    print(f"[*] Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(result.stdout)
    if result.returncode != 0:
        print(f"[!] Error: {result.stderr}")
        sys.exit(result.returncode)
    return result.stdout.strip()


def fetch_aliases(formula_name):
    """从 API 获取该 Formula 的所有别名"""
    try:
        print(f"[*] Fetching aliases from {UPSTREAM_API}")
        resp = requests.get(UPSTREAM_API, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        payload = json.loads(data.get("payload", "[]"))

        for item in payload:
            if item.get("name") == formula_name:
                return item.get("aliases", [])
    except Exception as e:
        print(f"[!] Warning: Failed to fetch aliases: {e}")
    return []


def check_pr(formula):
    """检查当前 Formula 是否已经提过 Open 状态的 PR"""
    owner = "Harmonybrew"
    repo = "homebrew-core"
    url = f"https://api.atomgit.com/api/v5/repos/{owner}/{repo}/pulls"

    index = 1
    per_page = 100

    while True:
        params = {"access_token": ATOMGIT_TOKEN, "state": "open", "base": "main", "per_page": per_page, "page": index}

        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            prs = response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to check PR status: {e}")
            sys.exit(1)

        pr_titles = [pr["title"] for pr in prs]
        if formula in [title.split()[0] for title in pr_titles]:
            print(f"[!] PR already opened!")
            sys.exit(1)

        if len(prs) < per_page:
            break
        else:
            index += 1


def create_pr(head_branch, title):
    owner = "Harmonybrew"
    repo = "homebrew-core"

    # 构造请求数据
    url = f"https://api.atomgit.com/api/v5/repos/{owner}/{repo}/pulls"
    params = {"access_token": ATOMGIT_TOKEN}
    payload = {
        "title": title,
        "head": head_branch,  # 格式: "username:branch"
        "base": "main",
        "body": "Automatically migrated by [formula-migration-tool](https://atomgit.com/Harmonybrew/formula-migration-tool).",
        "prune_source_branch": True,  # 合入后删除源分支
    }

    try:
        response = requests.post(url, params=params, json=payload, timeout=30)
        response.raise_for_status()
        print(
            f"[SUCCESS] PR created: https://atomgit.com/Harmonybrew/homebrew-core/pull/{response.json().get('number')}"
        )
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to create PR: {e}")
        if "response" in locals() and response is not None:
            print(f"Response: {response.text}")
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: python3 migrate.py <formula>")

    formula = sys.argv[1]

    # 更新 Homebrew
    run_cmd(["brew", "update"])

    # 确定路径逻辑
    tap_path = run_cmd(["brew", "--repository", "harmonybrew/core"])
    os.chdir(tap_path)

    first_letter = "lib" if formula.startswith("lib") else formula[0].lower()
    target_rel_dir = f"Formula/{first_letter}"
    target_abs_dir = os.path.join(tap_path, target_rel_dir)
    rb_path = os.path.join(target_abs_dir, f"{formula}.rb")
    if os.path.exists(rb_path):
        sys.exit(f"Error: {formula} already migrated.")
    os.makedirs(target_abs_dir, exist_ok=True)

    # 检查 PR 是否已存在
    check_pr(formula)

    # 下载 Formula 文件
    print(f"[*] Fetching {formula}.rb...")
    upstream_url = f"https://raw.githubusercontent.com/Homebrew/homebrew-core/main/Formula/{first_letter}/{formula}.rb"

    resp = requests.get(upstream_url)
    if resp.status_code != 200:
        sys.exit(f"Error: Could not find {formula}.rb on upstream.")
    with open(rb_path, "w") as f:
        f.write(resp.text)

    # 创建 Aliases 软链接
    aliases = fetch_aliases(formula)
    if aliases:
        alias_dir = os.path.join(tap_path, "Aliases")
        os.makedirs(alias_dir, exist_ok=True)
        for alias in aliases:
            alias_path = os.path.join(alias_dir, alias)
            # 计算相对路径: 从 Aliases/ 到 Formula/x/name.rb
            # 结果通常是 ../Formula/x/name.rb
            rel_link_target = os.path.join("..", target_rel_dir, f"{formula}.rb")
            if os.path.lexists(alias_path):
                os.remove(alias_path)
            os.symlink(rel_link_target, alias_path)
            print(f"[*] Created alias: {alias} -> {rel_link_target}")

    # 构建与测试
    print(f"[*] Installing and testing {formula}...")
    run_cmd(["brew", "install", "-s", "-v", "--include-test", formula])
    run_cmd(["brew", "test", "-v", formula])

    # 获取版本号用于提交信息
    info_json = json.loads(run_cmd(["brew", "info", "--json=v2", formula]))
    version = info_json["formulae"][0]["versions"]["stable"]
    commit_msg = f"{formula} {version} (new formula)"

    # Git 操作
    print(f"[*] Committing and pushing to AtomGit...")
    branch_name = f"migrate-{formula}"

    run_cmd(["git", "config", "user.name", ATOMGIT_USER])
    run_cmd(["git", "config", "user.email", ATOMGIT_EMAIL])

    # 切换分支
    subprocess.run(["git", "checkout", "-b", branch_name])  # 允许失败（如果分支已存在）

    run_cmd(["git", "add", rb_path])
    for alias in aliases:
        run_cmd(["git", "add", os.path.join("Aliases", alias)])

    run_cmd(["git", "commit", "-m", commit_msg])
    run_cmd(["git", "push", "-f", ATOMGIT_REPO, branch_name])

    # 检查 PR 是否已存在
    check_pr(formula)

    # 生成 PR
    create_pr(f"{ATOMGIT_USER}:{branch_name}", commit_msg)

    print(f"\n[OK] Successfully migrated {formula}!")


if __name__ == "__main__":
    main()
