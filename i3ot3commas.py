from flask import (
    Flask,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
    json,
    send_file
)
import socket
from datetime import datetime
import time
import re
import requests
from collections import defaultdict
from amountManager import amountManager
from exchangeManager import exchangeManager
from telegramManager import telegramManager

class i3ot3commas:
    def __init__(self):
        self.config = self.read_config()

    def read_config(self):
        configFile = '../control/config.ini'
        #configFile = os.path.abspath('../control') + '/config.ini'
        oConfig = self.nested_dict(1,list)
        f = open(configFile, "r")
        for x in f:
            checkComment = re.match('^[#]', x.strip())
            if not checkComment and x.strip() != '':
                confDetails = x.strip().split('=')
                if len(confDetails) > 2 :                
                    j = 0
                    strData = ""
                    for item in confDetails :                                 
                        if j > 0:
                            if j == 1 :                            
                                strData = item
                            else :
                                strData = strData + "=" + item

                        j = j+1

                    oConfig[confDetails[0]] = strData            
                else:                
                    oConfig[confDetails[0]] = confDetails[1]
        return oConfig

    def nested_dict(self,n, type):
        if n == 1:
            return defaultdict(type)
        else:
            return defaultdict(lambda: nested_dict(n-1, type))

    def initialBot(self):
        self.config3commas={}
        configLocation = './'
        with open(configLocation + "3commas.json", "r") as fin:
            self.config3commas = json.load(fin)   

    def getTimeStamp(self):
        dateTimeObj = datetime.now()
        timestampStr = dateTimeObj.strftime('[%Y-%m-%d] %H:%M:%S.%f')[:-3] + " GMT +7"
        return timestampStr


api = Flask(__name__)


#trading for 3commas
@api.route('/trade_signal', methods=['GET', 'POST'])
def trade_signal():
    if request.method == 'POST':        
        #load all JSON from source
        json_request_data = request.get_json()
        print(json_request_data, flush=True)
        #Sample JSON  
        ###   {'owner': 'Knot', 'data': [{'side': 'buy', 'symbol': 'ALGOBTC', 'exchange': 'BINANCE'}]}

        #dump JSON after load
        dumpJson = json.dumps(json_request_data['data'])        

        msgIn = json.loads( dumpJson )        
        print(msgIn, flush=True)

        raw_msgBot = ({  
            "message_type": "bot",  
            "bot_id": 999999,  
            "email_token": "will be replaced by code",  
            "delay_seconds": 0,  
            "pair": "will be replaced by code"
        })
        
        msgBot = json.loads(json.dumps(raw_msgBot))

        #set end point for 3commas
        url = robot.config['3commas']
        rfq_details = {}

        # assign owner 
        owner = str(json_request_data['owner'])
        rfq_details['owner'] = str(json_request_data['owner'])

        #check direction
        if str(msgIn['side']).upper() == 'SELL' :
            print("Sell !!!", flush=True)
            msgBot['side'] = "sell"
            rfq_details['side'] = "sell"                                
            msgBot['action'] = "close_at_market_price"
        else :                
            print("Buy !!!", flush=True)
            msgBot['side'] = "buy"
            rfq_details['side'] = "buy"     


        if str(msgIn['exchange']).upper() == 'KUCOIN':
            print("KUCOIN", flush=True)
            if owner in robot.config3commas['owner'] :
                loadPairs = json.loads(json.dumps( robot.config3commas['pairs']['KUCOIN'] ))
                loadAmount = json.loads(json.dumps( robot.config3commas['owner'][owner]['amount']['KUCOIN'] ))
                ccyPair = str(loadPairs[ str(msgIn['symbol']) ])
                amount = str(loadAmount[ str(msgIn['symbol']) ])
                side = str(msgBot['side'])
                msgBot['pair'] = str(ccyPair)
        elif str(msgIn['exchange']).upper() == 'BINANCE':
            print("BINANCE", flush=True)
            #check user profiles            
            if owner in robot.config3commas['owner'] :                
                loadPairs = json.loads(json.dumps( robot.config3commas['pairs']['BINANCE'] ))
                loadAmount = json.loads(json.dumps( robot.config3commas['owner'][owner]['amount']['BINANCE'] ))
                ccyPair = str(loadPairs[ str(msgIn['symbol']) ])
                amount = str(loadAmount[ str(msgIn['symbol']) ])
                side = str(msgBot['side'])
                msgBot['pair'] = str(ccyPair)

        #prepare bot for send request
        msgBot['exchange'] = msgIn['exchange']
        msgBot['bot_id'] = robot.config3commas['owner'][owner]['credentials'][str(msgBot['exchange']).upper()]['BOT_ID']
        msgBot['email_token'] = robot.config3commas['owner'][owner]['credentials'][str(msgBot['exchange']).upper()]['EMAIL_TOKEN']        
        msgBot['timestamp'] = robot.getTimeStamp()              
        rfq_details['chat_id'] = json.loads(json.dumps( robot.config3commas['owner'][owner]['telegram']['chat_id'] ))
        r = requests.post(url, json = msgBot)

        if str(r.status_code) == '200':
            print("Place order COMPLETED !!!", flush=True)
        else:
            print("Place order FAILED !!!", flush=True)

        #send message service to Telegram
        tf = msgIn['tf']
        message_alert = "Signal: " +side.upper()+ " on " + msgIn['symbol'] + " exchange " + msgIn['exchange']
        message_alert = message_alert + " TimeFrame "+ tf +" !!!"
        data = {"type" : "individual",
                "token" : robot.config['telegram_token'],
                "chat_id" : rfq_details['chat_id'],
                "message" : message_alert
                }        
        msgService = json.dumps( data )
        messageService = telegramManager()
        messageService.send_alert_message(msgService)  
        
        print(msgBot, flush=True)
        return request.method, 201

    else :
        print("false")
        return request.method, 404


#default route is 404
@api.route('/', methods=['GET', 'POST'])
def root_randing():

    return request.method, 404


if __name__ == '__main__':
    #create obj robot
    robot = i3ot3commas()
    robot.initialBot()

    hostname = robot.config['domainName']
    remoteServerIP = str(socket.gethostbyname(hostname))
    api.run(host=remoteServerIP, port=8080)
    
