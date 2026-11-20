#!/usr/bin/env bash
set -u
PROTECTED=/home/samertts/workspace/projects/gula-platform
ISOLATED=/tmp/opencode/gula-national-completion-013
date -u +'UTC %Y-%m-%dT%H:%M:%SZ'
printf '%s\n' '--- PROTECTED STATUS ---'
git -C "$PROTECTED" status --short --branch
printf '%s\n' '--- PROTECTED HEAD ---'
git -C "$PROTECTED" rev-parse HEAD
printf '%s\n' '--- PROTECTED STATUS SHA256 ---'
git -C "$PROTECTED" status --porcelain=v1 -uall | sha256sum
printf '%s\n' '--- PROTECTED REMOTES ---'
git -C "$PROTECTED" remote -v
printf '%s\n' '--- PROTECTED WORKTREES ---'
git -C "$PROTECTED" worktree list --porcelain
printf '%s\n' '--- PROTECTED STASHES ---'
git -C "$PROTECTED" stash list
printf '%s\n' '--- PROTECTED PROCESSES (filtered) ---'
ps -eo pid,ppid,etime,args | grep -E '(gula-platform|gula-integration|opencode|postgres|redis|dockerd)' | grep -v grep || true
printf '%s\n' '--- ISOLATED STATUS ---'
git -C "$ISOLATED" status --short --branch
printf '%s\n' '--- ISOLATED HEAD ---'
git -C "$ISOLATED" rev-parse HEAD
printf '%s\n' '--- ISOLATED REMOTES ---'
git -C "$ISOLATED" remote -v
