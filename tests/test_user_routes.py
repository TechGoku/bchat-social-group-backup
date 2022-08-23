import pytest
from bsgs import db, utils
import werkzeug.exceptions as wexc
from request import bsgs_get, bsgs_post
from util import pad64
import time


def test_global_mods(client, room, room2, user, user2, mod, admin, global_admin, global_mod):

    assert not room2.check_moderator(user)
    assert not room2.check_moderator(user2)

    url_u1_mod = f'/user/{user.session_id}/moderator'
    url_u2_mod = f'/user/{user2.session_id}/moderator'

    # No one except global_admin should be able to add a global moderator:
    for u in (user, user2, mod, admin, global_mod):
        r = bsgs_post(client, url_u2_mod, {'global': True, 'moderator': True}, u)
        assert r.status_code == 403

    r = bsgs_post(client, url_u2_mod, {'global': True, 'moderator': True}, global_admin)
    assert r.status_code == 200

    user2._refresh()
    assert user2.global_moderator
    assert not user2.global_admin
    room2._refresh(perms=True)
    assert room2.check_moderator(user2)
    assert not room2.check_admin(user2)

    r = bsgs_post(client, url_u2_mod, {'global': True, 'moderator': True}, user2)
    assert r.status_code == 403

    r = bsgs_post(client, url_u2_mod, {'global': True, 'moderator': False}, global_admin)
    assert r.status_code == 200
    user2._refresh()
    room2._refresh(perms=True)
    assert not user2.global_moderator
    assert not user2.global_admin
    assert not room2.check_moderator(user2)

    r = bsgs_post(client, url_u2_mod, {'global': True, 'admin': True}, global_admin)
    assert r.status_code == 200
    user2._refresh()
    room2._refresh(perms=True)
    assert user2.global_moderator
    assert user2.global_admin
    assert room2.check_moderator(user2)
    assert room2.check_admin(user2)

    r = bsgs_post(client, url_u1_mod, {'global': True, 'admin': True}, user2)
    assert r.status_code == 200
    user._refresh()
    assert user.global_admin and user.global_moderator

    # Removing moderator also implicitly removes admin:
    r = bsgs_post(client, url_u1_mod, {'global': True, 'moderator': False}, user2)
    assert r.status_code == 200
    user._refresh()
    assert not user.global_admin and not user.global_moderator

    bsgs_post(client, url_u2_mod, {'global': True, 'moderator': False}, global_admin)

    # Test other admin/moderator parameter interactions
    r = bsgs_post(
        client, url_u2_mod, {'global': True, 'admin': True, 'moderator': True}, global_admin
    )
    assert r.status_code == 200
    user2._refresh()
    assert user2.global_admin and user2.global_moderator

    bsgs_post(
        client, url_u2_mod, {'global': True, 'admin': False, 'moderator': False}, global_admin
    )
    assert r.status_code == 200
    user2._refresh()
    assert not user2.global_admin and not user2.global_moderator

    # admin=false, moderator=true should remove admin (if present) and add moderator (if not)
    # First make u2 an admin:
    bsgs_post(client, url_u2_mod, {'global': True, 'admin': True}, global_admin)
    bsgs_post(client, url_u2_mod, {'global': True, 'admin': False, 'moderator': True}, global_admin)
    bsgs_post(client, url_u1_mod, {'global': True, 'admin': False, 'moderator': True}, global_admin)

    user._refresh()
    user2._refresh()
    assert user.global_moderator
    assert not user.global_admin
    assert user2.global_moderator
    assert not user2.global_admin

    # admin=false, moderator omitted: removes admin (if present), maintaining moderator if present,
    # but doesn't make non-mods/admins into mods.
    bsgs_post(client, url_u1_mod, {'global': True, 'moderator': False}, global_admin)
    bsgs_post(client, url_u2_mod, {'global': True, 'admin': True}, global_admin)

    # Preconditions:
    user._refresh()
    user2._refresh()
    assert not user.global_moderator
    assert not user.global_admin
    assert user2.global_moderator
    assert user2.global_admin

    bsgs_post(client, url_u1_mod, {'global': True, 'admin': False}, global_admin)
    bsgs_post(client, url_u2_mod, {'global': True, 'admin': False}, global_admin)

    user._refresh()
    user2._refresh()
    assert not user.global_moderator
    assert not user.global_admin
    assert user2.global_moderator
    assert not user2.global_admin

    # admin omitted, moderator=True: adds moderator permission if not present, doesn't affect admin
    bsgs_post(client, url_u1_mod, {'global': True, 'moderator': False}, global_admin)
    bsgs_post(client, url_u2_mod, {'global': True, 'admin': True}, global_admin)

    # Preconditions:
    user._refresh()
    user2._refresh()
    assert not user.global_moderator
    assert not user.global_admin
    assert user2.global_moderator
    assert user2.global_admin

    bsgs_post(client, url_u1_mod, {'global': True, 'moderator': True}, global_admin)
    bsgs_post(client, url_u2_mod, {'global': True, 'moderator': True}, global_admin)

    user._refresh()
    user2._refresh()
    assert user.global_moderator
    assert not user.global_admin
    assert user2.global_moderator
    assert user2.global_admin

    # moderator=false, admin=true: Impossible and is an error
    r = bsgs_post(
        client, url_u2_mod, {'global': True, 'moderator': False, 'admin': True}, global_admin
    )
    assert r.status_code == 400


def test_room_mods(client, room, room2, user, user2, mod, admin, global_admin, global_mod):

    assert not room.check_moderator(user)
    assert not room.check_moderator(user2)
    assert not room2.check_moderator(user)
    assert not room2.check_moderator(user2)

    def refresh():
        user._refresh()
        user2._refresh()
        room._refresh(perms=True)
        room2._refresh(perms=True)

    url_u2_mod = f'/user/{user2.session_id}/moderator'
    url_u1_mod = f'/user/{user.session_id}/moderator'

    # No one except admins should be able to add a room moderator:
    for u in (user, user2, mod, global_mod):
        r = bsgs_post(client, url_u2_mod, {'rooms': ['*'], 'moderator': True}, u)
        assert r.status_code == 403

    r = bsgs_post(client, url_u2_mod, {'rooms': ['test-room'], 'moderator': True}, global_admin)
    assert r.status_code == 200
    r = bsgs_post(client, url_u1_mod, {'rooms': ['*'], 'moderator': True}, admin)
    assert r.status_code == 200

    refresh()
    assert not user.global_moderator
    assert not user.global_admin
    assert not user2.global_moderator
    assert not user2.global_admin
    assert room.check_moderator(user2)
    assert room.check_moderator(user)
    assert not room.check_admin(user2)
    assert not room.check_admin(user)
    assert not room2.check_moderator(user)
    assert not room2.check_moderator(user2)

    r = bsgs_post(client, url_u2_mod, {'rooms': ['*'], 'moderator': True}, user2)
    assert r.status_code == 403

    r = bsgs_post(client, url_u1_mod, {'rooms': ['*'], 'moderator': False}, global_admin)
    r = bsgs_post(client, url_u2_mod, {'rooms': ['*'], 'moderator': False}, global_admin)
    assert r.status_code == 200
    refresh()
    assert not user.global_moderator
    assert not user2.global_moderator
    assert not room.check_moderator(user)
    assert not room.check_moderator(user2)
    assert not room2.check_moderator(user)
    assert not room2.check_moderator(user2)

    # Make user2 a moderator of both rooms
    r = bsgs_post(client, url_u2_mod, {'rooms': ['*'], 'moderator': True}, global_admin)
    assert r.status_code == 200
    refresh()
    assert not user.global_moderator
    assert not user2.global_moderator
    assert not room.check_moderator(user)
    assert room.check_moderator(user2)
    assert not room2.check_moderator(user)
    assert room2.check_moderator(user2)
    assert not room.check_admin(user)
    assert not room.check_admin(user2)
    assert not room2.check_admin(user)
    assert not room2.check_admin(user2)

    # Make user a admin of room2
    r = bsgs_post(client, url_u1_mod, {'rooms': ['room2'], 'admin': True}, global_admin)
    assert r.status_code == 200
    refresh()
    assert not user.global_moderator
    assert not user2.global_moderator
    assert not room.check_moderator(user)
    assert room.check_moderator(user2)
    assert room2.check_moderator(user)
    assert room2.check_moderator(user2)
    assert not room.check_admin(user)
    assert not room.check_admin(user2)
    assert room2.check_admin(user)
    assert not room2.check_admin(user2)

    # user can promote user2 to admin but only in room2
    r = bsgs_post(client, url_u2_mod, {'rooms': ['*'], 'admin': True}, user)
    assert r.status_code == 200
    refresh()
    assert not user.global_moderator
    assert not user2.global_moderator
    assert not room.check_moderator(user)
    assert room.check_moderator(user2)
    assert room2.check_moderator(user)
    assert room2.check_moderator(user2)
    assert not room.check_admin(user)
    assert not room.check_admin(user2)
    assert room2.check_admin(user)
    assert room2.check_admin(user2)

    # Make sure that we check *all* the given rooms for admin status:
    r = bsgs_post(client, url_u2_mod, {'rooms': ['room2', 'test-room'], 'moderator': True}, user)
    assert r.status_code == 403
    r = bsgs_post(client, url_u2_mod, {'rooms': ['test-room', 'room2'], 'moderator': True}, user)
    assert r.status_code == 403

    # Removing moderator also implicitly removes admin:
    r = bsgs_post(client, url_u1_mod, {'rooms': ['room2'], 'moderator': False}, user2)
    assert r.status_code == 200
    refresh()
    assert not user.global_moderator
    assert not user2.global_moderator
    assert not room.check_moderator(user)
    assert room.check_moderator(user2)
    assert not room2.check_moderator(user)
    assert room2.check_moderator(user2)
    assert not room.check_admin(user)
    assert not room.check_admin(user2)
    assert not room2.check_admin(user)
    assert room2.check_admin(user2)

    def clear():
        bsgs_post(client, url_u1_mod, {'rooms': ['*'], 'moderator': False}, global_admin)
        bsgs_post(client, url_u2_mod, {'rooms': ['*'], 'moderator': False}, global_admin)
        refresh()
        assert not any(r.check_moderator(u) for u in (user, user2) for r in (room, room2))

    # Multi-room addition:
    clear()
    bsgs_post(client, url_u1_mod, {'rooms': ['*'], 'admin': True}, global_admin)
    bsgs_post(client, url_u2_mod, {'rooms': ['*'], 'moderator': True}, user)
    assert r.status_code == 200
    refresh()
    assert not user.global_moderator
    assert not user2.global_moderator
    assert room.check_moderator(user)
    assert room.check_moderator(user2)
    assert room2.check_moderator(user)
    assert room2.check_moderator(user2)
    assert room.check_admin(user)
    assert not room.check_admin(user2)
    assert room2.check_admin(user)
    assert not room2.check_admin(user2)

    # Test other admin/moderator parameter interactions
    r = bsgs_post(
        client, url_u2_mod, {'rooms': ['test-room'], 'admin': True, 'moderator': True}, admin
    )
    assert r.status_code == 200
    refresh()
    assert room.check_moderator(user2)
    assert room.check_admin(user2)

    bsgs_post(
        client, url_u2_mod, {'rooms': ['test-room'], 'admin': False, 'moderator': False}, admin
    )
    assert r.status_code == 200
    refresh()
    assert not room.check_moderator(user2)

    # admin=false, moderator=true should remove admin (if present) and add moderator (if not)
    # First make u2 an admin:
    clear()
    bsgs_post(client, url_u2_mod, {'rooms': ['test-room'], 'admin': True}, admin)
    bsgs_post(
        client, url_u2_mod, {'rooms': ['test-room'], 'admin': False, 'moderator': True}, admin
    )
    bsgs_post(
        client, url_u1_mod, {'rooms': ['test-room'], 'admin': False, 'moderator': True}, admin
    )

    refresh()
    assert not room.check_admin(user)
    assert not room.check_admin(user2)
    assert room.check_moderator(user)
    assert room.check_moderator(user2)

    # admin=false, moderator omitted: removes admin (if present), maintaining moderator if present,
    # but doesn't make non-mods/admins into mods.
    bsgs_post(client, url_u1_mod, {'rooms': ['test-room'], 'moderator': False}, admin)
    bsgs_post(client, url_u2_mod, {'rooms': ['test-room'], 'admin': True}, admin)

    # Preconditions:
    refresh()
    assert not room.check_moderator(user)
    assert room.check_admin(user2)

    bsgs_post(client, url_u1_mod, {'rooms': ['test-room'], 'admin': False}, admin)
    bsgs_post(client, url_u2_mod, {'rooms': ['test-room'], 'admin': False}, admin)

    refresh()
    assert not room.check_moderator(user)
    assert room.check_moderator(user2)
    assert not room.check_admin(user2)

    # admin omitted, moderator=True: adds moderator permission if not present, doesn't affect admin
    bsgs_post(client, url_u1_mod, {'rooms': ['test-room'], 'moderator': False}, admin)
    bsgs_post(client, url_u2_mod, {'rooms': ['test-room'], 'admin': True}, admin)

    # Preconditions:
    refresh()
    assert not room.check_moderator(user)
    assert room.check_admin(user2)

    bsgs_post(client, url_u1_mod, {'rooms': ['test-room'], 'moderator': True}, admin)
    bsgs_post(client, url_u2_mod, {'rooms': ['test-room'], 'moderator': True}, admin)

    refresh()
    assert room.check_moderator(user)
    assert not room.check_admin(user)
    assert room.check_moderator(user2)
    assert room.check_admin(user2)

    # moderator=false, admin=true: Impossible and is an error
    r = bsgs_post(
        client, url_u2_mod, {'rooms': ['test-room'], 'moderator': False, 'admin': True}, admin
    )
    assert r.status_code == 400


def test_mod_visibility(client, room, user, user2, mod, admin, global_admin):
    s_mod, s_admin, s_gadmin, s_user = (
        mod.session_id,
        admin.session_id,
        global_admin.session_id,
        user.session_id,
    )

    def room_mods(u=user2):
        r = bsgs_get(client, '/room/test-room', u)
        assert r.status_code == 200
        return tuple(
            r.json.get(x, [])
            for x in ('moderators', 'admins', 'hidden_moderators', 'hidden_admins')
        )

    url_u1_mod = f'/user/{user.session_id}/moderator'
    r = bsgs_post(client, url_u1_mod, {'global': True, 'moderator': True}, global_admin)
    assert r.status_code == 200
    user._refresh()
    assert user.global_moderator
    assert not user.global_admin
    assert not user.visible_mod
    assert room_mods() == ([s_mod], [s_admin], [], [])
    assert room_mods(mod) == ([s_mod], [s_admin], [s_user], [s_gadmin])

    r = bsgs_post(
        client, url_u1_mod, {'global': True, 'moderator': True, 'visible': True}, global_admin
    )
    assert r.status_code == 200
    user._refresh()
    assert user.global_moderator
    assert not user.global_admin
    assert user.visible_mod
    assert room_mods() == (sorted([s_mod, s_user]), [s_admin], [], [])
    assert room_mods(mod) == (sorted([s_mod, s_user]), [s_admin], [], [s_gadmin])

    r = bsgs_post(
        client, url_u1_mod, {'global': True, 'moderator': True, 'visible': False}, global_admin
    )
    assert r.status_code == 200
    user._refresh()
    assert user.global_moderator
    assert not user.global_admin
    assert not user.visible_mod
    assert room_mods() == ([s_mod], [s_admin], [], [])
    assert room_mods(mod) == ([s_mod], [s_admin], [s_user], [s_gadmin])

    bsgs_post(client, url_u1_mod, {'global': True, 'moderator': False}, global_admin)
    bsgs_post(client, url_u1_mod, {'global': True, 'admin': True, 'visible': True}, global_admin)
    room._refresh(perms=True)
    user._refresh()
    assert room.check_moderator(user)
    assert room.check_admin(user)
    assert user.visible_mod
    assert room_mods() == ([s_mod], sorted([s_admin, s_user]), [], [])
    assert room_mods(mod) == ([s_mod], sorted([s_admin, s_user]), [], [s_gadmin])

    bsgs_post(client, url_u1_mod, {'global': True, 'admin': True}, global_admin)
    user._refresh()
    assert user.global_moderator
    assert user.global_admin
    assert not user.visible_mod
    assert room_mods() == ([s_mod], [s_admin], [], [])
    assert room_mods(mod) == ([s_mod], [s_admin], [], sorted([s_gadmin, s_user]))

    bsgs_post(client, url_u1_mod, {'global': True, 'moderator': False}, global_admin)

    r = bsgs_post(client, url_u1_mod, {'rooms': ['test-room'], 'moderator': True}, global_admin)
    assert r.status_code == 200
    assert room_mods() == (sorted([s_mod, s_user]), [s_admin], [], [])
    assert room_mods(mod) == (sorted([s_mod, s_user]), [s_admin], [], [s_gadmin])

    r = bsgs_post(
        client,
        url_u1_mod,
        {'rooms': ['test-room'], 'moderator': True, 'visible': True},
        global_admin,
    )
    assert r.status_code == 200
    assert room_mods() == (sorted([s_mod, s_user]), [s_admin], [], [])
    assert room_mods(mod) == (sorted([s_mod, s_user]), [s_admin], [], [s_gadmin])

    r = bsgs_post(
        client,
        url_u1_mod,
        {'rooms': ['test-room'], 'moderator': True, 'visible': False},
        global_admin,
    )
    assert r.status_code == 200
    assert room_mods() == ([s_mod], [s_admin], [], [])
    assert room_mods(mod) == ([s_mod], [s_admin], [s_user], [s_gadmin])

    bsgs_post(client, url_u1_mod, {'rooms': ['test-room'], 'moderator': False}, global_admin)
    bsgs_post(
        client, url_u1_mod, {'rooms': ['test-room'], 'admin': True, 'visible': True}, global_admin
    )
    assert room_mods() == ([s_mod], sorted([s_admin, s_user]), [], [])
    assert room_mods(mod) == ([s_mod], sorted([s_admin, s_user]), [], [s_gadmin])

    bsgs_post(
        client, url_u1_mod, {'rooms': ['test-room'], 'admin': True, 'visible': False}, global_admin
    )
    assert room_mods() == ([s_mod], [s_admin], [], [])
    assert room_mods(mod) == ([s_mod], [s_admin], [], sorted([s_user, s_gadmin]))

    bsgs_post(client, url_u1_mod, {'rooms': ['test-room'], 'admin': True}, global_admin)
    assert room_mods() == ([s_mod], sorted([s_admin, s_user]), [], [])
    assert room_mods(mod) == ([s_mod], sorted([s_admin, s_user]), [], [s_gadmin])


def test_bans(client, room, room2, user, user2, mod, global_mod):
    url_ban = f'/user/{user.session_id}/ban'
    url_unban = f'/user/{user.session_id}/unban'
    post = {"data": utils.encode_base64(b"post"), "signature": utils.encode_base64(pad64("sig"))}

    r = bsgs_post(client, "/room/test-room/message", post, user)
    assert r.status_code == 201

    r = bsgs_post(client, url_ban, {'rooms': ['test-room']}, mod)
    assert r.status_code == 200

    with pytest.raises(wexc.Forbidden):
        bsgs_post(client, "/room/test-room/message", post, user)

    r = bsgs_post(client, "/room/test-room/message", post, user2)
    assert r.status_code == 201
    r = bsgs_post(client, "/room/room2/message", post, user)
    assert r.status_code == 201

    r = bsgs_post(client, url_unban, {'rooms': ['test-room']}, mod)
    assert r.status_code == 200

    r = bsgs_post(client, "/room/test-room/message", post, user)
    assert r.status_code == 201

    r = bsgs_post(client, url_ban, {'rooms': ['*']}, global_mod)
    assert r.status_code == 200

    with pytest.raises(wexc.Forbidden):
        bsgs_post(client, "/room/test-room/message", post, user)

    with pytest.raises(wexc.Forbidden):
        bsgs_post(client, "/room/room2/message", post, user)

    r = bsgs_post(client, "/room/test-room/message", post, user2)
    assert r.status_code == 201

    r = bsgs_post(client, url_unban, {'rooms': ['*']}, mod)

    r = bsgs_post(client, "/room/test-room/message", post, user)
    assert r.status_code == 201
    with pytest.raises(wexc.Forbidden):
        r = bsgs_post(client, "/room/room2/message", post, user)

    r = bsgs_post(client, url_unban, {'rooms': ['*']}, global_mod)

    r = bsgs_post(client, "/room/test-room/message", post, user)
    assert r.status_code == 201
    r = bsgs_post(client, "/room/room2/message", post, user)
    assert r.status_code == 201

    r = bsgs_post(client, url_ban, {'global': True}, mod)
    assert r.status_code == 403
    r = bsgs_post(client, url_ban, {'global': True}, global_mod)
    assert r.status_code == 200

    # With a global ban we shouldn't be able to access
    r = bsgs_post(client, "/room/test-room/message", post, user)
    assert r.status_code == 403
    r = bsgs_post(client, "/room/room2/message", post, user)
    assert r.status_code == 403
    r = bsgs_get(client, "/rooms", user)
    assert r.status_code == 403

    r = bsgs_post(client, "/room/test-room/message", post, user2)
    assert r.status_code == 201

    r = bsgs_post(client, url_unban, {'global': True}, mod)
    assert r.status_code == 403
    r = bsgs_post(client, url_unban, {'global': True}, global_mod)
    assert r.status_code == 200
    r = bsgs_post(client, "/room/test-room/message", post, user)
    assert r.status_code == 201
    r = bsgs_post(client, "/room/room2/message", post, user)
    assert r.status_code == 201

    # Test bad arguments properly err:
    assert [
        bsgs_post(client, url_ban, data, global_mod).status_code
        for data in (
            {'global': True, 'rooms': ['abc']},
            {},
            {'rooms': []},
            {'global': False, 'rooms': []},
            {'global': False, 'rooms': None},
            {'rooms': ['test-room', '*']},
            {'rooms': ['*', 'test-room']},
        )
    ] == [400] * 7


def test_ban_timeouts(client, room, room2, user, mod, global_mod):
    url_ban = f'/user/{user.session_id}/ban'
    url_unban = f'/user/{user.session_id}/unban'
    post = {"data": utils.encode_base64(b"post"), "signature": utils.encode_base64(pad64("sig"))}

    r = bsgs_post(client, url_ban, {'rooms': ['*'], 'timeout': 0.001}, global_mod)
    assert r.status_code == 200

    with pytest.raises(wexc.Forbidden):
        bsgs_post(client, "/room/test-room/message", post, user)

    with pytest.raises(wexc.Forbidden):
        bsgs_post(client, "/room/room2/message", post, user)

    from bsgs.cleanup import cleanup

    time.sleep(0.002)
    assert cleanup() == (0, 0, 0, 2, 0)

    r = bsgs_post(client, "/room/test-room/message", post, user)
    assert r.status_code == 201
    r = bsgs_post(client, "/room/room2/message", post, user)
    assert r.status_code == 201

    r = bsgs_post(client, url_ban, {'rooms': ['*'], 'timeout': 30}, mod)
    assert r.status_code == 200

    with pytest.raises(wexc.Forbidden):
        bsgs_post(client, "/room/test-room/message", post, user)

    r = bsgs_post(client, "/room/room2/message", post, user)
    assert r.status_code == 201

    # The timed ban shouldn't expire yet:
    assert cleanup() == (0, 0, 0, 0, 0)

    with pytest.raises(wexc.Forbidden):
        bsgs_post(client, "/room/test-room/message", post, user)
    r = bsgs_post(client, "/room/room2/message", post, user)
    assert r.status_code == 201

    # Handle overlapping timeouts.

    # If we add a ban with a timeout then ban with a different timeout, the second one should
    # replace the first one.

    # Replace the currently active 30s ban with one that expires sooner
    r = bsgs_post(client, url_ban, {'rooms': ['*'], 'timeout': 0.001}, mod)
    assert r.status_code == 200

    with pytest.raises(wexc.Forbidden):
        bsgs_post(client, "/room/test-room/message", post, user)

    time.sleep(0.002)
    assert cleanup() == (0, 0, 0, 1, 0)

    r = bsgs_post(client, "/room/test-room/message", post, user)
    assert r.status_code == 201

    # Make sure we can replace a short one with a longer one
    r = bsgs_post(client, url_ban, {'rooms': ['*'], 'timeout': 0.001}, mod)
    assert r.status_code == 200
    r = bsgs_post(client, url_ban, {'rooms': ['*'], 'timeout': 30}, mod)
    assert r.status_code == 200

    time.sleep(0.002)
    assert cleanup() == (0, 0, 0, 0, 0)

    bsgs_post(client, url_ban, {'rooms': ['*'], 'timeout': 0.001}, mod)
    time.sleep(0.002)
    assert cleanup() == (0, 0, 0, 1, 0)

    r = bsgs_post(client, "/room/test-room/message", post, user)
    assert r.status_code == 201

    # If we add a ban with a timeout *then* we ban again without a timeout, we want to be sure the
    # timeout gets cancelled.

    assert bsgs_post(client, url_ban, {'rooms': ['*'], 'timeout': 0.001}, mod).status_code == 200
    assert bsgs_post(client, url_ban, {'rooms': ['*']}, mod).status_code == 200
    time.sleep(0.005)

    assert cleanup() == (0, 0, 0, 0, 0)

    with pytest.raises(wexc.Forbidden):
        bsgs_post(client, "/room/test-room/message", post, user)

    # Unbanning should remove the ban future
    assert bsgs_post(client, url_unban, {'rooms': ['*']}, mod).status_code == 200

    assert db.query('SELECT COUNT(*) FROM user_ban_futures').first()[0] == 0

    # Global bans can time out too:
    r = bsgs_post(client, url_ban, {'global': True, 'timeout': 0.001}, global_mod)
    assert r.status_code == 200

    r = bsgs_post(client, "/room/test-room/message", post, user)
    assert r.status_code == 403
    r = bsgs_post(client, "/room/room2/message", post, user)
    assert r.status_code == 403
    r = bsgs_get(client, "/rooms", user)
    assert r.status_code == 403

    time.sleep(0.002)
    assert cleanup() == (0, 0, 0, 1, 0)

    r = bsgs_post(client, "/room/test-room/message", post, user)
    assert r.status_code == 201
    r = bsgs_post(client, "/room/room2/message", post, user)
    assert r.status_code == 201

    # Re-banning with longer timeout:
    r = bsgs_post(client, url_ban, {'global': True, 'timeout': 0.001}, global_mod)
    assert r.status_code == 200
    r = bsgs_post(client, url_ban, {'global': True, 'timeout': 30}, global_mod)
    assert r.status_code == 200

    time.sleep(0.002)
    assert cleanup() == (0, 0, 0, 0, 0)

    r = bsgs_post(client, "/room/test-room/message", post, user)
    assert r.status_code == 403

    # global ban with a shorter timeout:
    r = bsgs_post(client, url_ban, {'global': True, 'timeout': 0.001}, global_mod)

    r = bsgs_post(client, "/room/test-room/message", post, user)
    assert r.status_code == 403

    time.sleep(0.002)
    assert cleanup() == (0, 0, 0, 1, 0)

    r = bsgs_post(client, "/room/test-room/message", post, user)
    assert r.status_code == 201
