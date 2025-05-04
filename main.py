import pygame
import asyncio
import platform
import time
import numpy as np
from scipy.io import wavfile
import warnings
from notes import piano_notes, note_to_name
from sheets.river import tempo, right_score, right_beat, left_score, left_beat

# 忽略 WAV 文件非數據塊警告
warnings.filterwarnings("ignore", category=wavfile.WavFileWarning)

# 初始化 Pygame
pygame.init()
pygame.mixer.set_num_channels(50)  # 支援多聲道
FPS = 60
SAMPLE_RATE = 44100  # WAV 檔案的取樣率

class PianoMusicGenerator:
    def __init__(self):
        
        self.piano_notes = piano_notes   # 鋼琴音符名稱
        self.note_to_name = note_to_name # 音符數字到音符名稱的映射
                
        # 預載音符的 WAV 文件
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
        self.quarter_duration = 60 / self.tempo  # 四分音符時長（秒）
        self.measure_duration = 4 * self.quarter_duration  # 小節時長
        self.decay_time = 0.5  # 額外衰減時間
        self.max_duration = self.measure_duration + self.decay_time  # 音符最大播放時長
        self.fade_samples = int(0.05 * SAMPLE_RATE)  # 增加到50ms淡入時間
        
        # 音量參數
        self.right_volume = 0.7  # 降低音量以防止削波
        self.left_volume = 0.6
        self.max_amplitude = 32767 * 0.7  # 降低最大振幅
    
    def get_piano_sound(self, note_num, hand='right'):
        """根據數字音符獲取對應的 Pygame 音頻物件"""
        if note_num == 0:
            return None
        note_name = self.note_to_name.get(note_num)
        if not note_name:
            print(f"警告: 無效音符 {note_num}")
            return None
        return self.sound_cache.get(note_name)
    
    def get_wav_data(self, note_num, hand='right'):
        """根據數字音符獲取對應的 WAV 數據"""
        if note_num == 0:
            return np.zeros((SAMPLE_RATE, 2), dtype=np.int16)
        note_name = self.note_to_name.get(note_num)
        if not note_name:
            print(f"警告: 無效音符 {note_num}")
            return np.zeros((SAMPLE_RATE, 2), dtype=np.int16)
        return self.wav_data_cache.get(note_name, np.zeros((SAMPLE_RATE, 2), dtype=np.int16))
    
    async def play_hand_part(self, score, beat, hand='right'):
        """播放單手部分音樂，支援平滑踏板效果"""
        current_measure_beats = 0  # 當前小節的累計節拍
        active_channels = []  # 存儲 (channel, start_time) 元組
        current_time = time.time()  # 記錄當前時間
        
        # 設置音量
        volume = self.right_volume if hand == 'right' else self.left_volume
        
        for note, beat_value in zip(score, beat):
            # 更新當前時間
            current_time = time.time()
            
            # 清理過期的聲道
            active_channels = [
                (ch, st) for ch, st in active_channels
                if ch.get_busy() and (current_time - st) < self.max_duration
            ]
            for ch, st in active_channels[:]:
                if (current_time - st) >= self.max_duration:
                    ch.stop()
                    active_channels.remove((ch, st))
            
            # 計算音符時長
            duration = self.quarter_duration * beat_value
            current_measure_beats += beat_value
            
            # 播放音符或和弦
            if isinstance(note, list):
                sounds = [self.get_piano_sound(n, hand) for n in note if n != 0]
                for sound in sounds:
                    if sound:
                        channel = sound.play(0, int(self.max_duration * 1000))
                        if channel:
                            channel.set_volume(volume)
                            active_channels.append((channel, current_time))
            else:
                sound = self.get_piano_sound(note, hand)
                if sound:
                    channel = sound.play(0, int(self.max_duration * 1000))
                    if channel:
                        channel.set_volume(volume)
                        active_channels.append((channel, current_time))
            
            # 檢查小節結束
            if current_measure_beats >= 4:
                current_measure_beats -= 4  # 重置小節計數，保留溢出節拍
            
            # 等待音符時長
            await asyncio.sleep(duration)
        
        # 播放結束後，等待最後音符衰減
        await asyncio.sleep(self.decay_time)
        for channel, _ in active_channels:
            if channel.get_busy():
                channel.stop()
    
    async def play_music(self, right_score, right_beat, left_score, left_beat):
        """同時播放右手和左手部分的音樂"""
        print("正在播放鋼琴合奏版《Wedding Dress》...")
        await asyncio.gather(
            self.play_hand_part(right_score, right_beat, 'right'),
            self.play_hand_part(left_score, left_beat, 'left')
        )
        print("播放完成！")
    
    def generate_wav_data(self, score, beat, hand='right'):
        """生成單手部分的WAV數據，改進版本以消除爆音"""
        total_samples = int(sum(beat) * self.quarter_duration * SAMPLE_RATE)
        audio_data = np.zeros((total_samples, 2), dtype=np.float64)  # 使用 float64 提高精度
        current_pos = 0
        current_measure_beats = 0
        volume = self.right_volume if hand == 'right' else self.left_volume
        
        # 使用更平滑的淡入淡出曲線（餘弦曲線）
        fade_in = (1 - np.cos(np.linspace(0, np.pi/2, self.fade_samples))[:, np.newaxis])
        fade_out = (np.cos(np.linspace(0, np.pi/2, self.fade_samples)))[:, np.newaxis]
        
        for note, beat_value in zip(score, beat):
            duration_samples = int(beat_value * self.quarter_duration * SAMPLE_RATE)
            measure_samples = int(self.measure_duration * SAMPLE_RATE)
            
            # 模擬踏板效果：音符持續到小節結束
            sustain_samples = min(measure_samples, total_samples - current_pos)
            
            if isinstance(note, list):  # 處理和弦
                for n in note:
                    if n != 0:
                        note_data = self.get_wav_data(n, hand).astype(np.float64)
                        end_pos = min(current_pos + sustain_samples, total_samples)
                        segment_length = end_pos - current_pos
                        
                        # 確保不會超出範圍
                        if segment_length > len(note_data):
                            note_data = np.pad(note_data, ((0, segment_length - len(note_data)), 'constant'))
                        
                        segment_data = note_data[:segment_length] * volume
                        
                        # 應用淡入效果
                        if segment_length > self.fade_samples:
                            segment_data[:self.fade_samples] *= fade_in
                        
                        # 疊加到音頻數據，使用 np.clip 防止溢出
                        audio_data[current_pos:end_pos] = np.clip(
                            audio_data[current_pos:end_pos] + segment_data,
                            -self.max_amplitude, self.max_amplitude
                        )
            else:  # 處理單音
                if note != 0:
                    note_data = self.get_wav_data(note, hand).astype(np.float64)
                    end_pos = min(current_pos + sustain_samples, total_samples)
                    segment_length = end_pos - current_pos
                    
                    # 確保不會超出範圍
                    if segment_length > len(note_data):
                        note_data = np.pad(note_data, ((0, segment_length - len(note_data)), 'constant'))
                    
                    segment_data = note_data[:segment_length] * volume
                    
                    # 應用淡入效果
                    if segment_length > self.fade_samples:
                        segment_data[:self.fade_samples] *= fade_in
                    
                    # 疊加到音頻數據，使用 np.clip 防止溢出
                    audio_data[current_pos:end_pos] = np.clip(
                        audio_data[current_pos:end_pos] + segment_data,
                        -self.max_amplitude, self.max_amplitude
                    )
            
            current_pos += duration_samples
            current_measure_beats += beat_value
            
            # 檢查小節結束
            if current_measure_beats >= 4:
                current_measure_beats -= 4
                
                # 在小節邊界應用淡出
                fade_out_samples = min(self.fade_samples, current_pos)
                if fade_out_samples > 0:
                    audio_data[current_pos-fade_out_samples:current_pos] *= fade_out
        
        # 正規化音量
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            audio_data = (audio_data / max_val * self.max_amplitude).astype(np.int16)
        
        return audio_data
    
    async def export_to_wav(self, right_score, right_beat, left_score, left_beat, filename="piano_output.wav"):
        """匯出鋼琴音樂為WAV檔案，改進版本以消除爆音"""
        print("正在生成WAV檔案...")
        
        # 確保檔案名稱包含 .wav 副檔名
        if not filename.endswith('.wav'):
            filename += '.wav'
        
        # 生成左右手音頻數據
        right_audio = self.generate_wav_data(right_score, right_beat, 'right')
        left_audio = self.generate_wav_data(left_score, left_beat, 'left')
        
        # 確保左右手長度一致
        min_length = min(len(right_audio), len(left_audio))
        right_audio = right_audio[:min_length]
        left_audio = left_audio[:min_length]
        
        # 混合左右手音頻，使用浮點運算
        mixed_audio = right_audio.astype(np.float64) + left_audio.astype(np.float64)
        
        # 使用動態壓縮來防止削波
        max_val = np.max(np.abs(mixed_audio))
        if max_val > 0:
            # 應用軟性限制器
            threshold = 0.9 * self.max_amplitude
            if max_val > threshold:
                # 只壓縮超過閾值的部分
                compression_ratio = threshold / max_val
                mixed_audio = np.where(
                    np.abs(mixed_audio) > threshold,
                    threshold * np.sign(mixed_audio) + (mixed_audio - threshold * np.sign(mixed_audio)) * compression_ratio,
                    mixed_audio
                )
        
        # 最終正規化
        max_val = np.max(np.abs(mixed_audio))
        if max_val > 0:
            mixed_audio = (mixed_audio / max_val * self.max_amplitude).astype(np.int16)
        
        # 寫入WAV檔案
        wavfile.write(filename, SAMPLE_RATE, mixed_audio)
        print(f"已成功匯出WAV檔案: {filename}")
    
    async def play_and_export(self, right_score, right_beat, left_score, left_beat, filename="piano_output.wav"):
        """同時播放並匯出音樂"""
        await asyncio.gather(
            self.play_music(right_score, right_beat, left_score, left_beat),
            self.export_to_wav(right_score, right_beat, left_score, left_beat, filename)
        )

async def main():
    
    piano_gen = PianoMusicGenerator()
    
    # 選擇要執行的操作
    print("請選擇操作:")
    print("1. 僅播放音樂")
    print("2. 僅匯出WAV檔案")
    print("3. 播放並匯出WAV檔案")
    
    choice = input("輸入選擇 (1/2/3): ")
    
    if choice == "1":
        await piano_gen.play_music(right_score, right_beat, left_score, left_beat)
    elif choice == "2":
        filename = input("輸入WAV檔案名稱 (例如: output.wav): ")
        await piano_gen.export_to_wav(right_score, right_beat, left_score, left_beat, filename)
    elif choice == "3":
        filename = input("輸入WAV檔案名稱 (例如: output.wav): ")
        await piano_gen.play_and_export(right_score, right_beat, left_score, left_beat, filename)
    else:
        print("無效選擇")

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())