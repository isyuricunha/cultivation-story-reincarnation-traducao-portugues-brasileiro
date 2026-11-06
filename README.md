[![Arte oficial de Reincarnation of a Cultivator (轮回修仙传)](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/3458620/4af3fb95010dd60f89242eaeffc12a7df1709797/header.jpg)](https://store.steampowered.com/app/3458620/)

# Reincarnation of a Cultivator (轮回修仙传)

**Tradução comunitária para português brasileiro**

[Steam](https://store.steampowered.com/app/3458620/) · [Releases](https://github.com/isyuricunha/cultivation-story-reincarnation-traducao-portugues-brasileiro/releases) · [Discord Vai Brasil](https://discord.gg/uFEwSMwUYb)

## Sobre o jogo

Cada reencarnação dá ao seu cultivador outra chance de desafiar o destino. Entre um confronto e outro, você decide se vale mais treinar, preparar pílulas ou sair em expedição. Talentos, raízes espirituais e a ordem das técnicas mudam suas opções em combate. As escolhas de cada vida abrem caminhos para novos aliados, rivais e finais.

## O que a tradução cobre

O projeto traduz diretamente do chinês simplificado. O escopo atual inclui **diálogos, eventos, itens, habilidades, talentos e finais**, além de outros textos das tabelas do jogo. Os menus gráficos e as imagens com texto têm cobertura separada. A exibição de acentos em todas as telas ainda precisa de validação no jogo.

## Download

Quando houver uma versão disponível, abra [Releases](https://github.com/isyuricunha/cultivation-story-reincarnation-traducao-portugues-brasileiro/releases), confira a compatibilidade indicada e baixe **PTBR.zip** em **Assets**. Esse é o pacote de instalação. Os arquivos **Source code** são destinados a quem quer consultar ou trabalhar no projeto.

## Instalação

Você precisa do jogo para **Windows** e do **BepInEx 5 para Unity Mono** configurado na instalação.

1. Feche o jogo. Na Steam, abra **Gerenciar → Explorar arquivos locais** para localizar a pasta de `Re-xiuxian Legend.exe`.
2. Se estiver atualizando a tradução, faça uma cópia de `BepInEx/plugins/CultivationPtBr/` antes de substituir os arquivos.
3. Extraia **PTBR.zip** na pasta do executável. Ao final, `CultivationPtBr.dll` e `tables.ptbr.json` devem estar em `BepInEx/plugins/CultivationPtBr/`.
4. Abra o jogo. O plugin aplica os textos das tabelas compatíveis durante o carregamento.

Para desinstalar, feche o jogo e remova apenas `BepInEx/plugins/CultivationPtBr/`. Se quiser voltar a uma versão anterior da tradução, restaure a cópia dessa pasta.

## Compatibilidade e suporte

A versão **1.2.1.18.1**, build **21565338**, foi a base usada na preparação do projeto. O plugin confere os dados originais de cada tabela antes de aplicar a tradução. Se uma atualização mudar esses dados, a tabela afetada pode aparecer em chinês até que haja um pacote compatível. A demo, o Steam Deck e a combinação com outros mods ainda precisam de testes.

Se encontrar um erro de tradução ou instalação, informe a **versão do jogo**, a **versão do pacote** e a **tela ou o evento** em que ocorreu. Uma captura ajuda a localizar o problema. Se estiver usando outros mods, liste quais estão ativos. [Discord Vai Brasil](https://discord.gg/uFEwSMwUYb) · [Issues no GitHub](https://github.com/isyuricunha/cultivation-story-reincarnation-traducao-portugues-brasileiro/issues)

## Contribuições

Sugestões de termos, correções e relatos com contexto ajudam na revisão. Para enviar alterações de texto, consulte as regras de contribuição e o guia da toolkit. [Como contribuir](./CONTRIBUTING.md) · [Guia técnico](./translation-work/README.md)

Conheça também o [portal de traduções](https://traducao.yuricunha.com/). Quem quiser apoiar o projeto pode usar o Pix voluntário `pix@yuricunha.com`.

## Créditos e licença

- **Coordenação e manutenção da tradução** — Yuri Cunha
- **Desenvolvimento do jogo** — Collider Studio
- **Publicação do jogo** — OKJOY

O material original do projeto que seus autores podem licenciar segue a **CC BY-NC-SA 4.0**. O reaproveitamento exige crédito, indicação das alterações e uso não comercial. Adaptações devem ser distribuídas sob a mesma licença ou uma licença compatível autorizada. Os direitos sobre o jogo, seus textos, suas marcas e sua arte pertencem aos respectivos titulares. [Licença completa](./LICENSE)

A autorização adicional permite que o titular do jogo e a editora autorizada incorporem e distribuam comercialmente o material coberto, com crédito. [Permissão para integração oficial](./GAME-DEVELOPER-PERMISSION.md)
