#!/usr/bin/env python3
# Decodificador baseado nos offsets e tipos de dados verificados no arquivo
# '20261009 1435 - 4573 50um 77K 500mV'.
# Esta NAO e uma especificacao oficial do formato DTLG; outros arquivos podem variar.

import argparse
import csv
import json
import math
import struct
from pathlib import Path


def decodificar(caminho):
    dados = caminho.read_bytes()
    if dados[:4] != b'DTLG':
        raise ValueError('Assinatura DTLG ausente nos quatro primeiros bytes.')
    if len(dados) < 0x5AC:
        raise ValueError('Arquivo menor que o cabecalho esperado.')

    # O offset 0x000C guarda um ponteiro para 0x03A4, que por sua vez
    # contem o inicio dos metadados 0x05A4 (todos inteiros big-endian).
    offset_ponteiro = struct.unpack_from('>I', dados, 0x000C)[0]
    if offset_ponteiro + 4 > len(dados):
        raise ValueError('Ponteiro do cabecalho fora do arquivo.')
    inicio_metadados = struct.unpack_from('>I', dados, offset_ponteiro)[0]
    if inicio_metadados != 0x05A4:
        raise ValueError(
            f'Cabecalho nao corresponde ao modelo validado: '
            f'inicio_metadados=0x{inicio_metadados:X}, esperado 0x05A4.'
        )

    cursor = inicio_metadados
    campos = []

    def ler(nome, formato):
        nonlocal cursor
        pos = cursor
        tam = struct.calcsize(formato)
        if pos + tam > len(dados):
            raise ValueError(f'Campo truncado: {nome}, offset=0x{pos:X}.')
        valor = struct.unpack_from(formato, dados, pos)[0]
        campos.append({'campo': nome, 'offset_hex': f'0x{pos:04X}',
                       'tipo': formato, 'valor': valor})
        cursor += tam
        return valor

    def ler_texto(nome):
        nonlocal cursor
        pos = cursor
        if pos + 4 > len(dados):
            raise ValueError(f'Tamanho de texto truncado em {nome}.')
        comprimento = struct.unpack_from('>I', dados, cursor)[0]
        cursor += 4
        if cursor + comprimento > len(dados):
            raise ValueError(f'Texto truncado: {nome}.')
        valor = dados[cursor:cursor + comprimento].decode('cp1252')
        cursor += comprimento
        campos.append({'campo': nome, 'offset_hex': f'0x{pos:04X}',
                       'tipo': '>I tamanho + cp1252', 'valor': valor})
        return valor

    ler('Temperatura', '>d')
    for nome in ('Data', 'Usuario', 'Diretorio de trabalho', 'Amostra', 'Nome do arquivo'):
        ler_texto(nome)

    gerais = [
        ('Inicio (Angstrom)', '>d'), ('Fim (Angstrom)', '>d'),
        ('Passo (Angstrom)', '>d'), ('Fim (eV)', '>d'),
        ('Inicio (eV)', '>d'), ('No de pontos informado no cabecalho', '>H'),
        ('Fenda de saida (mm)', '>d'), ('Fenda de entrada (mm)', '>d'),
        ('Medidas por ponto', '>B'), ('No de curvas', '>B'),
        ('Filtro de deteccao (nm)', '>d'), ('Espera entre passos (ms)', '>d'),
        ('Espera entre curvas (s)', '>B'), ('Altura S', '>B'),
        ('Altura E', '>B'), ('Rede de difracao (linhas/mm)', '>I')
    ]
    for nome, formato in gerais:
        ler(nome, formato)

    espectrometro = [
        ('Sensibilidade - codigo', '>H'),
        ('Constante de tempo pre - codigo', '>H'),
        ('Constante de tempo pos - codigo', '>H'),
        ('Filtro band pass - codigo', '>H'),
        ('Expand - codigo', '>H'),
        ('Filtro de linha - codigo', '>H'),
        ('Filtro de linha x2 - codigo', '>H'),
        ('Frequencia de deteccao', '>d'),
        ('Reserva dinamica - codigo', '>H'),
    ]
    for nome, formato in espectrometro:
        ler(nome, formato)

    lockin = [
        ('Laser - codigo', '>H'),
        ('Potencia (mW) - valor armazenado', '>d'),
        ('Filtros de potencia (%) - valor armazenado', '>d'),
        ('Filtro band pass (nm)', '>d'),
        ('Outra linha - valor armazenado', '>d'),
    ]
    for nome, formato in lockin:
        ler(nome, formato)

    ler('Identificador num. anterior a curva (significado desconhecido)', '>I')
    comprimento_inicial = ler('Inicio da curva (Angstrom)', '>I')
    passo = ler('Passo da curva (Angstrom)', '>d')
    quantidade = ler('Quantidade de valores da curva', '>I')

    inicio_curva = cursor
    if quantidade < 2 or inicio_curva + quantidade * 8 != len(dados):
        raise ValueError(
            f'Contagem invalida: {quantidade} pontos em 0x{inicio_curva:X} '
            f'nao corresponde ao tamanho total de {len(dados)} bytes.'
        )
    if not math.isfinite(passo) or passo <= 0:
        raise ValueError('Passo da curva invalido.')

    intensidades = struct.unpack_from(f'>{quantidade}d', dados, inicio_curva)
    if not all(math.isfinite(y) for y in intensidades):
        raise ValueError('A curva possui dados numericos nao finitos.')

    linhas = [(comprimento_inicial + i * passo, y)
              for i, y in enumerate(intensidades)]
    return linhas, campos, inicio_curva, len(dados)


def main():
    ap = argparse.ArgumentParser(description='Extrai curva e metadados do DTLG validado.')
    ap.add_argument('arquivo', type=Path, help='Arquivo binario original sem extensao')
    ap.add_argument('--saida', type=Path, default=None, help='Pasta de saida; padrao: mesma pasta')
    args = ap.parse_args()
    linhas, campos, offset, tamanho = decodificar(args.arquivo)
    pasta = args.saida if args.saida is not None else args.arquivo.parent
    pasta.mkdir(parents=True, exist_ok=True)

    csv_saida = pasta / 'curva_decodificada.csv'
    with csv_saida.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['comprimento_onda_A', 'sinal_bruto'])
        writer.writerows((f'{x:g}', repr(y)) for x, y in linhas)

    meta_saida = pasta / 'metadados_decodificados.json'
    with meta_saida.open('w', encoding='utf-8') as f:
        json.dump({
            'aviso': 'Decodificacao verificada apenas com o arquivo enviado; '
                     'nao implica especificacao oficial do formato.',
            'tamanho_em_bytes': tamanho,
            'inicio_curva_offset_hex': f'0x{offset:04X}',
            'amostras': len(linhas),
            'campos': campos,
        }, f, ensure_ascii=False, indent=2)

    imax = max(range(len(linhas)), key=lambda i: linhas[i][1])
    print(f'Arquivo: {args.arquivo}')
    print(f'Tamanho: {tamanho} bytes; dados em 0x{offset:04X}; pontos: {len(linhas)}')
    print(f'Eixo: {linhas[0][0]:g} a {linhas[-1][0]:g} Angstrom')
    print(f'Primeiro sinal: {linhas[0][1]!r}; ultimo: {linhas[-1][1]!r}')
    print(f'Maximo amostrado: {linhas[imax][1]!r} em {linhas[imax][0]:g} Angstrom')
    print(f'CSV: {csv_saida}')
    print(f'Metadados: {meta_saida}')


if __name__ == '__main__':
    main()
