# PinLearn — Mandarin Study App

App desktop para estudo de Mandarim com PyQt6 + SQLite.

## Como instalar e rodar

```bash
pip install PyQt6 matplotlib
python app.py
```

## Estrutura dos arquivos

```
mandarin_app/
├── app.py              # Interface gráfica principal
├── database.py         # Banco de dados SQLite + toda a lógica de dados
├── mandarin.db         # Criado automaticamente na primeira execução
├── licao14_exemplo.csv # CSV pronto para importar o vocabulário da Lição 14
└── README.md
```

## Como importar o vocabulários

1. Abra o app → aba **Vocabulário**
2. Clique em **⬆ Importar CSV**
3. Selecione o arquivo `vocabulario_exemplo.csv`
4. Pronto! 36 palavras importadas.

## Formato do CSV para importação

| Coluna       | Obrigatório | Exemplo           |
|-------------|-------------|-------------------|
| character   | ✓           | 北方               |
| pinyin      |             | běifāng           |
| translation |             | Norte             |
| gram_type   |             | p.l.              |
| example     |             | 他是北方人。        |
| chapter     |             | 14                |
| notes       |             | Observações       |
| difficulty  |             | 1 (1, 2 ou 3)     |

## Sistema SRS (Revisão Espaçada)

Usa o algoritmo **SM-2** (mesmo base do Anki):
- Ao avaliar um card, escolha: ✗ Errei / Difícil / Bom / Fácil / Muito fácil
- Cards errados voltam no dia seguinte
- Cards fáceis têm intervalos crescentes (1d → 6d → n*fator)
- O "fator de facilidade" aumenta com acertos e diminui com erros

## Modos de estudo

- **Caractere → Tradução**: vê o caractere + pinyin, lembra a tradução
- **Tradução → Caractere**: vê a tradução, lembra o caractere e pinyin
- **Pinyin → Caractere**: vê o pinyin + dica da tradução, lembra o caractere
