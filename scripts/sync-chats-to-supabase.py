#!/usr/bin/env python3
"""
Sync Antigravity conversation transcripts to Supabase via REST API.

Usage:
    python3 sync-chats-to-supabase.py [--all | --conversation-id <ID>]

Options:
    --all                 Sync all conversations (default)
    --conversation-id ID  Sync a specific conversation only
    --dry-run             Show what would be synced without writing

Requires:
    SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables.
"""

import os
import sys
import json
import argparse
from pathlib import Path

import requests

# --- Configuration ---
BRAIN_DIR = os.path.expanduser("~/.gemini/antigravity-cli/brain")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(SCRIPT_DIR, ".env.supabase")

# Auto-load .env.supabase if it exists
if os.path.isfile(ENV_FILE):
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")


def get_headers():
    """Return auth headers for Supabase REST API."""
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates",  # upsert behavior
    }


def supabase_upsert(table, data, on_conflict=None):
    """Upsert data into a Supabase table via PostgREST."""
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = get_headers()
    if on_conflict:
        headers["Prefer"] = f"resolution=merge-duplicates"

    resp = requests.post(url, headers=headers, json=data)
    if resp.status_code not in (200, 201, 204):
        raise Exception(f"Supabase error ({resp.status_code}): {resp.text}")
    return resp


def discover_conversations():
    """Find all conversation directories in the brain folder."""
    conversations = []
    if not os.path.isdir(BRAIN_DIR):
        print(f"❌ Brain directory not found: {BRAIN_DIR}")
        return conversations

    for entry in os.listdir(BRAIN_DIR):
        conv_dir = os.path.join(BRAIN_DIR, entry)
        transcript_path = os.path.join(conv_dir, ".system_generated", "logs", "transcript.jsonl")
        if os.path.isdir(conv_dir) and os.path.isfile(transcript_path):
            conversations.append({
                "id": entry,
                "dir": conv_dir,
                "transcript_path": transcript_path,
            })

    return conversations


def parse_transcript(transcript_path):
    """Parse a JSONL transcript file into a list of step dicts."""
    steps = []
    with open(transcript_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                step = json.loads(line)
                steps.append(step)
            except json.JSONDecodeError as e:
                print(f"  ⚠️  Skipping malformed line {line_num + 1}: {e}")
    return steps


def extract_conversation_metadata(conv_id, steps):
    """Extract conversation-level metadata from transcript steps."""
    title = ""
    first_user_message = ""
    created_at = None
    last_modified = None
    total_steps = len(steps)
    model_used = ""

    for step in steps:
        ts = step.get("created_at")
        if ts:
            if created_at is None:
                created_at = ts
            last_modified = ts

        # Extract first user message as title
        if step.get("type") == "USER_INPUT" and not first_user_message:
            content = step.get("content", "")
            if "<USER_REQUEST>" in content:
                start = content.find("<USER_REQUEST>") + len("<USER_REQUEST>")
                end = content.find("</USER_REQUEST>")
                if end > start:
                    first_user_message = content[start:end].strip()
                    title = first_user_message[:200]

        # Try to find model info
        content = step.get("content", "")
        if content and "Model Selection" in content and " to " in content:
            parts = content.split(" to ")
            if len(parts) > 1:
                model_candidate = parts[-1].split(".")[0].split("\n")[0].strip()
                if model_candidate and len(model_candidate) < 100:
                    model_used = model_candidate

    return {
        "id": conv_id,
        "title": title or f"Conversation {conv_id[:8]}",
        "first_message": (first_user_message[:1000]) if first_user_message else None,
        "created_at": created_at,
        "last_modified": last_modified,
        "total_steps": total_steps,
        "model_used": model_used or None,
        "synced_at": "now()",
    }


def prepare_steps_for_db(conv_id, steps):
    """Prepare transcript steps for database insertion."""
    db_steps = []
    for step in steps:
        content = step.get("content", "")
        thinking = step.get("thinking", "")
        tool_calls = step.get("tool_calls")

        # Truncate very large content to 50KB
        if content and len(content) > 50000:
            content = content[:50000] + "\n... [TRUNCATED]"
        if thinking and len(thinking) > 10000:
            thinking = thinking[:10000] + "\n... [TRUNCATED]"

        db_step = {
            "conversation_id": conv_id,
            "step_index": step.get("step_index", 0),
            "source": step.get("source", ""),
            "step_type": step.get("type", ""),
            "status": step.get("status", ""),
            "created_at": step.get("created_at"),
            "content": content if content else None,
            "thinking": thinking if thinking else None,
            "tool_calls": json.dumps(tool_calls) if tool_calls else None,
            "is_truncated": step.get("is_truncated", False),
        }
        db_steps.append(db_step)

    return db_steps


def sync_conversation(conv):
    """Sync a single conversation to Supabase."""
    conv_id = conv["id"]
    print(f"\n📤 Syncing conversation: {conv_id}")

    # Parse transcript
    steps = parse_transcript(conv["transcript_path"])
    if not steps:
        print(f"  ⚠️  No steps found, skipping.")
        return False

    # Extract metadata
    metadata = extract_conversation_metadata(conv_id, steps)
    # Remove the now() placeholder and handle it properly
    metadata_copy = {**metadata}
    del metadata_copy["synced_at"]  # Let DB default handle this
    
    print(f"  📝 Title: {(metadata['title'][:60])}...")
    print(f"  📊 Steps: {metadata['total_steps']}")

    # Upsert conversation metadata
    try:
        supabase_upsert("conversations", metadata_copy)
        print(f"  ✅ Conversation metadata upserted.")
    except Exception as e:
        print(f"  ❌ Failed to upsert conversation: {e}")
        return False

    # Prepare and upsert steps in batches of 30
    db_steps = prepare_steps_for_db(conv_id, steps)
    batch_size = 30
    total_inserted = 0

    for i in range(0, len(db_steps), batch_size):
        batch = db_steps[i:i + batch_size]
        try:
            supabase_upsert("conversation_steps", batch)
            total_inserted += len(batch)
            sys.stdout.write(f"\r  ⏳ Syncing steps: {total_inserted}/{len(db_steps)}")
            sys.stdout.flush()
        except Exception as e:
            print(f"\n  ❌ Failed to upsert steps batch {i // batch_size + 1}: {e}")
            return False

    print(f"\n  ✅ {total_inserted} steps synced.")
    return True


def check_connection():
    """Verify Supabase connection."""
    url = f"{SUPABASE_URL}/rest/v1/conversations?select=id&limit=1"
    headers = get_headers()
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            return True
        elif resp.status_code == 404:
            print("❌ Table 'conversations' not found. Run the schema SQL first.")
            return False
        else:
            print(f"❌ Supabase connection error ({resp.status_code}): {resp.text}")
            return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Sync Antigravity chats to Supabase")
    parser.add_argument("--all", action="store_true", default=True, help="Sync all conversations")
    parser.add_argument("--conversation-id", type=str, help="Sync a specific conversation")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()

    print("🔄 Antigravity Chat → Supabase Sync")
    print("=" * 40)

    # Validate env vars
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Missing environment variables.")
        print("   export SUPABASE_URL='https://wtmxypmnmvirwkbojyct.supabase.co'")
        print("   export SUPABASE_SERVICE_KEY='your-service-role-key'")
        sys.exit(1)

    # Discover conversations
    conversations = discover_conversations()
    if not conversations:
        print("❌ No conversations found.")
        sys.exit(1)

    # Filter if specific ID requested
    if args.conversation_id:
        conversations = [c for c in conversations if c["id"] == args.conversation_id]
        if not conversations:
            print(f"❌ Conversation {args.conversation_id} not found.")
            sys.exit(1)

    print(f"📂 Found {len(conversations)} conversation(s)")

    if args.dry_run:
        print("\n🔍 DRY RUN — no data will be written")
        for conv in conversations:
            steps = parse_transcript(conv["transcript_path"])
            meta = extract_conversation_metadata(conv["id"], steps)
            print(f"\n  {meta['id'][:8]}... | {meta['total_steps']} steps | {meta['title'][:50]}")
        return

    # Verify connection
    if not check_connection():
        print("\n💡 Tip: Make sure the database tables exist first.")
        print("   Run the SQL from: knowledge-base/scripts/supabase-chat-schema.sql")
        sys.exit(1)

    # Sync each conversation
    success = 0
    failed = 0
    for conv in conversations:
        if sync_conversation(conv):
            success += 1
        else:
            failed += 1

    print(f"\n{'=' * 40}")
    print(f"✅ Synced: {success} | ❌ Failed: {failed}")


if __name__ == "__main__":
    main()
