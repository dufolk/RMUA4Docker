# 用于客户端功能类定义
import socket
import threading
import time
import json
import rospy
from sentry.msg import Position, Positions
from sys import argv

# 报文类型
MSG_TYPE = {
    "LOCATION": 0,
    "MESSAGE": 1,
    "SERVER_COMMAND": 2,
}

# 服务器IP和端口
SERVER_IP = "192.168.1.9"
#SERVER_IP = "192.168.1.5"
SERVER_PORT = 19999

color_id = {"RED1":0, "RED2":1, "BLUE1":2, "BLUE2":3}

# 用于封装报文    
def myencoder(data:str):
    # 生成一个data的校验位
    check = sum([ord(i) for i in data]) % 256
    # 将校验位转换为16进制
    check = str(hex(check))[-2:]
    data = data + check
    length = str(len(data)).zfill(4)
    data = length + data
    return data.encode('utf-8')

# 用于解析报文
def mydecoder(data:bytes):
    data = data.decode('utf-8')
    check = sum([ord(i) for i in data[:-2]]) % 256
    check = str(hex(check))[-2:]
    if check == data[-2:]:
        return data[:-2]
    else:
        return None

# 用于判断报文类型
def msg_type(msg:dict):
    if "from" in msg and "msg" in msg:
        if "to" in msg:
            return MSG_TYPE['SERVER_COMMAND']
        else:
            return MSG_TYPE['MESSAGE']
    else:
        return MSG_TYPE['LOCATION']
    

class ClientModel:
    def __init__(self, server_ip, server_port):
        self.server_host = server_ip
        self.server_port = server_port
    
    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.server_host, self.server_port))

    def send_message(self, msg:str):
        msg = myencoder(msg)
        self.sock.send(msg)

    def receive_message(self):
        data = self.sock.recv(1024)
        data = data.decode('utf-8')
        # print(data)


class RobotEntity(ClientModel):
    global_location = Positions()
    id_index = {}
    def __init__(self, server_ip, server_port, id:str):
        ClientModel.__init__(self, server_ip, server_port) 
        self.location = [0, 0, 0]
        if id in color_id.keys():
            self.id = color_id[id]
        else:
            raise Exception('Invalid client id')
        
        self.robot_connect()
        self.loc_sub = rospy.Subscriber('position', Position, self.loc_callback)
        self.gloc_pub = rospy.Publisher('global_position', Positions, queue_size=1)
        self.lock = threading.Lock()
        self.receive_thread = threading.Thread(target=self.recv_msg)
        self.receive_thread.setDaemon(True)
        self.receive_thread.start()
        self.sending_thread = threading.Thread(target=self.send_msg)
        self.sending_thread.setDaemon(True)
        self.sending_thread.start()

# 接收服务器发出的全局坐标
    def recv_msg(self):
        while True:
            try:
                msg_len = self.sock.recv(4).decode('utf-8')
                # print(msg_len)
                msg_len = int(msg_len)
                msg = mydecoder(self.sock.recv(msg_len))
                if msg == None:
                    continue
                self.task(json.loads(msg))  
            except Exception as e:
                print(e)
                continue

# 向服务器发送自身坐标   
    def send_msg(self):
        while True:
            try:
                loc_msg = {"id": self.id, "location": self.location}
                loc_msg = myencoder(json.dumps(loc_msg))
                self.lock.acquire()
                try:
                    self.sock.send(loc_msg)
                finally:
                    self.lock.release()
                time.sleep(0.1)
            except Exception as e:
                print(e)
                continue

    def robot_connect(self):
        self.connect()
        self.send_message(str(self.id))

    def loc_callback(self, msg):
        self.location = [msg.x, msg.y, msg.yaw]
        # print(self.location)

# 根据报文类型进行不同的处理
    def task(self, msg:dict):
        type = msg_type(msg)
        color_map = [-1, -2, 1, 2]
        # print(msg)
        if type == MSG_TYPE['LOCATION']:
            # print(msg)
            for k,v in msg.items():
                mapid = color_map[int(k)]
                if not mapid in RobotEntity.global_location.id:
                    RobotEntity.global_location.id.append(mapid)
                    RobotEntity.global_location.x.append(v[0]) 
                    RobotEntity.global_location.y.append(v[1])
                    RobotEntity.global_location.yaw.append(v[2])
                    RobotEntity.global_location.len += 1
                    RobotEntity.id_index[mapid] = len(RobotEntity.global_location.id) - 1
                else:
                    RobotEntity.global_location.x[RobotEntity.id_index[mapid]] = v[0]
                    RobotEntity.global_location.y[RobotEntity.id_index[mapid]] = v[1]
                    RobotEntity.global_location.yaw[RobotEntity.id_index[mapid]] = v[2]
            self.gloc_pub.publish(RobotEntity.global_location)

        # TODO: 用于根据报文类型进行不同的处理
        else:
            # print(msg)
            pass

# 向其他机器人发送消息
    def send2message(self, to:int, msg:str):
        msg2robo = {
            "from": str(self.id),
            "to": str(to),
            "msg": msg
        }

        msg2robo = myencoder(json.dumps(msg2robo))
        self.lock.acquire()
        try:
            self.sock.send(msg2robo)
        finally:
            self.lock.release()


client = RobotEntity(SERVER_IP, SERVER_PORT, argv[1])
rospy.init_node('client', anonymous=True)
try:
    rospy.spin()
    time.sleep(1)
except KeyboardInterrupt:
    client.sock.shutdown(socket.SHUT_RDWR)
    client.sock.close()
except Exception as e:
    print(e)
    client.sock.shutdown(socket.SHUT_RDWR)
    client.sock.close()
