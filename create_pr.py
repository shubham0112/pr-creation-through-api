import json
import requests
from datetime import datetime
import base64


def raise_pr(gh_user, headers, repo, new_branch, base_branch):
    url_create_pr = f"https://api.github.com/repos/{gh_user}/{repo}/pulls"
    data_create_pr = {
        "title": "Pull Request Title",
        "body": "Pull Request Description",
        "head": new_branch,
        "base": base_branch
    }
    response_create_pr = requests.post(url_create_pr, json=data_create_pr, headers=headers)
    print("PR link => ", response_create_pr.json()["html_url"])


def overwrite_file(gh_user, headers, repo, file_path, created_branch, file_sha, new_content):
    payload = {
        "message": "Update file",
        "content": base64.b64encode(new_content.encode("utf-8")).decode("utf-8"),
        "sha": file_sha,
        "branch": created_branch
    }
    url_update_file = f"https://api.github.com/repos/{gh_user}/{repo}/contents/{file_path}"
    response_update_file = requests.put(url_update_file, json=payload, headers=headers)
    if response_update_file.status_code == 200:
        print("File updated successfully.")
    else:
        print("Failed to update the file.")
        print(response_update_file.json())


def manipulate(original_json, extra_fields_json):
    for field, dtype in extra_fields_json.items():
        if field in original_json.keys():
            if type(dtype) is not list:
                original_json[field] = manipulate(original_json[field], dtype)
            else:
                original_json[field] = [manipulate(original_json[field][0], dtype[0])]
        else:
            original_json[field] = dtype
    return original_json


def update_content(current_content, extra_fields_json):
    loc = current_content.find("self.schema") + 14
    og_schema_str = current_content[loc:].strip()
    og_schema = json.loads(og_schema_str)
    og_schema = manipulate(og_schema, extra_fields_json)
    current_content = current_content[:loc] + json.dumps(og_schema, indent=2)
    return current_content


def read_and_update_schema_file(gh_user, headers, repo, file_path, branch):
    url_get_file = f"https://api.github.com/repos/{gh_user}/{repo}/contents/{file_path}"
    params_get_file = {
        "ref": branch
    }
    response_get_file = requests.get(url_get_file, headers=headers, params=params_get_file).json()
    current_content = base64.b64decode(response_get_file["content"]).decode("utf-8")

    # extra fields you want to add in that file
    extra_fields_json = {
        "new_field1": "fake",
        "dataSource": {
            "age": 0
        },
        "phoneList": [
            {
                "new_field2": "fake"
            }
        ]
    }
    updated_content = update_content(current_content, extra_fields_json)
    return updated_content, response_get_file["sha"]


def create_new_branch(gh_user, headers, repo, sha_base_branch):
    url = f"https://api.github.com/repos/{gh_user}/{repo}/git/refs"
    now = str(datetime.now()).replace(' ', '__').replace(':', '-').replace('.', '')
    new_branch = f'new_branch_{now}'
    data_create_branch = {
        "ref": f"refs/heads/{new_branch}",
        "sha": sha_base_branch  # latest commit of base branch
    }
    response_create_branch = requests.post(url, json=data_create_branch, headers=headers).json()
    # new_branch_sha = response_create_branch["object"]["sha"]
    return new_branch


def get_branch_sha(gh_user, headers, repo_name, branch_name):
    url = f'https://api.github.com/repos/{gh_user}/{repo_name}/branches/{branch_name}'
    params_get_file = {
        "ref": branch_name
    }
    response = requests.get(url, headers=headers, params=params_get_file).json()
    sha = response['commit']['sha']
    return sha


def main():
    gh_user = "shubham0112"
    gh_token = "<PAT>"  # replace with your personal access token
    repo_name = "schemas"
    base_branch_name = "main"
    file_path = "original_schema.py"  # file you want to make change to
    headers = {
        "Authorization": f"token {gh_token}",
        "Accept": "application/vnd.github+json"
    }
    sha = get_branch_sha(gh_user, headers, repo_name, base_branch_name)
    new_branch_name = create_new_branch(gh_user, headers, repo_name, sha)
    updated_schema_file_content, file_sha = read_and_update_schema_file(gh_user, headers, repo_name, file_path, new_branch_name)
    overwrite_file(gh_user, headers, repo_name, file_path, new_branch_name, file_sha, updated_schema_file_content)
    raise_pr(gh_user, headers, repo_name, new_branch_name, base_branch_name)


if __name__ == '__main__':
    main()
