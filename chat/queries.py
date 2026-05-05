import bcrypt
from django.db import connection


def _rows_to_dicts(cursor):
    cols = [col[0] for col in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


# =============================================================
# AUTH
# =============================================================

def get_user_by_username(username: str):
    with connection.cursor() as cur:
        cur.execute(
            "SELECT * FROM users WHERE username = %s",
            [username]
        )
        cols = [col[0] for col in cur.description]
        row = cur.fetchone()
        return dict(zip(cols, row)) if row else None


def get_user_by_id(user_id: int):
    with connection.cursor() as cur:
        cur.execute(
            "SELECT * FROM users WHERE user_id = %s",
            [user_id]
        )
        cols = [col[0] for col in cur.description]
        row = cur.fetchone()
        return dict(zip(cols, row)) if row else None


# =============================================================
# QUERY 1 — create a new user account
# =============================================================

def create_user(email: str, username: str, nickname: str, password: str):
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    with connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (email, username, nickname, password_hash)
            VALUES (%s, %s, %s, %s)
            RETURNING user_id
            """,
            [email, username, nickname, pw_hash]
        )
        return cur.fetchone()[0]


def check_password(user, password: str) -> bool:
    return bcrypt.checkpw(password.encode(), user['password_hash'].encode())


# =============================================================
# WORKSPACES
# =============================================================

def get_workspaces_for_user(user_id: int):
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT w.workspace_id, w.name, w.description, wm.is_admin
            FROM workspaces w
            JOIN workspace_membership wm ON w.workspace_id = wm.workspace_id
            WHERE wm.user_id = %s AND wm.status = 'accepted'
            ORDER BY w.name
            """,
            [user_id]
        )
        return _rows_to_dicts(cur)


def create_workspace(name: str, description: str, user_id: int):
    with connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO workspaces (name, description, created_by)
            VALUES (%s, %s, %s)
            RETURNING workspace_id
            """,
            [name, description, user_id]
        )
        workspace_id = cur.fetchone()[0]
        cur.execute(
            """
            INSERT INTO workspace_membership
                (workspace_id, user_id, is_admin, status, invited_at, joined_at)
            VALUES (%s, %s, TRUE, 'accepted', NOW(), NOW())
            """,
            [workspace_id, user_id]
        )
        return workspace_id


def get_workspace(workspace_id: int):
    with connection.cursor() as cur:
        cur.execute(
            "SELECT * FROM workspaces WHERE workspace_id = %s",
            [workspace_id]
        )
        cols = [col[0] for col in cur.description]
        row = cur.fetchone()
        return dict(zip(cols, row)) if row else None


def is_workspace_member(workspace_id: int, user_id: int) -> bool:
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT 1 FROM workspace_membership
            WHERE workspace_id = %s AND user_id = %s AND status = 'accepted'
            """,
            [workspace_id, user_id]
        )
        return cur.fetchone() is not None


def is_workspace_admin(workspace_id: int, user_id: int) -> bool:
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT 1 FROM workspace_membership
            WHERE workspace_id = %s AND user_id = %s
              AND is_admin = TRUE AND status = 'accepted'
            """,
            [workspace_id, user_id]
        )
        return cur.fetchone() is not None


def invite_to_workspace(workspace_id: int, invitee_id: int, inviter_id: int):
    with connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO workspace_membership
                (workspace_id, user_id, is_admin, status, invited_by, invited_at)
            VALUES (%s, %s, FALSE, 'pending', %s, NOW())
            ON CONFLICT (workspace_id, user_id) DO NOTHING
            """,
            [workspace_id, invitee_id, inviter_id]
        )


def accept_workspace_invite(workspace_id: int, user_id: int):
    with connection.cursor() as cur:
        cur.execute(
            """
            UPDATE workspace_membership
            SET status = 'accepted', joined_at = NOW()
            WHERE workspace_id = %s AND user_id = %s AND status = 'pending'
            """,
            [workspace_id, user_id]
        )


def promote_to_admin(workspace_id: int, user_id: int):
    with connection.cursor() as cur:
        cur.execute(
            """
            UPDATE workspace_membership
            SET is_admin = TRUE
            WHERE workspace_id = %s AND user_id = %s AND status = 'accepted'
            """,
            [workspace_id, user_id]
        )


def get_workspace_members(workspace_id: int):
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT u.user_id, u.username, u.nickname, wm.is_admin, wm.status
            FROM workspace_membership wm
            JOIN users u ON wm.user_id = u.user_id
            WHERE wm.workspace_id = %s AND wm.status = 'accepted'
            ORDER BY wm.is_admin DESC, u.username
            """,
            [workspace_id]
        )
        return _rows_to_dicts(cur)


# =============================================================
# QUERY 3 — for each workspace, list all current admins
# =============================================================

def get_all_workspace_admins():
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT w.workspace_id, w.name AS workspace_name,
                   u.user_id, u.username, u.nickname
            FROM workspace_membership wm
            JOIN workspaces w ON wm.workspace_id = w.workspace_id
            JOIN users u      ON wm.user_id      = u.user_id
            WHERE wm.is_admin = TRUE AND wm.status = 'accepted'
            ORDER BY w.name, u.username
            """
        )
        return _rows_to_dicts(cur)


# =============================================================
# CHANNELS
# =============================================================

def get_channels_for_user(workspace_id: int, user_id: int):
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT c.channel_id, c.name, c.type
            FROM channels c
            JOIN channel_membership cm
              ON c.channel_id = cm.channel_id
             AND cm.user_id   = %s
             AND cm.status    = 'accepted'
            WHERE c.workspace_id = %s
            ORDER BY c.type, c.name
            """,
            [user_id, workspace_id]
        )
        return _rows_to_dicts(cur)


def get_public_channels_for_workspace(workspace_id: int):
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT channel_id, name
            FROM channels
            WHERE workspace_id = %s AND type = 'public'
            ORDER BY name
            """,
            [workspace_id]
        )
        return _rows_to_dicts(cur)


def get_channel(channel_id: int):
    with connection.cursor() as cur:
        cur.execute(
            "SELECT * FROM channels WHERE channel_id = %s",
            [channel_id]
        )
        cols = [col[0] for col in cur.description]
        row = cur.fetchone()
        return dict(zip(cols, row)) if row else None


def is_channel_member(channel_id: int, user_id: int) -> bool:
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT 1 FROM channel_membership
            WHERE channel_id = %s AND user_id = %s AND status = 'accepted'
            """,
            [channel_id, user_id]
        )
        return cur.fetchone() is not None


# =============================================================
# QUERY 2 — create a new public channel (checks user is workspace member)
# =============================================================

def create_channel(workspace_id: int, name: str, channel_type: str, user_id: int):
    if not is_workspace_member(workspace_id, user_id):
        raise PermissionError("User is not a member of this workspace.")
    with connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO channels (workspace_id, name, type, created_by)
            VALUES (%s, %s, %s, %s)
            RETURNING channel_id
            """,
            [workspace_id, name, channel_type, user_id]
        )
        channel_id = cur.fetchone()[0]
        cur.execute(
            """
            INSERT INTO channel_membership
                (channel_id, user_id, status, invited_at, joined_at)
            VALUES (%s, %s, 'accepted', NOW(), NOW())
            """,
            [channel_id, user_id]
        )
        return channel_id

def create_direct_channel(workspace_id: int, user1_id: int, user2_id: int):
    # Check a direct channel between these two doesn't already exist
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT c.channel_id FROM channels c
            JOIN channel_membership cm1
              ON cm1.channel_id = c.channel_id AND cm1.user_id = %s
            JOIN channel_membership cm2
              ON cm2.channel_id = c.channel_id AND cm2.user_id = %s
            WHERE c.workspace_id = %s AND c.type = 'direct'
            """,
            [user1_id, user2_id, workspace_id]
        )
        existing = cur.fetchone()
        if existing:
            return existing[0]  # reuse existing channel

        # Create new direct channel
        cur.execute(
            """
            INSERT INTO channels (workspace_id, name, type, created_by)
            VALUES (%s, NULL, 'direct', %s)
            RETURNING channel_id
            """,
            [workspace_id, user1_id]
        )
        channel_id = cur.fetchone()[0]
        cur.execute(
            """
            INSERT INTO channel_membership (channel_id, user_id, status, invited_at, joined_at)
            VALUES (%s, %s, 'accepted', NOW(), NOW()),
                   (%s, %s, 'accepted', NOW(), NOW())
            """,
            [channel_id, user1_id, channel_id, user2_id]
        )
        return channel_id

def get_direct_channels_for_user(workspace_id: int, user_id: int):
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT c.channel_id,
                   u.username  AS other_username,
                   u.nickname  AS other_nickname
            FROM channels c
            JOIN channel_membership cm1
              ON cm1.channel_id = c.channel_id
             AND cm1.user_id    = %s
             AND cm1.status     = 'accepted'
            JOIN channel_membership cm2
              ON cm2.channel_id = c.channel_id
             AND cm2.user_id   != %s
            JOIN users u ON u.user_id = cm2.user_id
            WHERE c.workspace_id = %s
              AND c.type         = 'direct'
            ORDER BY u.username
            """,
            [user_id, user_id, workspace_id]
        )
        return _rows_to_dicts(cur)

def invite_to_channel(channel_id: int, invitee_id: int, inviter_id: int):
    with connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO channel_membership
                (channel_id, user_id, status, invited_by, invited_at)
            VALUES (%s, %s, 'pending', %s, NOW())
            ON CONFLICT (channel_id, user_id) DO NOTHING
            """,
            [channel_id, invitee_id, inviter_id]
        )


def accept_channel_invite(channel_id: int, user_id: int):
    with connection.cursor() as cur:
        cur.execute(
            """
            UPDATE channel_membership
            SET status = 'accepted', joined_at = NOW()
            WHERE channel_id = %s AND user_id = %s AND status = 'pending'
            """,
            [channel_id, user_id]
        )


def join_public_channel(channel_id: int, user_id: int):
    with connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO channel_membership
                (channel_id, user_id, status, invited_at, joined_at)
            VALUES (%s, %s, 'accepted', NOW(), NOW())
            ON CONFLICT (channel_id, user_id) DO NOTHING
            """,
            [channel_id, user_id]
        )


# =============================================================
# QUERY 4 — pending invites older than 5 days per public channel
# =============================================================

def get_stale_pending_invites(workspace_id: int):
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT c.channel_id, c.name AS channel_name,
                   COUNT(*) AS pending_count
            FROM channel_membership cm
            JOIN channels c ON cm.channel_id = c.channel_id
            WHERE c.workspace_id = %s
              AND c.type         = 'public'
              AND cm.status      = 'pending'
              AND cm.invited_at  < NOW() - INTERVAL '5 days'
            GROUP BY c.channel_id, c.name
            ORDER BY c.name
            """,
            [workspace_id]
        )
        return _rows_to_dicts(cur)


# =============================================================
# QUERY 5 — all messages in a channel, chronological
# =============================================================

def get_messages(channel_id: int):
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT m.message_id, m.body, m.posted_at,
                   u.username, u.nickname
            FROM messages m
            JOIN users u ON m.posted_by = u.user_id
            WHERE m.channel_id = %s
            ORDER BY m.posted_at ASC
            """,
            [channel_id]
        )
        return _rows_to_dicts(cur)


# =============================================================
# QUERY 6 — all messages posted by a particular user
# =============================================================

def get_messages_by_user(user_id: int):
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT m.message_id, m.body, m.posted_at,
                   c.name  AS channel_name,
                   c.channel_id,
                   w.name  AS workspace_name,
                   w.workspace_id
            FROM messages m
            JOIN channels  c ON m.channel_id  = c.channel_id
            JOIN workspaces w ON c.workspace_id = w.workspace_id
            WHERE m.posted_by = %s
            ORDER BY m.posted_at DESC
            """,
            [user_id]
        )
        return _rows_to_dicts(cur)


# =============================================================
# QUERY 7 — keyword search across accessible messages
# =============================================================

def search_messages(user_id: int, keyword: str):
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT m.message_id, m.body, m.posted_at,
                   u.username,
                   c.name        AS channel_name,
                   c.channel_id,
                   w.name        AS workspace_name,
                   w.workspace_id
            FROM messages m
            JOIN users u        ON m.posted_by    = u.user_id
            JOIN channels c     ON m.channel_id   = c.channel_id
            JOIN workspaces w   ON c.workspace_id = w.workspace_id
            JOIN workspace_membership wm
                ON wm.workspace_id = c.workspace_id
               AND wm.user_id      = %s
               AND wm.status       = 'accepted'
            JOIN channel_membership cm
                ON cm.channel_id = m.channel_id
               AND cm.user_id    = %s
               AND cm.status     = 'accepted'
            WHERE m.body ILIKE %s
            ORDER BY m.posted_at DESC
            """,
            [user_id, user_id, f'%{keyword}%']
        )
        return _rows_to_dicts(cur)


# =============================================================
# POST A MESSAGE
# =============================================================

def post_message(channel_id: int, user_id: int, body: str):
    with connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO messages (channel_id, posted_by, body)
            VALUES (%s, %s, %s)
            RETURNING message_id
            """,
            [channel_id, user_id, body]
        )
        return cur.fetchone()[0]


# =============================================================
# PENDING INVITATIONS for a user
# =============================================================

def get_pending_workspace_invites(user_id: int):
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT wm.workspace_id, w.name AS workspace_name,
                   u.username AS invited_by_username, wm.invited_at
            FROM workspace_membership wm
            JOIN workspaces w ON wm.workspace_id = w.workspace_id
            LEFT JOIN users u ON wm.invited_by   = u.user_id
            WHERE wm.user_id = %s AND wm.status = 'pending'
            ORDER BY wm.invited_at DESC
            """,
            [user_id]
        )
        return _rows_to_dicts(cur)


def get_pending_channel_invites(user_id: int):
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT cm.channel_id, c.name AS channel_name,
                   w.workspace_id, w.name AS workspace_name,
                   u.username AS invited_by_username, cm.invited_at
            FROM channel_membership cm
            JOIN channels   c ON cm.channel_id  = c.channel_id
            JOIN workspaces w ON c.workspace_id = w.workspace_id
            LEFT JOIN users u ON cm.invited_by  = u.user_id
            WHERE cm.user_id = %s AND cm.status = 'pending'
            ORDER BY cm.invited_at DESC
            """,
            [user_id]
        )
        return _rows_to_dicts(cur)


# =============================================================
# USER LOOKUP
# =============================================================

def find_user_by_username(username: str):
    with connection.cursor() as cur:
        cur.execute(
            "SELECT user_id, username, nickname FROM users WHERE username = %s",
            [username]
        )
        cols = [col[0] for col in cur.description]
        row = cur.fetchone()
        return dict(zip(cols, row)) if row else None