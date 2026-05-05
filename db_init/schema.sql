
ALTER TABLE channels DROP CONSTRAINT IF EXISTS unique_channel_name_per_workspace;
DROP TABLE IF EXISTS messages           CASCADE;
DROP TABLE IF EXISTS channel_membership CASCADE;
DROP TABLE IF EXISTS channels            CASCADE;
DROP TABLE IF EXISTS workspace_membership CASCADE;
DROP TABLE IF EXISTS workspaces         CASCADE;
DROP TABLE IF EXISTS users              CASCADE;

-- User

CREATE TABLE users (
    user_id       SERIAL          PRIMARY KEY,
    email         VARCHAR(255)    NOT NULL UNIQUE,
    username      VARCHAR(50)     NOT NULL UNIQUE,
    nickname      VARCHAR(100),
    password_hash CHAR(60)        NOT NULL,
    created_at    TIMESTAMP       NOT NULL DEFAULT NOW()
);

-- Workspace
CREATE TABLE workspaces (
    workspace_id  SERIAL          PRIMARY KEY,
    name          VARCHAR(100)    NOT NULL,
    description   TEXT,
    created_by    INT             NOT NULL REFERENCES users(user_id),
    created_at    TIMESTAMP       NOT NULL DEFAULT NOW()
);

-- Workspace_Membership

CREATE TABLE workspace_membership (
    workspace_id  INT             NOT NULL REFERENCES workspaces(workspace_id),
    user_id       INT             NOT NULL REFERENCES users(user_id),
    is_admin      BOOLEAN         NOT NULL DEFAULT FALSE,
    status        VARCHAR(10)     NOT NULL DEFAULT 'pending'
                                  CHECK (status IN ('pending', 'accepted')),
    invited_by    INT             REFERENCES users(user_id),
    invited_at    TIMESTAMP       NOT NULL DEFAULT NOW(),
    joined_at     TIMESTAMP,      -- NULL until the user accepts the invitation

    PRIMARY KEY (workspace_id, user_id)
);

-- Channel

CREATE TABLE channels (
    channel_id    SERIAL          PRIMARY KEY,
    workspace_id  INT             NOT NULL REFERENCES workspaces(workspace_id),
    name          VARCHAR(100),   -- NULL allowed for direct channels
    type          VARCHAR(10)     NOT NULL
                                  CHECK (type IN ('public', 'private', 'direct')),
    created_by    INT             NOT NULL REFERENCES users(user_id),
    created_at    TIMESTAMP       NOT NULL DEFAULT NOW(),

    -- Channel names must be unique within a workspace for non-direct channels
    CONSTRAINT unique_channel_name_per_workspace
        UNIQUE (workspace_id, name)
);

-- Channel_Membership

CREATE TABLE channel_membership (
    channel_id    INT             NOT NULL REFERENCES channels(channel_id),
    user_id       INT             NOT NULL REFERENCES users(user_id),
    status        VARCHAR(10)     NOT NULL DEFAULT 'pending'
                                  CHECK (status IN ('pending', 'accepted')),
    invited_by    INT             REFERENCES users(user_id), 
    invited_at    TIMESTAMP       NOT NULL DEFAULT NOW(),
    joined_at     TIMESTAMP,      -- NULL until the user accepts

    PRIMARY KEY (channel_id, user_id)
);

-- Messsages

CREATE TABLE messages (
    message_id    SERIAL          PRIMARY KEY,
    channel_id    INT             NOT NULL REFERENCES channels(channel_id),
    posted_by     INT             NOT NULL REFERENCES users(user_id),
    body          TEXT            NOT NULL,
    posted_at     TIMESTAMP       NOT NULL DEFAULT NOW()
);


-- Index

CREATE INDEX idx_messages_channel   ON messages(channel_id, posted_at);
CREATE INDEX idx_messages_posted_by ON messages(posted_by);
CREATE INDEX idx_wm_user            ON workspace_membership(user_id);
CREATE INDEX idx_cm_user            ON channel_membership(user_id);

-- Enforce a direct channel has exactly two users
CREATE OR REPLACE FUNCTION check_direct_channel_membership()
RETURNS TRIGGER AS $$
BEGIN
    IF (SELECT c.type FROM channels c WHERE c.channel_id = NEW.channel_id) = 'direct' THEN
        IF (SELECT COUNT(*) FROM channel_membership
            WHERE channel_id = NEW.channel_id) >= 2 THEN
            RAISE EXCEPTION 'Direct channels cannot have more than 2 members';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER enforce_direct_channel_size
BEFORE INSERT ON channel_membership
FOR EACH ROW EXECUTE FUNCTION check_direct_channel_membership();