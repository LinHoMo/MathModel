# ENV["PYTHON"] = raw"C:/Users/Public/TongYuan/.julia/miniforge3/python.exe"

using TyFilterDesigner
using PyCall

function _patch_filterdesigner_logger!()
    try
        filterDesigner()
    catch err
        println("initial filterDesigner load failed as expected: ", err)
    end

    sys = pyimport("sys")
    builtins = pyimport("builtins")
    haskey(sys.modules, "filter_designer_main") ||
        error("filter_designer_main was not loaded")
    mod = sys.modules["filter_designer_main"]

    patch_code = """
import logging

if not hasattr(FilterDesigner, '_orig_init_log_monkey'):
    FilterDesigner._orig_init_log_monkey = FilterDesigner.init_log

    def _patched_init_log(self):
        try:
            FilterDesigner._orig_init_log_monkey(self)
        except Exception:
            pass

        if not hasattr(self, 'logger'):
            logger = logging.getLogger(f'filter_designer_fallback_{id(self)}')
            logger.setLevel(logging.INFO)
            if not logger.handlers:
                logger.addHandler(logging.NullHandler())
            self.logger = logger

    FilterDesigner.init_log = _patched_init_log
"""

    builtins.exec(patch_code, mod.__dict__)
    return mod
end

function patched_filterDesigner()
    mod = _patch_filterdesigner_logger!()
    app = mod.FilterDesigner()
    api = TyFilterDesigner.FilterDesignerAPI()
    TyFilterDesigner.setupapp(api, app)
    api.mod.show()
    return api
end
