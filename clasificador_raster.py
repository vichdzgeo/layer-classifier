# -*- coding: utf-8 -*-
'''
Qgis 3 o superior
'''


from qgis.core import *
from qgis.PyQt import QtCore, QtGui, QtWidgets, uic

import os
import processing as pr
import numpy as np 
from osgeo import gdal
from osgeo import osr
import math


def raster_min_max(path_raster):
    '''
    Esta funcion regresa los valores maximos y minimos de una capa raster

    :param path_raster: ruta de la capa raster
    :type path_raster: str 
    '''
    rlayer = QgsRasterLayer(path_raster,"raster")
    extent = rlayer.extent()
    provider = rlayer.dataProvider()
    stats = provider.bandStatistics(1,
                                    QgsRasterBandStats.All,
                                    extent,
                                    0)

    v_min = stats.minimumValue
    v_max = stats.maximumValue
    return v_min, v_max

def raster_nodata(path_raster):
    '''
    Esta función regresa el valor de no data de la capa raster de entrada

    :param path_raster: ruta de la capa raster
    :type path_raster: str 

    '''
    rlayer = QgsRasterLayer(path_raster,"raster")
    extent = rlayer.extent()
    provider = rlayer.dataProvider()
    rows = rlayer.rasterUnitsPerPixelY()
    cols = rlayer.rasterUnitsPerPixelX()
    block = provider.block(1, extent,  rows, cols)
    no_data = block.noDataValue()

    return no_data

def wf(fp=2, min=0, max=1, categories=5):
    '''
    Esta funcion regresa de cortes según el método de weber-fechner

    :param fp: factor de progresión 
    :type fp: float

    :param min: valor mínimo de la capa
    :type min: float

    :param max: valor máximo de la capa
    :type max: float

    :param categories: número de categorias
    :type categories: int 

    '''
    dicc_e = {}
    list_val = [min,]
    pm = max - min 
    cats = np.power(fp, categories)
    e0 = pm/cats
    for i in range(1 , categories + 1):
        dicc_e['e'+str(i)]= min + (np.power(fp,i) * e0)
        
    for i in range(1, categories + 1):
        list_val.append(dicc_e['e'+str(i)])

    return list_val


def progressive(fp=2, min=0, max=1, categories=5):
    '''
    Esta función regresa una lista de los cortes según el método progresivo
    :param fp: factor de progresión 
    :type fp: float
    :param min: valor mínimo de la capa
    :type min: float
    :param max: valor máximo de la capa
    :type max: float
    :param categories: número de categorias 
    :type categories: int 

    '''
    
    numeroDeCortes = categories - 1
    laSuma = 0

    for i in range(categories) :
        laSuma += ((fp) ** i)

    cachito = max / laSuma

    FuzzyCut = []

    for i in range(numeroDeCortes) :
        anterior = 0
        if i > 0:
            anterior = FuzzyCut[i - 1]

        corte = anterior + fp ** i * cachito
        FuzzyCut.append(corte)

    FuzzyCut.insert(0,min)
    FuzzyCut.append(max)
    
    return FuzzyCut

def tipo_clasificador(clasificador,path_r,fp=2,categories = 5,min=0,max=1):
    '''
        Esta función integra los modos de clasificación, weber-fechner, progresiva,
        cuartiles, quintiles, deciles o equidistante

        param tipo_clasificador: tipo de clasificador (progresiva, cuartiles, quintiles, deciles, equidistante)
        type tipo_clasificador: str

        :param fp: factor de progresión 
        :type fp: float

        :param categories: número de categorias 
        :type categories: int 

        :param min: valor mínimo de la capa
        :type min: float

        :param max: valor máximo de la capa
        :type max: float



    '''

    if clasificador.lower() == "progresiva":
        nombre ='pg'+"_"+str(fp).replace('.','_')+"_"+str(categories)+"cats"
        return progressive(fp,min,max,categories),nombre
        
    elif clasificador.lower() == "wf" or clasificador.lower() == "weber-fechner":
        nombre =clasificador.lower()+"_"+str(fp).replace('.','_')+"_"+str(categories)+"cats"
        return wf(fp,min,max,categories),nombre
    elif clasificador.lower()=='cuartiles':
        nombre = clasificador
        return cuantiles(path_r,4,min,max),nombre
    elif clasificador.lower()=='quintiles':
        nombre = clasificador
        return cuantiles(path_r,5,min,max),nombre
    elif clasificador.lower()== 'deciles':
        nombre = clasificador
        return cuantiles(path_r,10,min,max),nombre
    elif clasificador.lower()== 'equidistante':
        nombre = clasificador
        return equidistantes(categories,min,max),nombre
    else:
        print ("error en el nombre de clasificacion")
        
def cuantiles(path_r,quantil,min,max):
    '''
    Esta función regresa la lista de cortes según el cualtil 
    deseado de los valores de la capa raster de entrada

    :param path_r: ruta de la capa raster
    :type path_r: str
    
    :param quantil: cuantil  
    :type quantil: int 

    :param min: valor mínimo de la capa
    :type min: float

    :param max: valor máximo de la capa
    :type max: float
    
    '''
    

    raster = gdal.Open(path_r)
    band1 =raster.GetRasterBand(1).ReadAsArray()
    nodata_r=raster.GetRasterBand(1).GetNoDataValue()
    if nodata_r < 0:
        band2= band1[band1 > nodata_r]
    elif  nodata_r > 0:
        band2= band1[band1 < nodata_r]
    elif math.isnan(nodata_r):
        band2= band1[np.logical_not(np.isnan(band1))]
    band2 = band2.flatten()
    print (nodata_r)
    list_val = [min,]
    
    for i in range(1,quantil+1):
        #print (i,i/quantil)
        valor= i/quantil
        cuantil_c = np.quantile(band2,valor)
        list_val.append(cuantil_c)
    print (list_val)
    return list_val
    
def equidistantes (categories=5,min=0,max=1):
    '''
    Esta función regresa la lista de cortes equidistantes según el número 
    de categorias y el valor minimo y maximo ingresados.

    :param categories: número de categorias 
    :type categories: int 

    :param min: valor mínimo de la capa
    :type min: float

    :param max: valor máximo de la capa
    :type max: float
    
    '''

    list_val = [min,]
    incremento = (max - min) / categories
    for i in range(1,categories+1):
        valor = min + (incremento * i)
        list_val.append(valor)
    print (list_val)
    return list_val

def clasifica_raster(path_capa,clasificador,fp=2,categories=5):


    '''
    Funcion integradora para clasificar la capa raster
    
    :param path_capa: ruta de la capa raster
    :type path_capa: str 

    :param clasificador: nombre del clasificador
    :type clasificador: str

    :param fp: factor de progresión 
    :type fp: float
    
    :param categories: número de categorias 
    :type categories: int 

    '''

    v_min,v_max=raster_min_max(path_capa)
    cortes,nombre = tipo_clasificador(clasificador,path_capa,fp,categories,min=v_min,max=v_max)
    ecuacion = ecuacion_class(cortes)
    path_salida_tp = path_capa.split(".")[0]+"tp_"+nombre+".tif"
    path_salida = path_capa.split(".")[0]+"_"+nombre+".tif"
    dicc ={        
        'INPUT_A':path_capa,
        'BAND_A':1,
        'FORMULA':ecuacion,
        'NO_DATA': -9999,
        'RTYPE':1,
        'OUTPUT':path_salida_tp,}
    pr.run("gdal:rastercalculator",dicc)

    set_nulls(path_salida_tp,path_salida)
    remove_raster(path_salida_tp)
    cargar_raster(path_salida)

    
def nombre_capa(path_capa):
    '''
    Esta función regresa el nombre de una capa sin extensión 

    :param path_capa: ruta de la capa
    :type path_capa: str 


    '''
    nombre_capa=(path_capa.split("/")[-1:])[0]
    return nombre_capa

def ecuacion_class(cortes):
    '''
    Esta funcion regresa en formato de cadena la ecuación 
    para utilizarse en la calculadora de gdal a partir de una lista de cortes

    :param cortes: lista con los puntos de corte
    :type cortes: list 


    '''

    n_cortes = len(cortes)
    ecuacion =''
    for i in range(n_cortes):
        if i < n_cortes-2: 
            ecuacion+='logical_and(A>='+str(cortes[i])+',A<'+str(cortes[i+1])+')*'+str(i+1)+' + '
        elif i== n_cortes-2 :
            ecuacion+='logical_and(A>='+str(cortes[i])+', A<='+str(cortes[i+1])+')*'+str(i+1)
    print (ecuacion)
    return ecuacion

def cargar_raster(path_raster):
    '''
    Esta función carga una capa raster a un proyecto 
    de qgis 

    :param path_raster: ruta de la capa raster
    :type path_raster: str

    '''  
    nombre = nombre_capa(path_raster).split(".")[0]
    rlayer = QgsRasterLayer(path_raster, nombre)
    QgsProject.instance().addMapLayer(rlayer)

def get_region(path_layer):
    '''
    Esta función regresa en forma de cadena de texto 
    las coordenadas de la extensión de una capa raster

    param path_layer: ruta de la capa raster
    type path_layer: str
    '''

    layer = QgsRasterLayer(path_layer,"")
    ext = layer.extent()
    xmin = ext.xMinimum()
    xmax = ext.xMaximum()
    ymin = ext.yMinimum()
    ymax = ext.yMaximum()

    region = "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax)
    return region 
def set_nulls(map,output):
    '''
    Esta función asigna un valor de cero a los no_data de la capa
    
    :param map: ruta de la capa raster
    :type map: str

    :param output:ruta de la capa resultante
    :type output: str
    '''
    region=get_region(map)
    dicc={'map':map,
            'setnull':0,
            'output':output,
            'GRASS_REGION_PARAMETER':region,
            'GRASS_REGION_CELLSIZE_PARAMETER':0}
    pr.run("grass7:r.null",dicc)

def remove_raster(path_r):
    '''
    Esta función elimina una capa del sistema

    :param path_r: ruta de la capa 
    :type path_r: str

    '''
    os.remove(path_r)