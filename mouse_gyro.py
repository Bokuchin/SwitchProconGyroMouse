#!/usr/bin/env python3

import os
import threading
import time
import random

# Re-connect USB Gadget device
os.system('echo > /sys/kernel/config/usb_gadget/procon/UDC')
os.system('ls /sys/class/udc > /sys/kernel/config/usb_gadget/procon/UDC')

time.sleep(0.5)

gadget = os.open('/dev/hidg0', os.O_RDWR | os.O_NONBLOCK)
procon = os.open('/dev/hidraw3', os.O_RDWR | os.O_NONBLOCK)
mouse  = os.open('/dev/hidraw2', os.O_RDWR | os.O_NONBLOCK)
mouse_int = bytes([0,0,0,0])
def mouse_input():
    global mouse_int
    while True:
        try:
            mouse_int = os.read(mouse, 128)
            #print('<<<', output_data.hex())
            #print(output_mouse.hex())
            #os.write(gadget, output_mouse)
        except BlockingIOError:
            pass
        except:
            os._exit(1)



def procon_input():
    while True:
        try:
            input_data = os.read(gadget, 128)
            #print('>>>', input_data.hex())
            os.write(procon, input_data)
        except BlockingIOError:
            pass
        except:
            os._exit(1)

def convert(ou_dt_i, mo_in_i, weight, reflect):
    mo_in_i = int.from_bytes(mo_in_i, byteorder='little', signed=True)
    ou_dt_i = int.from_bytes(ou_dt_i, byteorder='little', signed=True)
    if reflect == True:
        mo_in_i = mo_in_i * -1
        ou_dt_i = ou_dt_i * -1
    merged_gy = ou_dt_i + mo_in_i * weight
    if merged_gy > 32767:
        merged_gy = 32767
    elif merged_gy < -32768:
        merged_gy = -32768
    else:
        pass
    merged_gy = merged_gy.to_bytes(2, byteorder='little', signed=True)

    return merged_gy

def replace_mouse(output_data, mouse_int):
    #a = output_data[0:13]

    #mouse no click wo migi no button ni henkan
    ri_btn = 0
    if mouse_int[0] == 1:#hidari click
        ri_btn = 0x80#ZR button
    elif mouse_int[0] == 2:#migi click
        ri_btn = 0x40#R button
    elif mouse_int[0] == 4:#chuu click
        ri_btn = 0x08#A button
    ri_btn = (output_data[3] + ri_btn).to_bytes(1, byteorder='little')
    a = output_data[0:3] + ri_btn + output_data[4:13]

    #kasokudo sensor ni tekitou ni atai wo ire naito setsuzoku ga kireru
    if mouse_int[1] != 0:
        b = 127
    else:
        b=0
    if mouse_int[2] != 0:
        b = 127
    else:
        b = 0
    d = bytes([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
    ac0 = bytes([255]) if output_data[14] + b > 255 else bytes([output_data[14] + b])
    ac1 = bytes([255]) if output_data[16] + b > 255 else bytes([output_data[16] + b])
    ac2 = bytes([255]) if output_data[18] + b > 255 else bytes([output_data[18] + b])
    ac0_1 = bytes([255]) if output_data[26] + b > 255 else bytes([output_data[26] + b])
    ac1_1 = bytes([255]) if output_data[28] + b > 255 else bytes([output_data[28] + b])
    ac2_1 = bytes([255]) if output_data[30] + b > 255 else bytes([output_data[30] + b])
    ac0_2 = bytes([255]) if output_data[38] + b > 255 else bytes([output_data[38] + b])
    ac1_2 = bytes([255]) if output_data[40] + b > 255 else bytes([output_data[40] + b])
    ac2_2 = bytes([255]) if output_data[42] + b > 255 else bytes([output_data[42] + b])

    #mouse no ugoki wo gyro no ugoki ni henkan
    gy0_0 = convert(output_data[19:21], mouse_int[1:2], 250, False)#
    gy1_0 = convert(output_data[21:23], mouse_int[2:3], 250, False)#
    gy2_0 = convert(output_data[23:25], mouse_int[2:3], 0, False)#

    gy0_1 = convert(output_data[31:33], mouse_int[1:2], 250, False)#
    gy1_1 = convert(output_data[33:35], mouse_int[2:3], 250, False)#
    gy2_1 = convert(output_data[35:37], mouse_int[2:3], 0, False)#

    gy0_2 = convert(output_data[43:45], mouse_int[1:2], 250, False)#
    gy1_2 = convert(output_data[45:47], mouse_int[2:3], 250, False)#
    gy2_2 = convert(output_data[47:49], mouse_int[2:3], 0, False)#

    e = a+output_data[13:14]+ac0+output_data[15:16]+ac1+output_data[17:18]+ac2 \
        +gy0_0+gy1_0+gy2_0 \
        +output_data[25:26]+ac0_1+output_data[27:28]+ac1_1+output_data[29:30]+ac2_1 \
        +gy0_1+gy1_1+gy2_1 \
        +output_data[37:38]+ac0_2+output_data[39:40]+ac1_2+output_data[41:42]+ac2_2 \
        +gy0_2+gy1_2+gy2_2 \
        +d

    print(int.from_bytes(gy1_0, byteorder='little'))
    #print(mouse_int[1])
    return e

def procon_output():
    global mouse_int
    while True:
        try:
            output_data = os.read(procon, 128)
            #output_mouse = os.read(mouse, 128)
            #print('<<<', output_data.hex())
            #print(output_data)
            e = replace_mouse(output_data, mouse_int)
            #print(e.hex())
            os.write(gadget, e)#output_data
            mouse_int = bytes([0,0,0,0])
        except BlockingIOError:
            pass
        except Exception as g:
            print(type(g))
            print(g)
            os._exit(1)

threading.Thread(target=procon_input).start()
threading.Thread(target=procon_output).start()
threading.Thread(target=mouse_input).start()