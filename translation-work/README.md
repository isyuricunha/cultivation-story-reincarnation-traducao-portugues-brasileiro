# Toolkit de localização — 轮回修仙传

A base é **Re-xiuxian Legend 1.2.1.18.1 / build 21565338**, Unity 2021.3 Mono para Windows. O catálogo usa chinês simplificado (`ZH_CN`) como idioma-fonte. Leia o [briefing](docs/briefing-do-jogo.md) antes da primeira rodada. As escolhas de estilo e terminologia são responsabilidade da tradução e devem ser registradas nas diretrizes e no glossário quando houver decisões concretas.

## Primeiro uso

Depois de clonar ou atualizar, execute da raiz:

```sh
python3 translation-work/toolkit.py doctor
```

A estação de tradução é Ubuntu Server 24.04 ARM64 com Python 3.10+. O preflight é somente leitura, verifica a arquitetura, a cadeia de hashes LF/binários, o catálogo e a aplicação de um delta a um fixture JSON válido. A autoria e o build do delta usam a biblioteca padrão. O plugin Windows já vem compilado e tem hash verificado. O preflight não carrega o runtime do jogo. **Windows AMD64 foi usado para desenvolvimento. A execução em Ubuntu ARM64 aguarda este preflight.** Se falhar, envie o erro antes de começar a traduzir.

O checkout público inclui a toolkit. Importe a fonte local com `update-sources --game-root CAMINHO` ou receba o diretório `translation-work/translations/` por um canal autorizado. Rode o preflight novamente para validar o catálogo. Depois, leia o briefing, estabeleça as diretrizes e o glossário e use `resume` para identificar o próximo ID. Edite apenas `PTBR` em `translations/batch-*.jsonl`. Campo vazio representa trabalho pendente. Preserve marcadores como `{0}` e `{1}`, tags e referências. O contexto de eventos não comprova o locutor.

## Comandos

| Comando | Efeito |
| --- | --- |
| `status`, `resume`, `check` | Validam o catálogo aceito, verificam os textos editados e mostram pendências. |
| `apply payload.json [--replace]` | Aplica por ID, exige a geração ativa, protege valores existentes e relata recusas individualmente. |
| `extract [--game-root CAMINHO] [--batch-size N]` | Importação inicial. Recusa catálogo existente. |
| `update-sources [--game-root CAMINHO] [--dry-run]` | Descobre a instalação via Steam ou caminho conhecido, verifica identidade e sincroniza com a base aceita. Use o caminho explícito se houver zero ou mais de uma instalação. |
| `sync --source-file BUNDLE` | Importa um bundle original explícito e compara seus registros com a última geração aceita. |
| `sync [--source-root DIRETORIO]` | Lê um conjunto local no formato de EN e confirma que os TextAssets correspondem ao bundle. |
| `diff [--game-root CAMINHO]` | Mostra o último relatório local ou compara uma instalação sem gravar. |
| `build`, `verify-output` | Gera o delta completo e a DLL em PTBR, ou valida a saída existente sem nova extração. |
| `recover [--rollback txn-ID]` | Reverte promoção interrompida ou desfaz um checkpoint preservado, desde que o estado atual corresponda ao diário. |
| `gc --dry-run`, `gc` | Mostram ou removem checkpoints elegíveis. A limpeza recusa transações pendentes. |

Prefixe cada comando com `python3 translation-work/toolkit.py` (ou `python` no Windows). Exemplo de payload, com valores apenas ilustrativos do formato:

```json
{"generation":"HASH_DE_STATUS","entries":[{"id":"DialogueInfo/7/Chinese","PTBR":"TEXTO_REVISADO"}]}
```

## Fontes, atualização e recuperação

Apenas a importação do UnityFS precisa de UnityPy. Em ambiente virtual local, instale `python -m pip install -r translation-work/requirements-import.txt`. Para revisar uma nova base, rode `update-sources --game-root "CAMINHO" --dry-run` antes de repetir sem a opção. O importador mantém uma cópia local byte a byte em `EN/Re-xiuxian Legend_Data/StreamingAssets/json` e extrai payloads exatos em `EN/TextAsset/`. O nome EN segue a convenção do projeto. Consulte o [perfil de formato](docs/formato-localizacao.md).

O catálogo aceito em `translations/source-catalog.json` permite comparar sem depender da cópia local anterior. Mesmos ID, texto e contexto preservam PT-BR. Edições retornam à fila de revisão. Registros retirados aparecem no relatório local, junto com textos e traduções anteriores. Mudança apenas na posição é classificada separadamente. Compare relatórios antes de atualizar Git. Histórico durável depende de manter a versão anterior em Git ou num ambiente de trabalho autorizado.

`EN/` fica ignorada para evitar incluir acidentalmente o bundle do jogo. O catálogo e os lotes contêm trechos do jogo em chinês. Confirme com os titulares a autorização para distribuir esse corpus antes de publicar os arquivos de trabalho em repositório público. O ZIP de instalação inclui somente o plugin do projeto e o delta PT-BR.

O journal em `translation-work/.state/` protege operações de escrita. Uma aplicação pequena grava somente lotes alterados e seus backups. A retenção padrão é 10 checkpoints e 128 MiB. A promoção exige espaço adicional temporário, verificado antes de começar. Depois de interrupção, execute `recover`, revise e repita a operação. Use `gc --dry-run` para consultar a limpeza. Guarde em Git o histórico necessário antes de podar checkpoints.

## Saída e releases

O build exige preenchimento de todos os registros do escopo e valida a estrutura do delta. O recibo fica em `translation-work/build-manifest.json`. A publicação usa somente `PTBR/BepInEx/plugins/CultivationPtBr/{CultivationPtBr.dll,tables.ptbr.json}`. O CI usa `verify-output`, gera `PTBR.zip` e publica a partir de `main`, começando em `v1.0.0` e avançando o patch para saída alterada. O changelog compara o catálogo da versão anterior. Alterações apenas nos lotes não disparam publicação. A partir de um pacote válido, baixe o ZIP em Releases e siga o [guia público](../README.md#instalação).

No Windows, rode `python -B -m unittest discover -s translation-work/tests -v` e `python translation-work/toolkit.py doctor --target host`. Para testar o parser compilado no Windows sem abrir o jogo, rode `pwsh -File translation-work/tests/smoke-runtime.ps1 -GameRoot "CAMINHO"` após importar as tabelas. O cliente de Releases tem testes com servidor HTTP local. A execução real no GitHub e a execução do novo plugin com o catálogo completo no jogo ainda precisam de validação.

A licença pública [CC BY-NC-SA 4.0](../LICENSE) cobre o material autorizado. A [permissão comercial para integração oficial](../GAME-DEVELOPER-PERMISSION.md) e a [autorização de contribuições](../CONTRIBUTING.md) são independentes do ZIP.
