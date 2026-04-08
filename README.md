# Análise de Sistemas Elétricos de Potência

Repositório acadêmico com estudos em Python voltados à análise de sistemas elétricos de potência.

Este projeto foi organizado para estudar análise de curto-circuito e estabilidade transitória a partir de dados configuráveis do sistema, modelagem em pu e cálculos típicos de disciplinas de sistemas de potência na graduação em Engenharia Elétrica.

## Visão Geral

O repositório contém dois artefatos principais de estudo:

- `short_circuit_analysis.py` - Script configurável para estudos de curto-circuito por componentes simétricas. Permite modelar diferentes elementos da rede, selecionar tipos de falta e obter resultados detalhados em pu e em unidades de engenharia.
- `transient_stability_case_study.py` - Estudo de caso que combina análise de estabilidade transitória pelo critério das áreas iguais com uma análise de falta em uma topologia fixa de sistema de transmissão.

## O Que Este Repositório Demonstra

- Modelagem de sistemas elétricos com geradores, transformadores, linhas de transmissão, cargas e barramento infinito
- Conversão para sistema por unidade e cálculo de impedâncias equivalentes
- Análise de curto-circuito para faltas `3F`, `1FT`, `FF` e `2FT`
- Avaliação de tensões e correntes durante condições de falta
- Estudo de estabilidade transitória com base no critério das áreas iguais
- Organização de scripts para resolução de problemas acadêmicos de engenharia

## Tecnologias Utilizadas

- Python 3
- NumPy

## Estrutura Do Repositório

- `short_circuit_analysis.py` - Script principal e mais reutilizável para análise de rede e faltas
- `transient_stability_case_study.py` - Exemplo orientado a exercício, com foco em estabilidade transitória e análise de falta
- `README.md` - Documentação do projeto

## Como Executar

```bash
python -m pip install numpy
python short_circuit_analysis.py
python transient_stability_case_study.py
```

## Como Usar `short_circuit_analysis.py`

A principal seção editável pelo usuário é o bloco `DADOS DO SISTEMA`.

Nele, é possível ajustar:

- Valores de base do sistema
- Barras adicionais
- Geradores
- Barramentos infinitos
- Transformadores
- Linhas de transmissão
- Cargas
- Tipo e local da falta
- Saídas opcionais, como correntes em ramos, tensões em barras específicas e resultados de SCC

Após editar os dados de entrada, basta executar o script para gerar a saída completa do estudo.

## Nota Importante

Este repositório foi desenvolvido com apoio de IA como parte de um fluxo de estudo acadêmico. O objetivo é servir como material de aprendizagem, experimentação e apoio à resolução de exercícios.

Ele não deve ser tratado como software profissional de engenharia, e os resultados devem ser conferidos com a teoria da disciplina, o enunciado do problema e, quando necessário, com cálculos independentes.
