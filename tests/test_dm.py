from request import bsgs_get, bsgs_post
from bsgs import config
from bsgs.hashing import blake2b
from bsgs.utils import encode_base64
from bsgs.model.user import SystemUser
import nacl.bindings as sodium
from nacl.utils import random
from util import from_now


def test_dm_default_empty(client, blind_user):
    r = bsgs_get(client, '/inbox', blind_user)
    assert r.status_code == 200
    assert r.json == []


def test_dm_banned_user(client, banned_user):
    r = bsgs_get(client, '/inbox', banned_user)
    assert r.status_code == 403


def make_post(message, sender, to):
    assert sender.is_blinded
    assert to.is_blinded
    a = sender.ed_key.to_curve25519_private_key().encode()
    kA = bytes.fromhex(sender.session_id[2:])
    kB = bytes.fromhex(to.session_id[2:])
    key = blake2b(sodium.crypto_scalarmult_ed25519_noclamp(a, kB) + kA + kB, digest_size=32)

    # MESSAGE || UNBLINDED_ED_PUBKEY
    plaintext = message + sender.ed_key.verify_key.encode()
    nonce = random(24)
    ciphertext = sodium.crypto_aead_xchacha20poly1305_ietf_encrypt(
        plaintext, aad=None, nonce=nonce, key=key
    )
    data = b'\x00' + ciphertext + nonce
    return {'message': encode_base64(data)}


def test_dm_send_from_banned_user(client, blind_user, blind_user2):
    blind_user2.ban(banned_by=SystemUser())
    r = bsgs_post(
        client,
        f'/inbox/{blind_user.session_id}',
        make_post(b'beep', sender=blind_user2, to=blind_user),
        blind_user2,
    )
    assert r.status_code == 403


def test_dm_send_to_banned_user(client, blind_user, blind_user2):
    blind_user2.ban(banned_by=SystemUser())
    r = bsgs_post(
        client,
        f'/inbox/{blind_user2.session_id}',
        make_post(b'beep', sender=blind_user, to=blind_user2),
        blind_user,
    )
    assert r.status_code == 404


def test_dm_send(client, blind_user, blind_user2):
    post = make_post(b'bep', sender=blind_user, to=blind_user2)
    msg_expected = {
        'id': 1,
        'message': post['message'],
        'sender': blind_user.session_id,
        'recipient': blind_user2.session_id,
    }

    r = bsgs_post(client, f'/inbox/{blind_user2.session_id}', post, blind_user)
    assert r.status_code == 201
    data = r.json
    assert data.pop('posted_at') == from_now.seconds(0)
    assert data.pop('expires_at') == from_now.seconds(config.DM_EXPIRY)
    assert data == {k: v for k, v in msg_expected.items() if k != 'message'}

    r = bsgs_get(client, '/inbox', blind_user2)
    assert r.status_code == 200
    assert len(r.json) == 1
    data = r.json[0]
    assert data.pop('posted_at') == from_now.seconds(0)
    assert data.pop('expires_at') == from_now.seconds(config.DM_EXPIRY)
    assert data == msg_expected

    r = bsgs_get(client, '/outbox', blind_user)
    assert len(r.json) == 1
    data = r.json[0]
    assert data.pop('posted_at') == from_now.seconds(0)
    assert data.pop('expires_at') == from_now.seconds(config.DM_EXPIRY)
    assert data == msg_expected
