from __future__ import annotations

import functools
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtWidgets
from PySide6.QtWidgets import QComboBox

from randovania.game.game_enum import RandovaniaGame
from randovania.game_description import default_database
from randovania.game_description.db.configurable_node import ConfigurableNode
from randovania.games.prime2.exporter.claris_randomizer_data import decode_randomizer_data
from randovania.games.prime2.gui.generated.preset_echoes_translators_ui import Ui_PresetEchoesTranslators
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.games.prime2.layout.translator_configuration import LayoutTranslatorRequirement, TranslatorConfiguration
from randovania.gui.lib.signal_handling import set_combo_with_value
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.lib.enum_lib import iterate_enum

if TYPE_CHECKING:
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


def _translator_config(editor: PresetEditor) -> TranslatorConfiguration:
    config = editor.configuration
    assert isinstance(config, EchoesConfiguration)
    return config.translator_configuration


def gate_data() -> tuple[dict[int, str], dict[NodeIdentifier, int]]:
    db = default_database.game_description_for(RandovaniaGame.METROID_PRIME_ECHOES)
    randomizer_data = decode_randomizer_data()

    gate_index_to_name = {gate["Index"]: gate["Name"] for gate in randomizer_data["TranslatorLocationData"]}
    identifier_to_gate = {
        node.identifier: node.extra["gate_index"] for node in db.region_list.iterate_nodes_of_type(ConfigurableNode)
    }
    return gate_index_to_name, identifier_to_gate


class PresetEchoesTranslators(PresetTab, Ui_PresetEchoesTranslators):
    _combo_for_gate: dict[NodeIdentifier, QComboBox]

    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.translators_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.translator_randomize_all_button.clicked.connect(self._on_randomize_all_gates_pressed)
        self.translator_randomize_all_with_unlocked_button.clicked.connect(
            self._on_randomize_all_gates_with_unlocked_pressed
        )
        self.translator_vanilla_actual_button.clicked.connect(self._on_vanilla_actual_gates_pressed)
        self.translator_vanilla_colors_button.clicked.connect(self._on_vanilla_colors_gates_pressed)

        self._combo_for_gate = {}

        gate_index_to_name, identifier_to_gate = gate_data()

        for i, (identifier, gate_index) in enumerate(sorted(identifier_to_gate.items(), key=lambda it: it[1])):
            label = QtWidgets.QLabel(self.translators_scroll_contents)
            label.setText(gate_index_to_name[gate_index])
            self.translators_layout.addWidget(label, 3 + i, 0, 1, 1)

            combo = QComboBox(self.translators_scroll_contents)
            combo.identifier = identifier  # type: ignore[attr-defined]
            for item in iterate_enum(LayoutTranslatorRequirement):
                combo.addItem(item.long_name, item)
            combo.currentIndexChanged.connect(functools.partial(self._on_gate_combo_box_changed, combo))

            self.translators_layout.addWidget(combo, 3 + i, 1, 1, 2)
            self._combo_for_gate[combo.identifier] = combo  # type: ignore[attr-defined]

    @classmethod
    def tab_title(cls) -> str:
        return "Translators Gate"

    @classmethod
    def header_name(cls) -> str | None:
        return None

    def _on_randomize_all_gates_pressed(self) -> None:
        with self._editor as editor:
            editor.set_configuration_field("translator_configuration", _translator_config(editor).with_full_random())

    def _on_randomize_all_gates_with_unlocked_pressed(self) -> None:
        with self._editor as editor:
            editor.set_configuration_field(
                "translator_configuration", _translator_config(editor).with_full_random_with_unlocked()
            )

    def _on_vanilla_actual_gates_pressed(self) -> None:
        with self._editor as editor:
            editor.set_configuration_field("translator_configuration", _translator_config(editor).with_vanilla_actual())

    def _on_vanilla_colors_gates_pressed(self) -> None:
        with self._editor as editor:
            editor.set_configuration_field("translator_configuration", _translator_config(editor).with_vanilla_colors())

    def _on_gate_combo_box_changed(self, combo: QComboBox, new_index: int) -> None:
        with self._editor as editor:
            editor.set_configuration_field(
                "translator_configuration",
                _translator_config(editor).replace_requirement_for_gate(combo.identifier, combo.currentData()),  # type: ignore[attr-defined]
            )

    def on_preset_changed(self, preset: Preset) -> None:
        config = preset.configuration
        assert isinstance(config, EchoesConfiguration)

        for identifier, combo in self._combo_for_gate.items():
            set_combo_with_value(combo, config.translator_configuration.translator_requirement[identifier])
