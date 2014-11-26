import serial
import sys
START = "\x02"
END = "\x04"
SEP = "\x03"
def recvdata(ser):
    b = ser.read(1)
    if b == "":
      return ""
    assert (b == "\x02")
    b = ser.read(1)
    data =  ""
    while b != END:
      data += b
      b = ser.read(1)
    return data


ser = serial.Serial(sys.argv[1],9600)

while True:
  data = recvdata(ser)
  if data == "p":
    ser.write("\x02\x06\x04")
  elif data == "c1":
    ser.write("\x02\x06\x04")
  elif data == "1026\x0304":
    ser.write(START+"0126\x98\x90\x800+000500+000000000000000000000\x0389"+END)
  elif data == "1001\x0301":
    ser.write(START+"0101050000000000000000192208000200000000000000000\xb4S\xb30702500\x0352"+END)
  else:
    print str([data])