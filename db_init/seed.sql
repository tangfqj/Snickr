-- -------------------------------------------------------------
-- USERS
-- -------------------------------------------------------------

INSERT INTO users (email, username, nickname, password_hash) VALUES
('alice@example.com', 'alice', 'Alice Admin',   '$2b$12$DdfsvdTvvzIVMaoKMQVrfeV/Hn/6i1QnPwsaM6MKW57SMFFbzEBhW'),
('bob@example.com',   'bob',   'Bob Builder',   '$2b$12$DdfsvdTvvzIVMaoKMQVrfeV/Hn/6i1QnPwsaM6MKW57SMFFbzEBhW'),
('carol@example.com', 'carol', 'Carol Singer',  '$2b$12$DdfsvdTvvzIVMaoKMQVrfeV/Hn/6i1QnPwsaM6MKW57SMFFbzEBhW'),
('dave@example.com',  'dave',  'Dave Developer','$2b$12$DdfsvdTvvzIVMaoKMQVrfeV/Hn/6i1QnPwsaM6MKW57SMFFbzEBhW'),
('eve@example.com',   'eve',   'Eve Engineer',  '$2b$12$DdfsvdTvvzIVMaoKMQVrfeV/Hn/6i1QnPwsaM6MKW57SMFFbzEBhW');

-- -------------------------------------------------------------
-- WORKSPACES
-- alice creates both workspaces (user_id = 1)
-- -------------------------------------------------------------

INSERT INTO workspaces (name, description, created_by) VALUES
('Acme Corp',      'Internal workspace for Acme Corp employees',      1),
('CS Department',  'Workspace for the university CS department',       1);

-- -------------------------------------------------------------
-- WORKSPACE MEMBERSHIP
-- Acme Corp (workspace_id=1): alice(admin), bob, carol, dave
-- CS Dept   (workspace_id=2): alice(admin), carol, eve
-- dave is invited to CS Dept but has NOT accepted yet (pending)
-- -- this gives query 3 multiple admins to show,
-- -- and query 4 a pending invite older than 5 days
-- -------------------------------------------------------------

-- Acme Corp memberships
INSERT INTO workspace_membership
    (workspace_id, user_id, is_admin, status, invited_by, invited_at, joined_at)
VALUES
-- alice: auto-joined as admin on creation
(1, 1, TRUE,  'accepted', NULL, NOW(),                       NOW()),
-- bob: invited by alice, accepted
(1, 2, FALSE, 'accepted', 1,    NOW() - INTERVAL '10 days',  NOW() - INTERVAL '9 days'),
-- carol: invited by alice, accepted, also made admin
(1, 3, TRUE,  'accepted', 1,    NOW() - INTERVAL '8 days',   NOW() - INTERVAL '7 days'),
-- dave: invited by alice, accepted
(1, 4, FALSE, 'accepted', 1,    NOW() - INTERVAL '6 days',   NOW() - INTERVAL '5 days');

-- CS Department memberships
INSERT INTO workspace_membership
    (workspace_id, user_id, is_admin, status, invited_by, invited_at, joined_at)
VALUES
-- alice: auto-joined as admin on creation
(2, 1, TRUE,  'accepted', NULL, NOW(),                       NOW()),
-- carol: invited by alice, accepted
(2, 3, FALSE, 'accepted', 1,    NOW() - INTERVAL '7 days',   NOW() - INTERVAL '6 days'),
-- eve: invited by alice, accepted
(2, 5, FALSE, 'accepted', 1,    NOW() - INTERVAL '5 days',   NOW() - INTERVAL '4 days'),
-- dave: invited by alice, NOT yet accepted (pending, invited 8 days ago)
-- this is the key row for query 4
(2, 4, FALSE, 'pending',  1,    NOW() - INTERVAL '8 days',   NULL);

-- -------------------------------------------------------------
-- CHANNELS
-- Acme Corp (workspace_id=1):
--   #general      (public)
--   #engineering  (public)
--   #hr-private   (private)
--   alice<->bob   (direct)
-- CS Dept (workspace_id=2):
--   #announcements (public)
--   #research       (private)
-- -------------------------------------------------------------

INSERT INTO channels (workspace_id, name, type, created_by) VALUES
(1, 'general',       'public',  1),   -- channel_id = 1
(1, 'engineering',   'public',  2),   -- channel_id = 2, created by bob
(1, 'hr-private',    'private', 3),   -- channel_id = 3, created by carol
(1, NULL,            'direct',  1),   -- channel_id = 4, alice <-> bob
(2, 'announcements', 'public',  1),   -- channel_id = 5
(2, 'research',      'private', 1);   -- channel_id = 6

-- -------------------------------------------------------------
-- CHANNEL MEMBERSHIP
-- #general (1):      alice, bob, carol, dave (all accepted)
--                    eve invited 6 days ago but NOT accepted
--                    --> shows up in query 4
-- #engineering (2):  alice, bob, dave (accepted)
--                    carol invited 3 days ago, not accepted
--                    --> does NOT show in query 4 (< 5 days)
-- #hr-private (3):   carol, alice (accepted)
-- direct (4):        alice, bob (accepted)
-- #announcements(5): alice, carol, eve (accepted)
-- #research (6):     alice, carol (accepted)
-- -------------------------------------------------------------

-- #general (channel_id = 1)
INSERT INTO channel_membership
    (channel_id, user_id, status, invited_by, invited_at, joined_at)
VALUES
(1, 1, 'accepted', NULL, NOW() - INTERVAL '10 days', NOW() - INTERVAL '10 days'), -- alice self-joined
(1, 2, 'accepted', 1,    NOW() - INTERVAL '9 days',  NOW() - INTERVAL '9 days'),  -- bob
(1, 3, 'accepted', 1,    NOW() - INTERVAL '8 days',  NOW() - INTERVAL '8 days'),  -- carol
(1, 4, 'accepted', 1,    NOW() - INTERVAL '7 days',  NOW() - INTERVAL '7 days'),  -- dave
(1, 5, 'pending',  1,    NOW() - INTERVAL '6 days',  NULL);

-- #engineering (channel_id = 2)
INSERT INTO channel_membership
    (channel_id, user_id, status, invited_by, invited_at, joined_at)
VALUES
(2, 1, 'accepted', NULL, NOW() - INTERVAL '10 days', NOW() - INTERVAL '10 days'), -- alice
(2, 2, 'accepted', NULL, NOW() - INTERVAL '9 days',  NOW() - INTERVAL '9 days'),  -- bob (creator)
(2, 4, 'accepted', 2,    NOW() - INTERVAL '8 days',  NOW() - INTERVAL '8 days'),  -- dave
-- carol: invited only 3 days ago, pending
-- --> does NOT appear in query 4 result (less than 5 days)
(2, 3, 'pending',  2,    NOW() - INTERVAL '3 days',  NULL);

-- #hr-private (channel_id = 3)
INSERT INTO channel_membership
    (channel_id, user_id, status, invited_by, invited_at, joined_at)
VALUES
(3, 3, 'accepted', NULL, NOW() - INTERVAL '7 days', NOW() - INTERVAL '7 days'), -- carol (creator)
(3, 1, 'accepted', 3,    NOW() - INTERVAL '6 days', NOW() - INTERVAL '6 days'); -- alice invited by carol

-- direct channel alice<->bob (channel_id = 4)
INSERT INTO channel_membership
    (channel_id, user_id, status, invited_by, invited_at, joined_at)
VALUES
(4, 1, 'accepted', NULL, NOW() - INTERVAL '5 days', NOW() - INTERVAL '5 days'), -- alice
(4, 2, 'accepted', 1,    NOW() - INTERVAL '5 days', NOW() - INTERVAL '5 days'); -- bob

-- #announcements (channel_id = 5)
INSERT INTO channel_membership
    (channel_id, user_id, status, invited_by, invited_at, joined_at)
VALUES
(5, 1, 'accepted', NULL, NOW() - INTERVAL '7 days', NOW() - INTERVAL '7 days'), -- alice
(5, 3, 'accepted', 1,    NOW() - INTERVAL '6 days', NOW() - INTERVAL '6 days'), -- carol
(5, 5, 'accepted', 1,    NOW() - INTERVAL '5 days', NOW() - INTERVAL '5 days'); -- eve

-- #research (channel_id = 6)
INSERT INTO channel_membership
    (channel_id, user_id, status, invited_by, invited_at, joined_at)
VALUES
(6, 1, 'accepted', NULL, NOW() - INTERVAL '6 days', NOW() - INTERVAL '6 days'), -- alice (creator)
(6, 3, 'accepted', 1,    NOW() - INTERVAL '5 days', NOW() - INTERVAL '5 days'); -- carol

-- -------------------------------------------------------------
-- MESSAGES
-- -------------------------------------------------------------

-- #general (channel_id = 1) -- accessible to alice, bob, carol, dave
INSERT INTO messages (channel_id, posted_by, body, posted_at) VALUES
(1, 1, 'Welcome everyone to the general channel!',                                        NOW() - INTERVAL '9 days'),
(1, 2, 'Thanks Alice! Happy to be here.',                                                 NOW() - INTERVAL '9 days' + INTERVAL '1 hour'),
(1, 4, 'Hey team, the two lines are perpendicular to each other in the new diagram.',     NOW() - INTERVAL '8 days'),
(1, 3, 'Good catch Dave. I noticed the perpendicular axis was mislabeled too.',           NOW() - INTERVAL '8 days' + INTERVAL '2 hours'),
(1, 1, 'Let us recheck all the geometry before the presentation.',                        NOW() - INTERVAL '7 days');

-- #engineering (channel_id = 2) -- accessible to alice, bob, dave
INSERT INTO messages (channel_id, posted_by, body, posted_at) VALUES
(2, 2, 'Starting the new sprint today.',                                                  NOW() - INTERVAL '7 days'),
(2, 4, 'I have updated the architecture doc.',                                            NOW() - INTERVAL '6 days'),
(2, 1, 'The load balancer config needs to be perpendicular to the data flow.',            NOW() - INTERVAL '5 days'),
(2, 2, 'Agreed, let us fix that in the next deploy.',                                     NOW() - INTERVAL '4 days');

-- #hr-private (channel_id = 3) -- accessible to alice, carol only
INSERT INTO messages (channel_id, posted_by, body, posted_at) VALUES
(3, 3, 'This channel is for HR discussions only.',                                        NOW() - INTERVAL '6 days'),
(3, 1, 'Understood. Keeping this confidential.',                                          NOW() - INTERVAL '5 days'),
(3, 3, 'The org chart lines are perpendicular in the new layout.',                        NOW() - INTERVAL '4 days');
-- note: bob and dave cannot see these even though one contains 'perpendicular'

-- direct alice<->bob (channel_id = 4)
INSERT INTO messages (channel_id, posted_by, body, posted_at) VALUES
(4, 1, 'Hey Bob, can you review my PR when you get a chance?',                            NOW() - INTERVAL '4 days'),
(4, 2, 'Sure, will do it this afternoon.',                                                NOW() - INTERVAL '4 days' + INTERVAL '1 hour');

-- #announcements (channel_id = 5) -- accessible to alice, carol, eve
INSERT INTO messages (channel_id, posted_by, body, posted_at) VALUES
(5, 1, 'Welcome to the CS Department workspace!',                                         NOW() - INTERVAL '6 days'),
(5, 3, 'Reminder: faculty meeting on Friday.',                                            NOW() - INTERVAL '4 days'),
(5, 5, 'The new curriculum has perpendicular tracks for theory and systems.',             NOW() - INTERVAL '3 days');

-- #research (channel_id = 6) -- accessible to alice, carol only
INSERT INTO messages (channel_id, posted_by, body, posted_at) VALUES
(6, 1, 'Sharing the new paper draft here.',                                               NOW() - INTERVAL '5 days'),
(6, 3, 'The vectors in section 3 are perpendicular -- worth highlighting.',               NOW() - INTERVAL '3 days'),
(6, 1, 'Great point, I will add a diagram.',                                              NOW() - INTERVAL '2 days');