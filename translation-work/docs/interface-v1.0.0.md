# Interface observada no teste da v1.0.0

Os textos editáveis das telas de início, talentos e HUD estão em
[`ui/catalog.jsonl`](../ui/catalog.jsonl). Preencha apenas `PTBR`. Cada linha
registra o componente e o caminho no prefab. Nos formatos dinâmicos, conserve
`{0}`. A duração de evento tem uma entrada para 1 ano e outra para os demais
valores. O contador principal usa o rótulo antes do número e oculta o sufixo
original no fim.

| Tela | Origem verificada |
| --- | --- |
| Menu inicial | Textos dos botões no prefab `MainPanel` do bundle `ui`. |
| Criação do personagem | `BSTalentPanel` contém título, nome, raiz espiritual e botões. O valor padrão `张不凡` também é atribuído em `GameModule.BSTalent.Presentation.BSTalentPanelPresenter.OnShow`. O valor editável do jogador fica preservado. |
| HUD | `GamePropertyPanel` contém atributos e contador de ano. Vida, energia, cultivo e barras de experiência recebem textos de `Atlpile.GamePropertyPanelEntity.SetHealth`, `SetLingLi`, `SetXiuWei`, `SetLianQi`, `SetLianDan` e variantes de nível máximo. |
| Cartas de evento | `Xpzhnl.OtherEvent.get_TypeName` fornece `事件`. `Xpzhnl.GameEventBtnEntity.SetSpendYearTxt` acrescenta `年` à duração. Nome e descrição já vêm de `EventInfo`. |
| Barra inferior | `GameItemPanel/Background/txt_Equip` e `txt_FaBao` são rótulos de texto. |

O perfil de layout pede ajuste de tamanho em uma linha para os nomes dos três
talentos, o estágio de cultivo e os títulos de alquimia e forja. Os nomes
continuam vindo das tabelas existentes. Confira em jogo truncamentos, legibilidade
e alinhamento dos cartões e do HUD após preencher os rótulos.

## Arte pendente

O bundle `ui` contém os sprites `首页_Logo` (logo), `首页_设置按钮`
(engrenagem com rótulo), `主界面_物品_法术按钮` (livro de técnicas) e
`主界面_物品_背包按钮` (mochila). Os emblemas dos cinco elementos e a
caligrafia nas capas dos cartões também precisam de revisão visual. Essa etapa
precisa de arte localizada e verificação de atlas e transparência antes de
empacotar as substituições.
