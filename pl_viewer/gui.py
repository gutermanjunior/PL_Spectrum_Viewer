"""Interface desktop científica (PySide6 + Matplotlib)."""
from __future__ import annotations
from copy import deepcopy
import json
from pathlib import Path

import numpy as np
from PySide6.QtCore import QObject, QThread, Qt, Signal, QSize
from PySide6.QtGui import QColor, QBrush
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QPlainTextEdit, QPushButton,
    QSplitter, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
    QHeaderView, QTabWidget, QScrollArea, QFormLayout, QDoubleSpinBox,
    QSizePolicy, QGridLayout
)
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt import NavigationToolbar2QT

from .models import Spectrum, ScanReport
from .readers import scan_source
from .exporting import export_curves_csv, export_scaled_curves_csv, export_metadata_json
from .plotting import (
    PlotSettings, VerticalAnnotation, HorizontalAnnotation, COLOR_OPTIONS, LINE_OPTIONS,
    render_plot, wavelength_nm_from_display, format_wavelength,
    signal_display, signal_v_from_display, LEGEND_FIELDS, FONT_FAMILIES, LEGEND_LOCATIONS,
    export_vector, create_export_figure, save_session, load_session, find_spectrum_maximum, validate_factor,
    PLOT_COLOR_CYCLE,
)
from .selection_order import SelectionOrder
from .multipanel import (Composition, PanelState, render_composition,
                         create_composition_export_figure, augment_session_json,
                         restore_composition_from_session)


class ResponsiveFigureCanvas(FigureCanvasQTAgg):
    """Provide a compact Qt layout hint; let Qt resize the Matplotlib figure.

    The base canvas calculates sizeHint from Figure.bbox.  A 13.5-inch figure
    could request over 1300 pixels and starve adjacent QSplitter panels.
    """
    def sizeHint(self):
        return QSize(520, 365)

    def minimumSizeHint(self):
        return QSize(160, 120)


class ScanTask(QObject):
    done = Signal(object)
    error = Signal(str)

    def __init__(self, path: str, recursive: bool, unit: str):
        super().__init__()
        self.path = path
        self.recursive = recursive
        self.unit = unit

    def run(self):
        try:
            data = scan_source(self.path, self.recursive, self.unit,
                               cancelled=lambda: QThread.currentThread().isInterruptionRequested())
            self.done.emit(data)
        except Exception as exc:
            self.error.emit(f"{type(exc).__name__}: {exc}")


class PLMainWindow(QMainWindow):
    def __init__(self, startup_path: str | None = None):
        super().__init__()
        self.setWindowTitle("PL Spectrum Viewer v1.5 · Fotoluminescência")
        self.resize(1550, 910)
        self.source: str | None = None
        self.pending_source: str | None = None
        self.records: list[Spectrum] = []
        self.by_uid: dict[str, Spectrum] = {}
        self.scan_thread: QThread | None = None
        self.scan_worker: ScanTask | None = None
        self._setting_up = False
        self.plot_settings = PlotSettings()
        self.annotations: list[VerticalAnnotation | HorizontalAnnotation] = []
        self.display_factors: dict[str, float] = {}  # indexed by acquisition uid
        self.plot_order = SelectionOrder()  # order of checkbox clicks, independent of table sorting
        self.peak_uid: str | None = None
        self._plot_axes = []
        self._drag_annotation: int | None = None
        self._annotation_setting_up = False
        self.composition = Composition()
        self._composition_initialized = False
        self._last_plot_mode = 0
        self._single_view = None
        self._changing_panel = False
        self._construct_ui()
        if startup_path:
            self.load_path(startup_path)

    def _construct_ui(self):
        base = QWidget(self)
        self.setCentralWidget(base)
        root = QVBoxLayout(base)
        root.setContentsMargins(9, 9, 9, 9)

        top = QHBoxLayout()
        self.open_folder = QPushButton("Abrir pasta…")
        self.open_zip = QPushButton("Abrir ZIP…")
        self.reload_button = QPushButton("Atualizar")
        self.recursive_box = QCheckBox("Incluir subpastas")
        self.dat_unit = QComboBox()
        self.dat_unit.addItem("DAT: detectar unidade", "auto")
        self.dat_unit.addItem("DAT: Å (forçar)", "angstrom")
        self.dat_unit.addItem("DAT: nm (forçar)", "nm")
        for w in (self.open_folder, self.open_zip, self.reload_button, self.recursive_box, self.dat_unit):
            top.addWidget(w)
        top.addStretch(1)
        root.addLayout(top)
        self.source_label = QLabel("Nenhuma pasta selecionada")
        self.source_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        root.addWidget(self.source_label)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        root.addWidget(splitter, 1)

        # Esquerda: pesquisa e seleção de medidas.
        sidebar = QWidget()
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(2, 2, 2, 2)
        side.addWidget(QLabel("<b>Espectros disponíveis</b>"))
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Pesquisar amostra, arquivo ou configuração…")
        side.addWidget(self.search_field)
        filters = QHBoxLayout()
        self.sample_filter = QComboBox()
        self.slit_filter = QComboBox()
        self.lockin_filter = QComboBox()
        for combo in (self.sample_filter, self.slit_filter, self.lockin_filter):
            combo.setMinimumWidth(100)
            filters.addWidget(combo)
        side.addLayout(filters)
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Exibir\n(ordem)", "Amostra", "Fenda\n(nome, µm)",
                                              "Lock-in\n(mV)", "T indicada", "Avisos", "Arquivo"])
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setColumnWidth(0, 82)
        self.table.setColumnWidth(1, 75)
        self.table.setColumnWidth(2, 90)
        self.table.setColumnWidth(3, 78)
        self.table.setColumnWidth(4, 134)
        self.table.setColumnWidth(5, 60)
        side.addWidget(self.table, 1)
        buttons = QHBoxLayout()
        self.mark_visible = QPushButton("Marcar visíveis")
        self.unmark_all = QPushButton("Desmarcar tudo")
        buttons.addWidget(self.mark_visible)
        buttons.addWidget(self.unmark_all)
        side.addLayout(buttons)
        self.count_label = QLabel("0 espectros")
        side.addWidget(self.count_label)
        order_hint = QLabel("As cores seguem a ordem em que você marca as curvas. "
                            "Desmarcar e remarcar envia a curva para o final.")
        order_hint.setWordWrap(True)
        side.addWidget(order_hint)

        # Each operation targets ONE highlighted row (not every checked plot curve).
        side.addWidget(QLabel("<b>Análise da série destacada</b>"))
        series_hint = QLabel("Selecione uma linha da tabela acima. As caixas 'Exibir' são independentes.")
        series_hint.setWordWrap(True)
        side.addWidget(series_hint)
        multiplier_row = QHBoxLayout()
        multiplier_row.addWidget(QLabel("Multiplicar sinal por"))
        self.series_factor = QDoubleSpinBox()
        self.series_factor.setRange(-1000000, 1000000)
        self.series_factor.setDecimals(8)
        self.series_factor.setSingleStep(0.1)
        self.series_factor.setValue(1.0)
        self.series_factor.setKeyboardTracking(False)
        self.series_factor.setToolTip("Fator adimensional aplicado somente à curva exibida e às exportações explicitamente ajustadas; os dados brutos não mudam.")
        multiplier_row.addWidget(self.series_factor, 1)
        side.addLayout(multiplier_row)
        factor_buttons = QHBoxLayout()
        self.apply_factor = QPushButton("Aplicar fator")
        self.reset_factor = QPushButton("Restaurar ×1")
        factor_buttons.addWidget(self.apply_factor)
        factor_buttons.addWidget(self.reset_factor)
        side.addLayout(factor_buttons)
        peak_buttons = QHBoxLayout()
        self.find_maximum = QPushButton("Localizar máximo")
        self.clear_maximum = QPushButton("Limpar destaque")
        peak_buttons.addWidget(self.find_maximum)
        peak_buttons.addWidget(self.clear_maximum)
        side.addLayout(peak_buttons)
        self.peak_result_label = QLabel("O máximo será calculado nos pontos medidos da série destacada.")
        self.peak_result_label.setWordWrap(True)
        self.peak_result_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.peak_result_label.setMinimumHeight(55)
        side.addWidget(self.peak_result_label)
        splitter.addWidget(sidebar)

        # Centro: Matplotlib incorporado e navegação.
        graph_panel = QWidget()
        chart = QVBoxLayout(graph_panel)
        chart.setContentsMargins(3, 2, 3, 2)
        chart_options = QHBoxLayout()
        chart_options.addWidget(QLabel("Modo:"))
        self.plot_mode = QComboBox()
        self.plot_mode.addItems(["Sobreposição — sinal bruto", "Curvas separadas — sinal bruto",
                                 "Sobreposição — normalizadas", "Composição — vários painéis"] )
        chart_options.addWidget(self.plot_mode)
        self.grid_box = QCheckBox("Grade")
        self.grid_box.setChecked(True)
        self.legend_box = QCheckBox("Legenda")
        self.legend_box.setChecked(True)
        chart_options.addWidget(self.grid_box)
        chart_options.addWidget(self.legend_box)
        chart_options.addStretch(1)
        chart.addLayout(chart_options)
        self.composition_bar = QWidget()
        comp_bar = QVBoxLayout(self.composition_bar)
        comp_bar.setContentsMargins(1, 1, 1, 1)
        comp_row1 = QHBoxLayout()
        comp_row1.addWidget(QLabel("Layout"))
        self.comp_layout = QComboBox()
        for key in ("1x1", "1x2", "2x1", "2x2"):
            self.comp_layout.addItem(key.replace('x',' × '), key)
        self.comp_layout.setCurrentIndex(1)
        comp_row1.addWidget(self.comp_layout)
        comp_row1.addWidget(QLabel("Painel ativo"))
        self.comp_panel = QComboBox()
        for i in range(4):
            self.comp_panel.addItem(f"({chr(97+i)})", i)
            if i >= 2:
                self.comp_panel.model().item(i).setEnabled(False)
        comp_row1.addWidget(self.comp_panel)
        self.comp_share_x = QCheckBox("Compartilhar X")
        self.comp_share_y = QCheckBox("Compartilhar Y")
        comp_row1.addWidget(self.comp_share_x)
        comp_row1.addWidget(self.comp_share_y)
        comp_row1.addStretch()
        comp_bar.addLayout(comp_row1)
        comp_row2 = QHBoxLayout()
        comp_row2.addWidget(QLabel("Sinal"))
        self.comp_signal = QComboBox()
        self.comp_signal.addItem("Bruto (V/mV)", 0)
        self.comp_signal.addItem("Normalizado", 2)
        comp_row2.addWidget(self.comp_signal)
        comp_row2.addWidget(QLabel("Espaço H"))
        self.comp_hspace = QDoubleSpinBox()
        self.comp_hspace.setRange(.02, .85)
        self.comp_hspace.setDecimals(2)
        self.comp_hspace.setSingleStep(.03)
        self.comp_hspace.setValue(self.composition.hspace)
        comp_row2.addWidget(self.comp_hspace)
        comp_row2.addWidget(QLabel("Espaço V"))
        self.comp_wspace = QDoubleSpinBox()
        self.comp_wspace.setRange(.02, .85)
        self.comp_wspace.setDecimals(2)
        self.comp_wspace.setSingleStep(.03)
        self.comp_wspace.setValue(self.composition.wspace)
        comp_row2.addWidget(self.comp_wspace)
        comp_row2.addStretch()
        comp_bar.addLayout(comp_row2)
        hint = QLabel("As caixas à esquerda escolhem as curvas do painel ativo. "
                      "Troque o painel para editar curvas, título, legenda, e anotações independentes. "
                      "As cores seguem a ordem de marcação em cada painel.")
        hint.setWordWrap(True)
        comp_bar.addWidget(hint)
        chart.addWidget(self.composition_bar)
        self.composition_bar.hide()
        # The screen preview is responsive; configured inch dimensions are
        # applied ONLY to a separate export figure (PDF/SVG/PNG).
        self.figure = Figure(figsize=(5.2, 3.65), dpi=100)
        self.canvas = ResponsiveFigureCanvas(self.figure)
        self.canvas.setMinimumSize(160, 120)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        chart.addWidget(NavigationToolbar2QT(self.canvas, graph_panel))
        chart.addWidget(self.canvas, 1)
        self.chart_note = QLabel("Selecione as curvas. Valores adquiridos em V, com exibição selecionável em V ou mV.")
        self.chart_note.setWordWrap(True)
        chart.addWidget(self.chart_note)
        # Two rows keep the central panel usable on smaller screens.
        export_bar = QGridLayout()
        self.save_graph = QPushButton("Exportar gráfico…")
        self.save_csv = QPushButton("Exportar CSV bruto…")
        self.save_scaled_csv = QPushButton("Exportar CSV ajustado…")
        self.save_json = QPushButton("Exportar metadados JSON…")
        for index, widget in enumerate((self.save_graph, self.save_csv,
                                         self.save_scaled_csv, self.save_json)):
            export_bar.addWidget(widget, index // 2, index % 2)
        chart.addLayout(export_bar)
        splitter.addWidget(graph_panel)

        # Direita: dados de aquisição e editor de figuras, em abas separadas.
        details = QTabWidget()
        info_panel = QWidget()
        detail = QVBoxLayout(info_panel)
        detail.setContentsMargins(6, 6, 6, 6)
        detail.addWidget(QLabel("<b>Metadados e rastreabilidade</b>"))
        detail.addWidget(QLabel("Temperatura efetiva (informada pelo operador):"))
        temp_box = QHBoxLayout()
        self.temp_input = QLineEdit()
        self.temp_input.setPlaceholderText("Ex.: 77")
        self.temp_apply = QPushButton("Aplicar às marcadas")
        temp_box.addWidget(self.temp_input)
        temp_box.addWidget(self.temp_apply)
        detail.addLayout(temp_box)
        self.temp_clear = QPushButton("Limpar temperatura manual das marcadas")
        detail.addWidget(self.temp_clear)
        temp_note = QLabel('Na lista, "T indicada" vem somente do nome do arquivo. Uma temperatura informada pelo operador é registrada separadamente nos metadados desta sessão.')
        temp_note.setWordWrap(True)
        detail.addWidget(temp_note)
        self.metadata_view = QPlainTextEdit()
        self.metadata_view.setReadOnly(True)
        self.metadata_view.setPlaceholderText("Selecione uma linha na tabela para consultar os metadados.")
        detail.addWidget(self.metadata_view, 1)
        details.addTab(info_panel, "Metadados")

        editor_scroll = QScrollArea()
        editor_scroll.setWidgetResizable(True)
        editor = QWidget()
        editor_layout = QVBoxLayout(editor)
        editor_layout.setContentsMargins(7, 7, 7, 7)
        editor_layout.setSpacing(7)
        editor_layout.addWidget(QLabel("<b>Formatação do gráfico</b>"))
        form = QFormLayout()
        self.title_edit = QLineEdit(self.plot_settings.title)
        self.subtitle_edit = QLineEdit(self.plot_settings.subtitle)
        self.xlabel_edit = QLineEdit(self.plot_settings.x_label)
        self.ylabel_edit = QLineEdit(self.plot_settings.y_label)
        self.footer_edit = QPlainTextEdit(self.plot_settings.footer)
        self.footer_edit.setMaximumHeight(65)
        self.show_title_box = QCheckBox("Mostrar título")
        self.show_subtitle_box = QCheckBox("Mostrar subtítulo")
        self.show_footer_box = QCheckBox("Mostrar nota inferior")
        for box in (self.show_title_box, self.show_subtitle_box, self.show_footer_box):
            box.setChecked(True)
            box.setToolTip("Desmarque para ocultar e devolver a área ocupada aos dados.")
        form.addRow(self.show_title_box, self.title_edit)
        form.addRow(self.show_subtitle_box, self.subtitle_edit)
        form.addRow("Eixo X", self.xlabel_edit)
        form.addRow("Eixo Y", self.ylabel_edit)
        form.addRow(self.show_footer_box, self.footer_edit)
        self.axis_unit = QComboBox()
        self.axis_unit.addItem("nm", "nm")
        self.axis_unit.addItem("Å (ångström)", "angstrom")
        form.addRow("Unidade X", self.axis_unit)
        self.signal_unit = QComboBox()
        self.signal_unit.addItem("V (volts)", "V")
        self.signal_unit.addItem("mV (milivolts)", "mV")
        self.signal_unit.setToolTip("Os dados instrumentais são armazenados em V; mV = 1000 × V. Não modifica arquivos.")
        form.addRow("Unidade Y", self.signal_unit)
        self.xmin_edit = QLineEdit()
        self.xmax_edit = QLineEdit()
        self.ymin_edit = QLineEdit()
        self.ymax_edit = QLineEdit()
        for w in (self.xmin_edit, self.xmax_edit, self.ymin_edit, self.ymax_edit):
            w.setPlaceholderText("auto")
        limits_a = QHBoxLayout()
        limits_a.addWidget(QLabel("mín."))
        limits_a.addWidget(self.xmin_edit)
        limits_a.addWidget(QLabel("máx."))
        limits_a.addWidget(self.xmax_edit)
        form.addRow("Limites X", limits_a)
        limits_b = QHBoxLayout()
        limits_b.addWidget(QLabel("mín."))
        limits_b.addWidget(self.ymin_edit)
        limits_b.addWidget(QLabel("máx."))
        limits_b.addWidget(self.ymax_edit)
        form.addRow("Limites Y", limits_b)
        editor_layout.addLayout(form)
        editor_layout.addWidget(QLabel("<b>Tipografia e dimensões da figura</b>"))
        dimensions_info = QLabel(
            "A pré-visualização ajusta-se automaticamente ao painel central. "
            "A largura e a altura em polegadas definem apenas o arquivo PDF/SVG/PNG exportado."
        )
        dimensions_info.setWordWrap(True)
        editor_layout.addWidget(dimensions_info)
        appearance = QFormLayout()
        self.font_family = QComboBox()
        for f in FONT_FAMILIES:
            self.font_family.addItem(f, f)
        appearance.addRow("Fonte", self.font_family)
        self.style_spins: dict[str, QDoubleSpinBox] = {}

        def style_spin(key: str, title: str, minimum: float, maximum: float,
                       decimals: int = 1, step: float = 1, suffix: str = ""):
            widget = QDoubleSpinBox()
            widget.setRange(minimum, maximum)
            widget.setDecimals(decimals)
            widget.setSingleStep(step)
            widget.setSuffix(suffix)
            widget.setValue(getattr(self.plot_settings, key))
            self.style_spins[key] = widget
            appearance.addRow(title, widget)

        style_spin("figure_width_in", "Largura exportada", 5, 24, 2, .5, " in")
        style_spin("figure_height_in", "Altura exportada", 3.5, 16, 2, .5, " in")
        style_spin("font_title", "Título · pt", 8, 36)
        style_spin("font_subtitle", "Subtítulo · pt", 7, 28)
        style_spin("font_axes", "Nomes dos eixos · pt", 7, 28)
        style_spin("font_ticks", "Números dos eixos · pt", 6, 24)
        style_spin("font_legend", "Legenda · pt", 6, 24)
        style_spin("font_annotations", "Anotações · pt", 6, 24)
        style_spin("font_footer", "Nota inferior · pt", 6, 22)
        editor_layout.addLayout(appearance)

        editor_layout.addWidget(QLabel("<b>Curvas, grade e espaçamento</b>"))
        line_form = QFormLayout()
        self.line_style = QComboBox()
        for label, value in LINE_OPTIONS.items():
            self.line_style.addItem(label, value)
        line_form.addRow("Estilo das curvas", self.line_style)
        editor_layout.addLayout(line_form)
        metrics = QFormLayout()
        for key, caption, lo, hi, decimals, step in (
            ("line_width", "Espessura das curvas (pt)", .35, 8, 2, .1),
            ("annotation_line_width", "Espessura das referências (pt)", .4, 5, 2, .1),
            ("grid_alpha", "Opacidade da grade (0–1)", 0, 1, 2, .05),
            ("grid_line_width", "Espessura da grade (pt)", .2, 3, 2, .1),
            ("margin_left", "Margem esquerda (fração)", .04, .45, 3, .01),
            ("margin_right", "Margem direita (fração)", .55, .99, 3, .01),
            ("margin_bottom", "Margem inferior (fração)", .07, .38, 3, .01),
            ("margin_top", "Margem superior (fração)", .65, .91, 3, .01),
            ("subplot_hspace", "Espaço entre gráficos separados", .02, .85, 2, .05),
        ):
            spin = QDoubleSpinBox()
            spin.setRange(lo, hi)
            spin.setDecimals(decimals)
            spin.setSingleStep(step)
            spin.setValue(getattr(self.plot_settings, key))
            metrics.addRow(caption, spin)
            self.style_spins[key] = spin
        editor_layout.addLayout(metrics)

        editor_layout.addWidget(QLabel("<b>Composição da legenda</b>"))
        legend_hint = QLabel("Selecione somente as informações que devem aparecer. "
                             "Campos ausentes do nome do arquivo serão omitidos, sem preenchimento artificial.")
        legend_hint.setWordWrap(True)
        editor_layout.addWidget(legend_hint)
        self.legend_fields_checks: dict[str, QCheckBox] = {}
        for key, caption in LEGEND_FIELDS.items():
            check = QCheckBox(caption)
            check.setChecked(key in self.plot_settings.legend_fields)
            self.legend_fields_checks[key] = check
            editor_layout.addWidget(check)
        legend_form = QFormLayout()
        self.legend_location = QComboBox()
        location_labels = {
            "upper right": "Superior direita", "upper left": "Superior esquerda",
            "lower right": "Inferior direita", "lower left": "Inferior esquerda",
            "best": "Automática", "center right": "Centro direita", "center left": "Centro esquerda",
            "upper center": "Superior centro", "lower center": "Inferior centro",
        }
        for loc in LEGEND_LOCATIONS:
            self.legend_location.addItem(location_labels.get(loc, loc), loc)
        self.legend_columns = QDoubleSpinBox()
        self.legend_columns.setRange(1, 4)
        self.legend_columns.setDecimals(0)
        self.legend_columns.setValue(self.plot_settings.legend_columns)
        self.legend_frame = QCheckBox("Moldura na legenda")
        legend_form.addRow("Posição", self.legend_location)
        legend_form.addRow("Colunas", self.legend_columns)
        legend_form.addRow("Moldura", self.legend_frame)
        editor_layout.addLayout(legend_form)
        self.update_style = QPushButton("Aplicar formatação ao gráfico")
        editor_layout.addWidget(self.update_style)
        editor_layout.addWidget(QLabel("<b>Anotações verticais e horizontais</b>"))
        self.ann_kind = QComboBox()
        self.ann_kind.addItem("Vertical — referência em λ", "vertical")
        self.ann_kind.addItem("Horizontal — referência em sinal Y", "horizontal")
        editor_layout.addWidget(self.ann_kind)
        self.click_to_add = QCheckBox("Adicionar linha ao clicar no gráfico")
        editor_layout.addWidget(self.click_to_add)
        self.drag_lines = QCheckBox("Arrastar linhas existentes no gráfico")
        editor_layout.addWidget(self.drag_lines)
        annform = QFormLayout()
        self.ann_wavelength = QLineEdit()
        self.ann_wavelength.setPlaceholderText("Ex.: 824.5")
        self.ann_text = QPlainTextEdit()
        self.ann_text.setPlaceholderText("Ex.: Feição relacionada ao GaAs")
        self.ann_text.setMaximumHeight(70)
        self.ann_color = QComboBox()
        for label, value in COLOR_OPTIONS.items():
            self.ann_color.addItem(label, value)
        self.ann_style = QComboBox()
        for label, value in LINE_OPTIONS.items():
            self.ann_style.addItem(label, value)
        self.ann_y = QDoubleSpinBox()
        self.ann_y.setRange(6, 96)
        self.ann_y.setDecimals(1)
        self.ann_y.setSuffix(" %")
        self.ann_y.setValue(76)
        self.ann_dx = QDoubleSpinBox()
        self.ann_dx.setRange(-240, 240)
        self.ann_dx.setDecimals(1)
        self.ann_dx.setSingleStep(5)
        self.ann_dx.setSuffix(" pt")
        self.ann_dx.setValue(0)
        self.ann_dx.setToolTip(
            "Deslocamento visual do texto em pontos tipográficos: "
            "negativo = esquerda; zero = sobre a linha; positivo = direita. "
            "A linha vertical e seu comprimento de onda não mudam."
        )
        self.ann_show_value = QCheckBox("Mostrar comprimento de onda junto do texto")
        self.ann_show_value.setChecked(True)
        self.ann_coordinate_label = QLabel("Comprimento de onda")
        annform.addRow(self.ann_coordinate_label, self.ann_wavelength)
        annform.addRow("Descrição", self.ann_text)
        annform.addRow("Cor", self.ann_color)
        annform.addRow("Estilo", self.ann_style)
        self.ann_percent_label = QLabel("Altura do rótulo")
        self.ann_offset_label = QLabel("Rótulo: ← / →")
        annform.addRow(self.ann_percent_label, self.ann_y)
        annform.addRow(self.ann_offset_label, self.ann_dx)
        editor_layout.addLayout(annform)
        self.ann_help = QLabel("Rótulo vertical: − pt esquerda, + pt direita.")
        self.ann_help.setWordWrap(True)
        editor_layout.addWidget(self.ann_help)
        editor_layout.addWidget(self.ann_show_value)
        ann_buttons = QHBoxLayout()
        self.ann_add = QPushButton("+ Adicionar")
        self.ann_update = QPushButton("Atualizar")
        self.ann_delete = QPushButton("Excluir")
        for btn in (self.ann_add, self.ann_update, self.ann_delete):
            ann_buttons.addWidget(btn)
        editor_layout.addLayout(ann_buttons)
        self.annotation_table = QTableWidget(0, 2)
        self.annotation_table.setHorizontalHeaderLabels(["Linha / posição", "Anotação"])
        self.annotation_table.setColumnWidth(0, 130)
        self.annotation_table.setColumnWidth(0, 95)
        self.annotation_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.annotation_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.annotation_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.annotation_table.setMinimumHeight(165)
        editor_layout.addWidget(self.annotation_table)
        editor_layout.addWidget(QLabel("As linhas são referências visuais; a interpretação física deve ser fornecida pelo pesquisador."))
        session_buttons = QHBoxLayout()
        self.save_profile = QPushButton("Salvar edição…")
        self.load_profile = QPushButton("Abrir edição…")
        session_buttons.addWidget(self.save_profile)
        session_buttons.addWidget(self.load_profile)
        editor_layout.addLayout(session_buttons)
        editor_layout.addStretch(1)
        editor_scroll.setWidget(editor)
        details.addTab(editor_scroll, "Gráfico / anotações")
        splitter.addWidget(details)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        splitter.setSizes([385, 780, 365])
        self.statusBar().showMessage("Pronto: abra uma pasta ou um arquivo ZIP de espectros.")

        self.open_folder.clicked.connect(self.choose_folder)
        self.open_zip.clicked.connect(self.choose_zip)
        self.reload_button.clicked.connect(self.reload_source)
        self.dat_unit.currentIndexChanged.connect(self.reload_source)
        self.recursive_box.toggled.connect(self.reload_source)
        self.table.itemChanged.connect(self.on_item_changed)
        self.table.itemSelectionChanged.connect(self.show_metadata)
        self.table.itemSelectionChanged.connect(self.on_series_selection_changed)
        self.apply_factor.clicked.connect(self.apply_series_factor)
        self.reset_factor.clicked.connect(self.restore_series_factor)
        self.find_maximum.clicked.connect(self.show_series_maximum)
        self.clear_maximum.clicked.connect(self.clear_peak_marker)
        self.search_field.textChanged.connect(self.filter_rows)
        for combo in (self.sample_filter, self.slit_filter, self.lockin_filter):
            combo.currentIndexChanged.connect(self.filter_rows)
        self.mark_visible.clicked.connect(lambda: self.set_checks(True, visible_only=True))
        self.unmark_all.clicked.connect(lambda: self.set_checks(False, visible_only=False))
        self.plot_mode.currentIndexChanged.connect(self.on_plot_mode_changed)
        self.plot_mode.currentIndexChanged.connect(self.change_annotation_kind)
        self.comp_layout.currentIndexChanged.connect(self.on_composition_change)
        self.comp_panel.currentIndexChanged.connect(self.on_panel_change)
        for widget in (self.comp_share_x, self.comp_share_y):
            widget.toggled.connect(self.on_composition_change)
        for widget in (self.comp_hspace, self.comp_wspace):
            widget.valueChanged.connect(self.on_composition_change)
        self.comp_signal.currentIndexChanged.connect(self.on_composition_change)
        self.comp_signal.currentIndexChanged.connect(self.change_annotation_kind)
        self.grid_box.toggled.connect(self.draw_plot)
        self.legend_box.toggled.connect(self.draw_plot)
        self.save_graph.clicked.connect(self.export_graph)
        self.save_csv.clicked.connect(self.export_curves)
        self.save_scaled_csv.clicked.connect(self.export_scaled_curves)
        self.save_json.clicked.connect(self.export_metadata)
        self.temp_apply.clicked.connect(self.assign_temperature)
        self.temp_clear.clicked.connect(self.clear_temperature)
        self.update_style.clicked.connect(self.apply_plot_settings)
        for box in (self.show_title_box, self.show_subtitle_box, self.show_footer_box):
            box.toggled.connect(self.toggle_figure_text)
        self.axis_unit.currentIndexChanged.connect(self.change_axis_unit)
        self.signal_unit.currentIndexChanged.connect(self.change_signal_unit)
        self.ann_kind.currentIndexChanged.connect(self.change_annotation_kind)
        self.ann_add.clicked.connect(self.add_annotation)
        self.ann_update.clicked.connect(self.update_annotation)
        self.ann_delete.clicked.connect(self.delete_annotation)
        self.annotation_table.itemSelectionChanged.connect(self.select_annotation)
        self.save_profile.clicked.connect(self.save_plot_profile)
        self.load_profile.clicked.connect(self.open_plot_profile)
        self.canvas.mpl_connect("button_press_event", self.on_chart_press)
        self.canvas.mpl_connect("motion_notify_event", self.on_chart_move)
        self.canvas.mpl_connect("button_release_event", self.on_chart_release)
        self.change_annotation_kind()
        self.draw_plot()

    def is_composing(self) -> bool:
        return self.plot_mode.currentIndex() == 3

    def _commit_current_panel(self):
        """Persist in-memory GUI/editor state before switching to another panel."""
        panel = self.composition.panels[self.composition.active]
        panel.uids = list(self.plot_order.uids)
        panel.settings = self.plot_settings
        panel.annotations = self.annotations
        panel.grid = self.grid_box.isChecked()
        panel.legend = self.legend_box.isChecked()

    def _sync_table_checked_from_order(self):
        self._setting_up = True
        try:
            keep = set(self.plot_order.uids)
            for row in range(self.table.rowCount()):
                item = self.table.item(row, 0)
                if item is not None:
                    item.setCheckState(Qt.CheckState.Checked if item.data(Qt.ItemDataRole.UserRole) in keep
                                       else Qt.CheckState.Unchecked)
        finally:
            self._setting_up = False
        self._sync_plot_order_labels()
        self.update_count()

    def _activate_panel(self, panel_index: int, *, commit_previous: bool = True):
        if panel_index >= self.composition.count:
            raise ValueError("Painel não existe no layout escolhido.")
        if commit_previous:
            self._commit_current_panel()
        self.composition.active = panel_index
        panel = self.composition.panels[panel_index]
        self.plot_settings = panel.settings
        self.annotations = panel.annotations
        self.plot_order.replace(panel.uids)
        self._fill_settings_editor()
        self._refresh_annotation_list()
        self.show_footer_box.setEnabled(panel_index == 0)
        self.footer_edit.setEnabled(panel_index == 0)
        self.show_footer_box.setToolTip(
            "Em composições, a nota inferior é comum à figura e configurada no painel (a).")
        self.grid_box.blockSignals(True)
        self.legend_box.blockSignals(True)
        self.grid_box.setChecked(panel.grid)
        self.legend_box.setChecked(panel.legend)
        self.grid_box.blockSignals(False)
        self.legend_box.blockSignals(False)
        self._sync_table_checked_from_order()
        self.change_annotation_kind()
        self.draw_plot()

    def on_plot_mode_changed(self, *_):
        new_mode = self.plot_mode.currentIndex()
        if new_mode == 3 and self._last_plot_mode != 3:
            self._single_view = (self.plot_settings, self.annotations, list(self.plot_order.uids),
                                 self.grid_box.isChecked(), self.legend_box.isChecked())
            if not self._composition_initialized:
                self.composition.panels[0] = PanelState(
                    uids=list(self.plot_order.uids), settings=deepcopy(self.plot_settings),
                    annotations=deepcopy(self.annotations), grid=self.grid_box.isChecked(),
                    legend=self.legend_box.isChecked())
                self._composition_initialized = True
            self.composition_bar.show()
            self._activate_panel(min(self.composition.active, self.composition.count-1),
                                 commit_previous=False)
        elif new_mode != 3 and self._last_plot_mode == 3:
            self._commit_current_panel()
            self.composition_bar.hide()
            self.show_footer_box.setEnabled(True)
            self.footer_edit.setEnabled(True)
            if self._single_view:
                self.plot_settings, self.annotations, uids, grid, legend = self._single_view
                self.plot_order.replace(uids)
                self._fill_settings_editor()
                self._refresh_annotation_list()
                self.grid_box.setChecked(grid)
                self.legend_box.setChecked(legend)
                self._sync_table_checked_from_order()
            self.draw_plot()
        else:
            self.draw_plot()
        self._last_plot_mode = new_mode

    def on_panel_change(self, *_):
        if not self.is_composing() or self._changing_panel:
            return
        index = self.comp_panel.currentData()
        if index is None or index == self.composition.active:
            return
        self._changing_panel = True
        try:
            if not self.apply_plot_settings():
                self.comp_panel.blockSignals(True)
                self.comp_panel.setCurrentIndex(self.composition.active)
                self.comp_panel.blockSignals(False)
                return
            self._activate_panel(index)
        finally:
            self._changing_panel = False

    def on_composition_change(self, *_):
        if not self.is_composing() or self._setting_up:
            return
        self._commit_current_panel()
        previous_layout = self.composition.layout
        self.composition.layout = self.comp_layout.currentData()
        self.composition.share_x = self.comp_share_x.isChecked()
        self.composition.share_y = self.comp_share_y.isChecked()
        self.composition.hspace = self.comp_hspace.value()
        self.composition.wspace = self.comp_wspace.value()
        self.composition.mode = self.comp_signal.currentData()
        count = self.composition.count
        self.comp_panel.blockSignals(True)
        for i in range(4):
            self.comp_panel.model().item(i).setEnabled(i < count)
        if self.composition.active >= count:
            self.comp_panel.setCurrentIndex(0)
            self.comp_panel.blockSignals(False)
            self._activate_panel(0)
        else:
            self.comp_panel.blockSignals(False)
        self.draw_plot()

    def _all_composition_uids(self) -> list[str]:
        result = []
        for panel in self.composition.panels[:self.composition.count]:
            for uid in panel.uids:
                if uid not in result and uid in self.by_uid:
                    result.append(uid)
        return result

    def _valid_composition(self) -> bool:
        try:
            self._commit_current_panel()
            self.composition.validate()
            return True
        except ValueError as exc:
            QMessageBox.warning(self, "Composição inválida", str(exc))
            return False

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Abrir pasta de espectros", self.source or str(Path.home()))
        if folder:
            self.load_path(folder)

    def choose_zip(self):
        chosen, _ = QFileDialog.getOpenFileName(self, "Abrir ZIP de medidas", str(Path.home()), "ZIP (*.zip)")
        if chosen:
            self.load_path(chosen)

    def reload_source(self, *_):
        if self.source and not self.scan_thread:
            self.load_path(self.source)

    def load_path(self, path: str):
        if self.scan_thread:
            return
        if self.source and path != self.source and (self.annotations or
                any(panel.annotations for panel in self.composition.panels)):
            answer = QMessageBox.question(
                self, "Anotações da fonte atual",
                "Ao trocar de conjunto, as anotações e a formatação atuais serão reiniciadas. "
                "Salve a edição em JSON antes de continuar. Prosseguir?")
            if answer != QMessageBox.StandardButton.Yes:
                return
        self.pending_source = path
        self.source_label.setText(f"Carregando: {path}")
        self.statusBar().showMessage("Lendo dados…")
        self.reload_button.setEnabled(False)
        self.open_folder.setEnabled(False)
        self.open_zip.setEnabled(False)
        thread = QThread(self)
        task = ScanTask(path, self.recursive_box.isChecked(), self.dat_unit.currentData())
        task.moveToThread(thread)
        thread.started.connect(task.run)
        task.done.connect(self.on_scan_done)
        task.error.connect(self.on_scan_error)
        task.done.connect(thread.quit)
        task.error.connect(thread.quit)
        thread.finished.connect(task.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self.on_scan_finished)
        self.scan_thread, self.scan_worker = thread, task
        thread.start()

    def on_scan_finished(self):
        self.scan_thread, self.scan_worker = None, None
        self.reload_button.setEnabled(True)
        self.open_folder.setEnabled(True)
        self.open_zip.setEnabled(True)

    def on_scan_done(self, report: ScanReport):
        same_source = self.source is not None and self.source == self.pending_source
        previous_order = self.plot_order.uids if same_source else []
        if self.source and self.source != self.pending_source:
            self.composition = Composition()
            self._composition_initialized = False
            if self.is_composing():
                self._single_view = None
            self.display_factors.clear()
            self.peak_uid = None
            self.peak_result_label.setText("Fonte alterada: fatores e destaque do máximo reiniciados.")
            self.series_factor.setValue(1.0)
            self.annotations.clear()  # prevent spectral labels leaking across different datasets
            self.plot_settings = PlotSettings()
            self._fill_settings_editor()
            self._refresh_annotation_list()
        self.source = self.pending_source
        self.pending_source = None
        self.source_label.setText(f"Fonte: {self.source}")
        self.records = report.spectra
        if self.is_composing() and not self._composition_initialized:
            self.composition.panels[0] = PanelState(settings=deepcopy(self.plot_settings),
                                                   annotations=deepcopy(self.annotations))
            self._composition_initialized = True
            self._activate_panel(0, commit_previous=False)
        self.by_uid = {s.uid: s for s in self.records}
        if same_source:
            for panel in self.composition.panels:
                panel.uids = [uid for uid in panel.uids if uid in self.by_uid]
        self.display_factors = {uid: factor for uid, factor in self.display_factors.items()
                                if uid in self.by_uid}
        if self.peak_uid not in self.by_uid:
            self.peak_uid = None
        if same_source:
            self.plot_order.replace(uid for uid in previous_order if uid in self.by_uid)
        else:
            # No automatic checkbox on a new source: first USER click gets color 1.
            self.plot_order.replace([])
        self._setting_up = True
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        for i, sp in enumerate(self.records):
            self.table.insertRow(i)
            check = QTableWidgetItem("")
            check.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsSelectable)
            check.setData(Qt.ItemDataRole.UserRole, sp.uid)
            check.setCheckState(Qt.CheckState.Checked if sp.uid in self.plot_order.uids
                                else Qt.CheckState.Unchecked)
            self.table.setItem(i, 0, check)
            entries = [sp.sample_display,
                       f"{sp.slit_filename_um:g}" if sp.slit_filename_um is not None else "—",
                       f"{sp.lockin_range_mv:g}" if sp.lockin_range_mv is not None else "—",
                       sp.temperature_indicated,
                       str(len(sp.warnings)) if sp.warnings else "—", sp.name]
            for col, v in enumerate(entries, 1):
                item = QTableWidgetItem(str(v))
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.table.setItem(i, col, item)
            if sp.warnings:
                self.table.item(i, 5).setForeground(QBrush(QColor("#b07c21")))
                self.table.item(i, 5).setToolTip("\n".join(sp.warnings))
        self.table.setSortingEnabled(True)
        self._sync_plot_order_labels()
        self._fill_filters()
        self._setting_up = False
        self.filter_rows()
        if self.table.rowCount():
            self.table.selectRow(0)
        self.draw_plot()
        self.statusBar().showMessage(
            f"Marque as curvas na ordem de cores desejada. {len(self.records)} aquisições | "
            f"{report.paired_duplicates} duplicações DAT/DTLG verificadas | "
            f"{len(report.errors)} erros | {report.ignored} ignorados")
        if report.errors:
            msg = "\n".join(report.errors[:30])
            if len(report.errors) > 30:
                msg += f"\n... mais {len(report.errors)-30} erros"
            QMessageBox.warning(self, "Arquivos não lidos", msg)

    def on_scan_error(self, message: str):
        self.pending_source = None
        self.source_label.setText(f"Fonte: {self.source}" if self.source else "Nenhuma pasta selecionada")
        self.statusBar().showMessage("Falha na leitura: " + message)
        QMessageBox.critical(self, "Erro de leitura", message)

    def _fill_filters(self):
        self._setting_up = True
        sets = (
            (self.sample_filter, "Todas amostras", sorted({s.sample for s in self.records})),
            (self.slit_filter, "Todas fendas", sorted({f"{s.slit_filename_um:g}" for s in self.records if s.slit_filename_um is not None}, key=float)),
            (self.lockin_filter, "Todos lock-ins", sorted({f"{s.lockin_range_mv:g}" for s in self.records if s.lockin_range_mv is not None}, key=float)),
        )
        for combo, title, options in sets:
            combo.clear()
            combo.addItem(title)
            combo.addItems(options)
        self._setting_up = False

    def filter_rows(self, *_):
        if self._setting_up:
            return
        search = self.search_field.text().casefold().strip()
        sample = self.sample_filter.currentText() if self.sample_filter.currentIndex() > 0 else None
        slit = self.slit_filter.currentText() if self.slit_filter.currentIndex() > 0 else None
        lockin = self.lockin_filter.currentText() if self.lockin_filter.currentIndex() > 0 else None
        visible = 0
        for row in range(self.table.rowCount()):
            s = self.by_uid.get(self.table.item(row, 0).data(Qt.ItemDataRole.UserRole))
            if not s: continue
            hay = " ".join([s.name, s.sample_display, " ".join(s.source_files)]).casefold()
            show = ((not search or search in hay)
                    and (sample is None or sample == s.sample)
                    and (slit is None or slit == f"{s.slit_filename_um:g}")
                    and (lockin is None or lockin == f"{s.lockin_range_mv:g}"))
            self.table.setRowHidden(row, not show)
            visible += int(show)
        self.update_count(visible)

    def update_count(self, visible: int | None = None):
        if visible is None:
            visible = sum(not self.table.isRowHidden(i) for i in range(self.table.rowCount()))
        self.count_label.setText(f"{visible} visíveis / {len(self.records)} aquisições · {len(self.checked_records())} marcadas")

    def checked_records(self) -> list[Spectrum]:
        """Chronological checkbox selection, unaffected by table sorting or filters."""
        return [self.by_uid[uid] for uid in self.plot_order.uids if uid in self.by_uid]

    def _sync_plot_order_labels(self):
        """Numbers and colored labels document selection order in the first column."""
        previous_setup = self._setting_up
        self._setting_up = True
        sorting = self.table.isSortingEnabled()
        self.table.setSortingEnabled(False)
        try:
            for row in range(self.table.rowCount()):
                item = self.table.item(row, 0)
                if item is None:
                    continue
                pos = self.plot_order.position(item.data(Qt.ItemDataRole.UserRole))
                item.setText(str(pos) if pos is not None else "")
                if pos is not None:
                    color = PLOT_COLOR_CYCLE[(pos - 1) % len(PLOT_COLOR_CYCLE)]
                    item.setToolTip(f"Curva {pos} na ordem da seleção · cor {color}")
                    item.setForeground(QBrush(QColor(color)))
                else:
                    item.setToolTip("Marque para incluir no gráfico e atribuir a próxima cor")
                    item.setForeground(QBrush(QColor("#242424")))
        finally:
            self.table.setSortingEnabled(sorting)
            self._setting_up = previous_setup

    def on_item_changed(self, item):
        if not self._setting_up and item.column() == 0:
            self.plot_order.set_checked(item.data(Qt.ItemDataRole.UserRole),
                                        item.checkState() == Qt.CheckState.Checked)
            if self.is_composing():
                self.composition.panels[self.composition.active].uids = list(self.plot_order.uids)
            self._sync_plot_order_labels()
            self.draw_plot()
            self.update_count()

    def set_checks(self, state: bool, visible_only: bool):
        self._setting_up = True
        try:
            # Process table rows in their CURRENT visible order (including sorting).
            # Already-checked curves retain their original selection rank.
            for row in range(self.table.rowCount()):
                if visible_only and self.table.isRowHidden(row):
                    continue
                item = self.table.item(row, 0)
                if item is None:
                    continue
                item.setCheckState(Qt.CheckState.Checked if state else Qt.CheckState.Unchecked)
                self.plot_order.set_checked(item.data(Qt.ItemDataRole.UserRole), state)
        finally:
            self._setting_up = False
        if self.is_composing():
            self.composition.panels[self.composition.active].uids = list(self.plot_order.uids)
        self._sync_plot_order_labels()
        self.draw_plot()
        self.update_count()

    def show_metadata(self):
        items = self.table.selectedItems()
        if not items: return
        row = items[0].row()
        s = self.by_uid.get(self.table.item(row, 0).data(Qt.ItemDataRole.UserRole))
        if s:
            self.metadata_view.setPlainText(json.dumps(s.summary, ensure_ascii=False, indent=2))

    def selected_spectrum(self) -> Spectrum | None:
        """The highlighted table row, independent of checkbox visibility and sort order."""
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return self.by_uid.get(item.data(Qt.ItemDataRole.UserRole)) if item else None

    def on_series_selection_changed(self):
        if self._setting_up:
            return
        sp = self.selected_spectrum()
        self.series_factor.setValue(self.display_factors.get(sp.uid, 1.0) if sp else 1.0)
        if sp is not None:
            self.peak_result_label.setText(
                f"Série #{sp.sample} selecionada. Clique em 'Localizar máximo' para obter λ e sinal.")
        else:
            self.peak_result_label.setText("Destaque uma linha da tabela para analisar.")
        if self.peak_uid is not None and (sp is None or sp.uid != self.peak_uid):
            self.peak_uid = None
            self.draw_plot()

    def _show_selected_on_plot(self, sp: Spectrum):
        """Ensure the highlighted row is also checked for visible plot operations."""
        row = self.table.currentRow()
        if row >= 0:
            item = self.table.item(row, 0)
            if item and item.checkState() != Qt.CheckState.Checked:
                item.setCheckState(Qt.CheckState.Checked)
        self.update_count()

    def apply_series_factor(self):
        sp = self.selected_spectrum()
        if sp is None:
            QMessageBox.information(self, "Selecione a série", "Clique sobre uma linha da tabela antes de aplicar o fator.")
            return
        try:
            factor = validate_factor(self.series_factor.value())
            # Validate the arithmetic without changing the raw source array.
            from .plotting import scaled_signal
            scaled_signal(sp, factor)
        except ValueError as exc:
            QMessageBox.warning(self, "Fator inválido", str(exc))
            return
        if factor == 1.0:
            self.display_factors.pop(sp.uid, None)
        else:
            self.display_factors[sp.uid] = factor
        self._show_selected_on_plot(sp)
        if self.peak_uid == sp.uid:
            self._report_peak(sp)  # refreshed after scale change
        else:
            self.peak_result_label.setText(
                f"#{sp.sample}: fator de exibição ×{factor:g} aplicado. "
                "Sinal bruto preservado; clique em 'Localizar máximo' para localizar o pico.")
        self.draw_plot()
        self.statusBar().showMessage(f"Fator ×{factor:g} aplicado somente à aquisição {sp.name} (sem alterar os dados brutos).")

    def restore_series_factor(self):
        self.series_factor.setValue(1.0)
        self.apply_series_factor()

    def _report_peak(self, sp: Spectrum):
        peak = find_spectrum_maximum(sp, self.display_factors.get(sp.uid, 1.0))
        loc = format_wavelength(peak.wavelength_nm, self.plot_settings.x_unit)
        scale_unit = self.plot_settings.y_unit
        maximum_display = signal_display(peak.scaled_value, scale_unit)
        raw_display = signal_display(peak.raw_value_at_peak, scale_unit)
        message = (f"#{sp.sample} | máximo (sinal ×{peak.factor:g}): {maximum_display:.8g} {scale_unit} "
                   f"em λ = {loc}.\n"
                   f"Valor bruto nesse ponto: {raw_display:.8g} {scale_unit}.")
        if peak.factor != 1:
            message += ("\nMáximo do sinal bruto: "
                        f"{signal_display(peak.original_peak_value, scale_unit):.8g} {scale_unit} em "
                        f"{format_wavelength(peak.original_peak_wavelength_nm, self.plot_settings.x_unit)}.")
        if peak.tied_points > 1:
            message += (f"\nMáximo não único: {peak.tied_points} pontos empatados; "
                        "λ indica o primeiro ponto, não um pico identificado.")
        message += "\nMáximo global discreto; sem interpolação. A conversão V↔mV não altera a aquisição."
        self.peak_result_label.setText(message)
        return peak

    def show_series_maximum(self):
        sp = self.selected_spectrum()
        if sp is None:
            QMessageBox.information(self, "Selecione a série", "Destaque uma linha da tabela para localizar o máximo.")
            return
        try:
            peak = self._report_peak(sp)
        except ValueError as exc:
            QMessageBox.warning(self, "Máximo indisponível", str(exc))
            return
        self.peak_uid = sp.uid if peak.tied_points == 1 else None
        self._show_selected_on_plot(sp)
        self.draw_plot()
        self.statusBar().showMessage(f"Máximo global da aquisição #{sp.sample}: "
                                     f"{signal_display(peak.scaled_value, self.plot_settings.y_unit):.8g} "
                                     f"{self.plot_settings.y_unit} em λ={format_wavelength(peak.wavelength_nm, self.plot_settings.x_unit)}.")

    def clear_peak_marker(self):
        self.peak_uid = None
        self.peak_result_label.setText("Destaque removido. Os dados e fatores permanecem inalterados.")
        self.draw_plot()

    def assign_temperature(self):
        try:
            value = float(self.temp_input.text().strip().replace(",", "."))
            if not np.isfinite(value) or not (0 < value < 10000): raise ValueError()
        except ValueError:
            QMessageBox.warning(self, "Temperatura inválida", "Informe uma temperatura positiva em kelvin, por exemplo 77.")
            return
        self._set_temperature(value)

    def clear_temperature(self):
        self._set_temperature(None)

    def _set_temperature(self, value: float | None):
        rows_changed = 0
        for row in range(self.table.rowCount()):
            chk = self.table.item(row, 0)
            if chk.checkState() != Qt.CheckState.Checked: continue
            s = self.by_uid[chk.data(Qt.ItemDataRole.UserRole)]
            s.temperature_operator_k = value
            self.table.item(row, 4).setText(s.temperature_indicated)
            rows_changed += 1
        if not rows_changed:
            QMessageBox.information(self, "Nenhuma curva marcada", "Marque uma ou mais curvas na primeira coluna.")
        self.show_metadata()
        self.draw_plot()
        self.statusBar().showMessage(f"Temperatura manual aplicada/limpa em {rows_changed} aquisições (apenas na sessão).")

    def _read_optional_float(self, field: QLineEdit) -> float | None:
        val = field.text().strip().replace(",", ".")
        if not val:
            return None
        x = float(val)
        if not np.isfinite(x):
            raise ValueError("Limites dos eixos devem ser finitos.")
        return x

    def _fill_settings_editor(self):
        s = self.plot_settings
        self.title_edit.setText(s.title)
        self.subtitle_edit.setText(s.subtitle)
        self.xlabel_edit.setText(s.x_label)
        self.ylabel_edit.setText(s.y_label)
        self.footer_edit.setPlainText(s.footer)
        for widget, checked in ((self.show_title_box, s.show_title),
                                (self.show_subtitle_box, s.show_subtitle),
                                (self.show_footer_box, s.show_footer)):
            widget.blockSignals(True)
            widget.setChecked(checked)
            widget.blockSignals(False)
        for widget, new_index in ((self.axis_unit, 0 if s.x_unit == "nm" else 1),
                                  (self.signal_unit, 0 if s.y_unit == "V" else 1)):
            widget.blockSignals(True)
            widget.setCurrentIndex(new_index)
            widget.blockSignals(False)
        for w, value in ((self.xmin_edit, s.x_min), (self.xmax_edit, s.x_max),
                         (self.ymin_edit, s.y_min), (self.ymax_edit, s.y_max)):
            w.setText("" if value is None else f"{value:g}")
        self.font_family.setCurrentIndex(max(0, self.font_family.findData(s.font_family)))
        self.line_style.setCurrentIndex(max(0, self.line_style.findData(s.line_style)))
        self.legend_location.setCurrentIndex(max(0, self.legend_location.findData(s.legend_location)))
        self.legend_columns.setValue(s.legend_columns)
        self.legend_frame.setChecked(s.legend_frame)
        for key, w in self.style_spins.items():
            w.setValue(getattr(s, key))
        for key, w in self.legend_fields_checks.items():
            w.setChecked(key in s.legend_fields)

    def toggle_figure_text(self, *_):
        """Text visibility responds immediately; the content stays editable."""
        if self._setting_up:
            return
        self.plot_settings.show_title = self.show_title_box.isChecked()
        self.plot_settings.show_subtitle = self.show_subtitle_box.isChecked()
        self.plot_settings.show_footer = self.show_footer_box.isChecked()
        self.draw_plot()

    def apply_plot_settings(self):
        try:
            updated = PlotSettings(
                title=self.title_edit.text().strip(),
                subtitle=self.subtitle_edit.text().strip(),
                x_label=self.xlabel_edit.text().strip(),
                y_label=self.ylabel_edit.text().strip(),
                footer=self.footer_edit.toPlainText().strip(),
                show_title=self.show_title_box.isChecked(),
                show_subtitle=self.show_subtitle_box.isChecked(),
                show_footer=self.show_footer_box.isChecked(),
                x_unit=self.axis_unit.currentData(),
                y_unit=self.signal_unit.currentData(),
                x_min=self._read_optional_float(self.xmin_edit),
                x_max=self._read_optional_float(self.xmax_edit),
                y_min=self._read_optional_float(self.ymin_edit),
                y_max=self._read_optional_float(self.ymax_edit),
                font_family=self.font_family.currentData(),
                line_style=self.line_style.currentData(),
                legend_fields=[key for key, c in self.legend_fields_checks.items() if c.isChecked()],
                legend_location=self.legend_location.currentData(),
                legend_columns=int(self.legend_columns.value()),
                legend_frame=self.legend_frame.isChecked(),
                **{key: float(w.value()) for key, w in self.style_spins.items()},
            )
            updated.validate()
        except ValueError as exc:
            QMessageBox.warning(self, "Formatação inválida", str(exc))
            return False
        self.plot_settings = updated
        if self.is_composing():
            self.composition.panels[self.composition.active].settings = updated
        self.draw_plot()
        return True

    def change_signal_unit(self, *_):
        """Transform text limits while keeping horizontal guides stored in volts."""
        old = self.plot_settings.y_unit
        new = self.signal_unit.currentData()
        if new == old:
            return
        ratio = 1000.0 if old == "V" and new == "mV" else .001
        if (self.composition.mode if self.is_composing() else self.plot_mode.currentIndex()) != 2:
            for edit, key in ((self.ymin_edit, "y_min"), (self.ymax_edit, "y_max")):
                if edit.text().strip():
                    try:
                        converted = float(edit.text().replace(",", ".")) * ratio
                        edit.setText(f"{converted:.12g}")
                        setattr(self.plot_settings, key, converted)
                    except ValueError:
                        setattr(self.plot_settings, key, None)
                else:
                    setattr(self.plot_settings, key, None)
        self.plot_settings.y_unit = new
        if self.ann_kind.currentData() == "horizontal":
            self.change_annotation_kind()
        idx = self._selected_annotation_index()
        if idx is not None and isinstance(self.annotations[idx], HorizontalAnnotation):
            ann = self.annotations[idx]
            value = (ann.signal_value if ann.reference_scale == "normalized"
                     else signal_display(ann.signal_value, new))
            self.ann_wavelength.setText(f"{value:.10g}")
        self._refresh_annotation_list(idx)
        if self.peak_uid in self.by_uid:
            self._report_peak(self.by_uid[self.peak_uid])
        self.draw_plot()

    def change_axis_unit(self, *_):
        # Keep both annotations and axis limits at the SAME physical wavelengths.
        old = self.plot_settings.x_unit
        new = self.axis_unit.currentData()
        if old == new:
            return
        factor = 10.0 if old == "nm" and new == "angstrom" else .1
        for edit, key in ((self.xmin_edit, "x_min"), (self.xmax_edit, "x_max")):
            if edit.text().strip():
                try:
                    converted = float(edit.text().replace(',', '.')) * factor
                    edit.setText(f"{converted:g}")
                    setattr(self.plot_settings, key, converted)
                except ValueError:
                    setattr(self.plot_settings, key, None)
            else:
                setattr(self.plot_settings, key, None)
        self.plot_settings.x_unit = new
        selected_annotation = self._selected_annotation_index()
        if self.ann_kind.currentData() == "vertical":
            self.ann_wavelength.setPlaceholderText("Ex.: 8245" if new == "angstrom" else "Ex.: 824.5")
            index = self._selected_annotation_index()
            if index is not None and isinstance(self.annotations[index], VerticalAnnotation):
                self.ann_wavelength.setText(
                    f"{self.annotations[index].wavelength_nm * (10 if new == 'angstrom' else 1):g}")
        self._refresh_annotation_list(selected_annotation)
        self.draw_plot()

    def change_annotation_kind(self, *_):
        horizontal = self.ann_kind.currentData() == "horizontal"
        self.ann_coordinate_label.setText(
            ("Sinal normalizado (adimensional)" if (self.composition.mode if self.is_composing() else self.plot_mode.currentIndex()) == 2
             else f"Sinal exibido ({self.plot_settings.y_unit})") if horizontal
            else "Comprimento de onda")
        self.ann_wavelength.setPlaceholderText(
            ("Ex.: 0.05 (normalizado)" if (self.composition.mode if self.is_composing() else self.plot_mode.currentIndex()) == 2 else
             "Ex.: 50" if self.plot_settings.y_unit == "mV" else "Ex.: 0.05") if horizontal else
            ("Ex.: 8245" if self.plot_settings.x_unit == "angstrom" else "Ex.: 824.5"))
        self.ann_percent_label.setText("Posição X do rótulo" if horizontal else "Altura do rótulo")
        self.ann_offset_label.setText("Rótulo: ↓ / ↑" if horizontal else "Rótulo: ← / →")
        self.ann_help.setText(
            "Linha horizontal: − pt desloca o texto para baixo; + pt para cima. "
            "Y usa V ou mV no gráfico bruto (convertido internamente para V); "
            "no gráfico normalizado, é adimensional." if horizontal else
            "Linha vertical: − pt desloca o texto para a esquerda; + pt para a direita. "
            "A coordenada física λ da linha não muda.")
        self.ann_show_value.setText("Mostrar valor Y junto do texto" if horizontal else
                                    "Mostrar comprimento de onda junto do texto")
        self.ann_dx.setToolTip("Deslocamento visual do rótulo em pt, sem mover a linha")

    def _read_annotation(self) -> VerticalAnnotation | HorizontalAnnotation:
        coordinate = float(self.ann_wavelength.text().strip().replace(",", "."))
        common = dict(text=self.ann_text.toPlainText().strip(), color=self.ann_color.currentData(),
                      linestyle=self.ann_style.currentData(), show_value=self.ann_show_value.isChecked())
        if self.ann_kind.currentData() == "horizontal":
            normalized = (self.composition.mode if self.is_composing() else self.plot_mode.currentIndex()) == 2
            ann = HorizontalAnnotation(
                signal_value=(coordinate if normalized else
                              signal_v_from_display(coordinate, self.plot_settings.y_unit)),
                reference_scale="normalized" if normalized else "signal_v",
                label_x=self.ann_y.value() / 100, label_dy_pt=self.ann_dx.value(), **common)
        else:
            ann = VerticalAnnotation(
                wavelength_nm=wavelength_nm_from_display(coordinate, self.plot_settings.x_unit),
                label_y=self.ann_y.value() / 100, label_dx_pt=self.ann_dx.value(), **common)
        ann.validate()
        return ann

    def _selected_annotation_index(self) -> int | None:
        rows = self.annotation_table.selectionModel().selectedRows()
        if not rows:
            return None
        row = rows[0].row()
        return row if 0 <= row < len(self.annotations) else None

    def _refresh_annotation_list(self, selected: int | None = None):
        self._annotation_setting_up = True
        self.annotation_table.setRowCount(len(self.annotations))
        for i, item in enumerate(self.annotations):
            display = ("V · " + format_wavelength(item.wavelength_nm, self.plot_settings.x_unit)
                       if isinstance(item, VerticalAnnotation) else
                       f"H · Y={item.signal_value:.6g} (norm.)" if item.reference_scale == "normalized" else
                       f"H · Y={signal_display(item.signal_value, self.plot_settings.y_unit):.6g} {self.plot_settings.y_unit}")
            self.annotation_table.setItem(i, 0, QTableWidgetItem(display))
            self.annotation_table.setItem(i, 1, QTableWidgetItem(item.text))
        if selected is not None and 0 <= selected < len(self.annotations):
            self.annotation_table.selectRow(selected)
        else:
            self.annotation_table.clearSelection()
        self._annotation_setting_up = False

    def select_annotation(self):
        if self._annotation_setting_up:
            return
        idx = self._selected_annotation_index()
        if idx is None:
            return
        a = self.annotations[idx]
        horizontal = isinstance(a, HorizontalAnnotation)
        self.ann_kind.setCurrentIndex(1 if horizontal else 0)
        coordinate = ((a.signal_value if a.reference_scale == "normalized" else
                       signal_display(a.signal_value, self.plot_settings.y_unit)) if horizontal else
                      a.wavelength_nm * (10 if self.plot_settings.x_unit == "angstrom" else 1))
        self.ann_wavelength.setText(f"{coordinate:.9g}")
        self.ann_text.setPlainText(a.text)
        self.ann_color.setCurrentIndex(max(0, self.ann_color.findData(a.color)))
        self.ann_style.setCurrentIndex(max(0, self.ann_style.findData(a.linestyle)))
        self.ann_y.setValue((a.label_x if horizontal else a.label_y) * 100)
        self.ann_dx.setValue(a.label_dy_pt if horizontal else a.label_dx_pt)
        self.ann_show_value.setChecked(a.show_value)
        self.draw_plot()

    def add_annotation(self):
        try:
            a = self._read_annotation()
            if len(self.annotations) >= 100:
                raise ValueError("Máximo de 100 anotações.")
        except (ValueError, TypeError) as exc:
            QMessageBox.warning(self, "Linha inválida", "Informe a posição da linha selecionada. " + str(exc))
            return
        self.annotations.append(a)
        self._refresh_annotation_list(len(self.annotations) - 1)
        self.draw_plot()

    def update_annotation(self):
        idx = self._selected_annotation_index()
        if idx is None:
            QMessageBox.information(self, "Selecionar linha", "Selecione uma linha na tabela de anotações.")
            return
        try:
            self.annotations[idx] = self._read_annotation()
        except (ValueError, TypeError) as exc:
            QMessageBox.warning(self, "Linha inválida", str(exc))
            return
        self._refresh_annotation_list(idx)
        self.draw_plot()

    def delete_annotation(self):
        idx = self._selected_annotation_index()
        if idx is not None:
            del self.annotations[idx]
            self._refresh_annotation_list()
            self.draw_plot()

    def _navigation_active(self) -> bool:
        return bool(self.canvas.toolbar and self.canvas.toolbar.mode)

    def on_chart_press(self, event):
        if (event.button != 1 or event.inaxes not in self._plot_axes
                or self._navigation_active()):
            return
        if self.is_composing():
            index = self._plot_axes.index(event.inaxes)
            if index != self.composition.active:
                self.comp_panel.setCurrentIndex(index)
            # Use the corresponding axis' data coordinates; units follow the panel.
        if self.click_to_add.isChecked():
            coordinate = (event.ydata if self.ann_kind.currentData() == "horizontal" else event.xdata)
            if coordinate is None or not np.isfinite(coordinate):
                return
            self.ann_wavelength.setText(f"{coordinate:.9g}")
            self.add_annotation()
        elif self.drag_lines.isChecked() and self.annotations:
            axis = event.inaxes
            nearby = []
            for i, ann in enumerate(self.annotations):
                if isinstance(ann, HorizontalAnnotation):
                    if (ann.reference_scale == "normalized") != ((self.composition.mode if self.is_composing() else self.plot_mode.currentIndex()) == 2):
                        continue
                    ycoord = (ann.signal_value if ann.reference_scale == "normalized" else
                              signal_display(ann.signal_value, self.plot_settings.y_unit))
                    pixel_y = axis.transData.transform((0, ycoord))[1]
                    distance = abs(float(event.y) - pixel_y)
                else:
                    val = ann.wavelength_nm * (10 if self.plot_settings.x_unit == "angstrom" else 1)
                    pixel_x = axis.transData.transform((val, 0))[0]
                    distance = abs(float(event.x) - pixel_x)
                if distance <= 9:
                    nearby.append((distance, i))
            if nearby:
                self._drag_annotation = min(nearby)[1]

    def on_chart_move(self, event):
        if self._drag_annotation is None or event.inaxes not in self._plot_axes:
            return
        ann = self.annotations[self._drag_annotation]
        if isinstance(ann, HorizontalAnnotation):
            if event.ydata is not None and np.isfinite(event.ydata):
                if (ann.reference_scale == "normalized") == ((self.composition.mode if self.is_composing() else self.plot_mode.currentIndex()) == 2):
                    ann.signal_value = (float(event.ydata) if ann.reference_scale == "normalized"
                                        else signal_v_from_display(float(event.ydata), self.plot_settings.y_unit))
                    self.draw_plot()
        else:
            if event.xdata is not None:
                nm = wavelength_nm_from_display(event.xdata, self.plot_settings.x_unit)
                if np.isfinite(nm) and nm > 0:
                    ann.wavelength_nm = nm
                    self.draw_plot()

    def on_chart_release(self, event):
        if self._drag_annotation is not None:
            idx = self._drag_annotation
            self._drag_annotation = None
            self._refresh_annotation_list(idx)
            self.draw_plot()

    def draw_plot(self, *_):
        if self._setting_up:
            return
        if self.is_composing():
            self._commit_current_panel()
            selected = [self.by_uid[uid] for uid in self._all_composition_uids()]
            mode = self.composition.mode
        else:
            selected = self.checked_records()
            mode = self.plot_mode.currentIndex()
        try:
            if self.is_composing():
                self._plot_axes = render_composition(
                    self.figure, self.by_uid, self.composition,
                    display_factors=self.display_factors, peak_uid=self.peak_uid,
                    selected_annotation=self._selected_annotation_index(),
                    resize_figure=False)
            else:
                self._plot_axes = render_plot(
                    self.figure, selected, self.plot_settings, self.annotations,
                    mode=mode, grid=self.grid_box.isChecked(),
                    legend=self.legend_box.isChecked(),
                    selected_annotation=self._selected_annotation_index(),
                    scale_factors=self.display_factors, highlight_peak_uid=self.peak_uid,
                    resize_figure=False,
                )
        except ValueError as exc:
            self.statusBar().showMessage("Falha no desenho: " + str(exc))
            return
        if not selected:
            self.chart_note.setText("Nenhum espectro selecionado.")
            self.canvas.draw_idle()
            return
        cautions = []
        if len({sp.slit_filename_um for sp in selected}) > 1:
            cautions.append("fendas diferentes")
        if len({sp.lockin_range_mv for sp in selected}) > 1:
            cautions.append("fundos de escala do lock-in diferentes")
        if len({sp.temperature_operator_k or sp.temperature_filename_k for sp in selected}) > 1:
            cautions.append("temperaturas declaradas diferentes")
        if any(any("satura" in w.lower() for w in sp.warnings) for sp in selected):
            cautions.append("possível saturação")
        if any(any("divergent" in w.lower() for w in sp.warnings) for sp in selected):
            cautions.append("divergência nome/cabeçalho")
        if any(self.display_factors.get(sp.uid, 1.0) != 1 for sp in selected):
            cautions.append("fatores visuais individuais (×f), sem alteração dos dados")
        if mode == 2:
            cautions.append("normalização visual pela amplitude máxima: fatores positivos podem se cancelar")
        if mode == 1 and len(selected) > 16:
            cautions.append("modo separado: primeiras 16 curvas")
        self.chart_note.setText(("Atenção: " + "; ".join(cautions) + ". " if cautions else "")
                                + f"Sinais adquiridos em V; eixo Y exibido em {self.plot_settings.y_unit} "
                                  "(no modo normalizado, Y é adimensional). Dados originais preservados.")
        self.canvas.draw_idle()

    def export_graph(self):
        if not self.apply_plot_settings():
            return
        if self.is_composing():
            if not self._valid_composition():
                return
            available = self._all_composition_uids()
        else:
            available = [s.uid for s in self.checked_records()]
        if not available:
            QMessageBox.information(self, "Sem curvas", "Marque curvas nos painéis antes de exportar.")
            return
        path, filter_name = QFileDialog.getSaveFileName(self, "Exportar gráfico",
                        "espectros_PL.pdf", "PDF vetorial (*.pdf);;SVG vetorial (*.svg);;PNG (*.png)")
        if not path:
            return
        if not Path(path).suffix:
            path += ".svg" if "SVG" in filter_name else ".png" if "PNG" in filter_name else ".pdf"
        try:
            if self.is_composing():
                export_figure = create_composition_export_figure(
                    self.by_uid, self.composition, display_factors=self.display_factors,
                    peak_uid=self.peak_uid)
            else:
                export_figure = create_export_figure(
                    self.checked_records(), self.plot_settings, self.annotations,
                    mode=self.plot_mode.currentIndex(), grid=self.grid_box.isChecked(),
                    legend=self.legend_box.isChecked(),
                    selected_annotation=self._selected_annotation_index(),
                    scale_factors=self.display_factors, highlight_peak_uid=self.peak_uid,
                )
            export_vector(export_figure, path, title=self.plot_settings.title)
            export_figure.clear()
            self.statusBar().showMessage(f"Gráfico salvo: {path}")
        except Exception as exc:
            QMessageBox.critical(self, "Erro na exportação", str(exc))

    def save_plot_profile(self):
        if not self.apply_plot_settings():
            return
        path, _ = QFileDialog.getSaveFileName(self, "Salvar edição de gráfico",
                                             "grafico_PL_edicao.json", "Sessão do gráfico (*.json)")
        if not path:
            return
        if not Path(path).suffix:
            path += ".json"
        try:
            if self.is_composing() and not self._valid_composition():
                return
            save_session(path, self.plot_settings, self.annotations, self.source,
                         [sp.uid for sp in self.checked_records()],
                         0 if self.is_composing() else self.plot_mode.currentIndex(),
                         self.grid_box.isChecked(), self.legend_box.isChecked(),
                         scale_factors=self.display_factors, highlight_peak_uid=self.peak_uid)
            augment_session_json(path, self.composition, self.is_composing())
            self.statusBar().showMessage(f"Edição do gráfico salva: {path}")
        except Exception as exc:
            QMessageBox.critical(self, "Erro ao salvar", str(exc))

    def open_plot_profile(self):
        path, _ = QFileDialog.getOpenFileName(self, "Abrir edição de gráfico",
                                             str(Path.home()), "Sessão do gráfico (*.json)")
        if not path:
            return
        try:
            if self.is_composing():
                self.plot_mode.setCurrentIndex(0)
            data, settings, annotations = load_session(path)
            multi_restore = restore_composition_from_session(data)
            original_source = data.get("data_source")
            if original_source and original_source != self.source:
                answer = QMessageBox.question(self, "Fonte de dados diferente",
                    "A edição foi salva para outra fonte de espectros. "
                    "Carregar somente formatação e anotações, sem selecionar curvas?")
                if answer != QMessageBox.StandardButton.Yes:
                    return
            self.plot_settings = settings
            self.annotations = annotations
            self._fill_settings_editor()
            self.plot_mode.setCurrentIndex(data.get("mode", 0))
            self.grid_box.setChecked(bool(data.get("grid", True)))
            self.legend_box.setChecked(bool(data.get("legend", True)))
            if original_source == self.source:
                self.display_factors = {uid: validate_factor(factor)
                                        for uid, factor in data.get("spectrum_display_factors", {}).items()
                                        if uid in self.by_uid and validate_factor(factor) != 1}
                self.peak_uid = data.get("highlight_peak_uid") if data.get("highlight_peak_uid") in self.by_uid else None
                saved_order = data.get("selected_spectrum_uids", [])
                checked_ids = set(saved_order)
                self._setting_up = True
                for row in range(self.table.rowCount()):
                    item = self.table.item(row, 0)
                    item.setCheckState(Qt.CheckState.Checked if item.data(Qt.ItemDataRole.UserRole) in checked_ids
                                       else Qt.CheckState.Unchecked)
                self._setting_up = False
                self.plot_order.replace(uid for uid in saved_order if uid in self.by_uid)
                self._sync_plot_order_labels()
            self._refresh_annotation_list()
            restored_peak_uid = self.peak_uid
            self.on_series_selection_changed()
            if restored_peak_uid is not None and restored_peak_uid in self.by_uid:
                self.peak_uid = restored_peak_uid
                self._report_peak(self.by_uid[restored_peak_uid])
            if multi_restore:
                enabled, comp = multi_restore
                if original_source != self.source:
                    for panel in comp.panels:
                        panel.uids = []
                else:
                    for panel in comp.panels:
                        panel.uids = [uid for uid in panel.uids if uid in self.by_uid]
                self.composition = comp
                self._composition_initialized = True
                for combo, value in ((self.comp_layout, comp.layout),
                                     (self.comp_signal, comp.mode)):
                    combo.blockSignals(True)
                    combo.setCurrentIndex(combo.findData(value))
                    combo.blockSignals(False)
                for widget, value in ((self.comp_share_x, comp.share_x),
                                      (self.comp_share_y, comp.share_y)):
                    widget.blockSignals(True)
                    widget.setChecked(value)
                    widget.blockSignals(False)
                for widget, value in ((self.comp_hspace, comp.hspace),
                                      (self.comp_wspace, comp.wspace)):
                    widget.blockSignals(True)
                    widget.setValue(value)
                    widget.blockSignals(False)
                self.comp_panel.blockSignals(True)
                self.comp_panel.setCurrentIndex(min(comp.active, comp.count-1))
                self.comp_panel.blockSignals(False)
                if enabled:
                    # Keep an independent single-graph state for switching back.
                    self.plot_mode.setCurrentIndex(3)
                    self._activate_panel(min(comp.active, comp.count-1), commit_previous=False)
                elif self.is_composing():
                    self.plot_mode.setCurrentIndex(0)
            self.draw_plot()
            self.update_count()
            self.statusBar().showMessage(f"Edição carregada: {path}")
        except Exception as exc:
            QMessageBox.critical(self, "Falha ao abrir edição", str(exc))

    def export_curves(self):
        selected = self.checked_records()
        if not selected:
            QMessageBox.information(self, "Sem curvas", "Marque as curvas antes de exportar.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Exportar curvas", "curvas_PL.csv", "CSV (*.csv)")
        if not path: return
        try:
            export_curves_csv(path, selected)
            self.statusBar().showMessage(f"Curvas exportadas: {path}")
        except Exception as exc:
            QMessageBox.critical(self, "Erro na exportação", str(exc))

    def export_scaled_curves(self):
        selected = self.checked_records()
        if not selected:
            QMessageBox.information(self, "Sem curvas", "Marque as curvas que deseja exportar.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Exportar valores ajustados (e brutos)",
                                              "curvas_PL_ajustadas.csv", "CSV (*.csv)")
        if not path:
            return
        if not Path(path).suffix:
            path += ".csv"
        try:
            export_scaled_curves_csv(path, selected, self.display_factors)
            self.statusBar().showMessage(f"CSV ajustado e bruto exportado: {path}")
        except Exception as exc:
            QMessageBox.critical(self, "Erro na exportação ajustada", str(exc))

    def export_metadata(self):
        selected = self.checked_records()
        if not selected:
            QMessageBox.information(self, "Sem curvas", "Marque as curvas antes de exportar.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Exportar metadados", "metadados_PL.json", "JSON (*.json)")
        if not path: return
        try:
            export_metadata_json(path, selected, self.source)
            self.statusBar().showMessage(f"Metadados exportados: {path}")
        except Exception as exc:
            QMessageBox.critical(self, "Erro na exportação", str(exc))

    def closeEvent(self, event):
        if self.scan_thread and self.scan_thread.isRunning():
            self.scan_thread.requestInterruption()
            QMessageBox.information(self, "Cancelamento solicitado", "A leitura está sendo interrompida; feche o programa após a conclusão.")
            event.ignore()
            return
        super().closeEvent(event)


def run_gui(startup_path: str | None = None):
    app = QApplication.instance() or QApplication([])
    app.setStyle("Fusion")
    win = PLMainWindow(startup_path)
    win.show()
    return app.exec()
