'''
* Title: Wedding Dress
* Piano Sheet Source: https://www.sophiesauveterre.com/wedding-dress-by-taeyang/
* Key: C大調(CDEFGABC)
* score: 用大括號[]括起來的scores是和弦(chord), 會同時發聲
* beat: 
  0.5: 八分音符(半拍)
    1: 四分音符(一拍)
  1.5: 附點四分音符(一拍半)
    2: 二分音符(二拍)
  2.5: 八分音符 + 二分音符(二拍半)
'''

tempo = 140

# 右手主旋律
right_score = [
    [8,12], 7, 8, [6,10],  [4,8], 5, 8, 9,  [5,8,10], 10, 11, 10, 10,  9, 8, 9,
]

right_beat = [
    1.5, 1.5, 0.5, 2,  1, 0.5, 0.5, 0.5,  1.5, 1, 0.5, 0.5, 2,  1.5, 0.5, 0.5,
]

# 左手伴奏z
left_score = [
    -2, 3, 6, 7,  -4, 1, 4, 7,  1, 5, 8, 10,  -3, 2, 5, 7,
]

left_beat = [
    0.5, 0.5, 0.5, 2.5,  0.5, 0.5, 0.5, 2.5,  0.5, 0.5, 0.5, 2.5,  0.5, 0.5, 0.5, 2.5,
]