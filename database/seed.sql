-- Seed data: the gallery layout. Contains no accounts or credentials.
-- Accounts are created with management commands (seed_system_account,
-- create_admin) so passwords are hashed and secrets encrypted properly.
--
-- Safe to run more than once: ON CONFLICT skips rows that already exist.
-- Replace the placeholder rooms below with your team's floor plan, but
-- keep the 'Outside' room: the application depends on it.

INSERT INTO gallery_rooms (name) VALUES
    ('Outside'),
    ('Lobby'),
    ('Impressionism'),
    ('Modern'),
    ('Sculpture Court')
ON CONFLICT (name) DO NOTHING;

-- Connections, looked up by name so this file doesn't depend on room IDs.
-- LEAST/GREATEST put the smaller ID in room_a, as the table requires.
INSERT INTO adjacent_rooms (room_a, room_b)
SELECT LEAST(a.room_id, b.room_id), GREATEST(a.room_id, b.room_id)
FROM (VALUES
    ('Outside',       'Lobby'),          -- the Lobby is the entrance
    ('Lobby',         'Impressionism'),
    ('Lobby',         'Modern'),
    ('Modern',        'Sculpture Court')
) AS pair (room_1, room_2)
JOIN gallery_rooms a ON a.name = pair.room_1
JOIN gallery_rooms b ON b.name = pair.room_2
ON CONFLICT (room_a, room_b) DO NOTHING;
