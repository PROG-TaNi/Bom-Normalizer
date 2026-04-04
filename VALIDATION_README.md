# 🔍 Validation Scripts - Quick Start

## Run Validation (5 minutes)

### Windows

```powershell
cd bom-normalizer
.\validate-submission.ps1 -PingUrl "https://tani-prog-bom-normalizer.hf.space"
```

### Linux/Mac

```bash
cd bom-normalizer
chmod +x validate-submission.sh
./validate-submission.sh https://tani-prog-bom-normalizer.hf.space
```

---

## What Gets Checked

1. ✅ **HF Space Ping** - Verifies Space is live
2. ✅ **Docker Build** - Ensures image builds successfully
3. ✅ **OpenEnv Validate** - Checks spec compliance

---

## Expected Result

```
========================================
  All 3/3 checks passed!
  Your submission is ready to submit.
========================================
```

---

## If Validation Fails

Read: `VALIDATION_INSTRUCTIONS.md`

---

## After Validation Passes

1. Read: `QUICK_REFERENCE.md`
2. Follow: `SUBMISSION_GUIDE.md`
3. Submit!

---

## Documentation Files

| File | Purpose |
|------|---------|
| `VALIDATION_README.md` | This file - quick start |
| `VALIDATION_INSTRUCTIONS.md` | Complete troubleshooting |
| `SUBMISSION_GUIDE.md` | Step-by-step submission |
| `QUICK_REFERENCE.md` | URLs and commands |
| `PRE_SUBMISSION_CHECKLIST.md` | 70-point checklist |
| `SUBMISSION_INDEX.md` | Navigation guide |

---

## Need Help?

- **Troubleshooting:** See `VALIDATION_INSTRUCTIONS.md`
- **Submission:** See `SUBMISSION_GUIDE.md`
- **Quick Reference:** See `QUICK_REFERENCE.md`

---

**Status:** ✅ READY  
**Action:** RUN VALIDATION NOW! 🚀

