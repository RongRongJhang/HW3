
## 1. Get Started

#### Dependencies and Installation
* Python 3.13.3

1. Clone Repo
```
git clone https://github.com/RongRongJhang/HW3.git
```
2. Install Dependencies
```
cd HW3
pip install -r requirements.txt
```
3. Run Code
```
python3 main.py
```

## 2. Program Functions

* Base Functions

|    Items     |  Description |
| :------------- |:-------------|
| Score      |   音符數字和音符名稱的 mapping 寫在 notes.py   |
| Beat      |  1. Beat lists: <br> - 0.125: 三十二分音符(八分之一拍) <br> - 0.25: 十六分音符(四分之一拍) <br> - 0.5: 八分音符(半拍) <br> - 1: 四分音符(一拍) <br> - 1.5: 附點四分音符(一拍半) <br> - 1.75: 雙重附點四分音符(一又四分之三拍) <br> - 2: 二分音符(二拍) <br> - 2.5: 八分音符 + 二分音符(二拍半) <br> 2. 引入裝飾音的概念：有幾個奇怪的數字是為了演奏裝飾音而設計的(0.03125、0.5625、0.0625、1.125)  |
| Music name     |  options.py 裡有 mapping music name 和 music sheets   |

* Extra Functions

|    Items     | Description |
| :------------- |:-------------|
| 模擬鋼琴音色 | notes 資料夾裡存放每個鋼琴鍵的聲音 wav 檔 |
| 模擬鋼琴彈法 | 樂譜分成左右手概念，各自有對照的 scores 和 beats  |
| 選擇樂譜的功能  |  目前有2份樂譜可選擇，樂譜具有擴充性，可自行添加新樂譜   |
| 選擇操作的功能 |   選項如下： <br> 1. 僅播放音樂 <br> 2. 僅匯出WAV檔案 <br> 3. 播放並匯出WAV檔案   |
|  Score 額外功能  |  - 和聲功能：用大括號[ ]括起來的scores是和聲(harmony)，能夠同時發聲 <br>  |
|  加入踏板的功能 | 每小節踩一次踏板，讓彈出的聲音產生延長效果 |
|  加入節拍概念 | 實現：樂譜裡的 tempo |
