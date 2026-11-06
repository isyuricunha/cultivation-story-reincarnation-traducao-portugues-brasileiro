# Briefing de 轮回修仙传

## Premissa e estrutura

**轮回修仙传** é um RPG de simulação de vida de Collider Studio, publicado por OKJOY. O protagonista tenta superar as imposições de 天道 através de sucessivas vidas. A escolha do que fazer antes dos confrontos é parte da história. Cultivar, refinar pílulas, fabricar artefatos e sair em expedições disputam o mesmo tempo. A progressão entre vidas permite investir pontos de reencarnação e redefinir talentos e raízes espirituais. A apresentação oficial descreve mais de dez finais principais e rotas com parceiros de cultivo. [Página oficial](https://store.steampowered.com/app/3458620/)

O tom alterna entre fantasia de cultivo tradicional e referências bem-humoradas. O material oficial usa o arquétipo 龙傲天 para apresentar a escalada de poder. Em batalha, elementos, pílulas, artefatos e sequência de técnicas influenciam a preparação. Os cinco elementos pertencem ao repertório cosmológico do gênero. Evite confundir atributo elemental, raiz espiritual, reino de cultivo e técnica só porque aparecem juntos no combate. [Página oficial](https://store.steampowered.com/app/3458620/)

## Personagens e facções

| Identificador na apresentação oficial | Relação e contexto |
| --- | --- |
| 赵明月 | Discípula direta da 灵剑宗. A apresentação a descreve como reservada e orgulhosa. |
| 林小叶 | Amiga de infância do protagonista, descrita como brincalhona e travessa. |
| 苏琉璃 | Figura de destaque da facção 魔教逆天门, apresentada como 圣女, impetuosa e voluntariosa. |

As rotas podem transformar possíveis parceiras em aliadas ou adversárias. Essas informações identificam personagens e relações da apresentação oficial. Atribuir uma fala, destinatário ou pessoa descrita exige evidência dentro da cena. [Apresentação das rotas](https://store.steampowered.com/app/3458620/#aboutThisGame)

## Leitura das tabelas

- `DialogueInfo` traz apenas `Id` e `Chinese` como campos nativos. Não há ali coluna de locutor, destinatário, pronome ou gênero.
- `EventInfo` possui `Character`, `Location`, `PreDialog`, `WinDialog` e `LoseDialog`. Os três últimos vinculam eventos a diálogos. O catálogo expõe os vínculos encontrados. `Character` vem do evento e pode descrever a figura associada à cena. Não comprova quem fala em cada linha.
- Examine os diálogos vizinhos, os nomes citados e os pronomes explícitos antes de decidir concordância. Pode haver múltiplos eventos vinculados ao mesmo ID. O ID não é garantia de ordem narrativa, voz ou gênero.
- `RealmInfo` guarda estágios e referências de avanço. `TalentInfo` traz descrições e dicas dos talentos. `SkillInfo`, `ItemInfo` e `BuffBaseInfo` vinculam prosa a regras numéricas preservadas pelo mod. `EndingInfo` identifica finais e descrições. `TimelineInfo` fornece listas de IDs e pesos para sequências de eventos.
- Termos como 天道, 轮回, 修仙, 灵根, 境界, 法器 e 双修 exigem decisões consistentes entre narrativa e mecânica. Registre essas escolhas no glossário depois de comparar ocorrências. Para 双修, verifique a relação e o tom da rota antes de decidir a redação.

A fonte desta edição é o chinês simplificado. A Steam lista interface e legendas nesse idioma. O catálogo conserva a linha chinesa sem adicionar um intermediário em inglês. A demo tem diferenças de dados e salvamentos e fica fora do escopo. [Ficha e descrição oficiais](https://store.steampowered.com/app/3458620/)
