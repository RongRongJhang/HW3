import pygame
import asyncio
import platform
import time
import numpy as np
from scipy.io import wavfile
import warnings
from notes import piano_notes, note_to_name
from options import SHEET_OPTIONS
import importlib

warnings.filterwarnings("ignore", category=wavfile.WavFileWarning)

pygame.init()
pygame.mixer.set_num_channels(50)  # 支援多聲道
FPS = 60
SAMPLE_RATE = 44100  # WAV 檔案的取樣率

class PianoMusicGenerator:
    def __init__(self, tempo, right_score, right_beat, left_score, left_beat):
        
        self.piano_notes = piano_notes   # 鋼琴音符名稱
        self.note_to_name = note_to_name # 音符數字到音符名稱的映射

        self.sound_cache = {}
        self.wav_data_cache = {}  # 用於匯出WAV的原始數據
        required_notes = set(self.note_to_name.values())
        
        for note in required_notes:
            try:
                # 載入用於播放的音效
                self.sound_cache[note] = pygame.mixer.Sound(f'notes/{note}.wav')
                # 載入用於匯出的原始WAV數據
                _, wav_data = wavfile.read(f'notes/{note}.wav')
                # 確保數據是立體聲
                if wav_data.ndim == 1:  # 單聲道轉立體聲
                    wav_data = np.column_stack((wav_data, wav_data))
                self.wav_data_cache[note] = wav_data
            except FileNotFoundError:
                print(f"警告: 找不到 notes/{note}.wav，該音符將無聲")
                self.sound_cache[note] = None
                self.wav_data_cache[note] = np.zeros((SAMPLE_RATE, 2), dtype=np.int16)
        
        # 播放參數
        self.tempo = tempo  # 拍子的速度(Beats Per Minute, BPM)
        self.quarter_duration = 60 / self.tempo  # 四分音符時長(秒)
        self.measure_duration = 4 * self.quarter_duration  # 小節時長
        self.decay_time = 0.5  # 額外衰減時間
        self.max_duration = self.measure_duration + self.decay_time  # 音符最大播放時長
        self.fade_samples = int(0.05 * SAMPLE_RATE)  # 增加到50ms淡入時間
        
        # 音量參數
        self.right_volume = 0.7  # 右手音量
        self.left_volume = 0.5   # 左手音量
        self.max_amplitude = 32767 * 0.7  # 降低最大振幅
        
        # 樂譜數據
        self.right_score = right_score
        self.right_beat = right_beat
        self.left_score = left_score
        self.left_beat = left_beat
    
    def get_piano_sound(self, note_num):
        if note_num == 0:
            return None
        note_name = self.note_to_name.get(note_num)
        if not note_name:
            print(f"警告: 無效音符 {note_num}")
            return None
        return self.sound_cache.get(note_name)
    
    def get_wav_data(self, note_num):
        if note_num == 0:
            return np.zeros((SAMPLE_RATE, 2), dtype=np.int16)
        note_name = self.note_to_name.get(note_num)
        if not note_name:
            print(f"警告: 無效音符 {note_num}")
            return np.zeros((SAMPLE_RATE, 2), dtype=np.int16)
        return self.wav_data_cache.get(note_name, np.zeros((SAMPLE_RATE, 2), dtype=np.int16))
    
    async def play_hand_part(self, score, beat, hand='right'):
        start_time = time.time()
        next_note_time = 0.0
        active_channels = []
        volume = self.right_volume if hand == 'right' else self.left_volume

        for note, beat_value in zip(score, beat):
            duration = self.quarter_duration * beat_value
            
            # 清理過期的聲道
            current_time = time.time() - start_time
            active_channels = [
                (ch, st) for ch, st in active_channels
                if ch.get_busy() and (current_time - st) < self.max_duration
            ]
            
            # 等待到下一個音符的時間點
            while (time.time() - start_time) < next_note_time:
                await asyncio.sleep(0.001)
            
            # 播放音符
            sounds = []
            if isinstance(note, list):
                sounds = [self.get_piano_sound(n) for n in note if n != 0]
            elif note != 0:
                sounds = [self.get_piano_sound(note)]
                
            for sound in sounds:
                if sound:
                    channel = sound.play(0, int(self.max_duration * 1000))
                    if channel:
                        channel.set_volume(volume)
                        active_channels.append((channel, time.time() - start_time))
            
            next_note_time += duration
        
        # 只停止已經超過最大時長的音符
        if active_channels:
            expected_end_time = next_note_time + self.decay_time
            
            while True:
                current_time = time.time() - start_time
                # 移除已完成播放的聲道
                active_channels = [
                    (ch, st) for ch, st in active_channels
                    if ch.get_busy() and (current_time - st) < expected_end_time
                ]
                
                if not active_channels:
                    break
                    
                # 對最後的音符應用淡出效果
                for channel, start_t in active_channels:
                    elapsed = current_time - start_t
                    remaining = expected_end_time - elapsed
                    if remaining < 0.5:  # 最後0.5秒開始淡出
                        channel.set_volume(volume * (remaining / 0.5))
                
                await asyncio.sleep(0.05)
    
    async def play_music(self):
        print("正在播放...")
        await asyncio.gather(
            self.play_hand_part(self.right_score, self.right_beat, 'right'),
            self.play_hand_part(self.left_score, self.left_beat, 'left')
        )
        print("播放完成！")
    
    def generate_wav_data(self, score, beat, hand='right'):
        total_samples = int(sum(beat) * self.quarter_duration * SAMPLE_RATE)
        audio_data = np.zeros((total_samples, 2), dtype=np.float64)
        current_pos = 0
        current_measure_beats = 0
        volume = self.right_volume if hand == 'right' else self.left_volume
        
        fade_in = (1 - np.cos(np.linspace(0, np.pi/2, self.fade_samples)))[:, np.newaxis]
        fade_out = (np.cos(np.linspace(0, np.pi/2, self.fade_samples)))[:, np.newaxis]
        
        for note, beat_value in zip(score, beat):
            duration_samples = int(beat_value * self.quarter_duration * SAMPLE_RATE)
            measure_samples = int(self.measure_duration * SAMPLE_RATE)
            sustain_samples = min(measure_samples, total_samples - current_pos)
            
            if isinstance(note, list):
                for n in note:
                    if n != 0:
                        note_data = self.get_wav_data(n).astype(np.float64)
                        end_pos = min(current_pos + sustain_samples, total_samples)
                        segment_length = end_pos - current_pos
                        
                        if segment_length > note_data.shape[0]:
                            pad_width = ((0, segment_length - note_data.shape[0]), (0, 0))
                            note_data = np.pad(note_data, pad_width, mode='constant')
                        
                        segment_data = note_data[:segment_length] * volume
                        if segment_length > self.fade_samples:
                            segment_data[:self.fade_samples] *= fade_in
                        
                        audio_data[current_pos:end_pos] += segment_data
            else:
                if note != 0:
                    note_data = self.get_wav_data(note).astype(np.float64)
                    end_pos = min(current_pos + sustain_samples, total_samples)
                    segment_length = end_pos - current_pos
                    
                    if segment_length > note_data.shape[0]:
                        pad_width = ((0, segment_length - note_data.shape[0]), (0, 0))
                        note_data = np.pad(note_data, pad_width, mode='constant')
                    
                    segment_data = note_data[:segment_length] * volume
                    if segment_length > self.fade_samples:
                        segment_data[:self.fade_samples] *= fade_in
                    
                    audio_data[current_pos:end_pos] += segment_data
            
            current_pos += duration_samples
            current_measure_beats += beat_value
            
            if current_measure_beats >= 4:
                current_measure_beats -= 4
                fade_out_samples = min(self.fade_samples, current_pos)
                if fade_out_samples > 0:
                    audio_data[current_pos-fade_out_samples:current_pos] *= fade_out
        
        return audio_data
    
    async def export_to_wav(self, filename):
        print("正在生成WAV檔案...")
        
        if not filename.endswith('.wav'):
            filename += '.wav'
        
        right_audio = self.generate_wav_data(self.right_score, self.right_beat, 'right')
        left_audio = self.generate_wav_data(self.left_score, self.left_beat, 'left')
        
        min_length = min(len(right_audio), len(left_audio))
        right_audio = right_audio[:min_length]
        left_audio = left_audio[:min_length]
        
        mixed_audio = right_audio + left_audio
        
        max_val = np.max(np.abs(mixed_audio))
        if max_val > 0:
            mixed_audio = (mixed_audio / max_val * self.max_amplitude).astype(np.int16)
        
        wavfile.write(filename, SAMPLE_RATE, mixed_audio)
        print(f"已成功匯出WAV檔案: {filename}")
    
    async def play_and_export(self, filename):
        # 同時播放並匯出音樂
        await asyncio.gather(
            self.play_music(),
            self.export_to_wav(filename)
        )

def load_sheet_music(sheet_name):
    # 動態載入樂譜模組
    try:
        module = importlib.import_module(f'sheets.{sheet_name}')
        return (
            module.tempo,
            module.right_score,
            module.right_beat,
            module.left_score,
            module.left_beat
        )
    except ImportError as e:
        print(f"錯誤: 無法載入樂譜 '{sheet_name}': {e}")
        return None

async def main():
    # 選擇樂譜
    print("請選擇樂譜:")
    for num, (sheet_name, display_name) in SHEET_OPTIONS.items():
        print(f"{num}. {display_name}")
    
    sheet_choice = input("輸入選擇 (1/2): ")
    if sheet_choice not in SHEET_OPTIONS:
        print("無效選擇")
        return
    
    sheet_name, display_name = SHEET_OPTIONS[sheet_choice]
    sheet_data = load_sheet_music(sheet_name)
    if not sheet_data:
        return
    
    tempo, right_score, right_beat, left_score, left_beat = sheet_data
    piano_gen = PianoMusicGenerator(tempo, right_score, right_beat, left_score, left_beat)
    
    # 選擇操作
    print("\n")
    print("請選擇操作:")
    print("1. 僅播放音樂")
    print("2. 僅匯出WAV檔案")
    print("3. 播放並匯出WAV檔案")
    
    choice = input("輸入選擇 (1/2/3): ")
    
    if choice == "1":
        await piano_gen.play_music()
    elif choice == "2":
        filename = sheet_name
        await piano_gen.export_to_wav(filename)
    elif choice == "3":
        filename = sheet_name
        await piano_gen.play_and_export(filename)
    else:
        print("無效選擇")

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())