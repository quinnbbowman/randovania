from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtCore

from randovania.games.prime2.gui.generated.preset_echoes_goal_ui import Ui_PresetEchoesGoal
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration, LayoutSkyTempleKeyMode
from randovania.gui.lib.signal_handling import set_combo_with_value
from randovania.gui.preset_settings.preset_tab import PresetTab

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetEchoesGoal(PresetTab, Ui_PresetEchoesGoal):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.goal_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.skytemple_combo.setItemData(0, LayoutSkyTempleKeyMode.ALL_BOSSES)
        self.skytemple_combo.setItemData(1, LayoutSkyTempleKeyMode.ALL_GUARDIANS)
        self.skytemple_combo.setItemData(2, int)

        self.skytemple_combo.currentIndexChanged.connect(self._on_sky_temple_key_combo_changed)
        self.skytemple_slider.valueChanged.connect(self._on_sky_temple_key_combo_slider_changed)

        # Default to False, since the slider defaults to a non-collect keys value.
        self._set_slider_visible(False)

    @classmethod
    def tab_title(cls) -> str:
        return "Goal"

    @classmethod
    def header_name(cls) -> str | None:
        return None

    def _set_slider_visible(self, visible: bool) -> None:
        for w in [self.skytemple_slider, self.skytemple_slider_label]:
            w.setVisible(visible)

    def _on_sky_temple_key_combo_changed(self) -> None:
        combo_enum = self.skytemple_combo.currentData()
        with self._editor as editor:
            if combo_enum is int:
                new_value = LayoutSkyTempleKeyMode(self.skytemple_slider.value())
                self._set_slider_visible(True)
            else:
                new_value = combo_enum
                self._set_slider_visible(False)

            editor.set_configuration_field("sky_temple_keys", new_value)

    def _on_sky_temple_key_combo_slider_changed(self) -> None:
        self.skytemple_slider_label.setText(str(self.skytemple_slider.value()))
        self._on_sky_temple_key_combo_changed()

    def on_preset_changed(self, preset: Preset) -> None:
        assert isinstance(preset.configuration, EchoesConfiguration)
        keys = preset.configuration.sky_temple_keys
        data: LayoutSkyTempleKeyMode | type[int]
        if isinstance(keys.value, int):
            self.skytemple_slider.setValue(keys.value)
            data = int
        else:
            data = keys
        set_combo_with_value(self.skytemple_combo, data)
