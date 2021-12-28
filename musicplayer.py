import wx
import pygame
import os
import re
import time
from threading import Thread
import math
from mutagen import File
#from wx.media import MediaCtrl

APP_TITLE = u'音乐播放器'
MAX_LYRIC_ROW = 18
LYRIC_ROW_REG = '\[[0-9]{2}:[0-9]{2}.[0-9]{2,}\]'
MAX_MUSIC_NAME_LEN = 70  # 歌名展示的时候最长字符限制


class MainFrame(wx.Frame):
    '''程序主窗口类，继承自wx.Frame'''

    def __init__(self):
        '''构造函数'''
        # 播放器的整体属性
        self.width = 1280
        self.height = 720
        self.volume = 0.5
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
        # 初始化本地歌曲列表
        self.get_local_music_list()
        self.current_music_static_text = None  # 当前播放的音乐的名字

        # 按钮使用的图片
        self.play_bmp = wx.Image("resources/play1.png", wx.BITMAP_TYPE_PNG).Rescale(50, 50).ConvertToBitmap()
        self.stop_bmp = wx.Image("resources/stop.png", wx.BITMAP_TYPE_PNG).Rescale(50, 50).ConvertToBitmap()
        self.last_music_bpm = wx.Image("resources/last_music.png", wx.BITMAP_TYPE_PNG).Rescale(40, 40).ConvertToBitmap()
        self.next_music_bpm = wx.Image("resources/next_music.png", wx.BITMAP_TYPE_PNG).Rescale(40, 40).ConvertToBitmap()

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
        self.draw_music_lyric_panel()

        self.music_cover_panel = None
        self.draw_music_cover_panel()

        pygame.mixer.init()
        self.music = pygame.mixer.music
        self.SONG_FINISHED = pygame.USEREVENT + 1

    '''        # 下载音乐面板

        self.down_music_panel = None
        self.input_url_text_ctrl = None  # 输入的下载路径
        self.down_button = None  # 下载按钮
        self.draw_down_music_panel()'''

    def get_path_by_name(self, file_name):
        '''
        通过名称获取音乐的完整路径
        :return:
        '''
        return os.path.join(self.local_music_folder, file_name)

    def get_local_music_list(self):
        '''
        获取本地音乐列表
        :return:
        '''
        self.local_music_name_list.clear()  # 这一步必须有
        for local_music_file_name in os.listdir(self.local_music_folder):
            if local_music_file_name.endswith((".wav", ".flac", ".mp3")):
                self.local_music_name_list.append(local_music_file_name)

    def draw_navi_panel(self):
        # 导航栏所在的panel
        self.navi_panel = wx.Panel(self, id=-1, pos=(0, 0), size=(100, self.height - 100))
        # 本地音乐
        local_music_text = wx.StaticText(self.navi_panel, -1, "本地音乐", pos=(20, 20), style=wx.ALIGN_LEFT)
        local_music_text.SetOwnForegroundColour((41, 36, 33))

    def draw_music_list_panel(self):
        '''
        绘制音乐列表所在的panel
        :param draw:
        :param show:
        :return:
        '''
        # 重新计算本地音乐列表
        self.get_local_music_list()
        # 绘制面板整体
        if self.music_list_panel is not None:
            self.music_list_panel.Destroy()
        self.music_list_panel = wx.Panel(self, id=-1, pos=(150, 0), size=(350, self.height - 150))
        # 音乐列表
        local_music_num = len(self.local_music_name_list)
        for music_index in range(local_music_num):
            music_full_name = self.local_music_name_list[music_index].split('.')[0]
            if len(music_full_name) > MAX_MUSIC_NAME_LEN:
                music_full_name = music_full_name[0:MAX_MUSIC_NAME_LEN] + "..."
            music_text = wx.StaticText(self.music_list_panel, -1, music_full_name,
                                       pos=(0, music_index * 40 + 25), size=(270, 30), style=wx.ALIGN_LEFT)
            music_text.SetOwnForegroundColour((41, 36, 33))
            music_text.Refresh()  # 这句话不能少
            play_button = wx.BitmapButton(self.music_list_panel, -1, self.play_bmp, pos=(280, music_index * 40 + 20),
                                          size=(20, 20))
            play_button.Bind(wx.EVT_LEFT_DOWN, lambda e, index=music_index: self.play_index_music(index))

    def draw_play_music_panel(self):
        # 播放音乐所在的panel
        self.play_music_panel = wx.Panel(self, id=-1, pos=(0, self.height - 150), size=(self.width, 150))
        # 歌的名字
        self.current_music_static_text = wx.StaticText(self.play_music_panel, -1, "请选择歌曲", pos=(210, 0), size=(80, 30), style=wx.ALIGN_LEFT)
        self.current_music_static_text.SetOwnForegroundColour((41, 36, 33))

        last_music_button = wx.BitmapButton(self.play_music_panel, -1, self.last_music_bpm, pos=(260, 50), size=(40, 40))
        last_music_button.SetToolTip(u'上一首')

        self.play_stop_button = wx.BitmapButton(self.play_music_panel, -1, self.play_bmp,  pos=(320, 45), size=(50, 50))
        self.play_stop_button.SetToolTip(u'播放/暂停')

        next_music_button = wx.BitmapButton(self.play_music_panel, -1, self.next_music_bpm, pos=(390, 50), size=(40, 40))
        next_music_button.SetToolTip(u'下一首')
        # 调节音量的按钮
        self.volume_slider = wx.Slider(self.play_music_panel, -1, int(self.volume*100), 0, 100, pos=(490, 30), size=(-1, 80), style=wx.SL_VERTICAL|wx.SL_INVERSE)
        #self.volume_slider.SetToolTipString(u'音量:%d%%' %self.volume_slider.GetValue())
        play_slider = wx.Slider(self.play_music_panel, -1, pos=(550, 55), size=(600, -1))
        play_slider.SetToolTip(u'播放进度')
        # 上述按钮的监听器
        last_music_button.Bind(wx.EVT_LEFT_DOWN, self.play_last_music)
        self.play_stop_button.Bind(wx.EVT_LEFT_DOWN, self.play_stop_music)
        next_music_button.Bind(wx.EVT_LEFT_DOWN, self.play_next_music)
        self.volume_slider.Bind(wx.EVT_SLIDER, self.change_volume)
        self.volume_slider.Bind(wx.EVT_SCROLL, self.change_volume)
        #self.volume_slider.Bind(wx.EVT_SCROLL, self.ChangeVolume)

    def redraw_music_lyric_panel(self, start_index=0):
        # 隐藏之前的歌词的每一行
        for x in self.lyrcis_static_text:
            x.SetLabelText("")
            x.Refresh()

        # 获取歌词
        lyric_list = self.get_lyrics()
        # 展示歌词
        for lyric_index in range(start_index, start_index + MAX_LYRIC_ROW, 1):
            if lyric_index < len(lyric_list):
                lyric_relative_index = lyric_index - start_index
                lyric = lyric_list[lyric_index]
                self.lyrcis_static_text[lyric_relative_index].SetLabelText(lyric)
                self.lyrcis_static_text[lyric_relative_index].SetOwnForegroundColour((41, 36, 33))
                self.lyrcis_static_text[lyric_relative_index].Refresh()

    def draw_music_lyric_panel(self):
        '''
        歌词所在的面板的控制
        :return:
        '''
        self.music_lyric_panel = wx.Panel(self, id=-1, pos=(400, 10), size=(self.width - 400, self.height - 160))

        # 获取歌词
        lyric_list = self.get_lyrics()
        # 展示歌词
        for lyric_index in range(MAX_LYRIC_ROW):
            if lyric_index < len(lyric_list):
                lyric = lyric_list[lyric_index]
            else:
                lyric = ""
            lyric_row = wx.StaticText(self.music_lyric_panel, -1, lyric, pos=(250, 30 * lyric_index + 10),
                                  size=(400, -1), style=wx.ALIGN_CENTER)
            lyric_row.SetOwnForegroundColour((41, 36, 33))
            self.lyrcis_static_text.append(lyric_row)

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
        # step1：播放音乐
        self.music.play(loops=1, start=0.0)
        # step2：重写歌词面板
        self.redraw_music_lyric_panel()
        self.current_music_name = current_music_path.split('\\')[-1]
        if self.current_music_name.split('.')[-1] == 'mp3':
            self.get_music_cover(current_music_path)
            self.redraw_music_cover_panel(current_music_path)
        else:
            self.draw_music_cover_panel()
        # step3：开启新线程，追踪歌词
        self.display_lyric()
        self.current_music_state = 1
        self.play_stop_button.SetBitmap(self.stop_bmp)
        # 更改当前播放的音乐的名字
        current_music_name = self.local_music_name_list[self.current_music_index]
        namelist = current_music_name.split('.')
        if len(current_music_name) > MAX_MUSIC_NAME_LEN:
            current_music_name = current_music_name[0:MAX_MUSIC_NAME_LEN] + "..."
        self.current_music_static_text.SetLabelText(namelist[0])

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
                print("有音乐在播放，需要暂停")
                self.music.pause()
                self.current_music_state = 0
                self.play_stop_button.SetBitmap(self.play_bmp)
                self.IsPaused = True
                print(self.music.get_busy())
            else:  # 恢复暂停的音乐
                self.music.unpause()
                self.current_music_state = 1
                self.IsPaused = False
                self.play_stop_button.SetBitmap(self.stop_bmp)
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
        '''
        修改音量
        :param evt:
        :return:
        '''
        #self.setVolumeAndTip()
        #value = self.volume_slider.GetValue()
        obj = evt.GetEventObject()
        val = obj.GetValue()
        self.volume = float(val / 100)
        self.music.set_volume(self.volume)


    '''    def setVolumeAndTip(self):
        value = self.volume_slider.GetValue()
        self.volume = value/100.0
        if self.volume != 0:
            self.lastvolume = self.volume
        self.mc.SetVolume(self.volume)
        self.volume_slider.SetToolTipString(u'音量:%d%%' %value)'''

    def get_lyrics(self):
        '''
        读取歌词，不带时间标记
        :param lyrics_file_path:
        :return:
        '''
        current_lyric_path = self.get_lyric_path()
        if current_lyric_path is None or not os.path.exists(current_lyric_path):
            return ["暂无歌词"]
        with open(current_lyric_path, 'r', encoding="utf-8") as file_pointer:
            content_list = file_pointer.readlines()
        lyrics_list = []
        for content in content_list:
            if re.match(LYRIC_ROW_REG, content):
                # 找到]符号第一次出现的地方
                index_of_right_blank = content.index(']')
                lyric_clause = content.replace('\n', '')[index_of_right_blank + 1:]
                lyrics_list.append(lyric_clause)
        return lyrics_list

    def display_lyric(self):
        lyric_refersh_thread = Thread(target=self.refersh_lyrics)
        lyric_refersh_thread.start()

    def parse_lyrics(self):
        current_lyric_path = self.get_lyric_path()
        if current_lyric_path is None or not os.path.exists(current_lyric_path):
            content_list = ["[00:00.00]纯音乐或暂无歌词"]
        else:
            # 读文件内容
            with open(current_lyric_path, 'r', encoding="utf-8") as file_pointer:
                content_list = file_pointer.readlines()
        #标准化处理
        for i in range(len(content_list)):
            content_list[i] = content_list[i].replace('\n', '')
            if content_list[i].index(']') == 6:
                templist = content_list[i].split(']')
                templist[0] = templist[0][:6] + '.00'
                content_list[i] = ']'.join(templist)
            elif content_list[i].index(']') == 10:
                templist = content_list[i].split(']')
                templist[0] = templist[0][:9]
                content_list[i] = ']'.join(templist)
            else:
                continue
        lyrics_list = []
        for content in content_list:
            if re.match(LYRIC_ROW_REG, content):
                time_lyric = dict()
                start_time = float(content[1:3]) * 60 + float(content[4:6]) + float(content[7:9]) / 100
                index_of_right_blank = content.index(']')
                time_lyric[start_time] = content.replace('\n', '')[index_of_right_blank + 1:]
                lyrics_list.append(time_lyric)
        return lyrics_list

    def refersh_lyrics(self):
        '''
        刷新歌词子线程
        :return:
        '''
        lyrics_time_dict_list = self.parse_lyrics()
        relative_start_index = 0  # 相对起始歌词索引
        while self.music.get_busy():  # 播放中
            current_time = float(self.music.get_pos() / 1000)
            for lyric_index, lyrics_time_dict in enumerate(lyrics_time_dict_list):
                lyric_time = list(lyrics_time_dict.keys())[0]
                if math.fabs(lyric_time - current_time) < 0.8:
                    # 当歌词已经超过底部了，则刷新歌词面板，展示第二页的歌词
                    if lyric_index > 0 and lyric_index % MAX_LYRIC_ROW == 0:
                        relative_start_index = lyric_index
                        self.redraw_music_lyric_panel(start_index=relative_start_index)
                    self.lyrcis_static_text[lyric_index - relative_start_index].SetOwnForegroundColour((61, 89, 171))
                    self.lyrcis_static_text[lyric_index - relative_start_index].Refresh()
                    if (lyric_index - relative_start_index - 1) != -1 :
                        self.lyrcis_static_text[lyric_index - relative_start_index - 1].SetOwnForegroundColour((41, 36, 33))
                        self.lyrcis_static_text[lyric_index - relative_start_index - 1].Refresh()
                    else:
                        self.lyrcis_static_text[0].SetOwnForegroundColour((41, 36, 33))
                        self.lyrcis_static_text[0].Refresh()
                    break
            time.sleep(1)

    def get_music_cover(self, filepath):
        audio = File(filepath)
        cover = audio.tags['APIC:'].data
        write_path = filepath.split('\\')[0] + '\.tmp\cover.png'
        #filename = self.current_music_name+'.png'
        with open(write_path, 'wb') as img:
            img.write(cover)


if __name__ == "__main__":
    app = wx.App()
    frame = MainFrame()
    frame.Show(True)
    app.MainLoop()
    wx.Exit()