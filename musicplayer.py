import wx
import pygame
import os
import re
import time
from threading import Thread
from mutagen import File
from mutagen.flac import FLAC
import sys
import win32api

APP_TITLE = u'音乐播放器'
MAX_LYRIC_ROW = 19
LYRIC_ROW_REG = '\[[0-9]{2}:[0-9]{2}.[0-9]{2,}\]'
MAX_MUSIC_NAME_LEN = 70  # 歌名展示的时候最长字符限制

class MainFrame(wx.Frame):
    '''程序主窗口类，继承自wx.Frame'''

    def __init__(self):
        '''构造函数'''
        # 播放器的整体属性
        self.width = 1280
        self.height = 720
        self.default_volume = 0.2
        #self.lastvolume = self.volume

        self.local_music_folder = "music_folder"
        wx.Frame.__init__(self, None, -1, APP_TITLE)
        self.SetSize(self.width, self.height)
        self.SetBackgroundColour((248, 248, 255))  # 设置界面的背景颜色

        # 音乐列表有关
        self.local_music_name_list = []  # 当前音乐名字列表
        self.lyrcis_static_text = []  # 当前播放的音乐的歌词列表
        self.play_stop_button = None  # 播放、暂停按钮
        self.current_music_state = 0  # 是否有音乐在播放，0表示否
        self.IsPaused = False  # 是否暂停
        self.current_music_index = 0  # 当前音乐的索引
        self.current_music_name = None
        self.current_music_path = None
        self.current_music_length = None
        # 初始化本地歌曲列表
        self.get_local_music_list()
        self.current_music_static_text = None  # 当前播放的音乐的名字

        # 按钮使用的图片
        self.play_png = wx.Image("resources/play.png", wx.BITMAP_TYPE_PNG).Rescale(50, 50).ConvertToBitmap()
        self.stop_png = wx.Image("resources/stop.png", wx.BITMAP_TYPE_PNG).Rescale(50, 50).ConvertToBitmap()
        self.last_music_png = wx.Image("resources/last_music.png", wx.BITMAP_TYPE_PNG).Rescale(40, 40).ConvertToBitmap()
        self.next_music_png = wx.Image("resources/next_music.png", wx.BITMAP_TYPE_PNG).Rescale(40, 40).ConvertToBitmap()

        # 导航栏所在的panel
        self.navi_panel = None
        self.draw_navi_panel()

        # 歌曲列表所在的panel
        self.music_list_panel = None
        self.draw_music_list_panel()

        # 播放部分所在的panel
        self.play_music_panel = None
        self.draw_play_music_panel()

        # 歌词部分所在的panel
        self.music_lyric_panel = None

        self.music_cover_panel = None
        self.draw_music_cover_panel()

        self.createTimer()
        self.settime = 0
        self.after_id = None
        self.timeleeplist = [0]

        self.upside_lyrics_list = []
        self.downside_lyrics_list = []
        self.current_lyrics_word_list = []
        self.current_lyrics_time_list = []

        pygame.mixer.pre_init(44100, -16, 2, 2048)
        pygame.mixer.init()
        self.music = pygame.mixer.music
        self.SONG_FINISHED = pygame.USEREVENT + 1

        
        if hasattr(sys, "frozen") and getattr(sys, "frozen") == "windows_exe":
            exeName = win32api.GetModuleFileName(win32api.GetModuleHandle(None))
            icon = wx.Icon(exeName, wx.BITMAP_TYPE_ANY)
        else : 
            icon = wx.Icon('resources/music.png', wx.BITMAP_TYPE_ANY)
            self.SetIcon(icon)        # 以下可以添加各类控件
            pass

        self.Bind(wx.EVT_CLOSE, self.OnClose)


    def get_path_by_name(self, file_name):
        #通过名称获取音乐的完整路径
        return os.path.join(self.local_music_folder, file_name)

    def get_local_music_list(self):
        #获取本地音乐列表
        self.local_music_name_list.clear()  # 这一步必须有
        for local_music_file_name in os.listdir(self.local_music_folder):
            if local_music_file_name.endswith((".wav", ".flac", ".mp3")):
                self.local_music_name_list.append(local_music_file_name)

    def draw_navi_panel(self):
        #导航栏panel
        self.navi_panel = wx.Panel(self, id=-1, pos=(0, 0), size=(100, self.height - 200))
        #self.navi_panel.SetBackgroundColour("yellow")
        # 本地音乐
        local_music_text = wx.StaticText(self.navi_panel, -1, "本地音乐", pos=(20, 10), style=wx.ALIGN_LEFT)
        local_music_text.SetOwnForegroundColour((41, 36, 33))

    def draw_music_list_panel(self):
        # 重新计算本地音乐列表
        self.get_local_music_list()
        # 绘制面板整体
        if self.music_list_panel is not None:
            self.music_list_panel.Destroy()
        self.music_list_panel = wx.Panel(self, id=-1, pos=(100, 0), size=(450, self.height - 150))
        #self.music_list_panel.SetBackgroundColour("green")
        # 音乐列表
        local_music_num = len(self.local_music_name_list)
        for music_index in range(local_music_num):
            music_full_name = self.local_music_name_list[music_index].split('.')[0]
            if len(music_full_name) > MAX_MUSIC_NAME_LEN:
                music_full_name = music_full_name[0:MAX_MUSIC_NAME_LEN] + "..."
            music_text_button = wx.Button(self.music_list_panel, -1, music_full_name, pos=(0, music_index * 35 + 10),
                                          size=(450, 30), style=wx.BU_LEFT)

            music_text_button.SetOwnForegroundColour((41, 36, 33))
            music_text_button.SetBackgroundColour((248, 248, 255))
            music_text_button.Bind(wx.EVT_LEFT_DOWN, lambda e, index=music_index: self.play_index_music(index))
            music_text_button.SetWindowStyleFlag(wx.NO_BORDER)
            music_text_button.Refresh()

    def draw_play_music_panel(self):
        # 播放音乐所在的panel
        self.play_music_panel = wx.Panel(self, id=-1, pos=(0, self.height - 130), size=(self.width, 150))
        #self.play_music_panel.SetBackgroundColour("blue")
        # 歌的名字
        self.current_music_static_text = wx.StaticText(self, -1, "请选择歌曲",
                                                       pos=(210, self.height - 140), size=(80, -1), style=wx.ALIGN_LEFT)
        self.current_music_static_text.SetOwnForegroundColour((41, 36, 33))

        self.play_stop_button = wx.BitmapButton(self.play_music_panel, -1, self.play_png,  pos=(320, 25), size=(50, 50))
        self.play_stop_button.SetWindowStyleFlag(wx.NO_BORDER)
        self.play_stop_button.SetToolTip(u'播放/暂停')

        last_music_button = wx.BitmapButton(self.play_music_panel, -1, self.last_music_png, pos=(260, 30), size=(40, 40))
        last_music_button.SetWindowStyleFlag(wx.NO_BORDER)
        last_music_button.SetToolTip(u'上一首')

        next_music_button = wx.BitmapButton(self.play_music_panel, -1, self.next_music_png, pos=(390, 30), size=(40, 40))
        next_music_button.SetWindowStyleFlag(wx.NO_BORDER)
        next_music_button.SetToolTip(u'下一首')
        # 调节音量的按钮
        self.volume_slider = wx.Slider(self.play_music_panel, -1, int(self.default_volume*100), 0, 100, pos=(490, 10),
                                       size=(-1, 80), style=wx.SL_VERTICAL|wx.SL_INVERSE)
        self.volume_slider.SetToolTip(u'音量:%d%%' % (self.default_volume*100))
        self.play_slider = wx.Slider(self.play_music_panel, -1, pos=(550, 35), size=(600, -1),style=wx.SL_HORIZONTAL)

        self.play_slider.SetToolTip('当前播放进度 00:00')

        self.progress = wx.StaticText(self, label='00:00', pos=(1165, 628))

        # 上述按钮的监听器
        last_music_button.Bind(wx.EVT_LEFT_DOWN, self.play_last_music)
        self.play_stop_button.Bind(wx.EVT_LEFT_DOWN, self.play_stop_music)
        next_music_button.Bind(wx.EVT_LEFT_DOWN, self.play_next_music)
        self.volume_slider.Bind(wx.EVT_SLIDER, self.change_volume)
        self.volume_slider.Bind(wx.EVT_SCROLL, self.change_volume)

    def draw_upside_lyrics_panel(self):
        self.upside_lyrics_list = []
        for row in range(int((MAX_LYRIC_ROW-1)/2)):
            lyrics_row = wx.StaticText(self.music_lyric_panel, -1, label='', pos=(100, 30 * row + 10), size=(400, -1), style=wx.ALIGN_CENTER)
            self.upside_lyrics_list.append(lyrics_row)

    def draw_downside_lyrics_panel(self):
        self.downside_lyrics_list = []
        for row in range(int((MAX_LYRIC_ROW+1)/2), MAX_LYRIC_ROW):
            lyrics_row = wx.StaticText(self.music_lyric_panel, -1, label='', pos=(100, 30 * row + 10), size=(400, -1), style=wx.ALIGN_CENTER)
            self.downside_lyrics_list.append(lyrics_row)


    def draw_music_cover_panel(self):
        self.music_cover_panel = wx.Panel(self, id=-1, pos=(0, 480), size=(200, 200))
        self.music_cover_panel.Refresh()

    def redraw_music_cover_panel(self,filepath):
        self.music_cover_panel = wx.Panel(self, id=-1, pos=(0, 480), size=(200, 200))
        path = filepath.split('\\')[0] +'\.tmp\cover.png'
        music_cover = wx.Image(path, wx.BITMAP_TYPE_ANY).Rescale(200, 200).ConvertToBitmap()
        music_cover_panel = wx.StaticBitmap(self.music_cover_panel, -1, music_cover, pos=(0, 0), size=(200, 200))
        music_cover_panel.Refresh()

    def get_lyric_path(self):
        current_music_path = self.get_path_by_name(self.local_music_name_list[self.current_music_index])
        lyric_path = current_music_path.split('.')[0]+'.lrc'
        if os.path.exists(lyric_path):
            return lyric_path
        else:
            return None

    def play_music(self):
        '''
        重新载入，播放音乐
        :return:
        '''
        current_music_path = self.get_path_by_name(self.local_music_name_list[self.current_music_index])
        self.music.load(current_music_path)
        self.current_music_path = current_music_path

        # step1：播放音乐
        self.music.play(loops=1, start=0.0)
        self.current_music_length = pygame.mixer.Sound(self.current_music_path).get_length()

        # step2：重写歌词面板
        #self.redraw_music_lyric_panel()
        self.current_music_name = current_music_path.split('\\')[-1]

        if self.current_music_name.split('.')[-1] == 'mp3':
            self.get_mp3_cover(current_music_path)
            self.redraw_music_cover_panel(current_music_path)
        elif self.current_music_name.split('.')[-1] == 'flac':
            #print(current_music_path)
            self.get_flac_cover(current_music_path)
            self.redraw_music_cover_panel(current_music_path)
        else:
            self.draw_music_cover_panel()
        self.update_total_music_time()

        # step3：开启新线程，追踪歌词
        self.music_lyric_panel = wx.Panel(self, id=-1, pos=(550, 0), size=(self.width - 550, self.height - 130))

        if self.get_lyric_path() is None or not os.path.exists(self.get_lyric_path()):
            self.current_lyrics_word_list = []
            self.current_lyrics_time_list = []
            self.medium_row = wx.StaticText(self.music_lyric_panel, -1, label='暂无歌词', pos=(100, 280),
                                            size=(400, -1), style=wx.ALIGN_CENTER)
            self.medium_row.SetOwnForegroundColour((61, 89, 171))
        else:
            self.get_lyrics_word()
            self.get_lyrics_time()
            self.medium_row = wx.StaticText(self.music_lyric_panel, -1, label='', pos=(100, 280),
                                            size=(400, -1), style=wx.ALIGN_CENTER)
            self.medium_row.SetOwnForegroundColour((61, 89, 171))

        self.draw_upside_lyrics_panel()
        self.draw_downside_lyrics_panel()
        #print(len(self.upside_lyrics_list))
        #print(len(self.downside_lyrics_list))
        self.current_music_state = 1
        self.play_stop_button.SetBitmap(self.stop_png)
        # 更改当前播放的音乐的名字
        current_music_name = self.local_music_name_list[self.current_music_index]
        namelist = current_music_name.split('.')
        if len(current_music_name) > MAX_MUSIC_NAME_LEN:
            current_music_name = current_music_name[0:MAX_MUSIC_NAME_LEN] + "..."
        self.current_music_static_text.SetLabelText(namelist[0])

        self.timeleeplist=[0]
        self.play_slider.SetRange(0, int(self.current_music_length))
        self.play_slider.SetValue(0)
        self.settime = 0
        self.play_slider.Bind(wx.EVT_SLIDER, self.timer)
        self.text_timer.Start(1000)
        #self.play_slider.Bind(wx.EVT_SCROLL, self.timer)
        #self.createTimer

    def play_index_music(self, music_index):
        '''
        播放指定索引的音乐
        :return:
        '''
        self.current_music_index = music_index
        # 载入音乐
        self.play_music()

    def play_stop_music(self, evt):
        if self.music.get_busy() or self.IsPaused:  # 有音乐在播放，需要暂停，或者音乐暂停中
            if self.current_music_state == 1:
                #print("有音乐在播放，需要暂停")
                self.music.pause()
                self.current_music_state = 0
                self.play_stop_button.SetBitmap(self.play_png)
                self.IsPaused = True
                #print(self.music.get_busy())
            else:  # 恢复暂停的音乐
                self.music.unpause()
                self.current_music_state = 1
                self.IsPaused = False
                self.play_stop_button.SetBitmap(self.stop_png)
        else:  # 重新载入音乐
            self.play_music()

    def play_last_music(self, evt):
        # 计算上一首音乐的名字和路径
        if self.current_music_index > 0:
            self.play_index_music(self.current_music_index - 1)
        else:
            self.play_index_music(0)

    def play_next_music(self, evt):
        # 计算下一首音乐的名字和路径
        if self.current_music_index < len(self.local_music_name_list) - 1:
            self.play_index_music(self.current_music_index + 1)
        else:
            self.play_index_music(len(self.local_music_name_list) - 1)

    def change_volume(self, evt):
        #修改音量
        #self.setVolumeAndTip()
        value = self.volume_slider.GetValue()
        obj = evt.GetEventObject()
        val = obj.GetValue()
        self.volume = float(val / 100)
        self.music.set_volume(self.volume)
        self.volume_slider.SetToolTip(u'音量:%d%%' % value)

    def get_lyrics_word(self):
        current_lyric_path = self.get_lyric_path()
        if current_lyric_path is None or not os.path.exists(current_lyric_path):
            return None

        with open(current_lyric_path, 'r', encoding="utf-8") as file_pointer:
            lyrics = file_pointer.readlines()

        self.current_lyrics_word_list = []
        for lyric in lyrics:
            if re.match(LYRIC_ROW_REG, lyric):
                index_of_right_blank = lyric.index(']')
                lyric_clause = lyric.replace('\n', '')[index_of_right_blank + 1:]
                self.current_lyrics_word_list.append(lyric_clause.strip())

    def get_lyrics_time(self):
        current_lyric_path = self.get_lyric_path()
        self.current_lyrics_time_list = []

        with open(current_lyric_path, 'r', encoding="utf-8") as file_pointer:
            lyrics = file_pointer.readlines()

        for i in range(len(lyrics)):
            lyrics[i] = lyrics[i].replace('\n', '')
            if lyrics[i].index(']') == 6:
                templist = lyrics[i].split(']')
                templist[0] = templist[0][:6] + '.00'
                templist[1] = templist[1].strip()
                lyrics[i] = ']'.join(templist)
            elif lyrics[i].index(']') == 10:
                templist = lyrics[i].split(']')
                templist[0] = templist[0][:9]
                templist[1] = templist[1].strip()
                lyrics[i] = ']'.join(templist)
            else:
                continue
        for lyric in lyrics:
            if re.match(LYRIC_ROW_REG, lyric):
                start_time = float(lyric[1:3]) * 60 + float(lyric[4:6]) + float(lyric[7:9]) / 100
                self.current_lyrics_time_list.append(start_time)

    def thread_sync_lyrics(self):
        #while self.music.get_busy():
        lyric_sync_thread = Thread(target=self.sync_lyrics)
        lyric_sync_thread.start()


    def sync_lyrics(self,evt):
        current_time = self.play_slider.GetValue()
        timelist = self.current_lyrics_time_list
        for point in range(len(timelist)):
            if abs(current_time-timelist[point])<=1:
                self.medium_row.SetLabelText(self.current_lyrics_word_list[point])
                self.set_upside_lyrics(point)
                self.set_downside_lyrics(point)
                #self.music_lyric_panel.Refresh()
                #time.sleep(0.5)
            else:
                pass

    def set_upside_lyrics(self,row):
        if row-9 <=0:
            start = 0
            for i in range(start, row):
                self.upside_lyrics_list[8 - i].SetLabelText(self.current_lyrics_word_list[row - i - 1])
        else:
            start = row-9
            j = 0
            for i in range(start,row):
                self.upside_lyrics_list[j].SetLabelText(self.current_lyrics_word_list[i])
                j += 1

    def set_downside_lyrics(self,row):
        if row+9 >= len(self.current_lyrics_word_list):
            j = 0
            for i in range(row+1, len(self.current_lyrics_word_list)):
                self.downside_lyrics_list[j].SetLabelText(self.current_lyrics_word_list[i])
                j += 1
        else:
            end = row+10
            j = 0
            for i in range(row+1, end):
                self.downside_lyrics_list[j].SetLabelText(self.current_lyrics_word_list[i])
                j += 1
                if j == 9:
                    return

    def get_mp3_cover(self, filepath):
        audio = File(filepath)
        cover = audio.tags['APIC:'].data
        write_path = filepath.split('\\')[0] + '\.tmp\cover.png'
        #filename = self.current_music_name+'.png'
        with open(write_path, 'wb') as img:
            img.write(cover)

    def get_flac_cover(self,filepath):
        audio = FLAC(filepath)
        pics = audio.pictures
        write_path = filepath.split('\\')[0] + '\.tmp\cover.png'
        for p in pics:
            if p.type == 3:  # front cover
                #print("\nfound front cover")
                with open(write_path, "wb") as img:
                    img.write(p.data)

    def update_total_music_time(self):
        showlength = time.strftime("%M:%S", time.gmtime(int(self.current_music_length)))
        play_slider_song_len = wx.StaticText(self, -1, f"/ {showlength}", pos=(1200, 628))
        play_slider_song_len.SetOwnForegroundColour((41, 36, 33))
        play_slider_song_len.Refresh()

    def updatemusicslider(self,evt):
        offest = int(self.music.get_pos()/1000)+self.settime
        self.play_slider.SetValue(offest)

    def onUpdateText(self,evt):
        #offset = int(self.music.get_pos()/1000)
        offset = self.play_slider.GetValue()
        #print('1')
        progress_text = time.strftime("%M:%S", time.gmtime(offset))
        #print(progress_text)
        self.progress.SetLabel(progress_text)
        self.play_slider.SetToolTip(f'当前播放进度 {progress_text}')

        #lyric_sync_thread = Thread(target=self.sync_lyrics())
        #lyric_sync_thread.start()
        #self.sync_lyrics()

    def createTimer(self):
        self.slider_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.updatemusicslider,self.slider_timer)
        self.slider_timer.Start(100)
        self.text_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onUpdateText,self.text_timer)

        self.sync_lyrics_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER,self.sync_lyrics,self.sync_lyrics_timer)
        self.sync_lyrics_timer.Start(100)

    def storgetimeleep(self,evt):
        obj = evt.GetEventObject()
        val = obj.GetValue()
        self.timeleeplist.append(val)

    def timer(self,evt):
        #if self.after_id is not None:
        #    self.after_cancel(self.after_id)
        #    self.after_id = None
        obj = evt.GetEventObject()
        val = obj.GetValue()
        #offset = self.play_slider.GetValue()
        #print(offset)
        #self.settime = 0
        self.settime = val
        self.timeleeplist.append(val)
        if len(self.timeleeplist) > 3:
            self.timeleeplist = self.timeleeplist[-3:]
        #print(offset)
        #self.music.stop()
        #self.music.play(loops=1, start=val)
        #print(self.timeleeplist)
        time.sleep(0.05)
        if abs(self.timeleeplist[-1]-self.timeleeplist[-2])>=2:
            #pygame.mixer.music.rewind()
            #self.music.set_pos(self.timeleeplist[-1])
            self.music.stop()
            self.music.play(loops=1, start=(self.timeleeplist[-1]))
            self.medium_row.SetLabel("* * * * * *")
            for i in range(len(self.upside_lyrics_list)):
                self.upside_lyrics_list[i].SetLabelText(' ')
            for i in range(len(self.downside_lyrics_list)):
                self.downside_lyrics_list[i].SetLabelText(' ')
            #self.timeleeplist = [0]

        #self.after_id = self.after(1000, self.timer)
        #evt.Skip()
        #self.music.set_pos(offset)

    def OnClose(self, evt):
        dlg = wx.MessageDialog(None, u'确定要关闭本窗口？', u'操作提示', wx.YES_NO | wx.ICON_QUESTION)
        if(dlg.ShowModal() == wx.ID_YES):
            self.music.stop()
            self.Destroy()


if __name__ == "__main__":
    app = wx.App()
    frame = MainFrame()
    frame.Show(True)
    app.MainLoop()
    wx.Exit()