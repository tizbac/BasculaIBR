#!/usr/bin/python
# -*- coding: utf-8 -*-
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
from PyQt4 import QtGui, QtCore
import sys
import BasculaIBR
import time

basc = BasculaIBR.BasculaIBR("/dev/ttyUSB0")
class BasculaThread(QtCore.QThread):
  def __init__(self, MW,lblpesoout, lbltaraout, Bascula):
    QtCore.QThread.__init__(self)
    self.lblpesoout = lblpesoout
    self.lbltaraout = lbltaraout
    self.Bascula = Bascula
    self.Bascula.connect()
    self.MW = MW
  def run(self):
    while True:
      time.sleep(0.1)
      p = self.Bascula.pesa()
      if len(p) < 1:
        continue
      self.lblpesoout.setText(str(p["peso"]-self.MW.tara)+" Kg")
      self.MW.last = p["peso"]
      pal = self.lblpesoout.palette()
      
      if p["flags1"] & BasculaIBR.FLAG1_OFFRANGE:
        self.lblpesoout.setText("Fuori scala!")
      if p["flags1"] & BasculaIBR.FLAG1_UNDERLOAD:
        self.lblpesoout.setText("Sottocarico!")
      if p["flags1"] & BasculaIBR.FLAG1_OVERLOAD:
        self.lblpesoout.setText("Sovraccarico!")
      if p["flags1"] & BasculaIBR.FLAG1_STABILE:
        pal.setColor(QtGui.QPalette.Foreground,QtCore.Qt.red)
        self.MW.btTara.setEnabled(True)
      else:
        pal.setColor(QtGui.QPalette.Foreground,QtCore.Qt.gray)
        self.MW.btTara.setEnabled(False)
      self.lblpesoout.setPalette(pal)
      
      
      
class ImpostaTaraThread(QtCore.QThread):
  def __init__(self, Bascula,tarabt,lbltara, tara=None):
    QtCore.QThread.__init__(self)
    self.tara = tara
    self.Bascula = Bascula
    self.tarabt = tarabt
    self.lbltara = lbltara
  def run(self):
    self.tarabt.setEnabled(False)
    
    self.lbltara.setText(str(self.Bascula.impostaTara(float(self.tara) if self.tara != None else None)))
    
    
    self.tarabt.setEnabled(True)

class BasculaGUI(QtGui.QWidget):
  def __init__(self):
    super(BasculaGUI,self).__init__()
    self.tara = 0.0
    self.last = 0.0
    
    self.resize(800,600)
    self.setWindowTitle("Bascula")
    
    vbox1 = QtGui.QVBoxLayout()#Container principale
    hbox1 = QtGui.QHBoxLayout()
    vbox1.addLayout(hbox1)

    lblpeso = QtGui.QLabel(self)
    lblpeso.setText("Peso Netto:")
    lblpeso.setStyleSheet("font-size: 32pt")
    hbox1.addWidget(lblpeso)

    self.lblpesoout = QtGui.QLabel(self)
    self.lblpesoout.setText("------ Kg")
    self.lblpesoout.setStyleSheet("font-size: 72pt; border: 2px solid; background-color: #000000; color: #ff0000;qproperty-alignment: AlignRight;")
    hbox1.addWidget(self.lblpesoout)

    self.editor = QtGui.QTextEdit()
    self.editor.setStyleSheet("font-size: 30pt;")



    hbox2 = QtGui.QHBoxLayout()
    vbox1.addLayout(hbox2)

    lbltara = QtGui.QLabel(self)
    lbltara.setText("Tara:")
    lbltara.setStyleSheet("font-size: 32pt")
    hbox2.addWidget(lbltara)

    self.lbltaraout = QtGui.QLabel(self)
    self.lbltaraout.setText("%0.1f Kg"%self.tara)
    self.lbltaraout.setStyleSheet("font-size: 72pt; border: 2px solid; background-color: #000000; color: #ff0000;qproperty-alignment: AlignRight;")
    hbox2.addWidget(self.lbltaraout)

    vbox1.addStretch()

    hbox3 = QtGui.QHBoxLayout()
    self.btAzzera = QtGui.QPushButton(self)
    self.btAzzera.setStyleSheet("font-size: 45pt;")
    self.btAzzera.setText("Azzera tara")
    hbox3.addWidget(self.btAzzera)
    self.btTaraManuale = QtGui.QPushButton(self)
    self.btTaraManuale.setStyleSheet("font-size: 45pt;")
    self.btTaraManuale.setText("Tara manuale")
    hbox3.addWidget(self.btTaraManuale)
    self.btTara = QtGui.QPushButton(self)
    self.btTara.setStyleSheet("font-size: 45pt;")
    self.btTara.setText("Tara")
    hbox3.addWidget(self.btTara)
    self.btStampa = QtGui.QPushButton(self)
    self.btStampa.setStyleSheet("font-size: 45pt;")
    self.btStampa.setText("Stampa")
    hbox3.addWidget(self.btStampa)
    vbox1.addLayout(hbox3)
    self.btTaraManuale.clicked.connect(self.taraManualeClick)
    self.btTara.clicked.connect(self.taraClick)
    self.btAzzera.clicked.connect(self.azzeraClick)
    self.btStampa.clicked.connect(self.stampa)
    self.setLayout(vbox1)
    basc.azzeraTara()
    self.bt = BasculaThread(self,self.lblpesoout,self.lbltaraout,basc)
    self.bt.start()
  def azzeraClick(self):
    self.tara = 0.0
    self.lbltaraout.setText("%0.1f Kg"%self.tara)
  def taraManualeClick(self):
    val , ok = QtGui.QInputDialog.getInt(self,"","Inserisci tara",0,0,1000000,int(basc.div))
    if ok:
      self.tara = float(val)
      self.lbltaraout.setText("%0.1f Kg"%self.tara)
  def taraClick(self):
    self.tara = self.last
    self.lbltaraout.setText("%0.1f Kg"%self.tara)
  def stampa(self):
    data = QtCore.QDateTime.currentDateTime().toString()
    self.editor.setPlainText("Data: "+data+"\nPeso lordo: "+str(self.last)+" Kg \nTara: "+str(self.lbltaraout.text())+"\nPeso netto: "+str(self.lblpesoout.text()))
    dialog = QtGui.QPrintDialog()
    if dialog.exec_() == QtGui.QDialog.Accepted:
      self.editor.document().print_(dialog.printer())


app = QtGui.QApplication(sys.argv)
w = BasculaGUI()
w.show()


sys.exit(app.exec_())