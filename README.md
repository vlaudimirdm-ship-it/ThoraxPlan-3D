# ThoraxPlan 3D — VATS & RATS Segmentectomy Planner

Extensão simplificada para o **3D Slicer** projetada especificamente para cirurgiões torácicos, reduzindo a curva de aprendizado e eliminando dezenas de cliques manuais no planejamento pré-operatório de segmentectomias anatômicas pulmonares por vídeo (VATS) ou robótica (RATS).

---

## 🎯 Objetivo
Transformar o fluxo complexo do 3D Slicer em uma interface intuitiva de **3 passos**:
1. **Importação Rápida:** Carregamento automático de séries tomográficas DICOM de tórax.
2. **Nódulo & Margens:** Marcação com 1 único clique no centro da lesão com cálculo dinâmico da esfera de margem oncológica livre (10 mm a 35 mm).
3. **Anatomia Crítica 3D:** Visualização limpa e desobstruída com alternância imediata de artérias segmentares (vermelho), veias intersegmentares (azul), árvore brônquica (ciano) e transparência do parênquima pulmonar.

---

## 🚀 Como Instalar e Testar no seu 3D Slicer

1. Abra o **3D Slicer**.
2. No menu superior, vá em:
   * **Edit** ➔ **Application Settings** (ou `Cmd + ,` no Mac).
3. Clique na aba **Modules** à esquerda.
4. Na seção **Additional module paths**, clique no botão **Add**.
5. Selecione a pasta deste módulo:
   ```text
   /Users/vlaudimird.marques/3D_Slicer_New/ThoraxPlan
   ```
6. Clique em **OK** e reinicie o 3D Slicer quando solicitado.
7. O módulo estará disponível na barra de módulos na categoria **Thoracic Surgery** ➔ **ThoraxPlan 3D - Segmentectomia**.

---

## 📦 Estrutura do Módulo

```text
ThoraxPlan/
├── ThoraxPlan.py         # Código-fonte principal (UI simplificada + Lógica MRML/VTK)
└── README.md             # Documentação e instruções de instalação
```

---

## 🌐 Publicação no seu GitHub

Para subir este projeto para o seu GitHub pessoal como um repositório independente:

```bash
# 1. Crie um novo repositório vazio no seu GitHub (ex: ThoraxPlan-3D)
# 2. No terminal desta pasta:
git remote add my-github https://github.com/<SEU-USUARIO>/ThoraxPlan-3D.git
git push -u my-github main
```

---

## 📄 Licença
Distribuído sob a licença de código aberto BSD (compatível com 3D Slicer).

