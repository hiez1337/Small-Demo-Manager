import os
import re
import struct
from typing import Callable, Optional

# Add bundled opus.dll to PATH before importing opuslib
_resources_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
_opus_path = os.path.join(_resources_dir, "opus.dll")
if os.path.isfile(_opus_path):
    os.environ["PATH"] = _resources_dir + os.pathsep + os.environ.get("PATH", "")
import opuslib

from demoparser2 import DemoParser
from models import AudioEntry


SAMPLE_RATE = 48000
CHANNELS = 1
SILENCE_THRESHOLD_TICKS = 128
TICK_INTERVAL = 1.0 / 64


def _write_wav(filepath: str, pcm_data: bytes, sample_rate: int = SAMPLE_RATE):
    num_channels = CHANNELS
    bits_per_sample = 16
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    data_size = len(pcm_data)

    with open(filepath, "wb") as f:
        f.write(b"RIFF")
        f.write(struct.pack("<I", 36 + data_size))
        f.write(b"WAVE")
        f.write(b"fmt ")
        f.write(struct.pack("<I", 16))
        f.write(struct.pack("<H", 1))
        f.write(struct.pack("<H", num_channels))
        f.write(struct.pack("<I", sample_rate))
        f.write(struct.pack("<I", byte_rate))
        f.write(struct.pack("<H", block_align))
        f.write(struct.pack("<H", bits_per_sample))
        f.write(b"data")
        f.write(struct.pack("<I", data_size))
        f.write(pcm_data)


def extract_voice(
    demo_path: str,
    output_dir: str,
    progress_callback: Optional[Callable[[float], None]] = None,
) -> dict[str, list[AudioEntry]]:
    os.makedirs(output_dir, exist_ok=True)
    parser = DemoParser(demo_path)

    player_info = parser.parse_player_info()
    steamid_to_name: dict[int, str] = {}
    for _, row in player_info.iterrows():
        sid = int(row.get("steamid", 0))
        if sid > 0:
            steamid_to_name[sid] = str(row.get("name", f"Player_{sid}"))

    voice_data = parser.parse_voice()
    if not voice_data:
        raise ValueError("No voice data found in demo")

    if progress_callback:
        progress_callback(10.0)

    total_packets = len(voice_data)
    processed = 0
    result: dict[str, list[AudioEntry]] = {}
    all_entries: list[AudioEntry] = []

    decoder = opuslib.Decoder(SAMPLE_RATE, CHANNELS)

    player_packets: dict[int, list[tuple[int, bytes]]] = {}
    for voice_item in voice_data:
        sid = voice_item.get("steamid", 0)
        tick = voice_item.get("tick", 0)
        data_bytes = voice_item.get("bytes", b"")
        if sid == 0 or not data_bytes:
            continue

        if sid not in player_packets:
            player_packets[sid] = []
        player_packets[sid].append((tick, data_bytes))

    if not player_packets:
        raise ValueError("No valid voice packets found")

    total_players = len(player_packets)
    player_idx = 0

    for steam_id, packets in player_packets.items():
        player_idx += 1
        packets.sort(key=lambda x: x[0])

        player_name = steamid_to_name.get(steam_id, f"Player_{steam_id}")
        safe_name = re.sub(r'[\\/*?:"<>|]', "_", player_name)
        player_dir = os.path.join(output_dir, safe_name)
        os.makedirs(player_dir, exist_ok=True)

        segments: list[list[tuple[int, bytes]]] = []
        current_segment: list[tuple[int, bytes]] = [packets[0]]

        for i in range(1, len(packets)):
            tick_gap = packets[i][0] - packets[i - 1][0]
            if tick_gap > SILENCE_THRESHOLD_TICKS:
                segments.append(current_segment)
                current_segment = []
            current_segment.append(packets[i])

        if current_segment:
            segments.append(current_segment)

        decoded_count = 0
        round_num = 1
        base_tick = packets[0][0] if packets else 0

        for seg_idx, segment in enumerate(segments):
            all_pcm = bytearray()
            first_tick = segment[0][0]

            for tick, opus_data in segment:
                try:
                    pcm = decoder.decode(opus_data, 960)
                    all_pcm.extend(pcm.tobytes())
                except opuslib.OpusError:
                    continue

            if len(all_pcm) < 160:
                continue

            time_seconds = (first_tick - base_tick) * TICK_INTERVAL
            duration = len(all_pcm) / (SAMPLE_RATE * 2)
            decoded_count += 1

            filename = f"round_{round_num}_t_{int(time_seconds)}s.wav"
            filepath = os.path.join(player_dir, filename)
            _write_wav(filepath, bytes(all_pcm))
            round_num += 1

            all_entries.append(AudioEntry(
                round=seg_idx + 1,
                time=time_seconds,
                duration=round(duration, 2),
                file_path=filepath,
            ))

        result[player_name] = [
            e for e in all_entries if e.file_path.startswith(player_dir)
        ]

        processed += 1
        if progress_callback:
            pct = 10.0 + (player_idx / total_players) * 85.0
            progress_callback(min(pct, 95.0))

    if progress_callback:
        progress_callback(100.0)

    return result
