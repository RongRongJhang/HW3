'''
* Title: Wedding Dress
* Piano Sheet Source: https://www.sophiesauveterre.com/wedding-dress-by-taeyang/
* Key: C大調(CDEFGABC)
* Score: 
  - 音符數字和音符名稱的mapping寫在notes.py
  - 用大括號[ ]括起來的scores是和聲(harmony)，能夠同時發聲
* Beat: 
  0.5: 八分音符(半拍)
    1: 四分音符(一拍)
  1.5: 附點四分音符(一拍半)
    2: 二分音符(二拍)
  2.5: 八分音符 + 二分音符(二拍半)
'''

tempo = 140

# 右手主旋律
right_score = [
    [12,19], 11, 12, [9,16],  [5,12], 7, 12, 14,  [7,12,16], 16, 17, 16, 16,  14, 12, 14,
]

right_beat = [
    1.5, 1.5, 0.5, 2,  1, 0.5, 0.5, 0.5,  1.5, 1, 0.5, 0.5, 2,  1.5, 0.5, 0.5,
]

# 左手伴奏
left_score = [
    -3, 4, 9, 11,  -7, 0, 5, 11,  0, 7, 12, 16,  -5, 2, 7, 11,
]

left_beat = [
    0.5, 0.5, 0.5, 2.5,  0.5, 0.5, 0.5, 2.5,  0.5, 0.5, 0.5, 2.5,  0.5, 0.5, 0.5, 2.5,
]