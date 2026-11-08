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
        self.noduleFiducialNode = None
        self.marginModelNode = None

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
        # PASSO 1: CARREGAR EXAME DICOM
        # ==========================================
        step1Box = ctk.ctkCollapsibleButton()
        step1Box.text = "1. Exame Tomográfico (DICOM)"
        self.layout.addWidget(step1Box)
        step1Layout = qt.QVBoxLayout(step1Box)

        self.loadDicomBtn = qt.QPushButton("📂 Selecionar Pasta DICOM / TC Tórax")
        self.loadDicomBtn.setStyleSheet(
            "font-size: 13px; font-weight: bold; height: 38px; background-color: #0284c7; color: white; border-radius: 6px;"
        )
        self.loadDicomBtn.connect("clicked(bool)", self.onLoadDicomClicked)
        step1Layout.addWidget(self.loadDicomBtn)

        self.examStatusLabel = qt.QLabel("Nenhum exame carregado no momento.")
        self.examStatusLabel.setStyleSheet("color: #64748b; font-size: 11px;")
        step1Layout.addWidget(self.examStatusLabel)

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
        togglesLayout.addWidget(self.chkArteries)

        self.chkVeins = qt.QCheckBox("Veias Intersegmentares (Azul)")
        self.chkVeins.setChecked(True)
        togglesLayout.addWidget(self.chkVeins)

        self.chkBronchi = qt.QCheckBox("Árvore Brônquica (Ciano)")
        self.chkBronchi.setChecked(True)
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
        directory = qt.QFileDialog.getExistingDirectory(
            None, "Selecionar Pasta DICOM do Exame"
        )
        if directory:
            volumeNode = self.logic.loadDicomVolume(directory)
            if volumeNode:
                self.examStatusLabel.setText(
                    f"✓ Carregado: {volumeNode.GetName()} (Pronto para análise)"
                )
                self.examStatusLabel.setStyleSheet("color: #10b981; font-weight: bold;")
                slicer.util.resetSliceViews()

    def onMarkNoduleClicked(self):
        """Ativa a mira de marcação para o cirurgião clicar no nódulo."""
        self.noduleFiducialNode = self.logic.setupNoduleFiducial()
        self.noduleFiducialNode.AddObserver(
            slicer.vtkMRMLMarkupsNode.PointModifiedEvent, self.onNodulePointModified
        )
        # Ativa o modo de inserção interativo de ponto único
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
            # Atualiza o modelo esférico da margem cirúrgica
            radius = self.marginSlider.value
            self.marginModelNode = self.logic.updateMarginSphere(coords, radius)

    def onMarginChanged(self, value):
        if self.noduleFiducialNode and self.noduleFiducialNode.GetNumberOfControlPoints() > 0:
            coords = [0.0, 0.0, 0.0]
            self.noduleFiducialNode.GetNthControlPointPosition(0, coords)
            self.marginModelNode = self.logic.updateMarginSphere(coords, value)

    def onToggleMargin(self, visible):
        if self.marginModelNode:
            self.marginModelNode.SetDisplayVisibility(visible)

    def onVatsViewClicked(self):
        self.logic.setCameraView(azimuth=35, elevation=15)

    def onHilumViewClicked(self):
        self.logic.setCameraView(azimuth=-60, elevation=5)

    def onResetCamClicked(self):
        slicer.util.resetThreeDViews()


class ThoraxPlanLogic(ScriptedLoadableModuleLogic):
    """Regras de negócio e operações computacionais."""

    def loadDicomVolume(self, dicomDir):
        try:
            return slicer.util.loadVolume(dicomDir)
        except Exception as e:
            slicer.util.errorDisplay(f"Erro ao carregar o exame: {str(e)}")
            return None

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

