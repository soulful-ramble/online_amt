import io


def test_sum():
    assert 1 + 1 == 2


# @pytest.mark.asyncio
# async def test_async_read():
#     async with async_open('../twinkle_twinkle.wav') as f:
#         b = await f.read(1024)
#         print('b:', b)
#         assert len(b) == 1024

def test_io():
    f = io.BytesIO(b"some initial binary data: \x00\x01")
    x = f.read(2)
    assert x == b"so"
    x = f.read(2)
    assert x == b"me"
