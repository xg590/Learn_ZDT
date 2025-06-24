import socket, time
class MotorError(RuntimeError):
    def __init__(self, reply):
        self.reply = reply

class StepperMotor(object):
    def __init__(self, ip='192.168.1.200', port=4196, debug=False):
        self.debug = debug
        self.rs485_bus = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.rs485_bus.settimeout(3)
        self.rs485_bus.connect((ip, port))

    def __comm__(self, cmd, note='No Note', debug=False):
        addr, func = cmd[:2]
        self.rs485_bus.sendall(cmd)
        reply = self.rs485_bus.recv(4)
        if   bytearray([addr, func, 0x02, 0x6B]) == reply:
            print(f'[Receive : {addr}] Done') 
        elif bytearray([addr, func, 0x9F, 0x6B]) == reply:
            print(f'[Reached : {addr}]', note) 
        elif bytearray([addr, func, 0xE2, 0x6B]) == reply:
            print(f'[Receive : {addr}] Unable')
        elif bytearray([addr, 0x00, 0xEE, 0x6B]) == reply: 
            print(f'[Receive : {addr}] Error')
        else:
            if debug: print(f'[Debug]', [hex(i) for i in list(reply)])
            self.rs485_bus.settimeout(1)
            reply = self.rs485_bus.recv(999)
            self.rs485_bus.settimeout(3)
            raise MotorError(reply)

    def __enable__(self, addr=0x02, state='Enable', sync = 0x00):
        addr = addr
        func = 0xF3
        cmd  = bytearray((addr, func, 0xAB, {'Disable':0x00, 'Enable':0x01}[state], sync, 0x6B))

        self.__comm__(cmd)
    
    def __setID_Addr__(self, old_id=0x01, new_id=0x02):
        addr = old_id
        func = 0xAE
        save = 0x01
        cmd  = bytearray((addr, func, 0x4B, save, new_id, 0x6B))   
    
        self.__comm__(cmd)
    
    def __goSync__(self, addr=0x02):
        addr = addr
        func = 0xFF
        cmd  = bytearray((addr, func, 0x66, 0x6B))  
        
        self.__comm__(cmd) 

    def halt(self, addr=0x02, sync = 0x00):
        addr = addr
        func = 0xFE
        cmd  = bytearray((addr, func, 0x98, sync, 0x6B))
        
        self.__comm__(cmd) 
    
    def getHomingParameters(self, addr=0x02):
        addr = addr
        func = 0x22
        cmd  = bytearray((addr, func, 0x6B))

        self.rs485_bus.sendall(cmd)
        reply = self.rs485_bus.recv(18)
        if bytearray([addr, 0x22, 0xEE, 0x6B]) == reply[:4]:
            print('Error')
        else:
            O_Mode   = reply[ 2   ]
            O_Dir    = reply[ 3   ]
            O_Vel    = reply[ 4: 6]
            O_Tmo_Ms = reply[ 6:10]
            O_SL_Rpm = reply[10:12]
            O_SL_Ma  = reply[12:14]
            O_SL_Ms  = reply[14:16]
            O_POT_En = reply[16]
            chsm     = reply[17]
            print(f'''
回零模式 O_Mode            : { {0x00:'单圈就近回零 Nearest', 
                              0x01:'单圈方向回零 Dir', 
                              0x02:'多圈无限位碰撞回零 Senless', 
                              0x03:'多圈有限位开关回零 EndStop'}[O_Mode] }, 
回零方向                   : { {0x00:'顺时针 CW', 0x01:'逆时针 CCW'}[O_Dir] }
回零转速                   : {int.from_bytes(O_Vel)}RPM
回零超时时间                : {int.from_bytes(O_Tmo_Ms)/1000}s
无限位碰撞回零检测转速        : {int.from_bytes(O_SL_Rpm)}RPM
无限位碰撞回零检测电流        : {int.from_bytes(O_SL_Ma)}mA
无限位碰撞回零检测时间        : {int.from_bytes(O_SL_Ms)}ms
上电自动触发回零功能 O_POT_En : { {0x00:'不使能', 0x01:'使能'}[O_POT_En] } ''') 

    def setCurrentPositionAsOrigin(self, addr=0x02):
        addr = addr
        func = 0x0A
        cmd  = bytearray((addr, func, 0x6D, 0x6B))   
    
        self.__comm__(cmd)

    def getPulCnt(self, addr = 0x05):
        addr = addr
        func = 0x32
        cmd  = bytearray((addr, func, 0x6B))
        
        self.rs485_bus.sendall(cmd)
        reply = self.rs485_bus.recv(8)
        if bytearray([addr, 0x00, 0xEE, 0x6B]) == reply:
            print('Error')
            return None, None
        else:
            Dir = '+' if reply[2] else '-'
            pul_cnt = int.from_bytes(reply[3:7])
            print(Dir,  pul_cnt) 
            return Dir, pul_cnt

    # 切换开环/闭环模式
    def setP_Pul(self, addr=0x02, P_Pul='PUL_FOC'):
        addr = addr
        func = 0x46
        save = 0x01
        P_Pul = {'PUL_OFF' :0x00, '关闭脉冲输入端口': 0x00,
                 'PUL_OPEN':0x01, '开环':0x01,
                 'PUL_FOC' :0x02, '闭环':0x02,
                 'ESI_RCO' :0x03, 
                }[P_Pul]
        cmd  = bytearray((addr, func, 0x69, save, P_Pul, 0x6B))   
    
        self.__comm__(cmd)

    def getSettings(self, addr=0x02):
        addr = addr
        func = 0x42 
        cmd  = bytearray((addr, func, 0x6C, 0x6B))   
    
        self.rs485_bus.sendall(cmd)
        reply = self.rs485_bus.recv(33)
        if bytearray([addr, 0x00, 0xEE, 0x6B]) == reply[:4]:
            print('Error')
            return None
        else:
            _len     = reply[ 2]                           
            nParms   = reply[ 3]                        
            MotType  = reply[ 4]                 
            P_Pul    = reply[ 5]                     
            P_Serial = reply[ 6]                 
            En       = reply[ 7]    
            Dir      = reply[ 8]             
            MStep    = reply[ 9]        
            MPlyer   = reply[10]               
            AutoSSD  = reply[11]    
            Ma       = reply[12:14] 
            Ma_Limit = reply[14:16] 
            Op_Limit = reply[16:18] 
            UartBaud = reply[18]    
            CAN_Baud = reply[19]    
            ID_Addr  = reply[20]    
            Checksum = reply[21]
            # XOR from functools import reduce es = reduce(lambda x, y: x ^ y, cmd) 
            Response = reply[22]    
            Clog_Pro = reply[23]    
            Clog_Rpm = reply[24:26] 
            Clog_Ma  = reply[26:28] 
            Clog_Ms  = reply[28:30] 
            Err_Lmt  = reply[30:32]
            print(f'''
返回命令所包含的字节数      : {_len}
返回命令的配置参数个数      : {nParms}
电机类型                 : { {25:'每步1.8度', 50:'每步0.9度'}[MotType]}
脉冲端口控制模式 P_Pul     : {['PUL_OFF 关闭脉冲输入端口', 'PUL_OPEN 开环模式', 'PUL_FOC 矢量闭环', 'ESI_RCO 复用为限位输入和到位输出'][P_Pul]}
通讯协议                 : {['RxTx_OFF', 'ESI_ALO', 'UART/RS232/RS485', 'CAN'][P_Serial]}
En引脚的有效电平          : {['L', 'H', 'Hold'][En] }
Dir引脚的有效方向         : {['CW', 'CCW'][Dir] }
脉冲控制下的细分步数       : {MStep}细分
脉冲控制下的细分插补功能    : {MPlyer}
自动熄屏功能              : {['不自动熄屏', '自动熄屏'][AutoSSD] }
开环模式工作电流           : {int.from_bytes(Ma)} mA
闭环模式堵转时的最大电流    : {int.from_bytes(Ma_Limit)} mA
闭环模式最大输出电压       : {int.from_bytes(Op_Limit)} mV
串口波特率                : {['9600', '19200', '25000', '38400', '57600', '115200', '256000', '512000', '921600'][UartBaud]}
CAN 通讯速率             : {['10KHz','20KHz','50KHz','83333','100KHz','125KHz','250KHz','500KHz','800KHz','1MHz'][CAN_Baud]}
ID 地址（串口通用）        : {ID_Addr}
通讯校验方式              : {['0x6B', 'XOR', 'CRC-8', 'Modbus'][Checksum]}
控制命令应答 (到位应答)    : {['None', 'Receive', 'Reached', 'Both', 'Other'][Response]}
堵转保护功能              : {['Disable', 'Enable'][Clog_Pro]}
堵转保护转速阈值           : {int.from_bytes(Clog_Rpm)} rpm
堵转保护电流阈值           : {int.from_bytes(Clog_Ma)} mA
堵转保护检测时间阈值        : {int.from_bytes(Clog_Ms)} ms
位置到达窗口               : {int.from_bytes(Err_Lmt)/10} deg
每圈脉冲数                : { {25:200, 50:400}[MotType] * MStep }''')  #  {25: 360 /1.8, 50: 360 /0.9}
        return MotType, P_Pul, P_Serial, En, Dir, MStep, MPlyer, AutoSSD, Ma, \
               Ma_Limit, Op_Limit, UartBaud, CAN_Baud, ID_Addr, Checksum,     \
               Response, Clog_Pro, Clog_Rpm, Clog_Ma, Clog_Ms, Err_Lmt
        
    def getStatus(self, addr=0x02):
        addr = addr
        func = 0x43
        cmd  = bytearray((addr, func, 0x7A, 0x6B))   
    
        self.rs485_bus.sendall(cmd)
        reply = self.rs485_bus.recv(31)
        assert reply[30] == 0x6B
        if bytearray([addr, 0x00, 0xEE, 0x6B]) == reply[:4]:
            print('Error')
        elif bytearray([addr, func]) == reply[:2]:
            SS = {
                '返回命令所包含的字节数'  :                reply[2]                                ,
                '返回命令的配置参数个数'  :                reply[3]                                ,
                '总线电压(V)'           : int.from_bytes(reply[4:6]) // 100 / 10                 , 
                '总线相电流(mA)'        : int.from_bytes(reply[6:8])                              ,
                '校准后编码器值'         : int.from_bytes(reply[8:10])                             ,
                '电机目标位置'           : int.from_bytes(reply[10:15])                            ,
                '电机实时转速'           : int.from_bytes(reply[15:18])                            ,
                '电机实时位置'           : int.from_bytes(reply[18:23])                            ,
                '电机位置误差'           : int.from_bytes(reply[23:28])                            ,
                '编码器状态'             : '就绪'      if reply[28] >> 0 & 0b0001 else '未知'       ,
                '校准表状态'             : '就绪'      if reply[28] >> 1 & 0b0001 else '未知'       ,
                '回零状态'              : '在回零中'    if reply[28] >> 2 & 0b0001 else '不在回零中' ,
                '回零结果'              : '失败'       if reply[28] >> 3 & 0b0001 else '成功'      ,
                '电机使能状态'           : '使能'       if reply[29] & 0x01 else '失能'      ,
                '电机到位状态'           : '到位'       if reply[29] & 0x02 else '未到位'     ,
                '电机堵转状态'           : '堵转中'     if reply[29] & 0x04 else '不在堵转中'     ,
                '电机堵转保护状态'        : '已进入状态'  if reply[29] & 0x08 else '未进入状态' 
            }
            [print(k,v) for k, v in SS.items()] 
        # print(f'[getStatus]', [hex(i) for i in list(reply)]) 

    def setting(self, addr=0x02, Dir='CW'):
        addr = addr
        func = 0x48
        save = 0x01
        
        MotType  = ['每步1.8度','每步0.9度'].index('每步1.8度') 
        P_Pul    = ['PUL_OFF', 'PUL_OPEN', 'PUL_FOC', 'ESI_RCO'].index('ESI_RCO')
        P_Serial = ['RxTx_OFF', 'ESI_ALO', 'UART/RS232/RS485', 'CAN'].index('UART/RS232/RS485')
        En       = ['L', 'H', 'Hold'].index('Hold')
        Dir      = ['CW', 'CCW'].index(Dir)
        MStep    = 2**4 # 1、2、4、8、16、32、64、128、256  # 细分步数
        MPlyer   = ['Disable', 'Enable'].index('Enable') # 
        AutoSSD  = ['不自动熄屏', '自动熄屏'].index('不自动熄屏')
        Ma       = int(1000).to_bytes(length=2, byteorder='big')  
        Ma_Limit = int(1000).to_bytes(length=2, byteorder='big') # 闭环模式堵转时的最大电流 in milliampere
        Op_Limit = int(4000).to_bytes(length=2, byteorder='big') # 闭环模式最大输出压 in millivolt
        UartBaud = ['9600', '19200', '25000', '38400', '57600', '115200', '256000', '512000', '921600'].index('115200')
        CAN_Baud = ['10KHz', '20KHz', '50KHz', '83333', '100KHz', '125KHz', '250KHz', '500KHz', '800KHz', '1MHz'].index('500KHz') 
        ID_Addr  = 0x00 #
        Checksum = ['0x6B', 'XOR', 'CRC-8', 'Modbus'].index('0x6B')
        Response = ['None', 'Receive', 'Reached', 'Both', 'Other '].index('Other') # 电机使能也是控制动作命令，若设置为Reached，则使电机失能时不会收到电机应答，若设置为Other，则会收到应答。
        Clog_Pro = ['Disable', 'Enable'].index('Enable')
        Clog_Rpm = int(40     ).to_bytes(length=2, byteorder='big') # 堵转保护转速阈值 in RPM
        Clog_Ma  = int(2400   ).to_bytes(length=2, byteorder='big') # 堵转保护电流阈值 in milliampere
        Clog_Ms  = int(500    ).to_bytes(length=2, byteorder='big') # 堵转保护检测时间阈值 in millisecond
        Err_Lmt  = int(30     ).to_bytes(length=2, byteorder='big') # 位置到达窗口 in 0.1° (tenth degree)
        
        cmd  = bytearray((addr, func, 0xD1, save, MotType, P_Pul, P_Serial, En, Dir, MStep, MPlyer, AutoSSD)) + Ma + Ma_Limit + Op_Limit + bytearray((UartBaud, CAN_Baud, ID_Addr, Checksum, Response, Clog_Pro)) + Clog_Rpm + Clog_Ma + Clog_Ms + Err_Lmt + b'\x6B' 
        self.__comm__(cmd)

    def setHomingParameters(self, addr=0x02, O_Mode='限位开关回零', O_Dir='CW', O_Vel=30, O_Tmo_Ms = 100_000, O_POT_En='不使能'):
        addr = addr
        func = 0x4C 
        save = 0x01 
        O_Mode   = {'单圈就近回零': 0x00, 'Nearest': 0x00,
                    '单圈方向回零': 0x01, 
                    '碰撞回零': 0x02, 
                    '限位开关回零': 0x03, 'EndStop': 0x03} [O_Mode]
        O_Dir    = {'顺时针':0x00, 'CW':0x00, '逆时针':0x01, 'CCW':0x01} [O_Dir]
        O_Vel    = int(O_Vel   ).to_bytes(length=2, byteorder='big') # 回零转速 rpm
        O_Tmo_Ms = int(O_Tmo_Ms).to_bytes(length=4, byteorder='big') # 回零超时时间
        O_SL_Rpm = int(300     ).to_bytes(length=2, byteorder='big') # 无限位碰撞回零检测转速
        O_SL_Ma  = int(800     ).to_bytes(length=2, byteorder='big') 
        O_SL_Ms  = int(60      ).to_bytes(length=2, byteorder='big') 
        O_POT_En = {'不使能':0x00, '使能':0x01} [O_POT_En] # 使能上电自动触发回零功能
        cmd  = bytearray([addr, func, 0xAE, save, O_Mode, O_Dir]) + O_Vel + O_Tmo_Ms + O_SL_Rpm + O_SL_Ma + O_SL_Ms + bytearray((O_POT_En, 0x6B)) 
    
        self.__comm__(cmd)

    def setHomingZero(self):
        addr = 0x02
        func = 0x93
        save = 0x01
        cmd  = bytearray((addr, func, 0x88, save, 0x6B)) 
    
        self.__comm__(cmd)

    def homing(self, addr=0x02, O_Mode='限位开关回零', sync=0x00): # 触发回零, 并且所有数值归零。
        addr = addr
        func = 0x9A 
        O_Mode   = {'单圈就近回零': 0x00, # 在本圈内转到零点，就算本来角度是400度，单圈归零后角度也归零。
                    '单圈方向回零': 0x01, 
                    '碰撞回零'   : 0x02, 
                    '限位开关回零': 0x03} [O_Mode]  
        cmd  = bytearray((addr, func, O_Mode, sync, 0x6B))   
    
        self.__comm__(cmd)

    def quitHoming(self, addr=0x02, sync=0x00):
        addr = addr
        func = 0x9C 
        cmd  = bytearray((addr, func, 0x48, 0x6B))   
    
        self.__comm__(cmd)
        
    def deClog(self, addr=0x01):
        addr = addr
        func = 0x0E 
        cmd  = bytearray((addr, func, 0x52, 0x6B))   
    
        self.__comm__(cmd)

    def getPosition(self, addr = 0x05):
        addr = addr
        func = 0x36
        cmd  = bytearray((addr, func, 0x6B))
        
        self.rs485_bus.sendall(cmd)
        reply = self.rs485_bus.recv(8)
        if bytearray([addr, 0x00, 0xEE, 0x6B]) == reply:
            print('Error')
        else:
            Dir = '+' if reply[2] else '-'
            print(Dir, int.from_bytes(reply[3:7]) * 3200 / 0x1_00_00, int.from_bytes(reply[3:7]) ) 
            return Dir, int.from_bytes(reply[3:7]) * 3200 / 0x1_00_00

    def moveByPulseCount(self, addr=0x01, Dir='CW', velo=50, acc=0x01, pul_cnt=0, mode='A', kamikaze=False, note='No Note', debug=False):
        addr = addr
        func = 0xFD
        Dir  = {'CW': 0x00, 'CCW': 0x01} [Dir]
        velo = int(velo if velo < 0x1_00_00 else 1500).to_bytes(length=2, byteorder='big') 
        # t2-t1    = (256-acc) *   50  (us)，   Vt2 = Vt1 + 1(RPM)
        # deltaT   = (256-acc) / 20_000 (s), deltaV = 1/60   (RPS)
        # accInRPM = deltaV/deltaT = (20_000/60) / (256-acc) (Round per second per second)
        acc  = int(acc  if acc  < 0x1_00    else    1)
        pul_cnt = pul_cnt if pul_cnt > 0 else 0
        pul_cnt = int(pul_cnt if pul_cnt < 0x1_00_00_00_00 else 3200).to_bytes(length=4, byteorder='big') # 3200 is one round
        mode = {'R': 0x00, 'A': 0x01}[mode] # relative or absolute angle
        sync = 0x00
        chsm = 0x6B
    
        cmd  = bytearray((addr, func, Dir, 0x00, 0x00, acc, 0x00, 0x00, 0x00, 0x00, mode, sync, chsm))
        cmd[3: 5] = velo
        cmd[6:10] = pul_cnt
        
        if kamikaze:
            self.rs485_bus.settimeout(1)
            try:
                self.__comm__(cmd, note=note, debug=debug)
            except socket.timeout as e:
                print('kamikaze timeout')
                pass
            self.rs485_bus.settimeout(3)
        else:
            self.rs485_bus.settimeout(None)
            self.__comm__(cmd, note=note, debug=debug)
            self.rs485_bus.settimeout(3)