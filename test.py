import BasculaIBR
import time
b = BasculaIBR.BasculaIBR("/dev/ttyUSB0")

b.connect()

print b.pesa()
while True:
  time.sleep(1.0)
  print str([b.pesa()])

b.end()
