#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import argparse
from hashlib import md5
import glob
import os
import logging
from shutil import copyfile

#log = logging.getLogger(__name__)
log = logging.getLogger('unifier')
logging.basicConfig(
            level=logging.WARNING,
            format='%(asctime)s %(name)s (%(levelname)s): %(message)s',
            datefmt='%F %T'
            )

def get_args():
    parser = argparse.ArgumentParser(
            description="Verifica árvore de arquivos unificando-os.",
            epilog='%(prog)s -d /tmp/unified',
    )
    parser.add_argument('-d', '--destino', help='''especifica a pasta que 
            conterá os arquivos unificados.''', default='./unifier')
    parser.add_argument('-v', '--verbose', action='count', default=0,
            help="Aumenta verbosidade.")
    parser.add_argument('caminho',  help='''diretório que deve
            ser unificado.''')

    opts = parser.parse_args()

    levels = [ logging.WARNING, logging.INFO, logging.DEBUG ]
    log.setLevel(levels[ min(len(levels)-1, opts.verbose) ])

    return opts

def arqhash(arquivo: str) -> str:
    '''Retorna o hash md5 de [arquivo].'''
    with open(arquivo, 'rb') as arq:
        return md5(arq.read()).hexdigest()

def dbfiles(caminho: str) -> dict:
    '''Função que escaneia caminho recursivamente, e separa os arquivos
    por hash, retornando um dicionário em que as chaves são os hashes.'''
    dbdict = {}
    for filename in glob.iglob(f'{caminho}/**/*', recursive=True):
        if not os.path.isfile(filename) or os.path.islink(filename): continue
        hasharq = arqhash(filename)
        try:
            dbdict[hasharq].append(filename)
        except KeyError:
            dbdict[hasharq] = [ filename ]
    return dbdict

def cparqs(diciarq: dict, destino: str):
    '''Função que copia os arquivos para  o destino.'''
    for k, v in diciarq.items():
        arq = v[0]
        dst = os.path.join(destino, os.path.basename(arq))

        os.makedirs(f'{destino}', exist_ok=True)

        if os.path.exists(dst):
            dst = versiona(dest = dst, check = k)
            if not dst: continue
        log.info(f'copiando ({k}) - {arq} para {dst}')
        copyfile(arq, dst)

def versiona(dest: str, check: str, depth: int = 0) -> str:
    '''Função que versiona o arquivo para que não seja sobreescrito.'''
    log.debug(f'Versionando arquivo({check}): {dest}')
    if depth == 1:
        dest = dest.replace(dest[dest.rindex('.'):],f'_v{depth}{dest[dest.rindex("."):]}')
    if not os.path.exists(dest): return dest

    if arqhash(dest) != check:
        log.debug(f'Arquivo({check}): {dest} existe porém hash não confere.')
        depth += 1
        dest = dest.replace(f'_v{depth - 1}{dest[dest.rindex("."):]}', f'_v{depth}{dest[dest.rindex("."):]}')
        return versiona(dest=dest, check=check, depth=depth)
    else:
        log.debug(f'Arquivo({check}): {dest} existe e o hash corresponde.')
        log.info(f'Arquivo: ({check}){dest} já existe, pulando!')
        return None

if __name__ == "__main__":
    opts = get_args()

    log.debug(f'Iniciando coleta de arquivos.')
    arqdic = dbfiles(opts.caminho)
    log.debug(f'{len(arqdic)} arquivos encontrados.')
    cparqs(diciarq=arqdic, destino=opts.destino)

# vim: sw=4 ts=4 et sm cursorline tw=79 fo+=t fileencoding=utf-8
