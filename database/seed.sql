-- Seed data for gallery layout (no accounts/credetials).
-- 'Outside' indicates the outside world (entrances/exits).
-- If is_restricted is TRUE, the room is staff-only.

INSERT INTO gallery_rooms (name, is_restricted) VALUES
    ('Outside',         FALSE),
    ('Lobby',           FALSE),
    ('Main Hall',       FALSE),
    ('Modern Art',      FALSE),
    ('Portrait Hall',   FALSE),
    ('Exhibit Hall',    FALSE),
    ('Sculptures',      FALSE),
    ('Local Art',       FALSE),
    ('Lecture Hall',    FALSE),
    ('Storage',         TRUE),
    ('Security Office', TRUE),
    ('Staff Offices',   TRUE)
ON CONFLICT (name) DO UPDATE SET is_restricted = EXCLUDED.is_restricted;

-- Connections between rooms
INSERT INTO adjacent_rooms (room_a, room_b)
SELECT LEAST(a.room_id, b.room_id), GREATEST(a.room_id, b.room_id)
FROM (VALUES
    ('Outside',         'Lobby'),
    ('Outside',         'Staff Offices'),
    ('Outside',         'Lecture Hall'),
    ('Storage',         'Modern Art'),
    ('Storage',         'Portrait Hall'),
    ('Modern Art',      'Portrait Hall'),
    ('Modern Art',      'Main Hall'),
    ('Portrait Hall',   'Exhibit Hall'),
    ('Portrait Hall',   'Main Hall'),
    ('Exhibit Hall',    'Sculptures'),
    ('Exhibit Hall',    'Local Art'),
    ('Exhibit Hall',    'Main Hall'),
    ('Sculptures',      'Local Art'),
    ('Sculptures',      'Lecture Hall'),
    ('Local Art',       'Main Hall'),
    ('Lecture Hall',    'Main Hall'),
    ('Main Hall',       'Security Office'),
    ('Main Hall',       'Lobby'),
    ('Main Hall',       'Staff Offices'),
    ('Security Office', 'Lobby'),
    ('Lobby',           'Staff Offices')
) AS pair (room_1, room_2)
JOIN gallery_rooms a ON a.name = pair.room_1
JOIN gallery_rooms b ON b.name = pair.room_2
ON CONFLICT (room_a, room_b) DO NOTHING;