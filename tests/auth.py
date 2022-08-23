from nacl.signing import SigningKey
from nacl.public import PublicKey
from typing import Optional
import time
from bsgs.hashing import blake2b, sha512
import nacl.bindings as sodium
from nacl.utils import random

import bsgs.utils
import bsgs.crypto


def x_bsgs_nonce():
    return random(16)


def x_bsgs_raw(
    s: SigningKey,
    B: PublicKey,
    method: str,
    full_path: str,
    body: Optional[bytes] = None,
    *,
    b64_nonce: bool = True,
    blinded: bool = False,
    timestamp_off: int = 0,
):
    """
    Calculates X-BSGS-* headers.

    Returns 4 elements: the headers dict, the nonce bytes, timestamp int, and signature bytes.

    Use x_bsgs(...) instead if you don't need the nonce/timestamp/signature values.
    """
    n = x_bsgs_nonce()
    ts = int(time.time()) + timestamp_off

    if blinded:
        a = s.to_curve25519_private_key().encode()
        k = sodium.crypto_core_ed25519_scalar_reduce(
            blake2b(bsgs.crypto.server_pubkey_bytes, digest_size=64)
        )
        ka = sodium.crypto_core_ed25519_scalar_mul(k, a)
        kA = sodium.crypto_scalarmult_ed25519_base_noclamp(ka)
        pubkey = '15' + kA.hex()
    else:
        pubkey = '00' + s.verify_key.encode().hex()

    to_sign = [B.encode(), n, str(ts).encode(), method.encode(), full_path.encode()]
    if body:
        to_sign.append(blake2b(body, digest_size=64))

    if blinded:
        H_rh = sha512(s.encode())[32:]
        r = sodium.crypto_core_ed25519_scalar_reduce(sha512([H_rh, kA, *to_sign]))
        sig_R = sodium.crypto_scalarmult_ed25519_base_noclamp(r)
        HRAM = sodium.crypto_core_ed25519_scalar_reduce(sha512([sig_R, kA, *to_sign]))
        sig_s = sodium.crypto_core_ed25519_scalar_add(
            r, sodium.crypto_core_ed25519_scalar_mul(HRAM, ka)
        )
        sig = sig_R + sig_s

    else:
        sig = s.sign(b''.join(to_sign)).signature

    h = {
        'X-BSGS-Pubkey': pubkey,
        'X-BSGS-Nonce': bsgs.utils.encode_base64(n) if b64_nonce else n.hex(),
        'X-BSGS-Timestamp': str(ts),
        'X-BSGS-Signature': bsgs.utils.encode_base64(sig),
    }

    return h, n, ts, sig


def x_bsgs(*args, **kwargs):
    return x_bsgs_raw(*args, **kwargs)[0]


def x_bsgs_for(user, *args, **kwargs):
    B = bsgs.crypto.server_pubkey
    return x_bsgs(user.ed_key, B, *args, blinded=user.is_blinded, **kwargs)
