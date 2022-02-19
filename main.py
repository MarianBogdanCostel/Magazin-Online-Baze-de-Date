import sys
import cx_Oracle
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import QDate
from PyQt5.QtGui import QPixmap, QFont, QStandardItemModel
from PyQt5.QtWidgets import QDialog, QApplication, QTableWidgetItem, QPushButton, QHeaderView, QTextEdit, QInputDialog, \
    QMessageBox, QDialogButtonBox, QLineEdit, QFormLayout, QDateEdit, QLabel, QGridLayout
from PyQt5.uic import loadUi
from sortedcontainers import SortedList
from collections import defaultdict
from PyQt5.Qt import Qt


con = cx_Oracle.connect("bd072", "bd072", "bd-dc.cs.tuiasi.ro:1539/orcl")
username = ''

def printErrorMessage(text):
    msg = QMessageBox()
    msg.setWindowTitle("Eroare!")
    msg.setText(text)
    msg.setIcon(QMessageBox.Critical)
    msg.exec_()


class Login(QDialog):
    def __init__(self):
        super(Login,self).__init__()
        loadUi("login.ui", self)
        self.loginbutton.clicked.connect(self.loginfunction)
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.createaccbutton.clicked.connect(self.gotocreate)


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            self.loginfunction()

    def loginfunction(self):
       global username

       user=self.username.text()
       password=self.password.text()

       if user == 'admin' and password == 'admin':
           self.gotoadmin()
           return

       cur = con.cursor()
       cur.execute("select id_client from clienti where nume_utilizator = \'{}\' and parola = \'{}\'".format(user, password))
       rez = cur.fetchall()
       if len(rez) > 0:
           print("Successfully logged in with username: ", user, "and password:", password)
           username = user
           self.gotomagazin()
       else:
           printErrorMessage('Ati introdus gresit username sau parola!\nVerificati daca aveti un cont')
           print("Failed login, please retry")
       cur.close()

    def gotocreate(self):
        createacc=CreateAcc()
        widget.addWidget(createacc)
        widget.setCurrentIndex(widget.currentIndex()+1)

    def gotomagazin(self):
        magazin=Magazin()
        widget.addWidget(magazin)
        widget.setCurrentIndex(widget.currentIndex()+1)

    def gotoadmin(self):
        admin = Administrator()
        widget.addWidget(admin)
        widget.setCurrentIndex(widget.currentIndex()+1)

class CreateAcc(QDialog):
    def __init__(self):
        super(CreateAcc,self).__init__()
        loadUi("createacc.ui",self)
        self.signupbutton.clicked.connect(self.createaccfunction)
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.confirmpass.setEchoMode(QtWidgets.QLineEdit.Password)
        self.back_btn.clicked.connect(self.backtologin)

    def createaccfunction(self):
        if self.password.text()==self.confirmpass.text():
            nume = self.nume.text()
            prenume = self.prenume.text()
            email = self.email.text()
            username = self.username.text()
            password = self.password.text()

            cur = con.cursor()
            try:
                cur.execute("insert into clienti(nume, prenume, email, nume_utilizator, parola)\
                         values (\'{}\', \'{}\', \'{}\', \'{}\', \'{}\')"\
                        .format(nume, prenume, email, username, password))
                cur.execute("commit")
            except cx_Oracle.DatabaseError as exc:
                error, = exc.args
                print("Oracle-Error-Code:", error.code)
                print("Oracle-Error-Message:", error.message)
                printErrorMessage(str(error.message) +"\nAti introdus gresit un camp!\nConstrangerile la campuri sunt:\n"
                            +"Nume,Prenume,Username minim 3 caractere\n"
                            +"Email: [a-z0-9._%-]+@[a-z0-9._%-]+\.[a-z]{2,4}\n"
                            +"Parola minim 7 caractere\n")
                self.nume.clear()
                self.prenume.clear()
                self.email.clear()
                self.username.clear()
                self.password.clear()
                self.confirmpass.clear()
            else:
                login=Login()
                widget.addWidget(login)
                widget.setCurrentIndex(widget.currentIndex()+1)

            cur.close()
        else:
            msg = QMessageBox()
            msg.setWindowTitle("Parola gresita!")
            msg.setText("Parolele nu coincid")
            x = msg.exec_()

    def backtologin(self):
        login = Login()
        widget.addWidget(login)
        widget.setCurrentIndex(widget.currentIndex() + 1)

class Magazin(QDialog):

    def __init__(self):
        index = 0
        super(Magazin,self).__init__()
        self.cos_cumparaturi = defaultdict()
        self.prettotal = 0
        loadUi("magazin.ui",self)

        self.anulare_btn.setStyleSheet("background-color : red")
        self.anulare_btn.setFont(QFont('MS Shell Dlg 2', 14))
        self.anulare_btn.clicked.connect(self.emptyfunction)

        self.comanda_btn.setStyleSheet("background-color : green")
        self.comanda_btn.setFont(QFont('MS Shell Dlg 2', 14))
        self.comanda_btn.clicked.connect(self.orderfunction)

        self.logout_btn.setStyleSheet("background-color : gray")
        self.logout_btn.setFont(QFont('MS Shell Dlg 2', 12))
        self.logout_btn.clicked.connect(self.gotologin)

        self.refresh_btn.setStyleSheet("background-color : cyan")
        self.refresh_btn.setFont(QFont('MS Shell Dlg 2', 12))
        self.refresh_btn.clicked.connect(self.refreshfunction)


        self.user_name.setText(username)
        self.user_name.setStyleSheet("font-weight: bold")
        self.user_name.setFont(QFont('MS Shell Dlg 2', 14))


        self.table.horizontalHeader().setFont(QFont('MS Shell Dlg 2', 16))
        self.table.setRowCount(50)
        self.table.setColumnWidth(0, 300)
        self.table.setColumnWidth(1, 600)
        self.table.setColumnWidth(2, 75)
        self.table.setColumnWidth(3, 125)

        self.cos.setRowCount(50)
        self.cos.setColumnWidth(0, 300)
        self.cos.setColumnWidth(1, 130)
        self.cos.setColumnWidth(2, 130)

        cur = con.cursor()
        cur.execute("select prod.nume_produs, prod.descriere, prod.pret, magazin.cantitate_disponibila from produs prod, magazin where prod.id_produs = magazin.id_produs")
        produse = cur.fetchall()

        for produs in produse:
            btn = QPushButton()
            btn.setText('BUY')
            self.table.setItem(index, 0, QTableWidgetItem(produs[0]))
            self.table.setItem(index, 1, QTableWidgetItem(produs[1]))
            self.table.setItem(index, 2, QTableWidgetItem(str(produs[2])))
            self.table.setItem(index, 3, QTableWidgetItem(str(produs[3])))
            self.table.setCellWidget(index, 4, btn)
            btn.clicked.connect(self.buyfunction)
            index += 1


        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.show()
        self.table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)

        self.cos.horizontalHeader().setStretchLastSection(True)
        self.cos.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.cos.show()

    def buyfunction(self):
        #aflare care buton a fost apasat
        button = self.sender()
        index = self.table.indexAt(button.pos())
        product_name = self.table.item(index.row(), 0).text()
        pret = int(self.table.item(index.row(), 2).text())

        if index.isValid():
            cantitate_disponibila = int(self.table.item(index.row(), 3).text())
            if product_name in self.cos_cumparaturi:
                if cantitate_disponibila > self.cos_cumparaturi[product_name]:
                    self.cos_cumparaturi[product_name] += 1
                    self.prettotal += pret
            else:
                if cantitate_disponibila > 0:
                    self.cos_cumparaturi[product_name] = 1
                    self.prettotal += pret

            #print(self.prettotal)
            self.display_cos()


    def removefunction(self):
        button = self.sender()
        index = self.cos.indexAt(button.pos())
        product_name = self.cos.item(index.row(), 0).text()
        self.cos_cumparaturi[product_name] -= 1

        if self.cos_cumparaturi[product_name] == 0:
            self.cos_cumparaturi.pop(product_name)

        if len(self.cos_cumparaturi) == 0:
            self.emptyfunction()

        self.display_cos()

    def display_cos(self):
        index = 0
        self.cos.clear()

        for produs, cantitate in self.cos_cumparaturi.items():
            btn = QPushButton()
            btn.setText('REMOVE')
            self.cos.setItem(index, 0, QTableWidgetItem(produs))
            self.cos.setItem(index, 1, QTableWidgetItem(str(cantitate)))
            self.cos.setCellWidget(index, 2, btn)
            btn.clicked.connect(self.removefunction)
            index += 1

        self.labelpret.setText(str(self.prettotal))
        self.labelpret.setStyleSheet("font-weight: bold")
        self.labelpret.setFont(QFont('MS Shell Dlg 2', 14))

    def emptyfunction(self):
        self.cos_cumparaturi.clear()
        self.cos.clear()
        self.labelpret.clear()
        self.prettotal = 0

    def orderfunction(self):
        if len(self.cos_cumparaturi) == 0:
            printErrorMessage("Cos gol\nNu puteti plasa o comanda!")
            return

        dialog = InputDialogComanda()
        if dialog.exec():
            adresa, data = dialog.getInputs()
            if not adresa or not data:
                printErrorMessage('Adresa si data sunt obligatorii!')
            else:
                cur = con.cursor()
                queries = []
                queries.append(
                    "insert into comenzi(id_client, adresa_livrare, data_comanda) values (find_id_by_username(\'{}\'), \'{}\', \'{}\')".format(
                        username, adresa, data))

                for produs, cantitate in self.cos_cumparaturi.items():
                    queries.append("insert into tipuri_produse(id_comanda, id_produs, cantitate) \
                                                values (comenzi_id_comanda_seq.currval, \
                                                (select id_produs from produs where nume_produs = \'{}\'), {})" \
                                   .format(produs, cantitate))
                con.begin()

                try:
                    for query in queries:
                        cur.execute(query)
                except cx_Oracle.DatabaseError as exc:
                    error, = exc.args
                    print("Oracle-Error-Code:", error.code)
                    print("Oracle-Error-Message:", error.message)
                    printErrorMessage(str(error.message))
                else:
                    self.refreshfunction()
                    con.commit()
                    self.emptyfunction()
                    self.refreshfunction()
                    msg = QMessageBox()
                    msg.setWindowTitle("Multumim")
                    msg.setText("Va multumim pentru comanda!")
                    x = msg.exec_()
                cur.close()


    def refreshfunction(self):
        index = 0

        self.table.clear()
        self.table.setHorizontalHeaderLabels(['Nume produs', 'Descriere', 'Pret', 'Cantitate',''])
        self.table.horizontalHeader().setFont(QFont('MS Shell Dlg 2', 16))

        cur = con.cursor()
        cur.execute(
            "select prod.nume_produs, prod.descriere, prod.pret, magazin.cantitate_disponibila from produs prod, magazin where prod.id_produs = magazin.id_produs")
        produse = cur.fetchall()

        for produs in produse:
            btn = QPushButton()
            btn.setText('BUY')
            self.table.setItem(index, 0, QTableWidgetItem(produs[0]))
            self.table.setItem(index, 1, QTableWidgetItem(produs[1]))
            self.table.setItem(index, 2, QTableWidgetItem(str(produs[2])))
            self.table.setItem(index, 3, QTableWidgetItem(str(produs[3])))
            self.table.setCellWidget(index, 4, btn)
            btn.clicked.connect(self.buyfunction)
            index += 1

    def gotologin(self):
        self.emptyfunction()
        login = Login()
        widget.addWidget(login)
        widget.setCurrentIndex(widget.currentIndex() + 1)

class InputDialogComanda(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.first = QLineEdit(self)
        self.second = QLineEdit(self)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        layout = QFormLayout(self)
        layout.addRow("Adresa", self.first)
        layout.addRow("Data", self.second)
        layout.addWidget(buttonBox)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

    def getInputs(self):
        return (self.first.text(), self.second.text())

class InputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.first = QLineEdit(self)
        self.second = QLineEdit(self)
        self.third = QLineEdit(self)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        layout = QFormLayout(self)
        layout.addRow("Cantitate", self.first)
        layout.addRow("Pret achizitie", self.second)
        layout.addRow("Data achizitie (DD-Mon-YYYY)", self.third)
        layout.addWidget(buttonBox)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

    def getInputs(self):
        return (self.first.text(), self.second.text(), self.third.text())


class Istoric(QDialog):
    def __init__(self):
        super(Istoric,self).__init__()
        loadUi("istoric.ui",self)
        self.close_btn.clicked.connect(self.backtoadmin)
        self.refresh_btn.clicked.connect(self.refreshfunc)
        self.intrari.setHorizontalHeaderLabels(['Nume', 'Cantitate', 'Pret achizitie', 'Data achizitiei', 'Schimba data','Schimba cantitatea'])
        self.intrari.resizeColumnsToContents()
        self.intrari.horizontalHeader().setFont(QFont('MS Shell Dlg 2', 13))

        self.iesiri.setHorizontalHeaderLabels(['Nume produs', 'ID comanda', 'Cantitate', 'Data comanda', 'Schimba data','Schimba cantitate'])
        self.iesiri.resizeColumnsToContents()
        self.iesiri.horizontalHeader().setFont(QFont('MS Shell Dlg 2', 13))

        self.intrari.setRowCount(50)
        self.intrari.setColumnWidth(0, 150)
        self.intrari.setColumnWidth(1, 100)
        self.intrari.setColumnWidth(2, 140)
        self.intrari.setColumnWidth(3, 150)

        self.iesiri.setRowCount(50)
        self.iesiri.setColumnWidth(0, 150)
        self.iesiri.setColumnWidth(1, 100)
        self.iesiri.setColumnWidth(2, 140)
        self.iesiri.setColumnWidth(3, 150)


        self.printentries()
        self.printsales()

    def printentries(self):
        index = 0
        cur = con.cursor()
        cur.execute(
            "select * from aprovizionari")
        intrari = cur.fetchall()

        cur2 = con.cursor()
        cur2.execute(
            "select prod.nume_produs from produs prod, aprovizionari where prod.id_produs = aprovizionari.id_produs")
        produse = cur2.fetchall()

        for intrare in intrari:
            self.intrari.setItem(index, 0, QTableWidgetItem(produse[index][0]))
            btn_data = QPushButton()
            btn_data.setText('Data')
            btn_data.setStyleSheet("background-color : green")
            btn_data.setFont(QFont('MS Shell Dlg 2', 12))

            btn_cantitate = QPushButton()
            btn_cantitate.setText('Cantitate')
            btn_cantitate.setStyleSheet("background-color : yellow")
            btn_cantitate.setFont(QFont('MS Shell Dlg 2', 12))

            #self.intrari.setItem(index, 0, QTableWidgetItem(str(intrare[0])))
            self.intrari.setItem(index, 1, QTableWidgetItem(str(intrare[1])))
            self.intrari.setItem(index, 2, QTableWidgetItem(str(intrare[2])))
            self.intrari.setItem(index, 3, QTableWidgetItem(str(intrare[3])))

            self.intrari.setCellWidget(index, 4, btn_data)
            self.intrari.setCellWidget(index, 5, btn_cantitate)

            self.intrari.setColumnWidth(4, 140)
            self.intrari.setColumnWidth(5, 150)

            btn_data.clicked.connect(self.changeEntryDate)
            btn_cantitate.clicked.connect(self.changeEntryCantitate)
            index += 1

        self.intrari.horizontalHeader().setStretchLastSection(True)
        self.intrari.show()
        self.intrari.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)

    def changeEntryDate(self):
        date, ok = QInputDialog.getText(self, 'Introduceti data', 'Introduceti data achizitiei\nFormatul este: DD-Mon-YY')
        button = self.sender()
        index = self.intrari.indexAt(button.pos())
        nume_produs = self.intrari.item(index.row(), 0).text()

        if ok:
            cur = con.cursor()
            try:
                cur.execute(
                    "update aprovizionari set data_aprovizionare = \'{}\' where id_produs = \
                    (select id_produs from produs where nume_produs = \'{}\')".format(date, nume_produs))
            except cx_Oracle.DatabaseError as exc:
                error, = exc.args
                printErrorMessage(error.message)
            else:
                con.commit()
                self.refreshfunc()


    def changeEntryCantitate(self):
        cantitate, ok = QInputDialog.getText(self, 'Introduceti cantitatea', 'Introduceti noua cantitate')
        button = self.sender()
        index = self.intrari.indexAt(button.pos())
        nume_produs = self.intrari.item(index.row(), 0).text()

        if ok:
            cur = con.cursor()
            try:
                cur.execute(
                    "update aprovizionari set cantitate = {} where id_produs = \
                    (select id_produs from produs where nume_produs = \'{}\')".format(cantitate, nume_produs))
            except cx_Oracle.DatabaseError as exc:
                error, = exc.args
                printErrorMessage(error.message)
            else:
                con.commit()
                self.refreshfunc()



    def printsales(self):
        index = 0
        cur = con.cursor()
        try:
            cur.execute(
                "select prod.nume_produs, tp.id_comanda, tp.cantitate, comenzi.data_comanda from tipuri_produse tp, produs prod, comenzi\
                 where tp.id_produs = prod.id_produs and tp.id_comanda = comenzi.id_comanda")
        except cx_Oracle.DatabaseError as exc:
            error, = exc.args
            print("Oracle-Error-Code:", error.code)
            print("Oracle-Error-Message:", error.message)
        else:
            comenzi = cur.fetchall()


        for comanda in comenzi:
            btn_data = QPushButton()
            btn_data.setText('Data')
            btn_data.setStyleSheet("background-color : green")
            btn_data.setFont(QFont('MS Shell Dlg 2', 12))

            btn_cantitate = QPushButton()
            btn_cantitate.setText('Cantitate')
            btn_cantitate.setStyleSheet("background-color : yellow")
            btn_cantitate.setFont(QFont('MS Shell Dlg 2', 12))

            self.iesiri.setItem(index, 0, QTableWidgetItem(str(comanda[0])))
            self.iesiri.setItem(index, 1, QTableWidgetItem(str(comanda[1])))
            self.iesiri.setItem(index, 2, QTableWidgetItem(str(comanda[2])))
            self.iesiri.setItem(index, 3, QTableWidgetItem(str(comanda[3])))

            self.iesiri.setCellWidget(index, 4, btn_data)
            self.iesiri.setCellWidget(index, 5, btn_cantitate)

            self.iesiri.setColumnWidth(3, 150)
            self.iesiri.setColumnWidth(4, 150)

            btn_data.clicked.connect(self.changeSaleDate)
            btn_cantitate.clicked.connect(self.changeSaleCantitate)

            index += 1

        self.iesiri.horizontalHeader().setStretchLastSection(True)
        self.iesiri.show()
        self.iesiri.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)

    def changeSaleDate(self):
        date, ok = QInputDialog.getText(self, 'Introduceti data', 'Introduceti data achizitiei\nFormatul este: DD-Mon-YY')
        button = self.sender()
        index = self.iesiri.indexAt(button.pos())
        id_comanda = int(self.iesiri.item(index.row(), 1).text())

        if ok:
            cur = con.cursor()
            try:
                cur.execute(
                    "update comenzi set data_comanda = \'{}\' where id_comanda = {}".format(date, id_comanda))
            except cx_Oracle.DatabaseError as exc:
                error, = exc.args
                printErrorMessage(error.message)
            else:
                con.commit()
                self.refreshfunc()

    def changeSaleCantitate(self):
        cantitate, ok = QInputDialog.getText(self, 'Introduceti cantitatea', 'Introduceti noua cantitate')
        button = self.sender()
        index = self.iesiri.indexAt(button.pos())
        id_comanda = int(self.iesiri.item(index.row(), 1).text())

        if ok:
            cur = con.cursor()
            try:
                cur.execute(
                    "update tipuri_produse set cantitate = {} where id_comanda = {}".format(cantitate, id_comanda))
            except cx_Oracle.DatabaseError as exc:
                error, = exc.args
                printErrorMessage(error.message)
            else:
                con.commit()
                self.refreshfunc()

    def refreshfunc(self):
        self.printsales()
        self.printentries()
        self.intrari.setHorizontalHeaderLabels(['Nume', 'Cantitate', 'Pret achizitie', 'Data achizitiei', 'Schimba data', 'Schimba cantitatea'])
        self.iesiri.setHorizontalHeaderLabels(['Nume produs', 'ID comanda', 'Cantitate', 'Data comanda', 'Schimba data', 'Schimba cantitate'])

    def backtoadmin(self):
        admin = Administrator()
        widget.addWidget(admin)
        widget.setCurrentIndex(widget.currentIndex()+1)


class Administrator(QDialog):

    def __init__(self):
        cur = con.cursor()
        cur.execute("savepoint before_modifications")
        cur.close()

        super(Administrator, self).__init__()
        loadUi("administrator.ui", self)

        self.refresh_btn.setStyleSheet("background-color : cyan")
        self.refresh_btn.setFont(QFont('MS Shell Dlg 2', 12))
        self.refresh_btn.clicked.connect(self.refreshfunction)

        self.logout_btn.setStyleSheet("background-color : gray")
        self.logout_btn.setFont(QFont('MS Shell Dlg 2', 12))
        self.logout_btn.clicked.connect(self.gotologin)

        self.add_btn.setStyleSheet("background-color : cyan")
        self.add_btn.setFont(QFont('MS Shell Dlg 2', 12))
        self.add_btn.clicked.connect(self.addfunction)

        self.btn_istoric.setStyleSheet("background-color : yellow")
        self.btn_istoric.setFont(QFont('MS Shell Dlg 2', 16))
        self.btn_istoric.clicked.connect(self.istoric)

        self.luna.currentIndexChanged.connect(self.profitPerLunaFunc)
        self.table.setHorizontalHeaderLabels(['Nume produs', 'Descriere', 'Pret', 'Intrari', 'Iesiri', 'Stoc', 'Aprovizionare', 'Elimina produs', 'Modifica pret'])

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setFont(QFont('MS Shell Dlg 2', 16))
        self.table.setRowCount(50)
        self.table.setColumnWidth(0, 250)
        self.table.setColumnWidth(1, 550)
        self.table.setColumnWidth(2, 50)
        self.table.setColumnWidth(3, 50)
        self.table.setColumnWidth(4, 50)
        self.table.setColumnWidth(5, 50)
        self.table.setColumnWidth(6, 110)
        self.table.setColumnWidth(7, 130)
        self.table.setColumnWidth(8, 110)

        self.printProducts()
        self.printStatistics()

    def printProducts(self):
        index = 0
        cur = con.cursor()
        cur.execute("select prod.nume_produs, prod.descriere, prod.pret, magazin.intrari, magazin.iesiri, magazin.cantitate_disponibila from produs prod, magazin where prod.id_produs = magazin.id_produs")
        produse = cur.fetchall()

        for produs in produse:
            btn_aprovizionare = QPushButton()
            btn_aprovizionare.setText('Aprovizionare')
            btn_aprovizionare.setStyleSheet("background-color : green")
            btn_aprovizionare.setFont(QFont('MS Shell Dlg 2', 12))

            btn_stergere = QPushButton()
            btn_stergere.setText('X')
            btn_stergere.setStyleSheet("background-color : red")
            btn_stergere.setFont(QFont('MS Shell Dlg 2', 12))

            btn_pret = QPushButton()
            btn_pret.setText('PRET')
            btn_pret.setStyleSheet("background-color : gray")
            btn_pret.setFont(QFont('MS Shell Dlg 2', 12))


            self.table.setItem(index, 0, QTableWidgetItem(produs[0]))
            self.table.setItem(index, 1, QTableWidgetItem(produs[1]))
            self.table.setItem(index, 2, QTableWidgetItem(str(produs[2])))
            self.table.setItem(index, 3, QTableWidgetItem(str(produs[3])))
            self.table.setItem(index, 4, QTableWidgetItem(str(produs[4])))
            self.table.setItem(index, 5, QTableWidgetItem(str(produs[5])))
            self.table.setCellWidget(index, 6, btn_aprovizionare)
            self.table.setCellWidget(index, 7, btn_stergere)
            self.table.setCellWidget(index, 8, btn_pret)

            btn_aprovizionare.clicked.connect(self.aprovizionarefunction)
            btn_stergere.clicked.connect(self.stergerefunction)
            btn_pret.clicked.connect(self.modificapret)
            index += 1

        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.show()
        self.table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)

    def profitPerLunaFunc(self):
        luna = self.luna.currentIndex() + 1

        cur = con.cursor()
        cur.execute("select sum(pret) from comenzi where to_number(to_char(data_comanda, 'MM')) = {}".format(luna))

        profit_luna = cur.fetchone()[0]
        self.profit_lunar.setText(str(profit_luna))

        cur.close()

    def printStatistics(self):
        cur = con.cursor()

        #calcul totaluri
        cur.execute("select total_investit, total_vandut, profit_brut, profit_net from venituri")
        total_investit, total_vandut, profit_brut, profit_net = cur.fetchone()

        #calcul profit per luna selectata
        luna = self.luna.currentIndex() + 1
        cur.execute("select sum(pret) from comenzi where to_number(to_char(data_comanda, 'MM')) = {}".format(luna))
        profit_luna = cur.fetchone()[0]

        #calcul cel mai vandut produs
        cur.execute("with rezumat_produse as (\
                        select produs.id_produs, sum(tipuri_produse.cantitate) as cantitate_vanduta\
                        from produs, tipuri_produse\
                        where produs.id_produs = tipuri_produse.id_produs\
                        group by produs.id_produs)\
                    select produs.nume_produs, rez_prod.cantitate_vanduta\
                    from produs, rezumat_produse rez_prod\
                    where produs.id_produs = rez_prod.id_produs\
                    and rez_prod.cantitate_vanduta = ( select max(cantitate_vanduta) from rezumat_produse )")
        cel_mai_vandut_produs, cantitate_vanduta = cur.fetchone()

        #calcul produs cu cel mai mare venit
        cur.execute("with rezumat_produse as (\
                        select produs.id_produs, sum(tipuri_produse.cantitate*produs.pret) as venit_produs\
                        from produs, tipuri_produse\
                        where produs.id_produs = tipuri_produse.id_produs\
                        group by produs.id_produs)\
                    select produs.nume_produs, rez_prod.venit_produs\
                    from produs, rezumat_produse rez_prod\
                    where produs.id_produs = rez_prod.id_produs\
                    and rez_prod.venit_produs = ( select max(venit_produs) from rezumat_produse)")
        cel_mai_profitabil_produs, total_venit = cur.fetchone()

        #calcul client cu cele mai multe comenzi
        cur.execute("with rezumat_clienti as (\
                        select clienti.id_client, count(comenzi.id_comanda) as nr_comenzi\
                        from clienti, comenzi\
                        where clienti.id_client = comenzi.id_client\
                        group by clienti.id_client)\
                    select clienti.nume, clienti.prenume, rezumat_clienti.nr_comenzi\
                    from clienti, rezumat_clienti\
                    where clienti.id_client = rezumat_clienti.id_client\
                    and rezumat_clienti.nr_comenzi = (select max(nr_comenzi) from rezumat_clienti)")
        best_client_nume, best_client_prenume, total_comenzi = cur.fetchone()

        #afisare statistici
        self.investit.setText(str(total_investit))
        self.vandut.setText(str(total_vandut))
        self.brut.setText(str(profit_brut))
        self.net.setText(str(profit_net))

        self.profit_lunar.setText(str(profit_luna))
        self.cel_mai_vandut_produs.setText(str(cel_mai_vandut_produs + " : " + str(cantitate_vanduta) + " buc"))
        self.cel_mai_profitabil.setText(str(cel_mai_profitabil_produs + " : " + str(total_venit)))
        self.best_client.setText(str(best_client_nume + " " + best_client_prenume + " : " + str(total_comenzi) + " comenzi"))

    def aprovizionarefunction(self):
        button = self.sender()
        index = self.table.indexAt(button.pos())
        nume_produs = self.table.item(index.row(), 0).text()

        dialog = InputDialog()
        if dialog.exec():
            cantitate, pret_achizitie, data_achizitie = dialog.getInputs()
            if not cantitate or not pret_achizitie:
                printErrorMessage('Cantitatea si pretul de achizitie sunt obligatorii!')
            elif not cantitate.isdigit() or not pret_achizitie.isdigit():
                printErrorMessage("Campurile introduse trebuie sa contina doar cifre!")
            else:
                cur = con.cursor()
                con.begin()
                query = "insert into aprovizionari(id_produs, cantitate, pret_achizitie, data_aprovizionare)\
                        values ((select id_produs from produs where nume_produs = \'{}\'), {}, {}, \'{}\')"\
                        .format(nume_produs, cantitate, pret_achizitie, data_achizitie)
                try:
                    cur.execute(query)
                except cx_Oracle.DatabaseError as exc:
                    error, = exc.args
                    print("Oracle-Error-Code:", error.code)
                    print("Oracle-Error-Message:", error.message)
                    printErrorMessage(str(error.message))
                else:
                    pass
                    #con.commit()
                cur.close()
                self.refreshfunction()

    def stergerefunction(self):
        button = self.sender()
        index = self.table.indexAt(button.pos())
        nume_produs = self.table.item(index.row(), 0).text()

        query1 = "delete from magazin where id_produs = (select id_produs from produs where nume_produs = \'{}\')".format(nume_produs)
        query2 = "delete from tipuri_produse where id_produs = (select id_produs from produs where nume_produs = \'{}\')".format(nume_produs)
        query3 = "delete from aprovizionari where id_produs = (select id_produs from produs where nume_produs = \'{}\')".format(nume_produs)
        query4 = "delete from produs where nume_produs = \'{}\'".format(nume_produs)

        cur = con.cursor()
        con.begin()

        try:
            cur.execute(query1)
            cur.execute(query2)
            cur.execute(query3)
            cur.execute(query4)
        except cx_Oracle.DatabaseError as exc:
            error, = exc.args
            print("Oracle-Error-Code:", error.code)
            print("Oracle-Error-Message:", error.message)
            printErrorMessage(str(error.message))
        else:
            #con.commit()
            cur.close()
            self.refreshfunction()

    def modificapret(self):
        pret, ok = QInputDialog.getText(self, 'Modificare pret', 'Introduceti pretul nou')
        if ok:
            button = self.sender()
            index = self.table.indexAt(button.pos())
            nume_produs = self.table.item(index.row(), 0).text()

            query = "update produs set pret = {} where nume_produs = \'{}\'".format(pret, nume_produs)

            cur = con.cursor()
            con.begin()

            try:
                cur.execute(query)
            except cx_Oracle.DatabaseError as exc:
                error, = exc.args
                print("Oracle-Error-Code:", error.code)
                print("Oracle-Error-Message:", error.message)
                printErrorMessage(str(error.message+'\nPretul trebuie sa contina doar cifre!'))
            else:
                #con.commit()
                self.refreshfunction()
            cur.close()


    def refreshfunction(self):
        self.table.clear()
        self.table.setHorizontalHeaderLabels(
            ['Nume produs', 'Descriere', 'Pret', 'Intrari', 'Iesiri', 'Stoc', 'Aprovizionare', 'Elimina produs','Modifica pret'])
        self.table.horizontalHeader().setFont(QFont('MS Shell Dlg 2', 16))
        self.printProducts()
        self.printStatistics()
        self.nume_produs.clear()
        self.descriere.clear()
        self.pret.clear()

    def gotologin(self):
        reply = QMessageBox.question(self,'Quit','Doriti sa salvati modificarile facute?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:

            cur = con.cursor()
            cur.execute("commit")
            cur.close()

        if reply == QMessageBox.No:
            cur = con.cursor()
            cur.execute("rollback to before_modifications")
            cur.close()

        login = Login()
        widget.addWidget(login)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def istoric(self):
        reply = QMessageBox.question(self, 'Quit', 'Doriti sa salvati modificarile facute?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            cur = con.cursor()
            cur.execute("commit")
            cur.close()

        if reply == QMessageBox.No:
            cur = con.cursor()
            cur.execute("rollback to before_modifications")
            cur.close()

        istoric = Istoric()
        widget.addWidget(istoric)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def addfunction(self):
        nume_produs = self.nume_produs.text()
        descriere = self.descriere.toPlainText()
        pret = self.pret.text()

        if not nume_produs or not pret:
            printErrorMessage("Campurile Nume Produs si Pret sunt obligatorii!")
            self.nume_produs.clear()
            self.pret.clear()
        elif not pret.isdigit():
            printErrorMessage("Pretul trebuie sa contina doar cifre!")
            self.nume_produs.clear()
            self.pret.clear()
        else:
            query1 = "insert into produs(nume_produs, descriere, pret) values (\'{}\', \'{}\', {})"\
                     .format(nume_produs, descriere, pret)
            query2 = "insert into magazin(id_produs) values (produs_id_produs_seq.currval)"

            cur = con.cursor()
            con.begin()

            try:
                cur.execute(query1)
                cur.execute(query2)
            except cx_Oracle.DatabaseError as exc:
                error, = exc.args
                print("Oracle-Error-Code:", error.code)
                print("Oracle-Error-Message:", error.message)
                printErrorMessage(str(error.message))
            else:
                #con.commit()
                self.refreshfunction()
            cur.close()



if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainwindow = Login()
    widget = QtWidgets.QStackedWidget()
    widget.addWidget(mainwindow)
    widget.setFixedWidth(1920)
    widget.setFixedHeight(1080)
    widget.setWindowTitle("Baze de date")
    widget.show()
    app.exec_()
