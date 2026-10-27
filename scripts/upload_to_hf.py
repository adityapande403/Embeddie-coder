"""
Upload EmbeddieCoder AI model to Hugging Face Hub.
"""

import sys
from pathlib import Path
from huggingface_hub import HfApi


def main():
    repo_id = "Adityapande403/embeddie-coder"
    folder_path = Path("models/embeddedcoder_merged")

    if not folder_path.exists():
        print(f"Error: Folder {folder_path} does not exist!")
        sys.exit(1)

    print(f"[*] Uploading folder {folder_path.resolve()} to Hugging Face: {repo_id}...")
    api = HfApi()

    # Verify repository exists
    if not api.repo_exists(repo_id=repo_id, repo_type="model"):
        print(f"[*] Creating repository {repo_id}...")
        api.create_repo(repo_id=repo_id, repo_type="model", exist_ok=True)

    # Upload folder
    api.upload_folder(
        repo_id=repo_id,
        folder_path=str(folder_path.resolve()),
        repo_type="model",
        commit_message="feat: upload EmbeddieCoder AI 1.5B merged model, tokenizer, and LoRA adapter"
    )
    print(f"[+] Successfully uploaded to https://huggingface.co/{repo_id}")


if __name__ == "__main__":
    main()
