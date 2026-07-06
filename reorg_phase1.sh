#!/bin/bash
# Phase 1: Quick Wins — delete dead, fix naming, merge duplicate
set -euo pipefail
cd /data/data/com.termux/files/home/.agents/skills

echo "=== Phase 1a: Delete 4 incomplete folders ==="
rm -rf gsap-skills-repo hallmark ponytail-repo taste-skill
echo "Deleted: gsap-skills-repo, hallmark, ponytail-repo, taste-skill"

echo ""
echo "=== Phase 1b: Fix 2 uppercase names ==="
mv Guardian-Gate guardian-gate 2>/dev/null && echo "Guardian-Gate → guardian-gate" || echo "Guardian-Gate already renamed"
mv Repo-Request repo-request 2>/dev/null && echo "Repo-Request → repo-request" || echo "Repo-Request already renamed"

echo ""
echo "=== Phase 1c: Merge duplicate ==="
if [ -d "tinystruct-pat" ] && [ -d "tinystruct-patterns" ]; then
  rm -rf tinystruct-pat
  echo "Deleted tinystruct-pat (keeping tinystruct-patterns)"
else
  echo "tinystruct-pat already removed or doesn't exist"
fi

echo ""
echo "=== Phase 1 complete ==="
ls -1d */ | wc -l
echo "folders remaining"
