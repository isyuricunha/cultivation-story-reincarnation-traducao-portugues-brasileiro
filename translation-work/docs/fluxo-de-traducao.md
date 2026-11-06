# Fluxo de tradução

1. Rode o preflight indicado no [guia técnico](../README.md). Em caso de falha, pare antes de editar os lotes e registre o erro.
2. Leia o [briefing](briefing-do-jogo.md) e organize diretrizes e glossário com decisões verificáveis. Compare texto, contexto e vínculos antes de atribuir gênero ou voz.
3. Abra o lote que contém o próximo ID indicado por `resume`. Preencha apenas `PTBR` e preserve os marcadores. Deixe casos incertos vazios até revisar.
4. Rode `check` e revise o diff dos lotes. Em mudanças de fonte, consulte também o relatório da sincronização.
5. Após concluir todo o catálogo, rode `build` e `verify-output`. Revise o recibo e a árvore PTBR junto com as alterações de tradução.
