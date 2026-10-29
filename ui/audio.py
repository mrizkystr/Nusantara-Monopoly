"""Procedural Audio Engine using pygame.mixer with automatic fallback and WAV generation."""
import os
import math
import wave
import struct
import pygame
from typing import Dict, Optional


class SoundGenerator:
    """Generates 16-bit 44.1kHz mono PCM WAV files procedurally using standard library."""
    SAMPLE_RATE = 44100

    @classmethod
    def generate_all(cls, base_dir: str) -> None:
        sfx_dir = os.path.join(base_dir, "assets", "audio", "sfx")
        music_dir = os.path.join(base_dir, "assets", "audio", "music")
        os.makedirs(sfx_dir, exist_ok=True)
        os.makedirs(music_dir, exist_ok=True)

        sounds = {
            os.path.join(sfx_dir, "click.wav"): cls._make_click,
            os.path.join(sfx_dir, "dice_roll.wav"): cls._make_dice_roll,
            os.path.join(sfx_dir, "dice_land.wav"): cls._make_dice_land,
            os.path.join(sfx_dir, "step.wav"): cls._make_step,
            os.path.join(sfx_dir, "buy.wav"): cls._make_buy,
            os.path.join(sfx_dir, "rent.wav"): cls._make_rent,
            os.path.join(sfx_dir, "card.wav"): cls._make_card,
            os.path.join(sfx_dir, "build_house.wav"): cls._make_build_house,
            os.path.join(sfx_dir, "build_hotel.wav"): cls._make_build_hotel,
            os.path.join(sfx_dir, "jail.wav"): cls._make_jail,
            os.path.join(sfx_dir, "bankruptcy.wav"): cls._make_bankruptcy,
            os.path.join(sfx_dir, "victory.wav"): cls._make_victory,
            os.path.join(music_dir, "ambient_loop.wav"): cls._make_ambient_music
        }

        for path, generator in sounds.items():
            if not os.path.exists(path):
                samples = generator()
                cls._save_wav(path, samples)

    @classmethod
    def _save_wav(cls, path: str, samples: list[float]) -> None:
        with wave.open(path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(cls.SAMPLE_RATE)
            packed = bytearray()
            for s in samples:
                val = max(-32767, min(32767, int(s * 32767)))
                packed.extend(struct.pack("<h", val))
            wf.writeframes(packed)

    @classmethod
    def _make_click(cls) -> list[float]:
        dur = 0.04
        n = int(dur * cls.SAMPLE_RATE)
        return [math.sin(2 * math.pi * 950 * (i / cls.SAMPLE_RATE)) * (1.0 - (i / n)) * 0.4 for i in range(n)]

    @classmethod
    def _make_dice_roll(cls) -> list[float]:
        dur = 0.7
        n = int(dur * cls.SAMPLE_RATE)
        samples = []
        for i in range(n):
            t = i / cls.SAMPLE_RATE
            # Noise-like tumbling rattle with frequency modulation
            noise = math.sin(2 * math.pi * (240 + 80 * math.sin(t * 30)) * t)
            click_burst = math.sin(t * 90) > 0.6
            env = math.sin(math.pi * (i / n))
            samples.append(noise * 0.3 * env if click_burst else 0.05 * env)
        return samples

    @classmethod
    def _make_dice_land(cls) -> list[float]:
        dur = 0.12
        n = int(dur * cls.SAMPLE_RATE)
        return [math.sin(2 * math.pi * 140 * (i / cls.SAMPLE_RATE)) * math.exp(-25 * (i / cls.SAMPLE_RATE)) * 0.6 for i in range(n)]

    @classmethod
    def _make_step(cls) -> list[float]:
        dur = 0.05
        n = int(dur * cls.SAMPLE_RATE)
        return [math.sin(2 * math.pi * 520 * (i / cls.SAMPLE_RATE)) * (1.0 - (i / n)) * 0.3 for i in range(n)]

    @classmethod
    def _make_buy(cls) -> list[float]:
        # Cheerful ascending coin chime
        dur = 0.28
        n = int(dur * cls.SAMPLE_RATE)
        half = n // 2
        samples = []
        for i in range(half):
            samples.append(math.sin(2 * math.pi * 587.33 * (i / cls.SAMPLE_RATE)) * (1.0 - (i / half)) * 0.45)
        for i in range(n - half):
            samples.append(math.sin(2 * math.pi * 880.00 * (i / cls.SAMPLE_RATE)) * (1.0 - (i / (n - half))) * 0.5)
        return samples

    @classmethod
    def _make_rent(cls) -> list[float]:
        # Descending coin payment sound
        dur = 0.25
        n = int(dur * cls.SAMPLE_RATE)
        samples = []
        for i in range(n):
            freq = 600 - (300 * (i / n))
            samples.append(math.sin(2 * math.pi * freq * (i / cls.SAMPLE_RATE)) * (1.0 - (i / n)) * 0.4)
        return samples

    @classmethod
    def _make_card(cls) -> list[float]:
        dur = 0.3
        n = int(dur * cls.SAMPLE_RATE)
        samples = []
        for i in range(n):
            t = i / cls.SAMPLE_RATE
            freq = 400 + 400 * (i / n)
            samples.append(math.sin(2 * math.pi * freq * t) * math.sin(math.pi * (i / n)) * 0.35)
        return samples

    @classmethod
    def _make_build_house(cls) -> list[float]:
        dur = 0.22
        n = int(dur * cls.SAMPLE_RATE)
        samples = []
        for i in range(n):
            t = i / cls.SAMPLE_RATE
            # Construction tap with pleasant tone
            samples.append((math.sin(2 * math.pi * 220 * t) + 0.5 * math.sin(2 * math.pi * 660 * t)) * math.exp(-15 * t) * 0.5)
        return samples

    @classmethod
    def _make_build_hotel(cls) -> list[float]:
        dur = 0.5
        n = int(dur * cls.SAMPLE_RATE)
        samples = []
        chords = [523.25, 659.25, 783.99, 1046.50]  # C Major arpeggio
        seg = n // len(chords)
        for idx, freq in enumerate(chords):
            for i in range(seg):
                t = i / cls.SAMPLE_RATE
                env = (1.0 - (i / seg)) * 0.4
                samples.append(math.sin(2 * math.pi * freq * t) * env)
        return samples

    @classmethod
    def _make_jail(cls) -> list[float]:
        dur = 0.4
        n = int(dur * cls.SAMPLE_RATE)
        samples = []
        for i in range(n):
            t = i / cls.SAMPLE_RATE
            clang = (math.sin(2 * math.pi * 120 * t) + 0.6 * math.sin(2 * math.pi * 310 * t)) * math.exp(-10 * t) * 0.55
            samples.append(clang)
        return samples

    @classmethod
    def _make_bankruptcy(cls) -> list[float]:
        dur = 0.6
        n = int(dur * cls.SAMPLE_RATE)
        samples = []
        for i in range(n):
            t = i / cls.SAMPLE_RATE
            freq = 380 - (200 * (i / n))
            samples.append(math.sin(2 * math.pi * freq * t) * (1.0 - (i / n)) * 0.45)
        return samples

    @classmethod
    def _make_victory(cls) -> list[float]:
        # Gamelan-inspired celebration pentatonic melody (Pelog/Slendro notes: 440, 493.88, 587.33, 659.25, 783.99)
        notes = [440, 587.33, 659.25, 783.99, 880, 1046.50]
        note_dur = 0.22
        samples = []
        for freq in notes:
            n_step = int(note_dur * cls.SAMPLE_RATE)
            for i in range(n_step):
                t = i / cls.SAMPLE_RATE
                env = math.exp(-8 * t) * 0.45
                samples.append(math.sin(2 * math.pi * freq * t) * env)
        return samples

    @classmethod
    def _make_ambient_music(cls) -> list[float]:
        # Calm Indonesian gamelan-inspired pentatonic bell chime loop (~10s)
        dur = 10.0
        n = int(dur * cls.SAMPLE_RATE)
        samples = [0.0] * n
        # Pattern of tranquil bell chimes at specific timestamps
        bell_notes = [
            (0.0, 440.0), (1.2, 523.25), (2.4, 587.33), (3.8, 659.25),
            (5.0, 587.33), (6.2, 523.25), (7.4, 440.0), (8.6, 392.0)
        ]
        for start_t, freq in bell_notes:
            start_idx = int(start_t * cls.SAMPLE_RATE)
            decay_len = int(2.4 * cls.SAMPLE_RATE)
            for i in range(decay_len):
                if start_idx + i < n:
                    t = i / cls.SAMPLE_RATE
                    # Bell chime with 2 harmonics
                    val = (math.sin(2 * math.pi * freq * t) + 0.3 * math.sin(2 * math.pi * (freq * 2.76) * t)) * math.exp(-3.5 * t) * 0.18
                    samples[start_idx + i] += val
        return samples


class AudioManager:
    """Manages audio playback, volume controls, and graceful fallbacks."""
    _instance: Optional["AudioManager"] = None

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or os.path.dirname(os.path.dirname(__file__))
        self.is_initialized = False
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.bgm_sound: Optional[pygame.mixer.Sound] = None
        self.bgm_channel: Optional[pygame.mixer.Channel] = None

        self.master_volume: float = 0.8
        self.music_volume: float = 0.5
        self.sfx_volume: float = 0.8
        self.is_muted: bool = False

        self._init_mixer()

    @classmethod
    def get_instance(cls, base_dir: Optional[str] = None) -> "AudioManager":
        if cls._instance is None:
            cls._instance = cls(base_dir)
        return cls._instance

    def _init_mixer(self) -> None:
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.is_initialized = True

            # Generate default procedural WAV assets if missing
            SoundGenerator.generate_all(self.base_dir)

            # Load SFX
            sfx_dir = os.path.join(self.base_dir, "assets", "audio", "sfx")
            for filename in os.listdir(sfx_dir):
                if filename.endswith(".wav"):
                    name = os.path.splitext(filename)[0]
                    path = os.path.join(sfx_dir, filename)
                    try:
                        self.sounds[name] = pygame.mixer.Sound(path)
                    except Exception:
                        pass

            # Load BGM
            music_path = os.path.join(self.base_dir, "assets", "audio", "music", "ambient_loop.wav")
            if os.path.exists(music_path):
                try:
                    self.bgm_sound = pygame.mixer.Sound(music_path)
                except Exception:
                    pass

            self.apply_volume()
        except Exception:
            # Silent fallback if host has no audio device or SDL audio is disabled
            self.is_initialized = False

    def play_sfx(self, name: str) -> None:
        """Play a sound effect if mixer is available and not muted."""
        if not self.is_initialized or self.is_muted:
            return
        sound = self.sounds.get(name)
        if sound:
            effective_vol = self.sfx_volume * self.master_volume
            sound.set_volume(effective_vol)
            sound.play()

    def start_bgm(self) -> None:
        """Start ambient background music on endless loop."""
        if not self.is_initialized or self.is_muted or not self.bgm_sound:
            return
        if self.bgm_channel is None or not self.bgm_channel.get_busy():
            self.bgm_channel = self.bgm_sound.play(loops=-1)
            self.apply_volume()

    def stop_bgm(self) -> None:
        """Stop background music."""
        if self.bgm_channel:
            self.bgm_channel.stop()

    def set_master_volume(self, val: float) -> None:
        self.master_volume = max(0.0, min(1.0, val))
        self.apply_volume()

    def set_music_volume(self, val: float) -> None:
        self.music_volume = max(0.0, min(1.0, val))
        self.apply_volume()

    def set_sfx_volume(self, val: float) -> None:
        self.sfx_volume = max(0.0, min(1.0, val))
        self.apply_volume()

    def set_mute(self, muted: bool) -> None:
        self.is_muted = muted
        self.apply_volume()
        if not self.is_muted:
            self.start_bgm()
        else:
            self.stop_bgm()

    def toggle_mute(self) -> bool:
        self.set_mute(not self.is_muted)
        return self.is_muted

    def apply_volume(self) -> None:
        """Apply current volume parameters across all channels."""
        if not self.is_initialized:
            return

        effective_sfx = 0.0 if self.is_muted else (self.sfx_volume * self.master_volume)
        effective_music = 0.0 if self.is_muted else (self.music_volume * self.master_volume)

        for s in self.sounds.values():
            s.set_volume(effective_sfx)

        if self.bgm_channel:
            self.bgm_channel.set_volume(effective_music)
