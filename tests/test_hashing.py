from bsgs.hashing import blake2b


def test_blake2b():
    # Test inputs/outputs from libsodium:
    salt = b'5b6b41ed9b343fe0'
    person = b'5126fb2a37400d2a'
    key = bytes(range(64))
    data = bytes(range(64))

    expected = [
        "ba",
        "6139",
        "3a1666",
        "5797e9d0",
        "834a26efe6",
        "d7e9e862bbce",
        "40d8b84c374750",
        "276789189244cf04",
        "16f73ffe0673cc9992",
        "b3835bfaf6eb71d94078",
        "8c624e844d34f4a59f34cc",
        "e0a394962413ad09975df3cf",
        "47f043c3aacb501f97e0458ae3",
        "b4a11f2fb72a7e6f96fdacf98d49",
        "f434079e9adeb244047cb6855f9854",
        "5fbe885c4b2d4e0d78dc5905622a277a",
        "e262ba3e2ab76efdf83513108e3b987d1b",
        "add93dde78d32e77bc039c34a49043f19d26",
        "093842ac10e2eb1237ddc9ca9e7990cf397772",
        "09e7f6a0e2ea4888f1dbf6562effd1561c65029c",
        "bd33a9ec914f5b81864a49184338e4062d6c6b2b2e",
        "8dc46295235d94f5881d429a5ad47f9db9e35cf8c6b3",
        "ba5df554dca7ac1cba4889fa88adf3070fbf4ab5d187b5",
        "1ff84715e71c66214d271d421395fb6166db97b1d47ed697",
        "75a0d227c70549f5b0c933b7b21f151355bd47e04b6085c91f",
        "a32a5c9439a0fa771dcbe7f338b5dcef62a754edc4952614d6f0",
        "53a87de519cdcc7f64730d58bce6baaf7b44c5c428a4611a208ad4",
        "5e5ad8f0c4f083f9b7a5154d9c0dfd0f3d2fce94cf54fc215450314a",
        "9c76b9e63c77e6564b1e5111c2fb140046e1e5a4f900a7cfc2bac3fcfa",
        "bb919251ca310eb9b994e5d7883bc9fa2144b59b8d5d940677b7130ac777",
        "faa492a66f08ef0c7adb868fcb7b523aedd35b8ff1414bd1d554794f144474",
        "9b273ebe335540b87be899abe169389ed61ed262c3a0a16e4998bbf752f0bee3",
        "1e0070b92429c151b33bdd1bb4430a0e650a3dfc94d404054e93c8568330ecc505",
        "e3b64149f1b76231686d592d1d4af984ce2826ba03c2224a92f95f9526130ce4eb40",
        "5f8e378120b73db9eefa65ddcdcdcb4acd8046c31a5e47f298caa400937d5623f1394b",
        "74c757a4165a1782c933e587353a9fd8f6d7bf26b7f51b52c542747030bfb3d560c2e5c2",
        "2d5ee85cc238b923806dd98db18919d1924f2340ec88917d4ce1799cbfd5f2cb9df99db2e1",
        "c93ff727e6f9822efec0a77eed0025c0eff19127bf8746b7c71c2a098f57cef02febb86a1e6c",
        "adfb6d7ba13779a5dd1bbf268e400f4156f0f5c9d5b670ff539e1d9c1a63373416f3001f338407",
        "3a6900e58a448887d77c5911e4bdde620e64f25b2d71723fa60f7cb3efa7c320b6153bdbc3287949",
        "413eb0fd379b32dd88e82242a87cc58ce3e64c72352387a4c70f92ee5c8d23fa7ecd86f6df170a32d2",
        "92d0d3cacc3e25628caf6f2c4cd50d25d154ac45098f531d690230b859f37cfe089eb169f76bba72a3ff",
        "92f6ccc11a9a3bee520b17e0cddc4550c0e9cf47ddd9a6161284259ffb161c1d0675b505cb1066872768e8",
        "a3cd675804e6be7f120138a9eaadcd56bb7763d1c046e87fe0d358c8276b0d24621f46c60b46e397933b75b4",
        "304a1af53cbdd6486b8419d1ebd5e9528c540d8dc46a10be49067f46a0617229577015d776783f702b2954df43",  # noqa: E501
        "d8a6358970446453ac0c82c758644ab68989b5b4f06f9768807ce0c5f2a0dbac1e8450f4e3a02deecf7b54b6a45d",  # noqa: E501
        "1264b8dee9ac4aa8de69a43ada95cc95f20230f33836d4a1db8c2466ab38361686e5ac282025ccc2e0f6a1cd98a4dd",  # noqa: E501
        "7eed787abaa7f4e8b8aa3090f0676201cfbaaf350899661cdd5216ac0b5cd874443f5c0688ffd7ca1ccbfe1ca7e1a3f5",  # noqa: E501
        "8907f0218585167962a8e8213559a643dd03c2bf1a7a5ad3e3bc5f88c0ff1532ee8cd29880e7e0e68da22a5798aef27cc5",  # noqa: E501
        "12dea17b0733e5060751b1115e10c3d4b2f4583bcd009d9f1f42ec23d4a6a0df1185d3abbdbe86de08569e70583d6de1c1fe",  # noqa: E501
        "8ff75e91f1de547dc3a25472db2f51f5910a290c449603da54207b5e39bd735d240ec913b52df90709b5d29357971d6c341452",  # noqa: E501
        "4a3b16b12400f38e74778efc3a4caa52ec6fdf6b0180a5bfac9189e52e162c10e8911a54ab33e2b389ee1949e58edaa119e2b2b9",  # noqa: E501
        "c9943e7186fdc9bbfa1d7087fa7086babe6fcf95a6196d1772187854071304e2f1fff39e6e6f48f76addb16d5c00249e0523aac91f",  # noqa: E501
        "0297f16fdd34add9cc87b4adf816525b590ba08ac733c43f8d225d194df4f9c83b4dce617be51e25b5f6c80dff249f27c707de20e422",  # noqa: E501
        "576bb891eab9930998e2e73b5d0498e3c5f040f8dec9397a8c7a622c17de01fee7cc936e3bd4de1f7fd8b31dea9e70c65462bbb5dc7b50",  # noqa: E501
        "9416a57ae7c8c51c6e008f940fe06d8ebc02c350c19a2f71583a6d260b085670d73a95248fef0f4cae5292ba7db1189a7cd9c51122ba7913",  # noqa: E501
        "ea644b9051cca5eee8868a553e3f0f4e14739e1555474151156e10578256b288a233870dd43a380765400ea446df7f452c1e03a9e5b6731256",  # noqa: E501
        "f99cc1603de221abc1ecb1a7eb4bbf06e99561d1cc5541d8d601bae2b1dd3cbe448ac276667f26de5e269183a09f7deaf35d33174b3cc8ad4aa2",  # noqa: E501
        "ee2be1ec57fdac23f89402a534177eca0f4b982a4ed2c2e900b6a79e1f47a2d023eff2e647baf4f4c0da3a28d08a44bc780516974074e2523e6651",  # noqa: E501
        "9cda001868949a2bad96c5b3950a8315e6e5214d0b54dcd596280565d351806ef22cf3053f63623da72fcad9afa3896641658632334c9ec4f644c984",  # noqa: E501
        "c6d6722a916651a8671383d8260873347d9c248696b4cb3dac4dea9ba57ed971127cb18e44211d7e14177ace248b3c6e0785356ee261ebdc6ef0faf143",  # noqa: E501
        "5dd258a3e7505bc6b9776b0df25676a1c19e2c8258c7b5f2e361423523d96299eb6827bc7c27e7bca2d2b59d717c2ebcb05e6dcaa32289d96fae9a4077ef",  # noqa: E501
        "19c14de35fe19c92cc0e624280e4136355d4cfa9a0a98b090c4b06f5665021920725852ff1f566b0c8c37157b25fb9f947a2e70b40577a17860a0732c170ac",  # noqa: E501
        "5fcdcc02be7714a0dbc77df498bf999ea9225d564adca1c121c9af03af92cac8177b9b4a86bcc47c79aa32aac58a3fef967b2132e9352d4613fe890beed2571b",  # noqa: E501
    ]

    for i in range(64):
        assert (
            blake2b(data[:i], digest_size=i + 1, key=key[: i + 1], salt=salt, person=person).hex()
            == expected[i]
        )

    assert (
        blake2b(data, digest_size=64, salt=salt, person=person).hex()
        == "1afc8ec818bef0a479d2b4cac81d40a52cafa27f6d80c42fc23cbaf4141882ab59ab1101922fcb6e707ef2f61efd07cce5d09094e6bee420b1b96998c7cee96d"  # noqa: E501
    )

    assert (
        blake2b(data, digest_size=64, key=key, person=person).hex()
        == "5789f474edd5206ededaccfc35e7dd3ed730748125b5395abf802b2601126b19b109a1db67556945bc79bb25e1ab59610599d155070e0e04354f11a6a5d6f3ac"  # noqa: E501
    )

    assert (
        blake2b(data, digest_size=64, key=key, salt=salt).hex()
        == "e78efc663a5547c089f2b3b08973c974c4bfd365eac18b80c68bdb3b1ba4554b54d6b8465a68a3b9aa0bc020621f16efd5b8dd8c7c01ed9ee3ec5544aae465ff"  # noqa: E501
    )

    exp = "fb4e2ad6b7fe6afd2ba06d5c1d79379c5bf10e336a35c89a1aaf408a805171716e0635a5b1d18190131e15b6888510bcb3e3752b050f892a09dbbde60b051495"  # noqa: E501
    assert blake2b(data, digest_size=64, key=key, salt=salt, person=person).hex() == exp
    assert (
        blake2b((data[0:7], data[7:]), digest_size=64, key=key, salt=salt, person=person).hex()
        == exp
    )
    assert (
        blake2b([data[0:7], data[7:]], digest_size=64, key=key, salt=salt, person=person).hex()
        == exp
    )
    assert (
        blake2b(
            [data[i : i + 1] for i in range(len(data))],
            digest_size=64,
            key=key,
            salt=salt,
            person=person,
        ).hex()
        == exp
    )
    assert (
        blake2b(
            [data[8 * i : 8 * i + 8] for i in range(8)],
            digest_size=64,
            key=key,
            salt=salt,
            person=person,
        ).hex()
        == exp
    )
    assert (
        blake2b(
            (data[8 * i : 8 * i + 8] for i in range(8)),
            digest_size=64,
            key=key,
            salt=salt,
            person=person,
        ).hex()
        == exp
    )
