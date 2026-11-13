"""Audio decoding for engines that require mono 16 kHz PCM."""

def decode_mono(path: str):
    import av
    import numpy as np

    parts = []
    resample = av.AudioResampler(format="flt", layout="mono", rate=16000)
    with av.open(path) as source:
        for frame in source.decode(audio=0):
            parts.extend(out.to_ndarray().reshape(-1) for out in resample.resample(frame))
    parts.extend(out.to_ndarray().reshape(-1) for out in resample.resample(None))
    if not parts:
        raise ValueError("Audio contains no samples")
    return np.ascontiguousarray(np.concatenate(parts), dtype=np.float32)
