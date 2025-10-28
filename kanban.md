# TODO

- [X] Criar a lista de atividades a serem realizadas

- [X] Enviar termo de ciencia do fabiano

- [ ] Validar referencias
  - [ ] YOLOv3: An Incremental Improvement
  - [ ] Survey of Visual Surveillance Technologies for Public Safety
  - [ ] Person Re-identification: Past, Present and Future
  - [ ] Unsupervised Graph Association for Person Re-identification
  - [ ] Privacy-preserving video surveillance on edge devices using deep learning
  - [ ] Omni-Scale Feature Learning for Person Re-Identification
  - [ ] Beyond Part Models: Person Retrieval with Refined Part Pooling (and A Strong Convolutional Baseline)
  - [ ] Gradient-based learning applied to document recognition
  - [ ] Deep Learning
  - [ ] ImageNet Classification with Deep Convolutional Neural Networks
  - [ ] Very Deep Convolutional Networks for Large-Scale Image Recognition
  - [ ] Deep Residual Learning for Image Recognition
  - [ ] MobileNets: Efficient Convolutional Neural Networks for Mobile Vision Applications

- [ ] 2.1 Visão Computacional e Aprendizado Profundo
  - [x] 2.1.1 Redes Neurais Convolucionais (CNNs)
  - [ ] 2.1.2 Avanços recentes em deep learning aplicados à visão computacional

- [ ] 2.2 Detecção de Pessoas em Vídeo
  - [ ] 2.2.1 Modelos clássicos e limitações
  - [ ] 2.2.2 Detectores modernos em tempo real (YOLO, SSD, Faster R-CNN)

- [ ] 2.3 Person Re-Identification (ReID)
  - [ ] 2.3.1 Definição e importância da tarefa
  - [ ] 2.3.2 Principais desafios (oclusão, variação de pose, iluminação, vestimentas)
  - [ ] 2.3.3 Modelos e arquiteturas de ReID (OSNet, FastReID, PCB, MGN)
  - [ ] 2.3.4 Métricas de avaliação (mAP, Rank-1, CMC)

- [ ] 2.4 Arquiteturas de Sistemas para Múltiplas Câmeras
  - [ ] 2.4.1 Arquitetura Centralizada
  - [ ] 2.4.2 Arquitetura Edge-first
  - [ ] 2.4.3 Comparação entre abordagens

- [ ] 2.5 Protocolos e Tecnologias de Comunicação
  - [ ] 2.5.1 Protocolos de transmissão de vídeo (RTSP, WebRTC, SRT)
  - [ ] 2.5.2 Protocolos de comunicação de dados (gRPC, MQTT, Protobuf)
  - [ ] 2.5.3 Questões de privacidade e segurança

- [ ] 3 Desenvolvimento

- [ ] 4 Conclusão e resultados

- [ ] Avaliar outros modelos de IA

- [x] [TR] Desenvolvimento do servidor
  - [x] [TR] Criar estrutura de classe para o servidor
  - [x] [TR] Criar estrutura de log
  - [x] [TR] Realziar a digestão em threads
  - [x] [TR] Debugar porque o servidor demora para receber as mensagens dos nós
  - [X] [TR] Debugar problema de expection of frame ....
  - [X] [TR] Correção o servidor tá criando thread sem limite, o reId deveria ser feito via fila igual o handle client
  - [X] [TR] A fila do REID não está andando
  - [ ] [TR] As mensagens estão ficando desordenadas
  - [ ] [TR] Teste do deep_sort_realtime
  - [ ] [TR] Refatorar o recebimento de imagens para uma forma mais otimizada e que me fale qual é o nó

- [ ] Analise e avaliação das arquiteturas
  - [ ] Estudar como os datasets estão estruturados
  - [ ] [TR] Padronizar o servidor para salvar da mesma forma que o dataset
  - [ ] [EF] Padronizar o servidor para salvar da mesma forma que o dataset
  - [ ] Criar um script para comparar os datasets das arquiteturas com o original e levantar métricas de acuracia, perda de pacotes e confiabilidade
  - [ ] Criar automação com git action para subir e já gerar as analises

- [ ] [EF] Desenvolver arquitetura de arquivos e leitura dinamica de config.yaml
- [ ] [EF] Desenvolver o nó
- [ ] [EF] Desenvolver o servidor
