#!/usr/bin/env python
version = "1.0"


from pyparsing import *
import argparse
#Cuidado: la salida de debug no va a los archivos de salida, solo a la salida de error estandar.
import logging
import sys


p = ParserElement
# p.setDefaultWhitespaceChars(" ")

nombreArchivo = 'zoneshow.txt'
# nombreArchivo = 'zoneshow.txt'


##################################################################################################
#Sintaxis del archivo, simil BNF

#Un nombre de algo. Zona, alias, etc. Algunas palabras de zonas son listitas de puerto o asi, por eso la ",".
nombre =  Word(alphanums + "_")

# Es importante separar las posibilidades, porque si hiciera un Word(alphanums + ":") los delimitadores zone: y alias: entrarian como nombres tb.
rangopuertos = Combine(Word(nums) + "," + Word(nums))

##### World-Wide Port Name
w_bit = Word(hexnums, exact=2)
#TODO: multiplicar en lugar de sumar
#un wwpn completo es una suma de 8 pedacitos,
# o sea 7 veces <hh><:> mas un ultimo <hh>.
wwpn = Combine( (w_bit + ":") * 7 + w_bit)

# Una entrada en una lista cualquiera, sera entonces o un nombre (cha01_bl01_coso9) o un wwpn (12:23:a4:49:bc:...)
# entrada = Or(nombre, wwpn, rangopuertos)
entrada = nombre ^ wwpn ^ rangopuertos

elemento = NotAny("zone:") + NotAny("alias:") + Suppress(Optional(Literal(";"))) + entrada

listaEntradas =  entrada + ZeroOrMore(elemento)

# Lista de nombres de zonas, separadas por ;, dentro de una configuracion definida
listaZonas = NotAny("zone:") + delimitedList(entrada, delim=';')

# una entrada en la lista de configuraciones definidas
DefConf = Group(Literal("cfg:") + nombre + Optional(listaZonas))
#La lista de configuraciones definidas
DefinedConfig = Group(Literal("Defined configuration:"))

#Zonas y aliases del centro del archivo
Zona  = Group(Literal("zone:")  + nombre + listaEntradas)
Alias = Group(Literal("alias:") + nombre + delimitedList(entrada, ';'))

#Zonas de puertos de la configuracion efectiva
EffectiveConfig = Group(Literal("Effective configuration:"))


multiparser = EffectiveConfig ^ DefinedConfig ^ Zona ^ Alias ^ DefConf
listaMulti = OneOrMore(multiparser)


##################################################################################################
if __name__ == "__main__":
	parser = argparse.ArgumentParser(
		description="Filtro de informacion de zoning para la SAN",
		epilog="Procesamiento distribuido. Frank@5123 Mar/18")
	parser.add_argument('-v','--version', #
		action='version',
		version='%(prog)s version ' + version,
		help='Muestra el numero de version y sale.'
		)
	parser.add_argument('-d',#debug, opcional
		type=str,
		choices=["CRITICAL","ERROR","WARNING","INFO","DEBUG","NOTSET"],
		required=False,
		help='(Opcional) Salida de depuracion o debug.',
		dest='debug',
		default='CRITICAL'
		)
	parser.add_argument('-i', #Archivo de entrada.
		nargs='?',
		type=str, #String con nombre de archivo de entrada. Antes: argparse.FileType('r'),
		dest='archivoentrada',
		required=True,
		help='Nombre del archivo de entrada, generado por los switches de SAN?',
		)
	parser.add_argument('-o', #Archivo de salida. Opcional
		nargs='?',
		type=argparse.FileType('w'),
		default=sys.stdout,
		dest='archivosalida',
		help='(Opcional) Nombre de archivo de salida. De no completarse, se usa la salida estandar.',
		)

	############Capturar parametros
	args =  parser.parse_args()
	
	debugs = {
		"CRITICAL": logging.CRITICAL,
		"ERROR": logging.ERROR,
		"WARNING": logging.WARNING,
		"INFO": logging.INFO,
		"DEBUG": logging.DEBUG,
		"NOTSET": logging.NOTSET,
	}

	logging.basicConfig(level=debugs[args.debug])


	logging.info("""Parametros recibidos:
		archivoentrada: {}
		debug: {}
		archivosalida: {}
		""".format(args.archivoentrada, args.debug, args.archivosalida))
	##################################
	#apertura del archivo

	with open(args.archivoentrada, 'r') as myfile:
		data = myfile.read()

	r = listaMulti.parseString(data).asList()

	for e in r:
		args.archivosalida.write(repr(e).replace(']', '').replace("[",""))
		args.archivosalida.write("\n")

	args.archivosalida.close()

