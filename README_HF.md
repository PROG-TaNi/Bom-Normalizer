---
title: BOM Normalizer
emoji: 🔧
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
license: mit
tags:
  - openenv
  - reinforcement-learning
  - supply-chain
  - data-cleaning
  - electronics
---

# BOM Normalizer - OpenEnv Competition Submission

Enterprise-grade Bill of Materials (BOM) normalization environment for training AI agents on real-world supply chain data cleaning tasks.

## 🎯 What This Does

This environment simulates the real-world task of normalizing messy Bill of Materials (BOM) data in electronics manufacturing - a $2.3B annual problem.

## 🚀 Quick Start

The environment is running! Test the API:

```bash
# Health check
curl https://YOUR_SPACE_URL/health

# List tasks
curl https://YOUR_SPACE_URL/tasks

# Reset environment
curl -X POST https://YOUR_SPACE_URL/reset?task_id=easy

# Execute action
curl -X POST https://YOUR_SPACE_URL/step?task_id=easy \
  -H "Content-Type: application/json" \
  -d '{"action_type":"normalize_vendor","row_id":1,"new_value":"Texas Instruments"}'
```

## 📊 Tasks

- **Easy:** Normalize vendor names across 10 rows
- **Medium:** Normalize vendor, value, and package across 50 rows  
- **Hard:** Full normalization + deduplication across ~100 rows

## 🏆 Features

- Dense reward function with partial progress signals
- Sophisticated grading with partial credit
- Creative mechanics: hints, batch operations, undo
- Deterministic and reproducible
- Real-world utility for supply chain optimization

## 📖 Full Documentation

See the complete README.md in the repository for:
- Detailed environment description
- Action and observation space definitions
- Task specifications
- Setup instructions
- Baseline scores

## 🔗 Links

- Competition: OpenEnv Hackathon 2025
- Category: Real-World Utility
- License: MIT
