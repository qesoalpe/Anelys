from PySide.QtGui import QSortFilterProxyModel
import re


class Sort_Filter_Proxy_Model(QSortFilterProxyModel):
    def __init__(self, *args, **kwargs):
        QSortFilterProxyModel.__init__(self, *args, **kwargs)
        self._regex = None

    @property
    def regex(self):
        return self._regex

    @regex.setter
    def regex(self, regex):
        if regex is not None:
            if isinstance(regex, str):
                self._regex = re.compile(regex)
            elif isinstance(regex, re._pattern_type):
                self._regex = regex
        else:
            self._regex = regex

    @property
    def source_model(self):
        return QSortFilterProxyModel.sourceModel(self)

    @source_model.setter
    def source_model(self, model):
        QSortFilterProxyModel.setSourceModel(model)

    def filterAcceptsRow(self, sourceRow, sourceParent):
        if self.regex is not None:
            pass
