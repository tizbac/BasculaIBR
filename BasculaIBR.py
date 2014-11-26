#*-* coding: utf-8 *-*
# Software per utilizzare le bascule di IBR e stamparne le pesate
# Copyright (C) 2014 Tiziano Bacocco
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of  MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.
import serial
import time
import threading
#['1021\x0303'] Azzeramento
#['10221\x0331'] Auto tara
#['10222@@@@@@\x0333'] Tara manuale , @ KG
#['10220\x0330'] Azzeramento tara
# Dopo SEP c'è un checksum calcolato con i byte del checksum e l'END messi a 0
DIVS = { "00" : 0.0001 , "01" : 0.0002 , "02" : 0.0005 , "03" : 0.001 , "04" : 0.002 , "05" : 0.005,
         "06" : 0.01 , "07" : 0.02 ,  "08" : 0.05 , "09" : 0.01, "10" : 0.02 , "11" : 0.05 , "12" : 0.1,
         "13" : 0.2, "14" : 0.5 , "15" : 1.0, "16" : 2.0, "17" : 5.0 , "18" : 10.0, "19" : 20.0,
         "20" : 50.0 }
START = "\x02"
END = "\x04"
SEP = "\x03"
FLAG1_NETTO = 1 << 0
FLAG1_UNK = 1 << 1
FLAG1_ZERO = 1 << 2
FLAG1_STABILE = 1 << 3
FLAG1_OFFRANGE = 1 << 4
FLAG1_UNDERLOAD = 1 << 5
FLAG1_OVERLOAD = 1 << 6
FLAG2_ZH = 1 << 3
FLAG2_ZL = 1 << 4
FLAG2_INSTABILE = 1 << 5
CHKSUMPLACEHOLDER = "\x00"*3
_WHITE = "\033[37;1m"
_NOFORM = "\033[0m"
_RED ="\033[31m"
_GREEN ="\033[32m"
class BasculaIBR:
  
  def __init__(self,porta,indirizzomaster=0,indirizzo=0):
    self.ser = serial.Serial(porta,9600,timeout=2)
    self.indirizzo = indirizzo
    self.indirizzomaster = indirizzomaster
    self.div = 1.0
    self.L = threading.Lock()
  def calcolaCheckSum(self,dati):
    num = 0
    d2 = list(dati)
    for c in dati:
      num ^= ord(c)
      num &= 0xff
    assert d2[len(dati)-3] == "\x00"
    assert d2[len(dati)-2] == "\x00"
    assert d2[len(dati)-1] == "\x00"
    
    d2[len(dati)-3] = "%X"%((num & 240) >> 4)
    d2[len(dati)-2] = "%X"%((num & 15))
    d2[len(dati)-1] = END
    
    return ''.join(d2)
    
  def recvdata(self):
    b = self.ser.read(1)
    if b == "":
      return ""
    assert (b == "\x02")
    b = self.ser.read(1)
    data =  ""
    while b != END:
      data += b
      b = self.ser.read(1)
    return data
  def connect(self):
    self.L.acquire()
    time.sleep(0.2)
    print _WHITE+"Inizializzazione bascula..."+_NOFORM
    self.ser.write(START+"p"+END)
    rec = self.recvdata()
    
    if rec != "\x06":
      print _RED+"Errore di inizializzazione, gia inizializzata"+str([rec])+_NOFORM
    else:
      time.sleep(0.3)
      self.ser.write(START+"c1"+END)
      rec = self.recvdata()
      if rec != "\x06":
        print _RED+"Errore di inizializzazione2,"+str([rec])+_NOFORM
        self.L.release()
        return
    time.sleep(1.0)
    #Richiesta configurazione
    print _GREEN+"Connessione stabilita"+_NOFORM
    print _WHITE+"Richiesta configurazione..."+_NOFORM
    self.ser.write(self.calcolaCheckSum(START+str(self.indirizzomaster)+str(self.indirizzo)+"01"+SEP+CHKSUMPLACEHOLDER))
    d = self.recvdata()
    print str([d])
    self.div = DIVS[d[22:24]]
    self.azzera()
    self.recvdata()
    print _GREEN+"Fatto, divisione: "+str(self.div)+_NOFORM
    time.sleep(0.5)
    self.L.release()
  def pesa(self):
    
    #6 : Peso netto , 0 : Peso lordo?
    self.L.acquire()
    #print "<PESA"
    self.ser.write(self.calcolaCheckSum(START+str(self.indirizzomaster)+str(self.indirizzo)+"26"+SEP+CHKSUMPLACEHOLDER))
    data = self.recvdata()
    if len(data) < 23+7:
      self.L.release()
      return {}
    ret = {}
    ret["batteria"] = data[7]
    flags1 = ord(data[4])
    flags2 = ord(data[5])
    ret["flags1"] = flags1
    ret["flags2"] = flags2
    if data[9] != "-":
      data2 = data[22:22+7]
    else:
      data2 = "-"+data[22:22+7]
    
    ret["peso"] = float(data2)*self.div 
    #print ">PESA"
    time.sleep(0.5)
    self.L.release()
    
    return ret
  def azzera(self):
    self.ser.write(self.calcolaCheckSum(START+str(self.indirizzomaster)+str(self.indirizzo)+"21"+SEP+CHKSUMPLACEHOLDER))
  def azzeraTara(self):
    self.L.acquire()
    d = START+str(self.indirizzomaster)+str(self.indirizzo)+"220"+SEP+CHKSUMPLACEHOLDER
    self.ser.write(self.calcolaCheckSum(d))
    data = self.recvdata()
    time.sleep(0.5)
    self.tara = 0.0
    self.L.release()
    
  def impostaTara(self,taraManuale=None):
    self.L.acquire()
    #print "<TARA"
    if taraManuale != None:
      d = START+str(self.indirizzomaster)+str(self.indirizzo)+"222"+("%06d"%(int(float(taraManuale)/self.div)))+SEP+CHKSUMPLACEHOLDER
      self.tara = float(taraManuale)
    else:
      d = START+str(self.indirizzomaster)+str(self.indirizzo)+"221"+SEP+CHKSUMPLACEHOLDER
    self.ser.write(self.calcolaCheckSum(d))
    data = self.recvdata()
    print str([data])
    if len(data) > 0:
      #print ">TARA"
      time.sleep(0.5)
      self.L.release()
      
      return taraManuale
    else:
      #print ">TARA"
      time.sleep(0.5)
      self.L.release()
      
      return "Errore"
    
  def end(self):
    self.L.acquire()
    self.ser.write(self.calcolaCheckSum(START+str(self.indirizzomaster)+str(self.indirizzo)+"13"+SEP+CHKSUMPLACEHOLDER))
    time.sleep(0.5)
    self.L.release()