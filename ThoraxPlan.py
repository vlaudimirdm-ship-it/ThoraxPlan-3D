import os
import qt
import ctk
import vtk
import slicer
from slicer.ScriptedLoadableModule import (
    ScriptedLoadableModule,
    ScriptedLoadableModuleWidget,
    ScriptedLoadableModuleLogic,
)
from slicer.util import VTKObservationMixin


class ThoraxPlan(ScriptedLoadableModule):
    """Metadados do Módulo de Planejamento de Segmentectomia Torácica."""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent.title = "ThoraxPlan 3D - Segmentectomia"
        self.parent.categories = ["Thoracic Surgery"]
        self.parent.dependencies = []
        self.parent.contributors = ["Thoracic Surgery Team & AI Engineering"]
        self.parent.helpText = (
            "Módulo simplificado em 3 passos para planejamento cirúrgico de "
            "segmentectomias anatômicas pulmonares por vídeo (VATS) ou robótica (RATS)."
        )
        self.parent.acknowledgementText = (
            "Desenvolvido para cirurgiões torácicos com foco em usabilidade, "
            "automação e segurança oncológica das margens cirúrgicas."
        )


class ThoraxPlanWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Interface do Usuário (UI) simplificada e focada no cirurgião."""

    def __init__(self, parent=None):
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)
        self.logic = None
        self._parameterNode = None
        self.currentVolumeNode = None
        self.noduleFiducialNode = None
        self.marginModelNode = None
        self.segmentationNode = None

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)
        self.logic = ThoraxPlanLogic()

        # Layout Principal com espaçamento limpo
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(12, 12, 12, 12)

        # Cabeçalho Informativo
        headerBox = qt.QFrame()
        headerBox.setStyleSheet(
            "background-color: #1e293b; border-radius: 8px; padding: 10px;"
        )
        headerLayout = qt.QVBoxLayout(headerBox)
        titleLabel = qt.QLabel("🫁 ThoraxPlan 3D — VATS/RATS Planner")
        titleLabel.setStyleSheet(
            "color: #38bdf8; font-size: 15px; font-weight: bold;"
        )
        subtitleLabel = qt.QLabel("Planejamento anatômico de ressecção sublobar")
        subtitleLabel.setStyleSheet("color: #94a3b8; font-size: 11px;")
        headerLayout.addWidget(titleLabel)
        headerLayout.addWidget(subtitleLabel)
        self.layout.addWidget(headerBox)

        # ==========================================
        # PASSO 1: CARREGAR EXAME DICOM & IA
        # ==========================================
        step1Box = ctk.ctkCollapsibleButton()
        step1Box.text = "1. Exame Tomográfico & Anatomia por IA"
        self.layout.addWidget(step1Box)
        step1Layout = qt.QVBoxLayout(step1Box)

        loadBtnRow = qt.QHBoxLayout()
        self.loadDicomBtn = qt.QPushButton("📂 Carregar DICOM / Volume")
        self.loadDicomBtn.setStyleSheet(
            "font-size: 12px; font-weight: bold; height: 36px; background-color: #0284c7; color: white; border-radius: 6px;"
        )
        self.loadDicomBtn.connect("clicked(bool)", self.onLoadDicomClicked)
        loadBtnRow.addWidget(self.loadDicomBtn)

        self.loadSampleBtn = qt.QPushButton("🧪 Carregar TC Tórax Teste (CTChest)")
        self.loadSampleBtn.setStyleSheet(
            "font-size: 12px; font-weight: bold; height: 36px; background-color: #6366f1; color: white; border-radius: 6px;"
        )
        self.loadSampleBtn.connect("clicked(bool)", self.onLoadSampleClicked)
        loadBtnRow.addWidget(self.loadSampleBtn)

        step1Layout.addLayout(loadBtnRow)

        self.examStatusLabel = qt.QLabel("Nenhum exame carregado no momento.")
        self.examStatusLabel.setStyleSheet("color: #64748b; font-size: 11px;")
        step1Layout.addWidget(self.examStatusLabel)

        # Botão de Auto-Segmentação de Vias Aéreas e Vasos com IA
        self.runAiBtn = qt.QPushButton("⚡ Auto-Segmentar Vasos & Brônquios (IA)")
        self.runAiBtn.setStyleSheet(
            "font-size: 12px; font-weight: bold; height: 34px; background-color: #0f766e; color: white; border-radius: 6px;"
        )
        self.runAiBtn.connect("clicked(bool)", self.onRunAiClicked)
        step1Layout.addWidget(self.runAiBtn)

        self.aiStatusLabel = qt.QLabel("IA Pronta (TotalSegmentator / Lung Vessels)")
        self.aiStatusLabel.setStyleSheet("color: #64748b; font-size: 10px;")
        step1Layout.addWidget(self.aiStatusLabel)

        # ==========================================
        # PASSO 2: MARCAÇÃO DO NÓDULO E MARGEM
        # ==========================================
        step2Box = ctk.ctkCollapsibleButton()
        step2Box.text = "2. Nódulo e Margem Cirúrgica"
        self.layout.addWidget(step2Box)
        step2Layout = qt.QFormLayout(step2Box)

        self.markNoduleBtn = qt.QPushButton("🎯 Clicar no Centro do Nódulo (1 Clique)")
        self.markNoduleBtn.setStyleSheet(
            "font-size: 13px; font-weight: bold; height: 38px; background-color: #f59e0b; color: #0f172a; border-radius: 6px;"
        )
        self.markNoduleBtn.connect("clicked(bool)", self.onMarkNoduleClicked)
        step2Layout.addRow(self.markNoduleBtn)

        # Slider de Margem Oncológica
        self.marginSlider = ctk.ctkSliderWidget()
        self.marginSlider.minimum = 10.0
        self.marginSlider.maximum = 35.0
        self.marginSlider.value = 20.0
        self.marginSlider.suffix = " mm"
        self.marginSlider.connect("valueChanged(double)", self.onMarginChanged)
        step2Layout.addRow("Margem de Segurança:", self.marginSlider)

        # Status da lesão
        self.noduleInfoLabel = qt.QLabel("Lesão: Aguardando clique na TC...")
        self.noduleInfoLabel.setStyleSheet("color: #64748b; font-size: 11px;")
        step2Layout.addRow(self.noduleInfoLabel)

        # ==========================================
        # PASSO 3: VISUALIZAÇÃO E CONTROLE ANATÔMICO
        # ==========================================
        step3Box = ctk.ctkCollapsibleButton()
        step3Box.text = "3. Anatomia Crítica & Relações 3D"
        self.layout.addWidget(step3Box)
        step3Layout = qt.QVBoxLayout(step3Box)

        # Controles de Alternância (Toggles rápidos)
        togglesFrame = qt.QFrame()
        togglesLayout = qt.QVBoxLayout(togglesFrame)
        togglesLayout.setSpacing(6)

        self.chkMargin = qt.QCheckBox("Margem Oncológica 3D (Translúcida)")
        self.chkMargin.setChecked(True)
        self.chkMargin.connect("toggled(bool)", self.onToggleMargin)
        togglesLayout.addWidget(self.chkMargin)

        self.chkArteries = qt.QCheckBox("Artérias Segmentares (Vermelho)")
        self.chkArteries.setChecked(True)
        self.chkArteries.connect("toggled(bool)", lambda v: self.onToggleSegment("artery", v))
        togglesLayout.addWidget(self.chkArteries)

        self.chkVeins = qt.QCheckBox("Veias Intersegmentares (Azul)")
        self.chkVeins.setChecked(True)
        self.chkVeins.connect("toggled(bool)", lambda v: self.onToggleSegment("vein", v))
        togglesLayout.addWidget(self.chkVeins)

        self.chkBronchi = qt.QCheckBox("Árvore Brônquica (Ciano)")
        self.chkBronchi.setChecked(True)
        self.chkBronchi.connect("toggled(bool)", lambda v: self.onToggleSegment("airway", v))
        togglesLayout.addWidget(self.chkBronchi)

        step3Layout.addWidget(togglesFrame)

        # Ângulos Cirúrgicos Pré-Op (Câmera 1-clique)
        camLabel = qt.QLabel("Posições Cirúrgicas Pré-Op:")
        camLabel.setStyleSheet("font-weight: bold; font-size: 11px; margin-top: 6px;")
        step3Layout.addWidget(camLabel)

        camBtnRow = qt.QHBoxLayout()
        self.btnVatsView = qt.QPushButton("🎯 Trocarte VATS")
        self.btnVatsView.connect("clicked(bool)", self.onVatsViewClicked)
        self.btnHilumView = qt.QPushButton("👁️ Hilum Vascular")
        self.btnHilumView.connect("clicked(bool)", self.onHilumViewClicked)
        self.btnResetCam = qt.QPushButton("🔄 Reset 3D")
        self.btnResetCam.connect("clicked(bool)", self.onResetCamClicked)

        camBtnRow.addWidget(self.btnVatsView)
        camBtnRow.addWidget(self.btnHilumView)
        camBtnRow.addWidget(self.btnResetCam)
        step3Layout.addLayout(camBtnRow)

        # Espaçador no fundo
        self.layout.addStretch(1)

    # -------------------------------------------------------------
    # AÇÕES DOS BOTÕES E EVENTOS
    # -------------------------------------------------------------

    def onLoadDicomClicked(self):
        path = qt.QFileDialog.getOpenFileName(
            None,
            "Selecionar Volume Tomográfico (.nrrd, .nii, .dcm)",
            "",
            "Volumes Médicos (*.nrrd *.nii *.nii.gz *.mha *.dcm);;Todos os Arquivos (*)",
        )
        if not path:
            path = qt.QFileDialog.getExistingDirectory(None, "Ou Selecionar Pasta DICOM")

        if path:
            volumeNode = self.logic.loadDicomVolume(path)
            if volumeNode:
                self.currentVolumeNode = volumeNode
                self.examStatusLabel.setText(
                    f"✓ Carregado: {volumeNode.GetName()} (Pronto para análise)"
                )
                self.examStatusLabel.setStyleSheet("color: #10b981; font-weight: bold;")
                slicer.util.resetSliceViews()

    def onLoadSampleClicked(self):
        """Baixa e carrega instantaneamente uma TC de tórax real oficial do 3D Slicer."""
        self.examStatusLabel.setText("⏳ Baixando TC de Tórax de teste (CTChest)...")
        self.examStatusLabel.setStyleSheet("color: #6366f1; font-weight: bold;")
        slicer.app.processEvents()
        try:
            import SampleData
            self.currentVolumeNode = SampleData.downloadSample("CTChest")
            self.examStatusLabel.setText("✓ Carregado: CTChest (TC de Tórax Real)")
            self.examStatusLabel.setStyleSheet("color: #10b981; font-weight: bold;")
            slicer.util.resetSliceViews()
            slicer.util.resetThreeDViews()
            slicer.util.infoDisplay(
                "Tomografia de Tórax (CTChest) carregada!\n\n"
                "Agora você pode clicar no botão:\n"
                "'2. Clicar no Centro do Nódulo' para posicionar a lesão e ver a esfera da margem 3D."
            )
        except Exception as e:
            slicer.util.errorDisplay(f"Erro ao carregar amostra: {str(e)}")

    def onRunAiClicked(self):
        if not self.currentVolumeNode:
            slicer.util.warningDisplay("Por favor, carregue uma Tomografia (DICOM) primeiro.")
            return

        self.aiStatusLabel.setText("⏳ Executando segmentação de vasos e brônquios...")
        self.aiStatusLabel.setStyleSheet("color: #f59e0b; font-weight: bold;")
        slicer.app.processEvents()

        self.segmentationNode = self.logic.runAiSegmentation(self.currentVolumeNode)
        if self.segmentationNode:
            self.aiStatusLabel.setText("✓ Vias Aéreas e Vasos Segmentados com Sucesso!")
            self.aiStatusLabel.setStyleSheet("color: #10b981; font-weight: bold;")
        else:
            self.aiStatusLabel.setText("TotalSegmentator não instalado ou processamento cancelado.")
            self.aiStatusLabel.setStyleSheet("color: #ef4444;")

    def onMarkNoduleClicked(self):
        """Ativa a mira de marcação para o cirurgião clicar no nódulo."""
        self.noduleFiducialNode = self.logic.setupNoduleFiducial()
        self.noduleFiducialNode.AddObserver(
            slicer.vtkMRMLMarkupsNode.PointModifiedEvent, self.onNodulePointModified
        )
        interactionNode = slicer.app.applicationLogic().GetInteractionNode()
        selectionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLSelectionNodeSingleton")
        selectionNode.SetActivePlaceNodeID(self.noduleFiducialNode.GetID())
        interactionNode.SetCurrentInteractionMode(interactionNode.Place)
        self.noduleInfoLabel.setText("Clique diretamente sobre o nódulo na fatia axial...")

    def onNodulePointModified(self, caller, event):
        """Chamado automaticamente quando o ponto do nódulo é inserido ou movido."""
        if caller.GetNumberOfControlPoints() > 0:
            coords = [0.0, 0.0, 0.0]
            caller.GetNthControlPointPosition(0, coords)
            self.noduleInfoLabel.setText(
                f"Nódulo Localizado em: X={coords[0]:.1f}, Y={coords[1]:.1f}, Z={coords[2]:.1f}"
            )
            self.noduleInfoLabel.setStyleSheet("color: #f59e0b; font-weight: bold;")
            radius = self.marginSlider.value
            self.marginModelNode = self.logic.updateMarginSphere(coords, radius)

            # Centraliza as fatias 2D (Axial, Sagital, Coronal) na coordenada do nódulo
            try:
                slicer.modules.markups.logic().JumpSlicesToLocation(coords[0], coords[1], coords[2], True)
            except Exception:
                pass

    def onMarginChanged(self, value):
        if self.noduleFiducialNode and self.noduleFiducialNode.GetNumberOfControlPoints() > 0:
            coords = [0.0, 0.0, 0.0]
            self.noduleFiducialNode.GetNthControlPointPosition(0, coords)
            self.marginModelNode = self.logic.updateMarginSphere(coords, value)

    def onToggleMargin(self, visible):
        if self.marginModelNode:
            self.marginModelNode.SetDisplayVisibility(visible)

    def onToggleSegment(self, keyword, visible):
        if not self.segmentationNode:
            return
        segmentation = self.segmentationNode.GetSegmentation()
        for i in range(segmentation.GetNumberOfSegments()):
            segmentId = segmentation.GetNthSegmentID(i)
            segment = segmentation.GetSegment(segmentId)
            name = segment.GetName().lower()
            if keyword in name:
                self.segmentationNode.GetDisplayNode().SetSegmentVisibility(segmentId, visible)

    def onVatsViewClicked(self):
        self.logic.setCameraView(azimuth=35, elevation=15)

    def onHilumViewClicked(self):
        self.logic.setCameraView(azimuth=-60, elevation=5)

    def onResetCamClicked(self):
        slicer.util.resetThreeDViews()


class ThoraxPlanLogic(ScriptedLoadableModuleLogic):
    """Regras de negócio e operações computacionais."""

    def loadDicomVolume(self, path):
        try:
            return slicer.util.loadVolume(path)
        except Exception as e:
            slicer.util.errorDisplay(f"Erro ao carregar o exame: {str(e)}")
            return None

    def runAiSegmentation(self, volumeNode):
        """Dispara a extração automática de vasos pulmonares e árvore traqueobrônquica."""
        try:
            import TotalSegmentator
            tsLogic = TotalSegmentator.TotalSegmentatorLogic()
            segNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode", "ThoraxPlan_Anatomy")
            segNode.CreateDefaultDisplayNodes()

            # Executa a tarefa especializada 'lung_vessels'
            tsLogic.process(
                inputVolume=volumeNode,
                outputSegmentation=segNode,
                task="lung_vessels",
                fast=True,
            )
            self.applySurgicalColors(segNode)
            return segNode
        except ImportError:
            confirm = qt.QMessageBox.question(
                None,
                "Instalar Módulo de IA",
                "A extensão TotalSegmentator é necessária para automação completa. Deseja instalar agora via Extension Manager?",
            )
            if confirm == qt.QMessageBox.Yes:
                slicer.app.extensionsManagerModel().installExtensionFromServer("TotalSegmentator")
                slicer.util.infoDisplay("TotalSegmentator instalado com sucesso! Reinicie o Slicer para ativar.")
            return None
        except Exception as e:
            slicer.util.errorDisplay(f"Falha ao executar TotalSegmentator: {str(e)}")
            return None

    def applySurgicalColors(self, segmentationNode):
        """Aplica a paleta de cores cirúrgicas padrão (A=Vermelho, V=Azul, B=Ciano)."""
        segmentation = segmentationNode.GetSegmentation()
        for i in range(segmentation.GetNumberOfSegments()):
            segmentId = segmentation.GetNthSegmentID(i)
            segment = segmentation.GetSegment(segmentId)
            name = segment.GetName().lower()

            if "artery" in name or "pulmonary_artery" in name:
                segment.SetColor(0.93, 0.26, 0.26)  # Vermelho cirúrgico
            elif "vein" in name or "pulmonary_vein" in name:
                segment.SetColor(0.23, 0.51, 0.96)  # Azul cirúrgico
            elif "airway" in name or "trachea" in name or "bronch" in name:
                segment.SetColor(0.02, 0.71, 0.83)  # Ciano vias aéreas
            elif "lobe" in name or "lung" in name:
                segment.SetColor(0.06, 0.72, 0.51)  # Verde esmeralda parênquima

        # Ativa a representação em superfície 3D (Closed Surface)
        segmentationNode.CreateClosedSurfaceRepresentation()

    def setupNoduleFiducial(self):
        nodeName = "NoduleTarget"
        fiducialNode = slicer.mrmlScene.GetFirstNodeByName(nodeName)
        if not fiducialNode:
            fiducialNode = slicer.mrmlScene.AddNewNodeByClass(
                "vtkMRMLMarkupsFiducialNode", nodeName
            )
            displayNode = fiducialNode.GetDisplayNode()
            displayNode.SetSelectedColor(1.0, 0.8, 0.0)  # Amarelo
            displayNode.SetTextScale(3.0)
            displayNode.SetGlyphScale(3.0)
        return fiducialNode

    def updateMarginSphere(self, center, radius):
        """Gera uma esfera 3D translúcida representando a margem oncológica livre."""
        sphere = vtk.vtkSphereSource()
        sphere.SetCenter(center[0], center[1], center[2])
        sphere.SetRadius(radius)
        sphere.SetThetaResolution(32)
        sphere.SetPhiResolution(32)
        sphere.Update()

        modelNode = slicer.mrmlScene.GetFirstNodeByName("SurgicalSafetyMargin")
        if not modelNode:
            modelNode = slicer.mrmlScene.AddNewNodeByClass(
                "vtkMRMLModelNode", "SurgicalSafetyMargin"
            )
            modelNode.CreateDefaultDisplayNodes()
            displayNode = modelNode.GetDisplayNode()
            displayNode.SetColor(1.0, 0.2, 0.2)  # Vermelho cirúrgico
            displayNode.SetOpacity(0.35)  # Translúcido para ver o interior
            displayNode.BackfaceCullingOff()

        modelNode.SetAndObservePolyData(sphere.GetOutput())
        return modelNode

    def setCameraView(self, azimuth=0, elevation=0):
        threeDWidget = slicer.app.layoutManager().threeDWidget(0)
        threeDView = threeDWidget.threeDView()
        cameraNode = threeDView.cameraNode()
        camera = cameraNode.GetCamera()
        camera.Azimuth(azimuth)
        camera.Elevation(elevation)
        camera.OrthogonalizeViewUp()
        threeDView.resetFocalPoint()
        threeDView.renderWindow().Render()
