# Copyright Contributors to the Rez project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from Qt import QtCore, QtWidgets
from functools import partial


class Config(QtCore.QSettings):
    """Persistent application settings.

    Methods are also provided for easily attaching widgets to settings.
    """
    def __init__(self, default_settings, organization=None, application=None,
                 parent=None):
        super(Config, self).__init__(organization, application, parent)
        self.default_settings = default_settings

    def value(self, key, type_=None):
        """Get the value of a setting.

        If `type` is not provided, the key must be for a known setting,
        present in `self.default_settings`. Conversely if `type` IS provided,
        the key must be for an unknown setting.
        """
        if type_ is None:
            default = self._default_value(key)
            val = self._value(key, default)
            if type(val) == type(default):
                return val
            else:
                return self._convert_value(val, type(default))
        else:
            val = self._value(key, None)
            if val is None:
                return None
            return self._convert_value(val, type_)

    def get(self, key, type_=None):
        return self.value(key, type_)

    def get_string_list(self, key):
        """Get a list of strings."""
        strings = []
        size = self.beginReadArray(key)
        for i in range(size):
            self.setArrayIndex(i)
            entry = str(self._value("entry"))
            strings.append(entry)
        self.endArray()
        return strings

    def prepend_string_list(self, key, value, max_length_key):
        """Prepend a fixed-length string list with a new string.

        The oldest string will be removed from the list. If the string is
        already in the list, it is shuffled to the top. Use this to implement
        things like a 'most recent files' entry.
        """
        max_len = self.get(max_length_key)
        strings = self.get_string_list(key)
        strings = [value] + [x for x in strings if x != value]
        strings = strings[:max_len]

        self.beginWriteArray(key)
        for i in range(len(strings)):
            self.setArrayIndex(i)
            self.setValue("entry", strings[i])
        self.endArray()

    def attach(self, widget, key):
        if isinstance(widget, QtWidgets.QComboBox):
            self._attach_combobox(widget, key)
        elif isinstance(widget, QtWidgets.QCheckBox):
            self._attach_checkbox(widget, key)
        else:
            raise NotImplementedError

    def _value(self, key, defaultValue=None):
        val = super(Config, self).value(key, defaultValue)
        if hasattr(val, "toPyObject"):
            val = val.toPyObject()
        return val

    @classmethod
    def _convert_value(cls, value, type_):
        if type_ is bool:
            return (str(value).lower() == "true")
        else:
            return type_(value)

    def _attach_checkbox(self, widget, key):
        if widget.isTristate():
            raise NotImplementedError

        value = self.value(key)
        widget.setCheckState(QtCore.Qt.Checked if value else QtCore.Qt.Unchecked)
        widget.stateChanged.connect(
            partial(self._checkbox_stateChanged, widget, key))

    def _checkbox_stateChanged(self, widget, key):
        value = widget.isChecked()
        self.setValue(key, value)

    def _attach_combobox(self, widget, key):
        value = str(self.value(key))
        index = widget.findText(value)
        if index == -1:
            widget.setEditText(value)
        else:
            widget.setCurrentIndex(index)

        widget.currentIndexChanged.connect(
            partial(self._combobox_currentIndexChanged, widget, key))
        widget.editTextChanged.connect(
            partial(self._combobox_editTextChanged, widget, key))

    def _combobox_currentIndexChanged(self, widget, key, index):
        value = widget.itemText(index)
        self.setValue(key, value)

    def _combobox_editTextChanged(self, widget, key, txt):
        self.setValue(key, txt)

    def _default_value(self, key):
        keys = key.lstrip('/').split('/')
        value = self.default_settings
        for k in keys:
            try:
                value = value[k]
            except KeyError:
                raise ValueError("No such application setting: %r" % key)
        return value
