# O objetivo desse trabalho é criar uma aplicação de uma rede centralizada de detecção de pressoas

o fluxo de funcionamento do sistema será o grafo que projeta a estrutura fisica do ambiente ou seja, caso a sala A tenha uma porta(ou qualquer conexão)com a sala B então haverá uma aresta entre essas 2

o servidor ficará responsavel por:

- Comandar todos os nós a pararem, ou iniciarem a rotina
- Processar as imagens das pessoas detectadas e definir seu id (realizar o reId)

## Problemas atuais

- Atualmente o sistema tá identificando as pessoas de forma diferente
- Parece que quando o video acaba ele continua lendo
- Tá consumindo muito processamento, devo parar de criar threads e começar a colocar em uma fila de jobs
  Aqui eu entendi que o que tá pesando mais no processamento são os nós porém o servidor também tem que ser otimizado
  Nos nós ainda é preciso criar mais threads para o envio ordenado das imagens
  No servidor é apenas necessario uma fila de jobs para garantir que as threads sejam liberadas de acordo com a filanização do seu serviço

## Problemas

- Atualmente o processo de reId é muito limitado, ele tem que comparar com todos as pessoas presentes para definir com quem mais parece
  Possivel solução ( descartar pessoas que não estavam presentes no último frame e descartar pessoas que já foram identificadas )
- Talvez trabalhar uma rotina para conferir se todos estão conectado e como será a comunicação deles

# Projeto básico

## O servidor

1. Lê o arquivo que possui o grafo que projeta o ambiente
2. Abre o terminal e espera a resposta
3. No terminal de comandos, caso start ele envia uma mensagem para que todos os nós comecem a rotina
4. No terminal de comandos, caso exit ele deve enviar uma mensagem para todos os nós encerrarem e depois deve encerrar
5. Na rotina de receber mensagem das imagens deve realizar o reId

## O nó

1. Espera o primeiro comando do servidor
2. Ao receber a mensagem de start ele inicia a rotina de detecção
3. Ao receber a mensagem de exit deve encerrar

# Abordagens

Dado o problema: Multiplas cameras ligadas por wifi com o objetivo de capturar imagens de pessoas, identificalas com um mesmo id independente de onde foram capturadas temos as seguintes abordagens

## Modelo Híbrido (edge detection com YOLO simples + envia o crop para o servidor)

- O modelo detecta o a pessoa via YOLO, cropa e transmite a imagem para o servidor

## Edge-First (edge detection com YOLO simples + embedding + envia os vetores do embedding e metadados (timestamp, camera_id, bbox))

- Cada nó deve capturar a imagem e aplicar o yolo para identificar pessoas e enviar para o servidor a imagem cortada contendo apenas a pessoa
- O servidor fica responsavel por identificar a pessoa atribuir o id e salvar em memoria para as proximas re identificações

## Terceira

- Cada nó deve capturar a imagem e aplicar o yolo para identificar pessoas e enviar para o servidor a imagem cortada contendo apenas a pessoa e de onde veio a informação
- o servidor deve além de aplicar o reId em cada pessoa realizar um controle de pesquisa inteligente com o seguinte criterio
- Cada nó só pode identificar pessoas que estiveram em nós vizinhos ou que estão presentes no próprio nó
- a Ideia é separar ainda mais as funções uma para o featureExtraction e uma para a atribuição e controle do Id

## Serverless

- cada nó deve capturar as pessoas e realizar o reId o atribuição e controle de id se dá por uma comunicação entre os nós, ou seja, não vai haver a transmissão de imagens e sim a transmissão de informações sobres as pessoas havistadas em cada camera

## Como vamos fazer?

- Usar webRTC para trasmitir as imagens e gRPC para transmitir dados
- Isso é uma aplicação dentro de uma rede real
- Explicar o problema para caracterizar o meu problema
- Como vou usar as tecnicas e porque
- Rede mesh
- sincronização da rede
- arquitetura
