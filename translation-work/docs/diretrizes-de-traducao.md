# Diretrizes de tradução PT-BR de 轮回修仙传

Documento vivo: decisões novas entram aqui e no glossário conforme aparecem. Em caso de dúvida, seguir `game-localization` (fonte normativa linguística) e o briefing do jogo.

## Fonte e tom

- Fonte é o chinês simplificado (ZH_CN), sem ponte em inglês.
- Tom: fantasia de cultivo (xianxia) com humor pontual. Diálogos soam fala em PT-BR; descrições de habilidade, item e efeito são entendidas na primeira leitura.
- Narrador em segunda pessoa: 你 → "você".
- Preservar humor, gíria e conteúdo maduro na força do original, sem suavizar.
- Vozes: cada personagem tem registro próprio (ver briefing). Antes de decidir quem fala ou de quem se fala, consultar falas vizinhas e os vínculos de eventos; o vínculo não comprova o locutor.
- Quando o original deixar gênero ou identidade em aberto, manter a abertura com frase natural; não fixar gênero por conveniência.

## Integridade estrutural

- Editar apenas o campo PTBR nos lotes JSONL. Campo vazio significa pendente.
- Marcadores numerados {0}, {1} preservados em quantidade; ordem pode se ajustar à sintaxe do PT quando necessário.
- Quebras de linha literais preservadas com a mesma contagem.
- Colchetes 【】 mantidos como no original: são delimitadores visuais do jogo.
- Números, valores de atributos, probabilidades e unidades preservados exatamente (67%, 1000, 15 anos).
- Pontuação chinesa convertida: ，。：？！、 → , . : ? ! , ; aspas "…" do original viram aspas retas "...".
- Reticências do original ("...") preservadas como "...".

## Convenções de texto

- Tratamento: "você" em toda a interface e narrativa.
- Protagonista: o original não fixa gênero, mas o talento 直男系统 (Sistema Hétero) e as rotas o descrevem como homem; onde a gramática exige, usa-se o masculino. Frases que dispensam marca de gênero ficam neutras. Revisar se surgir evidência contrária (seleção de gênero do jogo).
- Caixa de frase em títulos e rótulos (só inicial maiúscula e nomes próprios), sem copiar padrões de caixa do chinês.
- Linhas de delta de atributos no padrão "+10 de Compreensão, -20 de Longevidade.", preservando o ponto final quando o original tem.
- Reino de cultivo (境界) = reino; estágio (期) = estágio; patentes de alquimia e forja usam "nível".
- Graus de qualidade (次品/下品/中品/上品/极品/仙品) entram como sufixo concordado: "Núcleo Demoníaco Supremo", "Pílula de Lavar a Medula Baixa".
- Ano do jogo: "ano N da Era Imortal".
- Nominalizações de estatística seguem o glossário; mesma mecânica = mesmo termo em todo o catálogo.
- Travessões do original (——) nunca entram no texto PT: converter em dois-pontos, vírgula ou ponto.

## Processo

- Trabalho em passadas de 250 entradas, lote a lote; check ao fim de cada passada e revisão do diff antes do commit.
- Casos incertos ficam com PTBR vazio para revisão posterior; dúvida registrada nas notas do glossário.
- Termo alterado no glossário exige revisar as ocorrências anteriores na mesma passada ou na revisão transversal final.
- Ao fim do catálogo: revisão transversal de fluidez, concordância, vozes, nomes e terminologia; depois check, build e verify-output.
