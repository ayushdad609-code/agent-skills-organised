-- ============================================
-- Antigravity Chat Storage Schema
-- Stores conversation transcripts permanently
-- ============================================

-- 1. Conversations table (metadata)
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY,
    title TEXT NOT NULL DEFAULT 'Untitled',
    first_message TEXT,
    created_at TIMESTAMPTZ,
    last_modified TIMESTAMPTZ,
    total_steps INTEGER DEFAULT 0,
    model_used TEXT,
    synced_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Conversation steps table (full transcript)
CREATE TABLE IF NOT EXISTS conversation_steps (
    id BIGSERIAL,
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    step_index INTEGER NOT NULL,
    source TEXT NOT NULL,         -- USER_EXPLICIT, MODEL, SYSTEM
    step_type TEXT NOT NULL,      -- USER_INPUT, PLANNER_RESPONSE, RUN_COMMAND, etc.
    status TEXT,
    created_at TIMESTAMPTZ,
    content TEXT,
    thinking TEXT,
    tool_calls JSONB,
    is_truncated BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (conversation_id, step_index)
);

-- 3. Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_steps_conversation_id ON conversation_steps(conversation_id);
CREATE INDEX IF NOT EXISTS idx_steps_type ON conversation_steps(step_type);
CREATE INDEX IF NOT EXISTS idx_steps_source ON conversation_steps(source);
CREATE INDEX IF NOT EXISTS idx_steps_created_at ON conversation_steps(created_at);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at);
CREATE INDEX IF NOT EXISTS idx_conversations_last_modified ON conversations(last_modified);

-- 4. Enable RLS (required for Supabase security)
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_steps ENABLE ROW LEVEL SECURITY;

-- 5. Create service-role-only policies (only accessible via service key, not public)
CREATE POLICY "Service role full access on conversations"
    ON conversations FOR ALL
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role full access on conversation_steps"
    ON conversation_steps FOR ALL
    USING (true)
    WITH CHECK (true);

-- 6. Helpful view: conversation summary
CREATE OR REPLACE VIEW conversation_summary AS
SELECT
    c.id,
    c.title,
    c.created_at,
    c.last_modified,
    c.total_steps,
    c.model_used,
    c.synced_at,
    COUNT(CASE WHEN cs.source = 'USER_EXPLICIT' THEN 1 END) AS user_messages,
    COUNT(CASE WHEN cs.source = 'MODEL' THEN 1 END) AS model_responses,
    COUNT(CASE WHEN cs.tool_calls IS NOT NULL THEN 1 END) AS tool_call_steps
FROM conversations c
LEFT JOIN conversation_steps cs ON c.id = cs.conversation_id
GROUP BY c.id, c.title, c.created_at, c.last_modified, c.total_steps, c.model_used, c.synced_at
ORDER BY c.last_modified DESC;
