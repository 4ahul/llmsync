# Publish LLMSync to PyPI - Complete Guide

**GitHub Repository:** https://github.com/4ahul/llmsync

This guide will help you publish `llmsync` to PyPI so anyone can install it with `pip install llmsync`.

---

## 📋 Prerequisites

### 1. PyPI Account
```bash
# Create account at: https://pypi.org/account/register/

# Enable 2FA (required for new projects)
# Settings -> Account Security -> Add 2FA
```

### 2. API Token
```bash
# Create API token at: https://pypi.org/manage/account/token/
# Name: "llmsync-upload"
# Scope: "Entire account" (or specific to llmsync once published)

# Save token securely - you'll need it!
```

### 3. Install Build Tools
```bash
pip install --upgrade build twine
```

---

## 🚀 Publishing Steps

### Step 1: Prepare the Package

```bash
cd /path/to/llmsync/backend

# Verify files are in place
ls -la setup.py MANIFEST.in
ls -la llmsync/cli.py

# All should exist ✓
```

### Step 2: Build the Distribution

```bash
# Clean old builds
rm -rf dist/ build/ *.egg-info

# Build source distribution and wheel
python -m build

# You should see:
# dist/
#   llmsync-0.1.0-py3-none-any.whl
#   llmsync-0.1.0.tar.gz
```

### Step 3: Test the Build Locally

```bash
# Create test venv
python -m venv test_env
source test_env/bin/activate  # Windows: test_env\Scripts\activate

# Install from local build
pip install dist/llmsync-0.1.0-py3-none-any.whl

# Test CLI
llmsync --version
llmsync init --help

# Should work! ✓

# Deactivate
deactivate
```

### Step 4: Upload to Test PyPI (Optional but Recommended)

```bash
# Upload to Test PyPI first
twine upload --repository testpypi dist/*

# When prompted:
# username: __token__
# password: <your-testpypi-token>

# Test installation
pip install --index-url https://test.pypi.org/simple/ llmsync

# If works, proceed to real PyPI
```

### Step 5: Upload to PyPI

```bash
# Upload to real PyPI
twine upload dist/*

# When prompted:
# username: __token__
# password: <your-pypi-token>

# ✅ Published!
```

### Step 6: Verify Installation

```bash
# Wait 2-3 minutes for PyPI to index

# Test installation
pip install llmsync

# Verify
llmsync --version
# Should show: llmsync 0.1.0

# Test init
mkdir test-install
cd test-install
llmsync init

# Should create .env and docker-compose.yml ✓
```

---

## 🔄 Using pypirc (Easier Authentication)

Create `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-AgEIc... (your token)

[testpypi]
username = __token__
password = pypi-AgENd... (your token)
```

Then uploading is simpler:

```bash
twine upload dist/*
# No password prompt! Uses token from ~/.pypirc
```

---

## 📝 Publishing Checklist

### Before Publishing

- [x] Package name available on PyPI (`llmsync` ✓)
- [x] setup.py complete with all metadata
- [x] README.md exists and is informative
- [x] LICENSE file exists (MIT)
- [x] Version number set (0.1.0)
- [ ] PyPI account created
- [ ] 2FA enabled
- [ ] API token generated
- [ ] Tested locally
- [ ] (Optional) Tested on Test PyPI

### After Publishing

- [ ] Verify `pip install llmsync` works
- [ ] Update GitHub README with installation instructions
- [ ] Create GitHub release (v0.1.0)
- [ ] Announce on social media/forums
- [ ] Monitor for issues/feedback

---

## 🎯 Quick Commands Reference

```bash
# Build
python -m build

# Test locally
pip install dist/llmsync-0.1.0-py3-none-any.whl

# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*

# Install from PyPI
pip install llmsync

# Test CLI
llmsync --version
llmsync init
llmsync start --help
```

---

## 🔧 Troubleshooting

### Error: "Package name already taken"
```bash
# Check if name is actually taken
curl https://pypi.org/pypi/llmsync/json

# If taken, choose alternative:
# - llmsync-server
# - llm-sync
# Update setup.py name field
```

### Error: "Invalid distribution file"
```bash
# Clean and rebuild
rm -rf dist/ build/ *.egg-info
python -m build
```

### Error: "twine: command not found"
```bash
# Install twine
pip install --upgrade twine
```

### Error: "Invalid or expired token"
```bash
# Generate new token at: https://pypi.org/manage/account/token/
# Make sure to copy the FULL token starting with pypi-AgE...
```

---

## 📦 Publishing the SDK (llmsync-sdk)

After publishing the server, publish the SDK:

```bash
cd /path/to/llmsync/sdk/python

# Build SDK
python -m build

# Upload
twine upload dist/*

# Users can then:
pip install llmsync-sdk
```

**Note:** SDK implementation guide is in `SDK_IMPLEMENTATION_GUIDE.md` (12 hours to complete)

---

## 🔄 Publishing Updates

### Version 0.1.1, 0.1.2, etc. (Bug Fixes)

```bash
# Update version in setup.py
# version="0.1.1"

# Update in llmsync/cli.py
# version="llmsync 0.1.1"

# Rebuild and upload
rm -rf dist/
python -m build
twine upload dist/*
```

### Version 0.2.0 (New Features)

```bash
# Update version in setup.py
# version="0.2.0"

# Update changelog
# Add to README.md

# Rebuild and upload
python -m build
twine upload dist/*

# Create GitHub release
git tag v0.2.0
git push origin v0.2.0
```

---

## 📊 Post-Publishing Monitoring

### Check Package Stats

```bash
# View on PyPI
https://pypi.org/project/llmsync/

# Check download stats
https://pypistats.org/packages/llmsync
```

### Monitor Issues

```bash
# GitHub issues
https://github.com/4ahul/llmsync/issues

# PyPI project page comments
https://pypi.org/project/llmsync/#description
```

---

## ✅ Success Criteria

Your package is successfully published when:

1. ✅ `pip install llmsync` works
2. ✅ `llmsync --version` shows correct version
3. ✅ `llmsync init` creates config files
4. ✅ `llmsync start` launches server
5. ✅ Package appears on https://pypi.org/project/llmsync/
6. ✅ README and documentation visible on PyPI

---

## 🎉 After Publishing

### 1. Update README.md

Add installation section:

```markdown
## Installation

pip install llmsync

## Quick Start

llmsync init
llmsync start
```

### 2. Create GitHub Release

```bash
git tag v0.1.0
git push origin v0.1.0

# Create release on GitHub with changelog
```

### 3. Announce

- Twitter/X: "Just published llmsync to PyPI! 🚀"
- Reddit: r/Python, r/MachineLearning
- Hacker News: Show HN: LLMSync
- Dev.to: Write launch post

### 4. Add Badge to README

```markdown
[![PyPI version](https://badge.fury.io/py/llmsync.svg)](https://badge.fury.io/py/llmsync)
[![Downloads](https://pepy.tech/badge/llmsync)](https://pepy.tech/project/llmsync)
```

---

## 🚀 You're Ready!

Run these commands to publish:

```bash
cd backend
python -m build
twine upload dist/*
```

**That's it!** Your package will be live on PyPI! 🎉

---

## 📞 Support

- **PyPI Help:** https://pypi.org/help/
- **Packaging Guide:** https://packaging.python.org/
- **Issues:** https://github.com/4ahul/llmsync/issues

**Good luck with your PyPI debut!** 🚀
