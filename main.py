#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import math

import cPickle as pickle
from hcluster import pdist, linkage, dendrogram
import matplotlib.pyplot as plt

from form import *
from numpy import *


# ------------------------------------------------

# class of main form
class Form (QtGui.QWidget, Ui_Form):

    # variables
    rowsN    = 0
    ptsArr   = []
    clasters = []
    
    # ------------------------------------------------    

    # default constructor
    def __init__ (self):
        QtGui.QWidget.__init__(self)
        Ui_Form.setupUi(self, self)

        self.addPushButton.clicked.connect(self.insertRow)
        self.delPushButton.clicked.connect(self.deleteRow)
        self.countPushButton.clicked.connect(self.count)
        self.savePushButton.clicked.connect(self.save)
        self.loadPushButton.clicked.connect(self.load)

    # ------------------------------------------------

    # adds a row in the end of table
    def insertRow(self):
        size = self.pointsTableWidget.rowCount()
        self.pointsTableWidget.insertRow(size)

    # ------------------------------------------------

    # remove current row
    def deleteRow(self):
        curRow = self.pointsTableWidget.currentRow()
        self.pointsTableWidget.removeRow(curRow)

    # ------------------------------------------------

    # making calculations
    def count(self):
        self.rowsN = self.pointsTableWidget.rowCount()
        self.ptsArr = [[0.0, 0.0] for i in range(self.rowsN)]
        for i in range(self.rowsN):
            for j in range(2):
                item = self.pointsTableWidget.item(i,j)
                if not item :
                    title = QtGui.QApplication.translate("self", "Ошибка", None, QtGui.QApplication.UnicodeUTF8)
                    text  = QtGui.QApplication.translate("self", "Заполните все поля или удалите ненужные", None, QtGui.QApplication.UnicodeUTF8)
                    QtGui.QMessageBox.about(self, title, text)
                    return
                self.ptsArr[i][j] = self.pointsTableWidget.item(i,j).text().toDouble()[0]

        self.clasters = []

        options = { 0 : self.mSerial,
                    1 : self.mKing,
                    2 : self.mKMiddle,
                    3 : self.mTrout,
                    4 : self.mCrab}
        case = self.methodsComboBox.currentIndex()
        options[case]()


    # ------------------------------------------------

    # serial clasterisation
    def mSerial (self):

        y = pdist(self.ptsArr)
        z = linkage(y)
        dendrogram(z)
        plt.show()

    # ------------------------------------------------

    # King
    def mKing (self):

        label = QtGui.QApplication.translate("self", "Введите пороговое расстояние: ", None, QtGui.QApplication.UnicodeUTF8)
        limit = QtGui.QInputDialog.getDouble(self, 'Limit', label)
        if not limit[1]:
            return
        limit = limit[0]

        distMatrix = [[0.0 for i in range(self.rowsN)] for i in range(self.rowsN)]
        freePointsIndexes = [i for i in range(self.rowsN)]
        nonFreePointsIndexes = []
        edges = []
        clastersIndexes = []

        # make table
        for i in range(self.rowsN):
            for j in range(self.rowsN):
                distMatrix[i][j] = (self.ptsArr[i][0] - self.ptsArr[j][0])**2 + \
                (self.ptsArr[i][1] - self.ptsArr[j][1])**2

        while freePointsIndexes != []:

            # special situation
            if len(freePointsIndexes) == 1:
                clastersIndexes.append([])
                curClaster = len(clastersIndexes) - 1
                clastersIndexes[curClaster].append(freePointsIndexes[0])
                break

            # initial minimum
            pt1MinIndex = freePointsIndexes[0]
            pt2MinIndex = freePointsIndexes[1]
            for i in range(self.rowsN):
                for j in range(self.rowsN):
                    if i in freePointsIndexes and j in freePointsIndexes:
                        if i != j:
                            if distMatrix[i][j] < distMatrix[pt1MinIndex][pt2MinIndex]:
                                pt1MinIndex = i
                                pt2MinIndex = j

            clastersIndexes.append([])
            curClaster = len(clastersIndexes) - 1
            clastersIndexes[curClaster].append(pt1MinIndex)
            freePointsIndexes.remove(pt1MinIndex)

            if distMatrix[pt1MinIndex][pt2MinIndex] < limit:
                clastersIndexes[curClaster].append(pt2MinIndex)
                freePointsIndexes.remove(pt2MinIndex)
            else:
                continue


            # make claster
            while True:
                if freePointsIndexes == []:
                    break
                distsToCurClaster = {}
                for i in freePointsIndexes:
                    distance = 0.0
                    for point in clastersIndexes[curClaster]:
                        distance += distMatrix[point][i]
                    distsToCurClaster[i] = distance / len( clastersIndexes[curClaster] )
                minIndex = distsToCurClaster.keys()[0]
                for i in distsToCurClaster:
                    if distsToCurClaster[i] < distsToCurClaster[minIndex]:
                        minIndex = i
                if distsToCurClaster[minIndex] < limit:
                    clastersIndexes[curClaster].append(minIndex)
                    freePointsIndexes.remove(minIndex)
                else:
                    break

        # indexes -> points
        self.clasters = []
        for i in range(len(clastersIndexes)):
            self.clasters.append([])
            for pointIndex in clastersIndexes[i]:
                self.clasters[i].append(self.ptsArr[pointIndex][:])

        # uniting of clasters
        clastsN = len (self.clasters)
        centres = [[] for i in range(clastsN)]

        # find centres
        for i in range(clastsN):
            for j in range(clastsN):
                centresTmp = [[0.0, 0.0], [0.0, 0.0]]
                for point in self.clasters[i]:
                    centresTmp[0][0] += point[0]
                    centresTmp[0][1] += point[1]
                centresTmp[0][0] /= len(self.clasters[i])
                centresTmp[0][1] /= len(self.clasters[i])
                for point in self.clasters[j]:
                    centresTmp[1][0] += point[0]
                    centresTmp[1][1] += point[1]
                centresTmp[1][0] /= len(self.clasters[j])
                centresTmp[1][1] /= len(self.clasters[j])
                centres[i] = centresTmp[0][:]

        while clastsN != 1:

            clastersDistMatrix = [[0.0 for i in range(clastsN)] for j in range(clastsN)]
            for i in range(clastsN):
                for j in range(clastsN):
                    clastersDistMatrix[i][j] = (centres[i][0] - centres[j][0])**2 + \
                    (centres[i][1] - centres[j][1])**2

            cl1MinIndex = 0
            cl2MinIndex = 1
            for i in range(clastsN):
                for j in range(clastsN):
                    if i != j:
                        if clastersDistMatrix[i][j] < clastersDistMatrix[cl1MinIndex][cl2MinIndex]:
                            cl1MinIndex = i
                            cl2MinIndex = j

            if clastersDistMatrix[cl1MinIndex][cl2MinIndex] > limit:
                break

            x = [centres[cl1MinIndex][0], centres[cl2MinIndex][0]]
            y = [centres[cl1MinIndex][1], centres[cl2MinIndex][1]]
            plt.plot(x, y, 'bs--')

            centres[cl1MinIndex][0] = (centres[cl1MinIndex][0] + centres[cl2MinIndex][0]) / 2.0
            centres[cl1MinIndex][1] = (centres[cl1MinIndex][1] + centres[cl2MinIndex][1]) / 2.0
            centres.__delitem__(cl2MinIndex)
            clastsN -= 1

        self.drawClasters()

    # ------------------------------------------------

    # k-middle
    def mKMiddle (self):

        label = QtGui.QApplication.translate("self", "Введите число кластеров: ", None, QtGui.QApplication.UnicodeUTF8)
        clastNumb = QtGui.QInputDialog.getInt(self, 'Clasters', label)
        if not clastNumb[1]:
            return
        clastNumb = clastNumb[0]
        if clastNumb < 1:
            return

        if (clastNumb > self.rowsN):
            title = QtGui.QApplication.translate("self", "Ошибка", None, QtGui.QApplication.UnicodeUTF8)
            text  = QtGui.QApplication.translate("self", "Количество кластеров больше количества точек!", None, QtGui.QApplication.UnicodeUTF8)
            QtGui.QMessageBox.about(self, title, text)
            return

        centres = []
        clastersIndexesNew = [[] for i in range(clastNumb)]
        clastersIndexes = []

        # user enter init. centres
        for i in range(clastNumb):
            label = QtGui.QApplication.translate("self", "Введите центр кластера № %d:" % (i), None, QtGui.QApplication.UnicodeUTF8)
            index = QtGui.QInputDialog.getInt(self, 'Point', label)
            if not index[1]:
                return
            index = index[0] - 1
            if index < 0:
                return
            centres.append(self.ptsArr[index][:])

        # while clasters are not the same
        while clastersIndexes != clastersIndexesNew:

            clastersIndexes  = [0 for i in range(clastNumb)]
            for i in range(clastNumb):
                clastersIndexes[i] = clastersIndexesNew[i][:]

            clastersIndexesNew = [[] for i in range(clastNumb)]

            # make new clasters
            for i in range(self.rowsN):
                minDistance = 1000000
                minIndex = 0
                for j in range(clastNumb):
                    tmp = (self.ptsArr[i][0] - centres[j][0]) **2 + (self.ptsArr[i][1] - centres[j][1])**2
                    if tmp < minDistance:
                        minIndex = j
                        minDistance = tmp
                clastersIndexesNew[minIndex].append(i)

            # recount centres
            for i in range(clastNumb):
                x = 0.0
                y = 0.0
                for j in range(len(clastersIndexesNew[i])):
                    x += self.ptsArr[ clastersIndexesNew[i][j] ][0]
                    y += self.ptsArr[ clastersIndexesNew[i][j] ][1]
                x /= len(clastersIndexesNew[i])
                y /= len(clastersIndexesNew[i])
                centres[i][0] = x
                centres[i][1] = y

        # indexes -> points
        self.clasters = []
        for i in range(len(clastersIndexes)):
            self.clasters.append([])
            for pointIndex in clastersIndexes[i]:
                self.clasters[i].append(self.ptsArr[pointIndex][:])

        self.drawClasters()

    # ------------------------------------------------

    # trout (Форель)
    def mTrout(self):

        label = QtGui.QApplication.translate("self", "Введите радиус:", None, QtGui.QApplication.UnicodeUTF8)
        radius = QtGui.QInputDialog.getDouble(self, 'Radius', label)
        if not radius[1]:
            return
        radius = radius[0]

        freePoints = self.ptsArr[:]
        freePointsNew = []
        self.clasters = []
        curCentre = [0.0, 0.0]
        newCentre = [0.0, 0.0]
        circuitsCentres = []

        while freePoints != []:

            changed = True
            self.clasters.append([])
            newCentre = freePoints[0][:]
            self.clasters[len(self.clasters) - 1].append(newCentre[:])
            freePoints.__delitem__(0)

            while changed and (freePoints != []):

                curCentre = newCentre[:]
                cnt = 1.0

                for i in range(len(freePoints)):
                    if math.sqrt ((freePoints[i][0] - curCentre[0])**2 + \
                    (freePoints[i][1] - curCentre[1])**2 ) < radius:

                        newCentre[0] += freePoints[i][0]
                        newCentre[1] += freePoints[i][1]
                        cnt += 1.0
                        self.clasters[len(self.clasters) - 1].append(freePoints[i][:])
                        changed = True

                    else:
                        freePointsNew.append(freePoints[i][:])
                        changed = False

                freePoints = freePointsNew[:]
                freePointsNew = []
                newCentre[0] /= cnt
                newCentre[1] /= cnt

            circuitsCentres.append(newCentre[:])

        #plt.axes()
        for point in circuitsCentres:
            circle = plt.Circle(point, radius=radius, Fill=False, color='b')
            plt.gca().add_patch(circle)
        plt.axis('scaled')

        self.drawClasters()

    # ------------------------------------------------

    # crab
    def mCrab(self):

        label = QtGui.QApplication.translate("self", "Введите число кластеров: ", None, QtGui.QApplication.UnicodeUTF8)
        clastNumb = QtGui.QInputDialog.getInt(self, 'Clasters', label)
        if not clastNumb[1]:
            return
        clastNumb = clastNumb[0]

        if (clastNumb > self.rowsN):
            title = QtGui.QApplication.translate("self", "Ошибка", None, QtGui.QApplication.UnicodeUTF8)
            text  = QtGui.QApplication.translate("self", "Количество кластеров больше количества точек!", None, QtGui.QApplication.UnicodeUTF8)
            QtGui.QMessageBox.about(self, title, text)
            return

        distMatrix = [[0.0 for i in range(self.rowsN)] for i in range(self.rowsN)]
        freePointsIndexes = [i for i in range(self.rowsN)]
        nonFreePointsIndexes = []
        edges = []

        # make table
        for i in range(self.rowsN):
            for j in range(self.rowsN):
                distMatrix[i][j] = (self.ptsArr[i][0] - self.ptsArr[j][0])**2 + \
                (self.ptsArr[i][1] - self.ptsArr[j][1])**2

        # initial minimum
        pt1MinIndex = 0
        pt2MinIndex = 1
        for i in range(self.rowsN):
            for j in range(self.rowsN):
                if i != j:
                    if distMatrix[i][j] < distMatrix[pt1MinIndex][pt2MinIndex]:
                        pt1MinIndex = i
                        pt2MinIndex = j

        nonFreePointsIndexes.extend([pt1MinIndex, pt2MinIndex])
        freePointsIndexes.remove(pt1MinIndex)
        freePointsIndexes.remove(pt2MinIndex)
        edges.append([distMatrix[pt1MinIndex][pt2MinIndex], [pt1MinIndex, pt2MinIndex]])


        # link points
        while freePointsIndexes != []:

            pt1MinIndex = nonFreePointsIndexes[0]
            pt2MinIndex = freePointsIndexes[0]

            for i in nonFreePointsIndexes:
                for j in freePointsIndexes:
                    if distMatrix[i][j] < distMatrix[pt1MinIndex][pt2MinIndex]:
                        pt1MinIndex = i
                        pt2MinIndex = j

            nonFreePointsIndexes.append(pt2MinIndex)
            freePointsIndexes.remove(pt2MinIndex)
            edges.append([distMatrix[pt1MinIndex][pt2MinIndex], [pt1MinIndex, pt2MinIndex]])

        # remove biggest edges
        edges.sort()
        for i in range(clastNumb - 1):
            edges.__delitem__(len(edges) - 1)

        # have own drawing

        for point in self.ptsArr:
            x = [point[0] for i in range(len(point))]
            y = [point[1] for i in range(len(point))]
            plt.plot(x, y, 'ro')

        x, y = [[], []]
        for edge in edges:
            x.append(self.ptsArr[edge[1][0]][0])
            x.append(self.ptsArr[edge[1][1]][0])
            y.append(self.ptsArr[edge[1][0]][1])
            y.append(self.ptsArr[edge[1][1]][1])
            plt.plot(x, y, 'r-')
            x, y = [[], []]
        plt.axis('scaled')
        plt.show()

    # ------------------------------------------------

    # draw clasters
    def drawClasters(self):

        for claster in self.clasters:
            x = [claster[i][0] for i in range(len(claster))]
            y = [claster[i][1] for i in range(len(claster))]
            plt.plot(x, y, 'ro-')

        plt.show()

    # ------------------------------------------------

    # save points to file
    def save (self):

        # get points from table
        self.rowsN = self.pointsTableWidget.rowCount()
        self.ptsArr = [[0.0, 0.0] for i in range(self.rowsN)]
        for i in range(self.rowsN):
            for j in range(2):
                item = self.pointsTableWidget.item(i,j)
                if not item :
                    title = QtGui.QApplication.translate("self", "Ошибка", None, QtGui.QApplication.UnicodeUTF8)
                    text  = QtGui.QApplication.translate("self", "Заполните все поля или удалите ненужные", None, QtGui.QApplication.UnicodeUTF8)
                    QtGui.QMessageBox.about(self, title, text)
                    return
                self.ptsArr[i][j] = self.pointsTableWidget.item(i,j).text().toDouble()[0]

        # pick points to file
        fName = QtGui.QFileDialog.getSaveFileName(self, 'Save')
        if not fName:
            return
        fName = fName.toUtf8().data()
        f = open(fName, 'wb')
        pickle.dump(self.ptsArr, f, 2)
        f.close()

    # ------------------------------------------------

    # load points from file
    def load (self):

        # unpick points from file
        fName = QtGui.QFileDialog.getOpenFileName(self, 'Open')
        if not fName:
            return
        fName = fName.toUtf8().data()
        f = open(fName, 'rb')
        self.ptsArr = pickle.load(f)
        f.close()

        # put points to the table
        ptsN = len(self.ptsArr)
        self.pointsTableWidget.setRowCount(ptsN)
        for i in range(ptsN):
            x = QtGui.QTableWidgetItem(QtCore.QString.number(self.ptsArr[i][0]))
            y = QtGui.QTableWidgetItem(QtCore.QString.number(self.ptsArr[i][1]))
            self.pointsTableWidget.setItem(i, 0, x)
            self.pointsTableWidget.setItem(i, 1, y)

# ------------------------------------------------

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    w = Form()
    w.show()
    app.exec_()

