import wx


class mainFrame(wx.Frame):
    '''程序主窗口类，继承自wx.Frame'''

    def __init__(self):
        '''构造函数'''
        # 播放器的整体属性
        self.width = 1280
        self.height = 780
        wx.Frame.__init__(self, None, -1, "播放器")
        self.SetSize(self.width, self.height)

        # 定义一个面板（panel），self表示它的父组件是主界面，-1是面板的id，size表示面板的大小
        # pos表示面板的位置
        panel = wx.Panel(self, -1, size=(200, 200), pos=(50, 35))
        # 定义一个按钮，它的父组件是panel，就是说它在panel上
        # id是-1，上面的文字是“Panel里边“
        wx.Button(panel, -1, 'Panel里边', size=(100, 100), pos=(10, 10))
        # 定义一个按钮，它的父组件是主界面（self），就是说它在主界面上
        # id是-1，上面的文字是“Frame里边“
        wx.Button(self, -1, 'Frame里边')


app = wx.App()
frame = mainFrame()
frame.Show()
app.MainLoop()
