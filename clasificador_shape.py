import random
import numpy as np 
import os, sys, subprocess, processing
from qgis.core import QgsApplication
from qgis.core import *
from PyQt5.QtCore import *
from PyQt5.QtCore import QVariant
from PyQt5.QtGui import *
from qgis.analysis import *
import qgis.utils
from qgis.PyQt import QtGui
import qgis 

def progressive(fp=2, min=0, max=1, categories=5):

    # # Cortes de categories siguiendo Ley de Weber
    # print '\n\t\t////Cortes de categories siguiendo Ley de Weber-Feshner////\n'
    
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

def wf(fp=2,min=0,max=1,categories=5):
    
    dicc_e = {}
    lista_val = [min,]
    pm = max - min 
    cats = np.power(fp, categories)
    e0 = pm/cats
    for i in range(1 , categories + 1):
        dicc_e['e'+str(i)]= min + (np.power(fp,i) * e0)
        
    print (dicc_e)
    dicc_cortes ={}
    for i in range(1 , categories + 1):
        lista_val.append( dicc_e['e'+str(i)])
    print (lista_val)
    return lista_val



        
def cuantiles_s(path_v,quantil,field,min,max):

    '''
    Esta función regresa la lista de cortes según el cuantil 
    deseado de los valores de un campo de la capa vectorial de entrada

    :param path_v: ruta de la capa vectorial
    :type path_v: str
        
    :param quantil: cuantil  
    :type quantil: int 

    :param field: nombre del campo
    :type field: str

    :param min: valor mínimo de la capa
    :type min: float

    :param max: valor máximo de la capa
    :type max: float
    '''

    vlayer = QgsVectorLayer(path_v,"","ogr")
    no_geometry =  QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry)
    values = [v[field] for v in vlayer.getFeatures(no_geometry)]
    array_val = np.array(values)
    lista_val=[min,]
    for i in range(1,quantil+1):
        value= i/quantil
        cuantil_c = np.quantile(array_val,value)
        lista_val.append(cuantil_c)

    return lista_val
    
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

    lista_val = [min,]
    incremento = (max - min) / categories
    for i in range(1,categories+1):
        valor = min + (incremento * i)
        lista_val.append(valor)
    return lista_val

def max_min_vector(layer,campo):
    '''
    Esta función regresa el maximo y minimo del campo
    elegido de la capa vectorial de entrada

    :param layer: capa vectorial
    :type layer: QgsLayer

    :param campo: nombre del campo
    :type campo: str 


    '''
    idx=layer.fields().indexFromName(campo)
    return layer.minimumValue(idx),layer.maximumValue(idx)

def tipo_clasificador_s(clasificador, path_v, l_field, fp=2, categories = 5, min=0, max=1):
    '''
    Esta función integra los modos de clasificación, weber-fechner, progresiva,
        cuartiles, quintiles, deciles o equidistante

        param clasificador: tipo de clasificador (progresiva, cuartiles, quintiles, deciles, equidistante)
        type clasificador: str

        :param path_v: ruta de la capa vectorial
        :type path_v: str
        
        :param l_field: nombre del campo
        :type l_field: str 

        :param fp: factor de progresión 
        :type fp: float

        :param categories: número de categorias 
        :type categories: int 

        :param min: valor mínimo de la capa
        :type min: float

        :param max: valor máximo de la capa
        :type max: float


    '''

    if clasificador.lower() == "wf" or clasificador.lower() == "weber-fechner":
        nombre ='ct_wf_'+str(fp).replace(".","")
        return wf(fp,min,max,categories),nombre

    elif clasificador.lower() == "progressive":
        nombre ='ct_pg_'+str(fp).replace(".","")
        return progressive(fp,min,max,categories),nombre

    elif clasificador.lower()=='cuartiles':
        nombre = 'ct_cuartil'
        return cuantiles_s(path_v,4,l_field,min,max),nombre
    elif clasificador.lower()=='quintiles':
        nombre = 'ct_quintil'
        return cuantiles_s(path_v,5,l_field,min,max),nombre
    elif clasificador.lower()== 'deciles':
        nombre = 'ct_decil'
        return cuantiles_s(path_v,10,l_field,min,max),nombre
    elif clasificador.lower()== 'equidistante':
        nombre = 'ct_equidis'
        return equidistantes(categories, min, max),nombre
    else:
        print ("error en el nombre de clasificacion")

def clasificar_shape(path_v, clasificador, l_field, fp=2, categories=5):

    '''
    Funcion integradora para clasificar la capa vectorial
    
    :param path_v: ruta de la capa vectorial 
    :type path_v: str 

    :param clasificador: nombre del clasificador
    :type clasificador: str

    :param fp: factor de progresión 
    :type fp: float
    
    :param categories: número de categorias 
    :type categories: int 

    '''
    vlayer = QgsVectorLayer(path_v,"","ogr")
    v_min,v_max =max_min_vector(vlayer,l_field)
    cortes,nombre= tipo_clasificador_s(clasificador,path_v,l_field, fp,categories,min=v_min,max=v_max)
    campos = [field.name() for field in vlayer.fields()]
    if not nombre in campos:
        vlayer.dataProvider().addAttributes([QgsField(nombre,QVariant.Int)])
        vlayer.updateFields()
    
    categories_list = [x for x in range(1,categories+1)]
    for i in range(len(cortes)-1):
        myMin = cortes[i]
        myMax = cortes[i+1]
            
        vlayer.startEditing()        
        for element in vlayer.getFeatures():
            if element[l_field] >= myMin and element[l_field] <= myMax:
                element[nombre]=categories_list[i]
                vlayer.updateFeature(element)
        vlayer.commitChanges()



