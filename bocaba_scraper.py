# -*- coding: utf-8 -*-

#  bocaba_scraper.py
#  
#  Copyright 2018 Juan Manuel Dedionigis jmdedio@gmail.com
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from time import sleep
from urllib2 import urlopen
from PyPDF2 import PdfFileReader
from os import remove
from time import strftime
from xml.dom import minidom

reload(sys)
# Cambia la codificación predeterminada en todo el script
sys.setdefaultencoding('utf8')

class BocabaScraper():
    # Abre el navegador
    def abre_navegador(self):
        # Carga las opciones de Chromium
        chrome_options = Options()
        # deshabilita las notificaciones de Chrome
        prefs = {"profile.default_content_setting_values.notifications" : 2}
        chrome_options.add_experimental_option("prefs", prefs)
        # Abre el navegador
        self.driver = webdriver.Chrome(executable_path = chromedriver, chrome_options = chrome_options)
        self.driver.maximize_window()

    # Da formato fecha hora "YYYY-mm-dd HH:MM:SS"
    def formateafecha(self, fecha):
        lista = fecha[-10:].replace('/', ' ').split()
        return lista[2] + '-' + lista[1] + '-' + lista[0] + strftime(" %H:%M:%S")

    # Ingresa al sitio y extrae los enlaces de cada publicación.
    # Cada una de las cuales tiene al menos un fichero pdf.
    # Extrae la url de cada pdf, su título y la fecha de publicación.
    def extrae_datos(self):
        self.driver.get("https://boletinoficial.buenosaires.gob.ar/")
        sleep(10)
        fecha = self.formateafecha(self.driver.find_element(By.XPATH, '//h3[@id="boletinTit"]').text)
        enlaces = self.driver.find_elements(By.XPATH, '//div[@class="divOrganismo"]//a')
        return [enlaces[i].get_attribute("href") for i in range(0, len(enlaces))], [enlaces[i].text for i in range(0, len(enlaces))], fecha

    # Extrae el texto completo del pdf
    def extrae_texto(self, urlpdf):
        # extrae el dígito verificador de la norma
        nombreficheropdf = urlpdf[(urlpdf.rfind('/') + 1):]

        # Descarga el pdf y lo almacena en disco
        with open(nombreficheropdf, 'wb') as f:
            f.write(urlopen(urlpdf).read())
            f.close()

        # Extrae todo el texto del fichero pdf
        content = PdfFileReader(nombreficheropdf)
        texto = ''
        for i in range(0, content.getNumPages()):
                texto = texto + u''.join(content.getPage(i).extractText()).decode('utf-8')

        # Elimina el fichero pdf
        remove(nombreficheropdf)

        return texto, nombreficheropdf

    # Crea un fichero xml con la información obtenida del pdf
    def xml(self, titulo, texto, fecha, nombrefichero, enlace):
        doc = minidom.Document()
        root = doc.createElement("article")

        dato_cdata = doc.createCDATASection(titulo)
        cdv = doc.createElement('titulo')
        cdv.appendChild(dato_cdata)
        root.appendChild(cdv)
        doc.appendChild(root)

        dato_cdata = doc.createCDATASection(texto)
        cdv = doc.createElement('texto')
        cdv.appendChild(dato_cdata)
        root.appendChild(cdv)
        doc.appendChild(root)

        dato_cdata = doc.createCDATASection(enlace)
        cdv = doc.createElement('url')
        cdv.appendChild(dato_cdata)
        root.appendChild(cdv)
        doc.appendChild(root)

        dato = doc.createTextNode(fecha)
        cdv = doc.createElement('fechahora')
        cdv.appendChild(dato)
        root.appendChild(cdv)
        doc.appendChild(root)

        doc.writexml( open((nombrefichero + '.xml'), 'w'), indent = "  ", addindent = "  ", newl = '\n', encoding='utf-8')
        doc.unlink()

    def cierra_navegador(self):
        self.driver.quit()

if __name__ == "__main__":
    chromedriver = "AQUÍ VA LA RUTA DEL CHROMDRIVER"

    scraper = BocabaScraper()
    scraper.abre_navegador()
    scraper.extrae_datos()
    enlaces, titulos, fecha = scraper.extrae_datos()
    scraper.cierra_navegador()
    for enlace, titulo in zip(enlaces, titulos):
        texto, nombrefichero = scraper.extrae_texto(enlace)
        scraper.xml(titulo, texto, fecha, nombrefichero, enlace)
