import requests as req
import re
from io import StringIO
import numpy as np
import pandas as pd

# You can ignore these imports if you dont want visualization using plotly, 
# or you prefer to use other visualization packages such as matplotlib
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# URLs of groups, indices and historical data
STOCK_GRP_URL = "http://www.tsetmc.com/Loader.aspx?ParTree=111C1213"
STOCK_IND_URL = "http://www.tsetmc.com/Loader.aspx?ParTree=111C1417"
STOCK_DATA_URL = "http://www.tsetmc.com/tsev2/data/Export-txt.aspx?t=i&a=1&b=0&i={}"
class TSE:
    def __init__(self):
        self.styled_printer('Tehran Stock Exchange: Requesting groups...','i')
        self.groups_list = self.request_groups()
        self.styled_printer('Tehran Stock Exchange: Requesting List of all indices...','i')
        self.index_list = self.request_index_list()
        self.styled_printer('Tehran Stock Exchange: Ready.                           ','i')
        print()
    
    def styled_printer(self,msg,msg_type='error',end='\n\r'):
        # Print in a styled format
        # template: \x1b[ style;foreground_color;background_color m\x1b[0m
        # style in range(0,8), fg in range(30,38), bg in range(40,48)
        switcher = {
            'w':       "\x1b[1;37;43m{}\x1b[0m",
            'warning': "\x1b[1;37;43m{}\x1b[0m",
            'e':       "\x1b[0;37;41m{}\x1b[0m",
            'error':   "\x1b[0;37;41m{}\x1b[0m",
            'i':       "\x1b[0;37;44m{}\x1b[0m",
            'info':    "\x1b[0;37;44m{}\x1b[0m"}
        template = switcher.get(msg_type,'_{}_')
        print(template.format(msg),end=end)
    
    def request_groups(self):
        ls = []
        try:
            res = req.get(STOCK_GRP_URL)
            g = re.findall("<td>\d{2}|<td>.\d{1}",res.text)
            for group_id in g:
                ls.append(group_id)
        except Exception as e:
            print(str(e))
        return ls
            
    def request_index_list(self):
        ls = []
        try:
            res = req.get(STOCK_IND_URL)
            g = re.findall("<td><a href=.*ParTree=111C1412&inscode=.*</a></td>", res.text)
            cntr = 1
            for index_alias,index_name in zip(g[0::2],g[1::2]):
                index_id = re.findall("inscode=\d{14,}",index_alias)[0]
                index_id = index_id[8:]
                index_alias = re.findall("\"_blank\">.*</a>",index_alias)[0]
                index_alias = index_alias[9:-4]
                index_name = re.findall("\"_blank\">.*</a>",index_name)[0]
                index_name = index_name[9:-4]
                t = {'No':cntr,'index_id':index_id,
                    'index_alias': index_alias,
                    'index_name': index_name}
                     #'index_name': index_name.replace('\u200c',' ')}
                ls.append(t)
                cntr +=1
        except Exception as e:
            print(str(e))
        return ls
    
    def search_index_id(self,index_alias):
        if not self.index_list: 
            self.styled_printer('Inex list is not collected yet!','i')
            return None
        index_id = None
        for ind_ in self.index_list:
            if (index_alias in ind_['index_alias']) | (index_alias in ind_['index_name']):
                index_id = ind_['index_id']
                return index_id, ind_['index_name']
        if index_id is None:
            self.styled_printer('Index not found!','e')
            
        
    def get_index_data(self, index_id, from_date=None):
        # Index data provided by tsetmc.com are in csv format, so we use Pandas package to manage csv format
        try:
            res = req.get(STOCK_DATA_URL.format(index_id))
            df = pd.read_csv(StringIO(res.text),parse_dates=[1])
            if from_date is not None:
                df = df[df['<DTYYYYMMDD>']>from_date]
            return df
        except Exception as e:
            print(str(e))
    
    def candle_chart(self,S,title='Candle Chart'):
        # plot a candle chart using plotly
        fig = go.Figure()
        fig.update_layout(
            title='<b>'+title+'</b>',
            title_x=0.5,
            xaxis_title="Date",
            yaxis_title="Price",
            font=dict(
                family="Tahoma",
                size=14,
                color="#000000"
            )
        )
        fig.add_trace(go.Candlestick(x=S['<DTYYYYMMDD>'],
                open=S['<OPEN>'],
                high=S['<HIGH>'],
                low=S['<LOW>'],
                close=S['<CLOSE>']))
        #mx = np.max(S.loc[:,'<VOL>'])
        #fig.add_trace(go.Bar(x=S['<DTYYYYMMDD>'],y=df['<VOL>']/mx,name='Volume'))
        fig.show()
    
    def price_vol_chart(self,S,title='Price & Volume'):
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.update_layout(
            title='<b>'+title+'</b>',
            title_x=0.5,
            hovermode='closest',
            xaxis_title="Date",
            yaxis_title="Price",
            font=dict(
                family="Tahoma",
                size=12,
                color="#000000"
            )
        )
        fig.add_trace(go.Scatter(x=S['<DTYYYYMMDD>'],y=S['<CLOSE>'],name='Price'),secondary_y=False)
        fig.add_trace(go.Bar(x=S['<DTYYYYMMDD>'],y=S['<VOL>'],name='Volume'),secondary_y=True)
        #fig.update_yaxes(title_text="<b>primary</b> yaxis title", secondary_y=False)
        #fig.update_yaxes(title_text="<b>secondary</b> yaxis title", secondary_y=True)
        fig.show()


if __name__ = '__main__' :
    tse = TSE()
    index_id = tse.search_index_id('بن')
    data = tse.get_index_data(index_id, from_date='2019-1-1')
    print(data.head())
    tse.candle_chart(data)

