# PROJECT GENESIS

Laboratório gravitacional desktop em Python: explore sistemas planetários em 3D e veja os vetores que realmente determinam seus movimentos. Desenvolvido para apresentações de Geometria Analítica e Cálculo Vetorial.

## Executar no Windows

Recomendado: Python 3.12 de 64 bits e drivers gráficos atualizados. Não requer contas, APIs, serviços pagos ou conexão à internet durante o uso. Internet é necessária apenas para instalar as dependências.

Nesta pasta já foi preparado um ambiente virtual. No PowerShell:

```powershell
.\.venv\Scripts\python.exe main.py
```

Em outra máquina, instale Python 3.12 e execute na pasta do projeto:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

O ambiente local foi criado por `uv`, portanto pode não conter `pip`. Para reinstalar dependências nele, use `.\.tools\bin\uv.exe pip install --python .venv\Scripts\python.exe -r requirements-dev.txt` ou execute `python -m ensurepip` com o Python do ambiente.

## Experiência

- Abertura animada, estrela central, oito planetas e uma lua. Texturas, anéis, estrelas de fundo e guias são procedurais; nenhuma imagem é baixada.
- Gravitação N-body com NumPy e integrador Velocity Verlet de passo fixo.
- Sete experimentos: sistema Genesis, órbita circular, binário, encontro, queda por velocidade insuficiente, escape e colisão/fusão.
- Criar, editar e remover estrelas, planetas, luas e asteroides; editar posição, velocidade, massa, nome, cor e raios.
- Vetores independentes de posição, velocidade, aceleração, força de uma fonte e força resultante. Componentes X/Y/Z e legenda colorida.
- Câmera livre, seleção por clique ou lista paginada, foco e acompanhamento.
- Campo gravitacional amostrado no plano XZ com sondas sem massa (tecla B).
- Trilhas históricas, limpeza e comprimento configurável; previsão tracejada em cenários de exatamente dois corpos.
- Modo Professor com fórmulas, componentes, módulos, deslocamento, distância e substituições numéricas atualizadas.
- Telemetria integrada ao universo, com um gráfico por aba e exportação PNG opcional.
- Interface com painéis compactos, lista de corpos e aba separada de cenários.
- Criação simplificada: tipos e cores prontos, posição por clique ou coordenadas e movimento inicial sugerido.
- Ajustes de G, passo, suavização, escala das setas, limite de corpos, qualidade e fusão experimental.
- Colisões entre planetas com clarão, onda de choque e destroços visuais temporários; absorção de corpos por estrelas.

## Controles

| Ação | Controle |
|---|---|
| Orbitar câmera | Arrastar com botão direito |
| Mover câmera | Arrastar com botão central |
| Zoom | Roda do mouse |
| Navegar livremente | Segurar botão direito + W/A/S/D/Q/E |
| Pausar / executar | Espaço ou botão |
| Avançar um passo | N ou botão Passo |
| Reiniciar cenário | R |
| Focar / seguir seleção | F / T |
| Visão geral | Home |
| Modo Professor / gráficos | P / G |
| Campo gravitacional | B |
| Criar / remover corpo | Insert / Delete |
| Aumentar / reduzir taxa de tempo | Botões + / − |
| Ocultar painéis | H |
| Desselecionar / fechar editor | Esc |

Para **criar**, clique em **+ Adicionar corpo**, escolha o tipo e uma cor, e clique em **Escolher na cena**. Mova o cursor sobre a grade e clique para escolher o lugar. Você volta ao editor para confirmar; nenhum corpo é criado antes disso. Esc volta da escolha de posição sem descartar o formulário. Também é possível digitar X, Y e Z diretamente.

A escolha por clique projeta o cursor no **plano XZ na altura Y informada** (zero por padrão). Isso elimina a ambiguidade de um clique 2D no espaço 3D. É possível orbitar e aproximar a câmera durante a escolha; posições atrás da câmera ou raios paralelos ao plano não são aceitos. Para mudar a altura, digite Y antes de escolher o lugar.

Os movimentos **Orbitar**, **Parado** e **Escape** preenchem um estado inicial coerente. Orbitar sugere velocidade tangencial relativa ao corpo mais massivo, considerando G, as massas e a suavização; não é uma garantia de órbita estável no sistema N-body. Escape usa 1,6 vezes a velocidade circular sugerida. Parado usa velocidade zero no referencial global. Sem fontes, a sugestão é zero.

Para **editar**, selecione um corpo e clique em Editar. **Avançado** contém massa, tamanho visual, velocidade XYZ, raio de colisão e RGB. Uma velocidade digitada substitui a sugestão automática. Corpos existentes começam em movimento personalizado, preservando sua velocidade. Os formulários pausam a física; confirmar ou cancelar restaura o estado anterior. Tab avança entre campos da página. Use ponto decimal e vírgula entre componentes (`2.7, 0, 0`). Cores RGB vão de 0 a 1.

O botão **Fonte** alterna o corpo responsável pela força individual rosa e pelo cálculo detalhado no Modo Professor. A resultante roxa soma a influência de todos os outros corpos. Sem corpo selecionado, o painel mostra energia e momento globais. A Lua está na segunda página da lista inicial.

**Reiniciar** restaura o cenário demonstrativo selecionado e seus parâmetros padrão; ele não é um botão de desfazer edições. Dados são mantidos em memória durante a sessão, sem persistência automática de sistemas.

## Matemática e unidades

A física utiliza AU (unidade astronômica), ano juliano e massa solar (Msol). O valor convencional adotado é `G = 4π² AU³/(Msol ano²)`. É uma convenção astronômica aproximada, apropriada aos experimentos, não um conjunto de efemérides de alta precisão. O plano orbital principal é XZ; Y representa altura.

Para o corpo `i`, com fonte `j`:

```text
d_ij = r_j − r_i                         [AU]
F_ij = G m_i m_j d_ij / (|d_ij|² + ε²)^(3/2)
F_i = Σ(j ≠ i) F_ij                      [Msol AU/ano²]
a_i = F_i / m_i                          [AU/ano²]
```

Com `ε = 0`, recuperamos a lei inversa do quadrado de Newton. A suavização de Plummer (`ε > 0`) regulariza encontros próximos. **É um recurso numérico, não uma propriedade física da gravidade.** Corpos coincidentes com suavização zero são rejeitados.

Velocity Verlet:

```text
r(t+h) = r(t) + v(t)h + a(t)h²/2
a(t+h) = gravidade recalculada nas novas posições
v(t+h) = v(t) + [a(t) + a(t+h)]h/2
```

O passo padrão é `h = 0.0005 ano`. A renderização utiliza o estado mais recente; o acumulador da física avança em passos fixos independentes da taxa de quadros. A velocidade indicada, por exemplo `0.15 ano/s real`, é a taxa solicitada; em sobrecarga a aplicação limita os subpassos e informa que o tempo simulado está mais lento. Não aumenta silenciosamente o passo físico.

Diagnósticos consistentes com o potencial suavizado:

```text
E = Σ (m_i |v_i|²/2) − Σ(i<j) G m_i m_j / sqrt(|d_ij|² + ε²)
P = Σ m_i v_i
```

Energia é expressa em `Msol AU²/ano²`, momento linear em `Msol AU/ano`. Edições externas e mudanças de parâmetros estabelecem nova referência energética e limpam gráficos/trilhas. Fusões são inelásticas: preservam massa e momento linear, mas não energia mecânica. Em fusões, posição e velocidade são médias ponderadas pela massa; os volumes dos raios se somam. O indicador de variação de energia inclui essa dissipação.

## Física versus apresentação

- Uma unidade da cena corresponde a uma AU de posição. Raios visuais são ampliados e **não entram no cálculo da gravidade**.
- O raio físico de colisão é um campo separado, em AU. Corpos são massas pontuais para as forças; não há dinâmica de corpos extensos.
- **Absorção estelar:** ao atingir a superfície visível de uma estrela (ou o raio de colisão, se maior), o corpo é incorporado e não reaparece do outro lado. Essa superfície é uma regra didática de interação, independente das forças gravitacionais. A estrela preserva nome, cor e identidade; massa e momento são somados. Isso permanece ativo mesmo com colisões planetárias desativadas.
- **Impactos planetários:** usam os raios de colisão físicos configuráveis, não os tamanhos visuais ampliados. Colisões estão ligadas por padrão e podem ser desativadas em Ajustes. O corpo resultante preserva massa e momento. Clarões e fragmentos são apenas efeitos gráficos; não acrescentam massas ao N-body. Duram até 1,8 segundo real, com 18 fragmentos em Baixa ou 38 em Alta e limite de 12 efeitos simultâneos.
- O sistema inicial é uma arquitetura didática inspirada no Sistema Solar, com distâncias e fases adaptadas, não uma reprodução das posições reais. A lua utiliza separação didática dentro da esfera de Hill terrestre aproximada.
- A seta de posição parte da origem inercial até o corpo. As outras partem do corpo. Vetores de força/aceleração/velocidade usam comprimento logarítmico e multiplicador visual configurável; seus módulos físicos são os valores do painel, nunca o comprimento da seta.
- O campo mostra acelerações reais calculadas em uma grade XZ; suas setas usam escala logarítmica limitada e atualizam a 2 Hz. As sondas não influenciam os corpos. A lua pode ficar visualmente oculta pela Terra devido à ampliação dos raios; use a lista para selecioná-la e consultar seu estado.
- Força individual e força resultante são conceitos distintos apenas em sistemas com três ou mais corpos. Com dois corpos elas coincidem.
- Linhas circulares tênues são **guias iniciais**, não órbitas calculadas. As trilhas coloridas mostram posições realmente percorridas. A previsão tracejada é uma integração independente de dois corpos a partir do instante em que se clica em Prever; não se atualiza a cada quadro, não inclui fusões e usa horizonte de uma escala de período kepleriano (limitada a 2500 passos). Em trajetórias abertas, esse horizonte não é um período orbital real.

## Gráficos e desempenho

A tecla **G** abre a telemetria dentro da própria aplicação. As abas mostram **Energia**, **Velocidade**, **Aceleração**, **Distância** e **Posição**, uma visualização por vez. Energia destaca a variação percentual em relação à referência, com energia total no rodapé; se a referência for zero, mostra o valor absoluto para evitar divisão por zero. Os eixos têm valores explícitos, sem offsets numéricos ocultos. A escala mínima evita ampliar ruído numérico insignificante em séries quase constantes.

Selecione um corpo e uma fonte antes de abrir as séries individuais. Esc ou G fecha o painel; Espaço pausa/executa e N avança um passo enquanto o gráfico está aberto. A física continua evoluindo normalmente. **Salvar PNG** exporta a aba atual para `exports/`, usando Matplotlib sem abrir outra janela. Matplotlib só é importado na exportação.

Gráficos atualizados a no máximo 1 Hz; até 4000 amostras, coletadas a cada 10 passos físicos. Trilhas usam o mesmo intervalo; comprimento padrão de 900 pontos por corpo. Limpar trilhas não limpa as séries de telemetria. Uma série sem amostras mostra uma orientação, sem inventar dados.

Forças são calculadas em lote, com custo O(N²). O padrão limita a 128 corpos; a configuração permite 2–512, sem promessa de tempo real no limite superior. O cenário inicial contém 10 corpos. O fundo usa uma única malha de pontos; vetores e trilhas são redesenhados a 10 Hz. Qualidade Baixa reduz a resolução das texturas. Não há efeitos pesados de pós-processamento. Em um notebook intermediário, comece com 10–30 corpos.

Limitações: passo fixo, ausência de adaptação geral em encontros extremos, fusões sem fragmentação física/rotação, luz principal associada à primeira estrela, sem relatividade, atmosfera física ou marés. A detecção de colisões testa o segmento entre posições inicial e prevista, resolve o primeiro contato e integra o tempo restante após a fusão; assim evita atravessamentos retilíneos rápidos entre passos. O segmento aproxima a trajetória curva dentro do passo: reduza o passo em encontros muito curvos e acompanhe energia. A previsão de dois corpos não trata N-body nem absorções/colisões. Não há arraste contínuo de planetas já existentes: reposicione-os pelo editor, por clique no plano ou coordenadas. Suavização não substitui resolução temporal adequada. Texturas e explosões são ilustrativas.

## Arquitetura

```text
main.py                         entrada e argumentos
simulation/
  body.py                       validação de corpos e vetores
  gravity.py                    forças, acelerações e energia
  integrator.py                 Velocity Verlet
  physics.py                    estado, tempo, histórico e fusões
  scenarios.py                  sete experimentos
  creation.py                   projeção geométrica e velocidade sugerida
  collisions.py                 geometria de contato e eventos
visualization/
  universe.py                   coordenação do aplicativo Ursina
  planet_renderer.py            texturas e corpos procedurais
  vector_renderer.py            setas e componentes
  orbit_renderer.py             trilhas e previsão
  camera.py                     exploração e acompanhamento
  placement.py                  grade e prévia de posicionamento na cena
  collision_effects.py          explosões e absorções procedurais temporárias
interface/
  hud.py                        painéis e controles integrados
  body_editor.py                criação, edição e configurações
  educational_mode.py           explicações e valores físicos
  charts.py                     telemetria integrada e exportação PNG
  chart_data.py                 séries e limites numéricos dos eixos
  theme.py                      componentes e identidade visual
tests/test_physics.py           validação numérica sem janela
diagnostics.py                  verificação dos fluxos do aplicativo
```

## Verificação

```powershell
# Testes matemáticos, sem abrir janela:
.\.venv\Scripts\python.exe -m unittest discover -s tests -v

# Alternativa com pytest (requirements-dev.txt):
.\.venv\Scripts\python.exe -m pytest -q

# Abrir por alguns segundos e encerrar:
.\.venv\Scripts\python.exe main.py --smoke-test 8

# Exercitar os objetos da aplicação e gerar capturas do próprio renderizador:
.\.venv\Scripts\python.exe main.py --verify
```

`--verify` abre uma janela, testa os fluxos e grava PNGs em `exports/` (ignorado pelo Git). Testa projeção do cursor no plano, prévia sem criar corpo, criação, edição, remoção, ajustes, todos os cenários, vetores, Professor, previsão, abas de telemetria e exportação. Não substitui uma avaliação manual de seleção por mouse, câmera e legibilidade no computador da apresentação.

Os testes verificam distância, orientação, lei inversa do quadrado, soma de forças, aceleração, movimento uniforme, Verlet, suavização, fusão e conservação aproximada de energia/momento. A aceleração gravitacional de um corpo de teste é independente da própria massa quando as fontes são fixadas; para uma mesma força externa prescrita, vale `a=F/m`.

## Roteiro de apresentação

1. Explore o sistema, pause e selecione Terra; ative velocidade e aceleração.
2. Abra Modo Professor, alterne a fonte e mostre deslocamento, força individual e resultante.
3. Crie um planeta e edite massa e velocidade. Compare a trajetória antes e depois.
4. Carregue Estrelas binárias, mostre o centro de massa e a previsão tracejada.
5. Compare velocidade insuficiente com escape; por fim, carregue Colisão e fusão.
6. Abra os gráficos e discuta conservação, dissipação em fusões e erros de integração.

Documentação das dependências: [Ursina](https://www.ursinaengine.org/api_reference.html), [NumPy](https://numpy.org/doc/), [Matplotlib](https://matplotlib.org/stable/).
