Apply Patches Helper

This helper script applies patch artifacts produced by agents into a git repository and creates a branch and commit.

Usage example:

```bash
python "~/Library/Application Support/Code/User/prompts/agent-manager/apply_patches.py" \
  --repo /path/to/repo \
  --patch /path/to/outgoing_patches/patch-xxxx.patch \
  --branch agent/apply-patch-xxxx \
  --message "Apply agent patch"
```

Security
- Only run this on trusted repositories. The script uses `git apply --index` and `git commit`.
- Review patch contents before applying.
