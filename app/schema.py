from drf_spectacular.openapi import AutoSchema


class ModuleAwareAutoSchema(AutoSchema):
    def get_tags(self):
        explicit_tags = super().get_tags()
        if explicit_tags:
            return explicit_tags

        module_path = getattr(self.view, "__module__", "")
        module_root = module_path.split(".", 1)[0] if module_path else ""

        if module_root and module_root != "app":
            return [module_root.replace("_", " ").title()]

        return ["General"]
