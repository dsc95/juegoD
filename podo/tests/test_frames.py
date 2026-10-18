"""Input frames: serialización canónica, validación, streams."""
import pytest

from combatcore.frames import (InputStream, InputFrame, deserialize_frames,
                               frame_from_tuple, frame_to_tuple,
                               serialize_frames)


def test_roundtrip_serializable():
    frames = [
        InputFrame(frame=0, move_x=1, move_y=-1, basic=True),
        InputFrame(frame=1, switch=99, capture=True),
        InputFrame(frame=2),
    ]
    text = serialize_frames(frames)
    back = deserialize_frames(text)
    assert back == frames
    # byte-estable: misma entrada -> misma cadena
    assert serialize_frames(back) == text


def test_field_order_fixed():
    f = InputFrame(frame=3, move_x=-1, guard=True, switch=2)
    t = frame_to_tuple(f)
    assert t[0] == 3 and t[1] == -1 and t[6] is True and t[9] == 2
    assert frame_from_tuple(t) == f


def test_invalid_move_rejected():
    with pytest.raises(ValueError):
        frame_from_tuple((0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0))


def test_invalid_switch_rejected():
    with pytest.raises(ValueError):
        InputFrame(frame=0, switch=7)


def test_frame_length_checked():
    with pytest.raises(ValueError):
        frame_from_tuple((0, 0))


def test_input_stream_sparse_idle():
    s = InputStream(0, [InputFrame(frame=5, basic=True)])
    assert s.get(5).basic is True
    assert s.get(0) == InputFrame(frame=0)
    assert s.get(99) == InputFrame(frame=99)
    assert len(s) == 6


def test_input_stream_duplicate_rejected():
    with pytest.raises(ValueError):
        InputStream(0, [InputFrame(frame=1), InputFrame(frame=1)])
