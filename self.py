import wx

APP_TITLE = u'音乐播放器'

class MainFrame(wx.Frame):
    def __init__(self):
        self.width = 1920
        self.height = 1080
        wx.Frame.__init__(self, None, APP_TITLE)
        self.SetSize(self.width, self.height)
        self.SetBackgroundColour((248, 248, 255))
