from data.database import db


# ==================== MOVIES ====================

async def add_movie(
    code: str,
    file_id: str,
    file_type: str,
    added_by: int,
    archive_caption: str | None = None,
    user_caption: str | None = None,
):
    """Oddiy kino qo'shish (episode_number = NULL)."""
    query = """
    INSERT INTO movies (code, episode_number, archive_caption, user_caption, file_id, file_type, added_by)
    VALUES ($1, NULL, $2, $3, $4, $5, $6)
    ON CONFLICT (code, episode_number) DO NOTHING
    RETURNING id;
    """
    return await db.execute(
        query, code, archive_caption, user_caption,
        file_id, file_type, added_by, fetchval=True
    )


async def add_episode(
    code: str,
    episode_number: int,
    file_id: str,
    file_type: str,
    added_by: int,
    archive_caption: str | None = None,
    user_caption: str | None = None,
):
    """Serial qismini qo'shish."""
    query = """
    INSERT INTO movies (code, episode_number, archive_caption, user_caption, file_id, file_type, added_by)
    VALUES ($1, $2, $3, $4, $5, $6, $7)
    ON CONFLICT (code, episode_number) DO NOTHING
    RETURNING id;
    """
    return await db.execute(
        query, code, episode_number, archive_caption, user_caption,
        file_id, file_type, added_by, fetchval=True
    )


async def get_movie(code: str):
    """
    Kod bo'yicha kino/serial qidiradi.
    Natija episode_number bo'yicha tartiblangan (NULL birinchi).
    """
    query = """
    SELECT * FROM movies
    WHERE code = $1
    ORDER BY episode_number ASC NULLS FIRST;
    """
    return await db.execute(query, code, fetch=True)


async def code_exists(code: str) -> bool:
    query = "SELECT EXISTS(SELECT 1 FROM movies WHERE code = $1);"
    return await db.execute(query, code, fetchval=True)


async def delete_movie(code: str):
    """Kino va uning barcha qismlarini o'chiradi."""
    query = "DELETE FROM movies WHERE code = $1;"
    await db.execute(query, code)


async def get_movies_count() -> int:
    """Unikal kinolar sonini qaytaradi."""
    query = "SELECT COUNT(DISTINCT code) FROM movies;"
    return await db.execute(query, fetchval=True)


# ==================== USERS ====================

async def add_user(user_id: int, username: str | None, full_name: str | None):
    query = """
    INSERT INTO users (user_id, username, full_name)
    VALUES ($1, $2, $3)
    ON CONFLICT (user_id) DO NOTHING;
    """
    await db.execute(query, user_id, username, full_name)


async def check_user_exists(user_id: int) -> bool:
    query = "SELECT EXISTS(SELECT 1 FROM users WHERE user_id = $1);"
    return await db.execute(query, user_id, fetchval=True)


async def get_all_users():
    query = "SELECT user_id FROM users;"
    return await db.execute(query, fetch=True)


async def get_users_count() -> int:
    query = "SELECT COUNT(*) FROM users;"
    return await db.execute(query, fetchval=True)


# ==================== REQUIRED CHANNELS ====================

async def add_required_channel(channel_id: int, username: str | None, name: str):
    query = """
    INSERT INTO required_channels (channel_id, channel_username, channel_name)
    VALUES ($1, $2, $3)
    ON CONFLICT (channel_id) DO NOTHING;
    """
    await db.execute(query, channel_id, username, name)


async def get_required_channels():
    query = "SELECT * FROM required_channels;"
    return await db.execute(query, fetch=True)


async def delete_required_channel(channel_id: int):
    query = "DELETE FROM required_channels WHERE channel_id = $1;"
    await db.execute(query, channel_id)


# ==================== JOIN REQUESTS ====================

async def add_join_request(user_id: int, channel_id: int):
    query = """
    INSERT INTO join_requests (user_id, channel_id)
    VALUES ($1, $2)
    ON CONFLICT (user_id, channel_id) DO NOTHING;
    """
    await db.execute(query, user_id, channel_id)


async def has_join_request(user_id: int, channel_id: int) -> bool:
    query = """
    SELECT EXISTS(
        SELECT 1 FROM join_requests
        WHERE user_id = $1 AND channel_id = $2
    );
    """
    return await db.execute(query, user_id, channel_id, fetchval=True)