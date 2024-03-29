CREATE TABLE IF NOT EXISTS guild_settings(
    guild_id BIGINT PRIMARY KEY,
    prefix TEXT
);


CREATE TABLE IF NOT EXISTS user_settings(
    user_id BIGINT PRIMARY KEY
);


CREATE TABLE IF NOT EXISTS role_list(
    guild_id BIGINT,
    role_id BIGINT,
    key TEXT,
    value TEXT,
    PRIMARY KEY (guild_id, role_id, key)
);


CREATE TABLE IF NOT EXISTS channel_list(
    guild_id BIGINT,
    channel_id BIGINT,
    key TEXT,
    value TEXT,
    PRIMARY KEY (guild_id, channel_id, key)
);

CREATE TABLE IF NOT EXISTS frenzy_activated(
    channel_id BIGINT,
    activated BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (channel_id, activated)
);

CREATE TABLE IF NOT EXISTS name_id_pairs(
    channel_id BIGINT,
    name TEXT,
    id TEXT,
    UNIQUE(channel_id, name),
    UNIQUE(channel_id, id)
);